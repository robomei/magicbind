
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

import nanobind

from magicbind.codegen import generate_from_header


SOURCE_SUFFIXES = (".cpp", ".cc", ".cxx")


def _find_zig() -> str | None:
    """Return the zig binary path from the ziglang pip package, or None."""
    try:
        import ziglang
        zig = Path(ziglang.__file__).parent / ("zig.exe" if sys.platform == "win32" else "zig")
        if zig.exists():
            return str(zig)
    except ImportError:
        pass
    return shutil.which("zig")


def find_compiler(system: bool = False) -> tuple[list[str], str]:
    """Return (compiler_cmd, kind) where kind is "unix" or "msvc".

    By default uses Zig (bundled via ziglang pip package).
    Pass system=True to prefer the system compiler instead.
    """
    if not system:
        zig = _find_zig()
        if zig:
            return [zig, "c++"], "unix"
        print("[magicbind] warning: ziglang not installed, falling back to system compiler", file=sys.stderr)

    # System compiler path
    if sys.platform == "win32":
        if cl := shutil.which("cl"):
            return [cl], "msvc"
        raise RuntimeError(
            "No C++ compiler found. Open a Visual Studio Developer Command Prompt "
            "or run vcvarsall.bat, then retry."
        )
    for name in ("g++", "c++", "clang++"):
        if path := shutil.which(name):
            return [path], "unix"
    raise RuntimeError(
        "No C++ compiler found. "
        + ("Install Xcode Command Line Tools: xcode-select --install"
           if sys.platform == "darwin"
           else "Install one with: sudo apt install g++")
    )


def ext_suffix() -> str:
    suffix = sysconfig.get_config_var("EXT_SUFFIX")
    if not suffix:
        raise RuntimeError("Unable to determine Python extension suffix")
    return suffix


def site_packages_dir() -> Path:
    platlib = sysconfig.get_paths().get("platlib")
    if not platlib:
        raise RuntimeError("Unable to determine site-packages directory")
    return Path(platlib)


def auto_sources(header: Path) -> list[Path]:
    matches: list[Path] = []
    for suffix in SOURCE_SUFFIXES:
        candidate = header.with_suffix(suffix)
        if candidate.exists():
            matches.append(candidate)
    return matches


def build_dir_for(module_name: str) -> Path:
    return Path(".magicbind") / "build" / module_name


def detect_robin_map_include() -> Path:
    return Path(nanobind.__file__).resolve().parent / "ext" / "robin_map" / "include"


def magicbind_include_dir() -> Path:
    return Path(__file__).resolve().parent / "include"


def python_include_dir() -> Path:
    include = sysconfig.get_paths().get("include")
    if not include:
        raise RuntimeError("Unable to determine Python include directory")
    return Path(include)


def _build_unix_cmd(
    compiler: list[str], sources: list[str], includes: list[str],
    flags: list[str], output: Path,
) -> list[str]:
    pic = sysconfig.get_config_var("CCSHARED") or ""
    link_mode = (
        ["-bundle", "-undefined", "dynamic_lookup"]
        if sys.platform == "darwin"
        else ["-shared"]
    )
    compile_flags = [f for f in flags if not f.startswith("-l")]
    link_flags    = [f for f in flags if f.startswith("-l")]
    return [
        *compiler,
        *link_mode,
        "-std=c++20", "-O3", *([pic] if pic else []),
        "-fvisibility=hidden", "-DNDEBUG", "-DNB_COMPACT_ASSERTIONS", "-w",
        *includes,
        *compile_flags,
        *sources,
        *link_flags,
        "-o", str(output),
    ]


def _build_msvc_cmd(
    compiler: list[str], sources: list[str], includes: list[str],
    flags: list[str], output: Path,
) -> list[str]:
    extra: list[str] = []
    lib_dirs: list[str] = []
    lib_names: list[str] = []
    i = 0
    while i < len(flags):
        f = flags[i]
        if f == "-I" and i + 1 < len(flags):
            extra += ["-I", flags[i + 1]]; i += 2
        elif f.startswith("-I"):
            extra.append(f); i += 1
        elif f == "-L" and i + 1 < len(flags):
            lib_dirs.append(flags[i + 1]); i += 2
        elif f.startswith("-L"):
            lib_dirs.append(f[2:]); i += 1
        elif f.startswith("-l"):
            lib_names.append(f[2:] + ".lib"); i += 1
        else:
            extra.append(f); i += 1
    return [
        *compiler,
        "/LD", "/std:c++20", "/O2", "/EHsc", "/MD",
        "/DNDEBUG", "/DNB_COMPACT_ASSERTIONS", "/W0", "/nologo",
        *includes,
        *extra,
        *sources,
        f"/Fe:{output}",
        f"/Fo:{output.parent}\\",
        "/link",
        f"/LIBPATH:{Path(sys.prefix) / 'libs'}",
        *[f"/LIBPATH:{d}" for d in lib_dirs],
        *lib_names,
    ]


def pkg_config_flags(packages: list[str]) -> list[str]:
    if not packages:
        return []
    pkg_config = shutil.which("pkg-config")
    if not pkg_config:
        hint = (
            "install it via MSYS2 (pacman -S mingw-w64-x86_64-pkg-config) or vcpkg"
            if sys.platform == "win32"
            else "install it or use --include/--lib instead"
        )
        raise RuntimeError(f"pkg-config not found — {hint}")
    result = subprocess.run(
        [pkg_config, "--cflags", "--libs", *packages],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pkg-config failed for {packages}:\n{result.stderr.strip()}")
    return result.stdout.split()


def _run_cmd(cmd: list[str]) -> None:
    print(f"[build] {' '.join(cmd)}")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def compile_extension(
    module_name: str,
    generated_cpp: Path,
    header: Path,
    sources: list[Path],
    output_path: Path,
    extra_flags: list[str] | None = None,
    system_compiler: bool = False,
) -> None:
    compiler, kind = find_compiler(system=system_compiler)
    flags = extra_flags or []
    nb_src = Path(nanobind.source_dir()) / "nb_combined.cpp"
    all_sources = [str(nb_src), str(generated_cpp), *[str(s) for s in sources]]
    includes = [
        "-I", str(nanobind.include_dir()),
        "-I", str(detect_robin_map_include()),
        "-I", str(python_include_dir()),
        "-I", str(magicbind_include_dir()),
        "-I", str(header.parent),
    ]
    build = _build_msvc_cmd if kind == "msvc" else _build_unix_cmd
    _run_cmd(build(compiler, all_sources, includes, flags, output_path))


def install_extension(built_path: Path, module_name: str) -> Path:
    destination = site_packages_dir() / f"{module_name}{ext_suffix()}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(built_path, destination)
    return destination


def add_command(args: argparse.Namespace) -> int:
    header = Path(args.header).resolve()
    if not header.exists():
        print(f"[error] header not found: {header}", file=sys.stderr)
        return 1

    module_name = args.module or header.stem
    sources = [Path(src).resolve() for src in args.source]
    if not sources:
        sources = auto_sources(header)

    build_dir = build_dir_for(module_name)
    build_dir.mkdir(parents=True, exist_ok=True)
    generated_cpp = build_dir / f"{module_name}.cpp"
    built_extension = build_dir / f"{module_name}{ext_suffix()}"

    extra_flags: list[str] = []
    extra_flags += pkg_config_flags(list(args.pkg))
    for path in args.include:
        extra_flags += ["-I", path]
    for path in args.lib:
        extra_flags += ["-L", path]
    for name in args.link:
        extra_flags += [f"-l{name}"]

    include_flags = [f for i, f in enumerate(extra_flags)
                     if f.startswith("-I") or (i > 0 and extra_flags[i - 1] == "-I")]

    print(f"[magicbind] generating bindings for {header}")
    code = generate_from_header(
        header=header,
        module_name=module_name,
        clang_args=list(args.clang_arg) + include_flags,
    )
    generated_cpp.write_text(code)
    print(f"[magicbind] wrote {generated_cpp}")

    if args.source:
        print("[magicbind] using sources:")
        for src in sources:
            print(f"  - {src}")
    elif sources:
        print("[magicbind] auto-detected companion sources:")
        for src in sources:
            print(f"  - {src}")
    else:
        print("[magicbind] header-only mode: no companion source files provided or detected")
        print("[magicbind] note: this works only when the header contains full definitions")

    compile_extension(
        module_name=module_name,
        generated_cpp=generated_cpp,
        header=header,
        sources=sources,
        output_path=built_extension,
        extra_flags=extra_flags,
        system_compiler=args.system_compiler,
    )

    installed_path = install_extension(built_extension, module_name)

    config = {
        "header": str(header),
        "sources": [str(s) for s in sources],
        "pkg": list(args.pkg),
        "include": list(args.include),
        "lib": list(args.lib),
        "link": list(args.link),
        "clang_arg": list(args.clang_arg),
        "module": module_name,
        "system_compiler": args.system_compiler,
    }
    (build_dir / "config.json").write_text(json.dumps(config, indent=2))

    print(f"[magicbind] installed {module_name} to {installed_path}")
    print(f"[magicbind] import with: import {module_name}")
    return 0


def build_command(args: argparse.Namespace) -> int:
    configs: list[Path] = []
    if args.module:
        module_name = Path(args.module).stem
        cfg = build_dir_for(module_name) / "config.json"
        if not cfg.exists():
            print(f"[error] no config for '{module_name}' — run magicbind add first", file=sys.stderr)
            return 1
        configs = [cfg]
    else:
        configs = sorted(Path(".magicbind/build").glob("*/config.json"))
        if not configs:
            print("[error] no modules found — run magicbind add first", file=sys.stderr)
            return 1

    for cfg in configs:
        c = json.loads(cfg.read_text())
        print(f"[magicbind] rebuilding {c['module']}...")

        ns = argparse.Namespace(
            header=c["header"],
            source=c["sources"],
            pkg=c["pkg"],
            include=c["include"],
            lib=c["lib"],
            link=c["link"],
            clang_arg=c["clang_arg"],
            module=c["module"],
            system_compiler=c.get("system_compiler", False),
        )
        result = add_command(ns)
        if result != 0:
            return result
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="magicbind")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser_ = subparsers.add_parser(
        "build",
        help="Rebuild a previously added module using its saved configuration",
    )
    build_parser_.add_argument(
        "module",
        nargs="?",
        help="Module name to rebuild (rebuilds all if omitted)",
    )
    build_parser_.set_defaults(func=build_command)

    add_parser = subparsers.add_parser(
        "add",
        help="Generate nanobind bindings, build the extension, and install it into site-packages",
    )
    add_parser.add_argument("header", help="Path to the header file")
    add_parser.add_argument("--module", help="Python module name (defaults to the header stem)")
    add_parser.add_argument(
        "--source",
        action="append",
        default=[],
        help="C++ source file to compile for non-header-only code. May be passed multiple times.",
    )
    add_parser.add_argument(
        "--clang-arg",
        action="append",
        default=[],
        help="Additional argument to pass to libclang while parsing the header. May be passed multiple times.",
    )
    add_parser.add_argument(
        "--pkg",
        action="append",
        default=[],
        metavar="NAME",
        help="pkg-config package name to resolve include and link flags (e.g. opencv4). May be passed multiple times.",
    )
    add_parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="DIR",
        help="Additional include directory. May be passed multiple times.",
    )
    add_parser.add_argument(
        "--lib",
        action="append",
        default=[],
        metavar="DIR",
        help="Additional library search directory. May be passed multiple times.",
    )
    add_parser.add_argument(
        "--link",
        action="append",
        default=[],
        metavar="NAME",
        help="Library name to link (e.g. opencv_core). May be passed multiple times.",
    )
    add_parser.add_argument(
        "--system-compiler",
        action="store_true",
        default=False,
        help="Use the system compiler (g++/clang++/cl.exe) instead of Zig. "
             "Required when linking against system C++ libraries (e.g. OpenCV).",
    )
    add_parser.set_defaults(func=add_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
