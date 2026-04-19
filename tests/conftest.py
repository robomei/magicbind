import subprocess
import sys
import textwrap
from pathlib import Path

import clang.cindex as cl
from magicbind.codegen import generate_from_header
from magicbind.header_parser import walk_tu


def parse_header(tmp_path: Path, source: str, extra_args: list[str] | None = None) -> object:
    """Write source to a temp header and return the parsed IRTU."""
    h = tmp_path / "test.h"
    h.write_text(textwrap.dedent(source))
    index = cl.Index.create()
    tu = index.parse(
        str(h),
        args=["-x", "c++-header", "-std=c++20", *(extra_args or [])],
        options=(
            cl.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            | cl.TranslationUnit.PARSE_SKIP_FUNCTION_BODIES
        ),
    )
    return walk_tu(tu.cursor, h)


def generate(tmp_path: Path, source: str, extra_args: list[str] | None = None) -> str:
    """Write source to a temp header and return the generated binding code."""
    h = tmp_path / "test.h"
    h.write_text(textwrap.dedent(source))
    return generate_from_header(h, module_name="test", clang_args=extra_args or [])

