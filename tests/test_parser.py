"""Tests for header_parser: IR produced from C++ headers."""
from pathlib import Path

import pytest

from .conftest import parse_header


def test_free_functions(tmp_path):
    ir = parse_header(tmp_path, """
        int add(int a, int b);
        double square(double x);
        void reset();
    """)
    names = [f.name for f in ir.functions]
    assert "add" in names
    assert "square" in names
    assert "reset" in names


def test_function_return_types(tmp_path):
    ir = parse_header(tmp_path, """
        int get_int();
        double get_double();
        void do_nothing();
    """)
    by_name = {f.name: f for f in ir.functions}
    assert by_name["get_int"].return_type == "int"
    assert by_name["get_double"].return_type == "double"
    assert by_name["do_nothing"].return_type == "void"


def test_function_params(tmp_path):
    ir = parse_header(tmp_path, """
        int add(int a, int b);
    """)
    fn = ir.functions[0]
    assert len(fn.params) == 2
    assert fn.params[0].name == "a"
    assert fn.params[0].type == "int"
    assert fn.params[1].name == "b"


def test_const_ref_param(tmp_path):
    ir = parse_header(tmp_path, """
        #include <string>
        void print(const std::string& s);
    """)
    fn = ir.functions[0]
    assert fn.params[0].is_const
    assert fn.params[0].is_ref


def test_overloaded_functions(tmp_path):
    ir = parse_header(tmp_path, """
        int clamp(int v, int lo, int hi);
        double clamp(double v, double lo, double hi);
    """)
    names = [f.name for f in ir.functions]
    assert names.count("clamp") == 2


def test_stl_includes_detected(tmp_path):
    ir = parse_header(tmp_path, """
        #include <string>
        #include <vector>
        #include <optional>
        #include <vector>
        void foo(const std::string& s);
    """)
    assert "nanobind/stl/string.h" in ir.stl_includes


def test_enum(tmp_path):
    ir = parse_header(tmp_path, """
        enum class Color { Red, Green, Blue };
    """)
    assert len(ir.enums) == 1
    e = ir.enums[0]
    assert e.name == "Color"
    value_names = [v.name for v in e.values]
    assert "Red" in value_names
    assert "Green" in value_names
    assert "Blue" in value_names


def test_struct(tmp_path):
    ir = parse_header(tmp_path, """
        struct Point {
            float x;
            float y;
        };
    """)
    assert len(ir.structs) == 1
    s = ir.structs[0]
    assert s.name == "Point"
    field_names = [f.name for f in s.fields]
    assert "x" in field_names
    assert "y" in field_names


def test_class_methods(tmp_path):
    ir = parse_header(tmp_path, """
        class Counter {
        public:
            Counter(int start);
            void increment();
            int value() const;
        };
    """)
    assert len(ir.classes) == 1
    cls = ir.classes[0]
    assert cls.name == "Counter"
    method_names = [m.name for m in cls.methods]
    assert "increment" in method_names
    assert "value" in method_names


def test_namespace(tmp_path):
    ir = parse_header(tmp_path, """
        namespace math {
            double pi();
            double e();
        }
    """)
    assert all(f.namespace == "math" for f in ir.functions)


def test_default_param_ignored(tmp_path):
    ir = parse_header(tmp_path, """
        int clamp(int v, int lo = 0, int hi = 100);
    """)
    assert len(ir.functions) == 1
    assert len(ir.functions[0].params) == 3
