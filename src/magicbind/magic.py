from __future__ import annotations

import importlib
import shutil
import sys
from pathlib import Path

from magicbind.cli import (
    build_dir_for,
    compile_extension,
    ext_suffix,
    install_extension,
)
from magicbind.codegen import generate_from_header


def magicbind(line: str, cell: str) -> None:
    """Compile a C++ cell as a Python extension module and inject it into the namespace."""
    from IPython import get_ipython
    from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

    @magic_arguments()
    @argument("module", help="Python module name for the compiled extension")
    @argument("--system-compiler", action="store_true", default=False,
              help="Use the system compiler instead of Zig")
    @argument("--include", action="append", default=[], metavar="DIR",
              help="Additional include directory")
    @argument("--link", action="append", default=[], metavar="NAME",
              help="Library name to link")
    @argument("--pkg", action="append", default=[], metavar="NAME",
              help="pkg-config package name")
    def _parser(): pass

    ip = get_ipython()
    args = parse_argstring(_parser, line)
    module_name = args.module

    # use a versioned internal name so the old .so is never unloaded
    old_versions = [k for k in sys.modules if k.startswith(f"_mb_{module_name}_v")]
    version = len(old_versions)
    internal_name = f"_mb_{module_name}_v{version}"

    # clean up old build dirs (the .so stays loaded in memory but we don't need the files)
    for old in old_versions:
        old_dir = build_dir_for(old)
        if old_dir.exists():
            shutil.rmtree(old_dir)

    build_dir = build_dir_for(internal_name)
    build_dir.mkdir(parents=True, exist_ok=True)

    # write cell to a temp header so libclang can parse it
    header = build_dir / f"{internal_name}.h"
    header.write_text(cell)

    extra_flags: list[str] = []
    extra_flags += [f"-DNB_DOMAIN={internal_name}"]
    for path in args.include:
        extra_flags += ["-I", path]
    for name in args.link:
        extra_flags += [f"-l{name}"]
    if args.pkg:
        from magicbind.cli import pkg_config_flags
        extra_flags += pkg_config_flags(args.pkg)

    include_flags = [f for i, f in enumerate(extra_flags)
                     if f.startswith("-I") or (i > 0 and extra_flags[i - 1] == "-I")]

    print(f"[magicbind] generating bindings for {module_name}...")
    code = generate_from_header(
        header=header,
        module_name=internal_name,
        clang_args=include_flags,
    )
    generated_cpp = build_dir / f"{internal_name}.cpp"
    generated_cpp.write_text(code)

    built_extension = build_dir / f"{internal_name}{ext_suffix()}"
    compile_extension(
        module_name=internal_name,
        generated_cpp=generated_cpp,
        header=header,
        sources=[],
        output_path=built_extension,
        extra_flags=extra_flags,
        system_compiler=args.system_compiler,
        verbose=False,
    )

    install_extension(built_extension, internal_name)

    module = importlib.import_module(internal_name)

    module.__name__ = module_name
    ip.push({module_name: module})
    print(f"[magicbind] '{module_name}' is ready")


def load_ipython_extension(ip) -> None:
    ip.register_magic_function(magicbind, magic_kind="cell")
