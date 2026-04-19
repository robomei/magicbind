"""Tests for codegen: generated binding code structure."""
import pytest

from .conftest import generate


def test_includes_nanobind(tmp_path):
    code = generate(tmp_path, "void foo();")
    assert '#include <nanobind/nanobind.h>' in code


def test_includes_stl_vector(tmp_path):
    code = generate(tmp_path, """
        #include <vector>
        void foo(const std::vector<int>& v);
    """)
    assert 'nanobind/stl/vector.h' in code


def test_includes_stl_optional(tmp_path):
    code = generate(tmp_path, """
        #include <optional>
        std::optional<int> maybe();
    """)
    assert 'nanobind/stl/optional.h' in code


def test_module_name(tmp_path):
    code = generate(tmp_path, "void foo();")
    assert 'NB_MODULE(test, m)' in code


def test_free_function_bound(tmp_path):
    code = generate(tmp_path, "int add(int a, int b);")
    assert 'm.def("add", &add)' in code


def test_overloads_use_overload_cast(tmp_path):
    code = generate(tmp_path, """
        int clamp(int v, int lo, int hi);
        double clamp(double v, double lo, double hi);
    """)
    assert 'nb::overload_cast' in code
    assert code.count('m.def("clamp"') == 2


def test_enum_bound(tmp_path):
    code = generate(tmp_path, """
        enum class Color { Red, Green, Blue };
    """)
    assert 'nb::enum_' in code
    assert '"Red"' in code
    assert '"Green"' in code
    assert '"Blue"' in code


def test_struct_bound(tmp_path):
    code = generate(tmp_path, """
        struct Point { float x; float y; };
    """)
    assert 'nb::class_' in code or 'nb::struct_' in code or '"Point"' in code


def test_opencv_header_included(tmp_path):
    code = generate(tmp_path, "void foo();")
    assert 'magicbind_opencv.h' in code


def test_no_binding_for_private_methods(tmp_path):
    code = generate(tmp_path, """
        class Foo {
        private:
            void secret();
        public:
            void visible();
        };
    """)
    assert '"visible"' in code
    assert '"secret"' not in code
