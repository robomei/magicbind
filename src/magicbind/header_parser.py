"""Parse a C/C++ header into an Intermediate Representation using libclang."""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from pathlib import Path
import clang.cindex as cl


@dataclass
class IRParam:
    name:     str
    type:     str
    is_const: bool = False
    is_ptr:   bool = False
    is_ref:   bool = False

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

@dataclass
class IRField:
    name:     str
    type:     str
    is_const: bool = False
    access:   str  = "public"

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

@dataclass
class IRStruct:
    name:      str
    namespace: str = ""
    comment:   str = ""
    cpp_type:  str = ""  # concrete C++ type for template instantiations
    fields:    list[IRField] = field(default_factory=list)

@dataclass
class IRTU:
    """Top-level translation unit."""
    source_file: str
    functions:   list[IRFunction] = field(default_factory=list)
    classes:     list[IRClass]    = field(default_factory=list)
    structs:     list[IRStruct]   = field(default_factory=list)
    enums:       list[IREnum]     = field(default_factory=list)


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
    )


def make_function(cursor: cl.Cursor, namespace: str = "") -> IRFunction:
    rt = cursor.result_type.spelling
    is_op = cursor.spelling.startswith("operator")
    params = []
    for c in cursor.get_children():
        if c.kind == cl.CursorKind.PARM_DECL:
            params.append(make_param(c))
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
            cls.constructors.append(make_function(c, namespace))
        elif c.kind in (cl.CursorKind.CXX_METHOD, cl.CursorKind.DESTRUCTOR):
            cls.methods.append(make_function(c, namespace))
        elif c.kind == cl.CursorKind.FIELD_DECL:
            ts = c.type.spelling
            cls.fields.append(IRField(
                name=c.spelling,
                type=ts,
                is_const=ts.startswith("const "),
                access=access.name.lower(),
            ))
    return cls


def collect_struct(cursor: cl.Cursor, namespace: str) -> IRStruct:
    st = IRStruct(name=cursor.spelling, namespace=namespace, comment=cursor.brief_comment or "")
    for c in cursor.get_children():
        if c.kind == cl.CursorKind.FIELD_DECL:
            ts = c.type.spelling
            st.fields.append(IRField(
                name=c.spelling,
                type=ts,
                is_const=ts.startswith("const "),
            ))
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
                tu.classes.append(collect_class(cursor, namespace, header))

        elif kind == cl.CursorKind.STRUCT_DECL:
            usr = cursor.get_usr()
            if cursor.is_definition() and cursor.spelling and usr not in seen_usrs:
                seen_usrs.add(usr)
                tu.structs.append(collect_struct(cursor, namespace))

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
            tu.functions.append(make_function(cursor, namespace))

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
                    p.type     = _substitute(p.type, subst)
                    p.is_const = p.type.startswith("const ")
            for f in cls.fields:
                f.type     = _substitute(f.type, subst)
                f.is_const = f.type.startswith("const ")

        tu.classes.append(cls)

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
        elif decl.kind == cl.CursorKind.STRUCT_DECL and decl.is_definition():
            usr = decl.get_usr()
            if usr not in seen_usrs:
                seen_usrs.add(usr)
                st = collect_struct(decl, namespace)
                st.name = cursor.spelling
                tu.structs.append(st)
        else:
            for child in cursor.get_children():
                visit(child, namespace)

    for child in cursor.get_children():
        visit(child, namespace)

    return tu
