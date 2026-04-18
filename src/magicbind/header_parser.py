"""Parse a C/C++ header into an Intermediate Representation using libclang."""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
import clang.cindex as cl


STL_INCLUDE_MAP: dict[str, str] = {
    "std::string":        "nanobind/stl/string.h",
    "std::string_view":   "nanobind/stl/string_view.h",
    "std::vector":        "nanobind/stl/vector.h",
    "std::list":          "nanobind/stl/list.h",
    "std::map":           "nanobind/stl/map.h",
    "std::unordered_map": "nanobind/stl/unordered_map.h",
    "std::set":           "nanobind/stl/set.h",
    "std::unordered_set": "nanobind/stl/unordered_set.h",
    "std::optional":      "nanobind/stl/optional.h",
    "std::variant":       "nanobind/stl/variant.h",
    "std::pair":          "nanobind/stl/pair.h",
    "std::tuple":         "nanobind/stl/tuple.h",
    "std::function":      "nanobind/stl/function.h",
    "std::filesystem":    "nanobind/stl/filesystem.h",
    "std::shared_ptr":    "nanobind/stl/shared_ptr.h",
    "std::unique_ptr":    "nanobind/stl/unique_ptr.h",
}

def detect_stl_includes(type_str: str) -> list[str]:
    normalized = type_str.replace("std::__1::", "std::").replace("std::__cxx11::", "std::")
    return [inc for prefix, inc in STL_INCLUDE_MAP.items() if prefix in normalized]


@dataclass
class IRParam:
    name:         str
    type:         str
    is_const:     bool = False
    is_ptr:       bool = False
    is_ref:       bool = False
    stl_includes: list[str] = field(default_factory=list)

@dataclass
class IRFunction:
    name:         str
    return_type:  str
    params:       list[IRParam]
    comment:      str = ""
    namespace:    str = ""
    is_static:    bool = False
    is_const:     bool = False
    is_operator:  bool = False
    operator_sym: str = ""
    stl_includes: list[str] = field(default_factory=list)

@dataclass
class IRField:
    name:         str
    type:         str
    is_const:     bool = False
    access:       str  = "public"
    stl_includes: list[str] = field(default_factory=list)

@dataclass
class IREnumValue:
    name:  str
    value: int

@dataclass
class IREnum:
    name:      str
    values:    list[IREnumValue]
    namespace: str = ""
    comment:   str = ""

@dataclass
class IRClass:
    name:         str
    namespace:    str = ""
    comment:      str = ""
    cpp_type:     str = ""  # concrete C++ type for template instantiations, e.g. "Stack<int>"
    constructors: list[IRFunction] = field(default_factory=list)
    methods:      list[IRFunction] = field(default_factory=list)
    fields:       list[IRField]    = field(default_factory=list)
    stl_includes: list[str]        = field(default_factory=list)

@dataclass
class IRStruct:
    name:         str
    namespace:    str = ""
    comment:      str = ""
    cpp_type:     str = ""  # concrete C++ type for template instantiations
    fields:       list[IRField] = field(default_factory=list)
    stl_includes: list[str]     = field(default_factory=list)

@dataclass
class IRTU:
    """Top-level translation unit."""
    source_file:  str
    functions:    list[IRFunction] = field(default_factory=list)
    classes:      list[IRClass]    = field(default_factory=list)
    structs:      list[IRStruct]   = field(default_factory=list)
    enums:        list[IREnum]     = field(default_factory=list)
    stl_includes: list[str]        = field(default_factory=list)


def _substitute(type_str: str, subst: dict[str, str]) -> str:
    """Replace template parameter names with their concrete types (word-boundary aware)."""
    for param, concrete in subst.items():
        type_str = re.sub(r"\b" + re.escape(param) + r"\b", concrete, type_str)
    return type_str


OPERATOR_MAP: dict[str, str] = {
    "operator*":  "__mul__",
    "operator+":  "__add__",
    "operator-":  "__sub__",
    "operator/":  "__truediv__",
    "operator==": "__eq__",
    "operator!=": "__ne__",
    "operator<":  "__lt__",
    "operator>":  "__gt__",
    "operator[]": "__getitem__",
    "operator()": "__call__",
}


def make_param(cursor: cl.Cursor) -> IRParam:
    ts = cursor.type.spelling
    return IRParam(
        name=cursor.spelling or "_",
        type=ts,
        is_const=ts.startswith("const "),
        is_ptr="*" in ts,
        is_ref="&" in ts,
        stl_includes=detect_stl_includes(ts),
    )


def make_function(cursor: cl.Cursor, namespace: str = "") -> IRFunction:
    rt = cursor.result_type.spelling
    is_op = cursor.spelling.startswith("operator")
    stl = detect_stl_includes(rt)
    params = []
    for c in cursor.get_children():
        if c.kind == cl.CursorKind.PARM_DECL:
            p = make_param(c)
            stl += p.stl_includes
            params.append(p)
    return IRFunction(
        name=cursor.spelling,
        return_type=rt,
        params=params,
        comment=cursor.brief_comment or "",
        namespace=namespace,
        is_static=cursor.is_static_method() if hasattr(cursor, "is_static_method") else False,
        is_const=cursor.is_const_method() if hasattr(cursor, "is_const_method") else False,
        is_operator=is_op,
        operator_sym=OPERATOR_MAP.get(cursor.spelling, "") if is_op else "",
        stl_includes=list(dict.fromkeys(stl)),
    )


def collect_class(cursor: cl.Cursor, namespace: str, header: Path) -> IRClass:
    cls = IRClass(name=cursor.spelling, namespace=namespace, comment=cursor.brief_comment or "")
    for c in cursor.get_children():
        if not c.location.file:
            continue
        access = c.access_specifier
        if access == cl.AccessSpecifier.PRIVATE:
            continue
        if c.kind == cl.CursorKind.CONSTRUCTOR:
            fn = make_function(c, namespace)
            cls.constructors.append(fn)
            cls.stl_includes += fn.stl_includes
        elif c.kind in (cl.CursorKind.CXX_METHOD, cl.CursorKind.DESTRUCTOR):
            fn = make_function(c, namespace)
            cls.methods.append(fn)
            cls.stl_includes += fn.stl_includes
        elif c.kind == cl.CursorKind.FIELD_DECL:
            ts = c.type.spelling
            f = IRField(
                name=c.spelling,
                type=ts,
                is_const=ts.startswith("const "),
                access=access.name.lower(),
                stl_includes=detect_stl_includes(ts),
            )
            cls.fields.append(f)
            cls.stl_includes += f.stl_includes
    cls.stl_includes = list(dict.fromkeys(cls.stl_includes))
    return cls


def collect_struct(cursor: cl.Cursor, namespace: str) -> IRStruct:
    st = IRStruct(name=cursor.spelling, namespace=namespace, comment=cursor.brief_comment or "")
    for c in cursor.get_children():
        if c.kind == cl.CursorKind.FIELD_DECL:
            ts = c.type.spelling
            f = IRField(
                name=c.spelling,
                type=ts,
                is_const=ts.startswith("const "),
                stl_includes=detect_stl_includes(ts),
            )
            st.fields.append(f)
            st.stl_includes += f.stl_includes
    st.stl_includes = list(dict.fromkeys(st.stl_includes))
    return st


def collect_enum(cursor: cl.Cursor, namespace: str) -> IREnum:
    values = [
        IREnumValue(name=c.spelling, value=c.enum_value)
        for c in cursor.get_children()
        if c.kind == cl.CursorKind.ENUM_CONSTANT_DECL
    ]
    return IREnum(name=cursor.spelling, values=values, namespace=namespace, comment=cursor.brief_comment or "")


def walk_tu(cursor: cl.Cursor, header: Path, namespace: str = "") -> IRTU:
    tu = IRTU(source_file=str(header))

    # C typedef'd structs/enums produce two cursors (anonymous STRUCT_DECL + TYPEDEF_DECL).
    # Track USR so we visit only via TYPEDEF_DECL and skip the bare STRUCT_DECL.
    seen_usrs: set[str] = set()

    def visit(cursor: cl.Cursor, namespace: str) -> None:
        loc = cursor.location
        if loc.file and Path(loc.file.name).resolve() != header.resolve():
            return

        kind = cursor.kind

        if kind == cl.CursorKind.NAMESPACE:
            ns = f"{namespace}::{cursor.spelling}" if namespace else cursor.spelling
            for child in cursor.get_children():
                visit(child, ns)

        elif kind == cl.CursorKind.CLASS_DECL:
            if cursor.is_definition() and cursor.get_usr() not in seen_usrs:
                seen_usrs.add(cursor.get_usr())
                cls = collect_class(cursor, namespace, header)
                tu.classes.append(cls)
                tu.stl_includes += cls.stl_includes

        elif kind == cl.CursorKind.STRUCT_DECL:
            usr = cursor.get_usr()
            if cursor.is_definition() and cursor.spelling and usr not in seen_usrs:
                seen_usrs.add(usr)
                st = collect_struct(cursor, namespace)
                tu.structs.append(st)
                tu.stl_includes += st.stl_includes

        elif kind == cl.CursorKind.TYPE_ALIAS_DECL:
            _collect_alias(cursor, namespace)

        elif kind == cl.CursorKind.TYPEDEF_DECL:
            underlying = cursor.underlying_typedef_type.get_declaration()
            usr = underlying.get_usr()
            if underlying.kind == cl.CursorKind.STRUCT_DECL and underlying.is_definition():
                seen_usrs.add(usr)
                st = collect_struct(underlying, namespace)
                st.name = cursor.spelling
                tu.structs.append(st)
                tu.stl_includes += st.stl_includes
            elif underlying.kind == cl.CursorKind.ENUM_DECL and underlying.is_definition():
                seen_usrs.add(usr)
                en = collect_enum(underlying, namespace)
                en.name = cursor.spelling
                tu.enums.append(en)
            elif underlying.kind == cl.CursorKind.CLASS_TEMPLATE and underlying.is_definition():
                _collect_template_instance(cursor.spelling, cursor.underlying_typedef_type, underlying, namespace)
            elif (tmpl := _find_template_cursor(cursor)):
                _collect_template_instance(cursor.spelling, cursor.underlying_typedef_type, tmpl, namespace)
            else:
                for child in cursor.get_children():
                    visit(child, namespace)

        elif kind == cl.CursorKind.ENUM_DECL:
            usr = cursor.get_usr()
            if cursor.is_definition() and cursor.spelling and usr not in seen_usrs:
                seen_usrs.add(usr)
                tu.enums.append(collect_enum(cursor, namespace))

        elif kind == cl.CursorKind.FUNCTION_DECL:
            if cursor.is_definition():
                return
            fn = make_function(cursor, namespace)
            tu.functions.append(fn)
            tu.stl_includes += fn.stl_includes

        else:
            for child in cursor.get_children():
                visit(child, namespace)

    def _collect_template_instance(
        alias: str, underlying_type: cl.Type, template_cursor: cl.Cursor, namespace: str
    ) -> None:
        cpp_type    = underlying_type.spelling
        param_names = [c.spelling for c in template_cursor.get_children()
                       if c.kind == cl.CursorKind.TEMPLATE_TYPE_PARAMETER]
        concrete    = [underlying_type.get_template_argument_type(i).spelling
                       for i in range(underlying_type.get_num_template_arguments())]
        subst       = dict(zip(param_names, concrete))

        cls = collect_class(template_cursor, namespace, header)
        cls.name     = alias
        cls.cpp_type = cpp_type

        if subst:
            for fn in [*cls.constructors, *cls.methods]:
                fn.return_type = _substitute(fn.return_type, subst)
                for p in fn.params:
                    p.type        = _substitute(p.type, subst)
                    p.is_const    = p.type.startswith("const ")
                    p.stl_includes = detect_stl_includes(p.type)
            for f in cls.fields:
                f.type        = _substitute(f.type, subst)
                f.is_const    = f.type.startswith("const ")
                f.stl_includes = detect_stl_includes(f.type)

        cls.stl_includes = list(dict.fromkeys(
            inc
            for src in [*cls.constructors, *cls.methods]
            for p in src.params
            for inc in p.stl_includes
        ) | dict.fromkeys(detect_stl_includes(cpp_type)))

        tu.classes.append(cls)
        tu.stl_includes += cls.stl_includes

    def _find_template_cursor(cursor: cl.Cursor) -> cl.Cursor | None:
        """Return the CLASS_TEMPLATE cursor referenced by a TYPE_ALIAS_DECL/TYPEDEF_DECL, if any."""
        for child in cursor.get_children():
            if child.kind == cl.CursorKind.TEMPLATE_REF:
                ref = child.referenced
                if ref.kind == cl.CursorKind.CLASS_TEMPLATE and ref.is_definition():
                    return ref
        return None

    def _collect_alias(cursor: cl.Cursor, namespace: str) -> None:
        underlying_type = cursor.underlying_typedef_type
        decl = underlying_type.get_declaration()

        if decl.kind == cl.CursorKind.CLASS_TEMPLATE and decl.is_definition():
            _collect_template_instance(cursor.spelling, underlying_type, decl, namespace)
            return

        template_cursor = _find_template_cursor(cursor)
        if template_cursor:
            _collect_template_instance(cursor.spelling, underlying_type, template_cursor, namespace)
            return

        if decl.kind == cl.CursorKind.CLASS_DECL and decl.is_definition():
            usr = decl.get_usr()
            if usr not in seen_usrs:
                seen_usrs.add(usr)
                cls = collect_class(decl, namespace, header)
                cls.name = cursor.spelling
                tu.classes.append(cls)
                tu.stl_includes += cls.stl_includes
        elif decl.kind == cl.CursorKind.STRUCT_DECL and decl.is_definition():
            usr = decl.get_usr()
            if usr not in seen_usrs:
                seen_usrs.add(usr)
                st = collect_struct(decl, namespace)
                st.name = cursor.spelling
                tu.structs.append(st)
                tu.stl_includes += st.stl_includes
        else:
            for child in cursor.get_children():
                visit(child, namespace)

    for child in cursor.get_children():
        visit(child, namespace)

    tu.stl_includes = list(dict.fromkeys(tu.stl_includes))
    return tu

