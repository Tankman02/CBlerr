import sys
import os
import subprocess
import tempfile
import platform
from pathlib import Path
from typing import List, Optional, Tuple, Dict

DERR_FLAG = False
SAVE_C_FLAG = False

def _extract_cli_flags():
    global DERR_FLAG, SAVE_C_FLAG
    argv = sys.argv
    new_argv = [argv[0]] if argv else []
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '-derr':
            DERR_FLAG = True
            i += 1
            continue
        if a == '-c':
            SAVE_C_FLAG = True
            i += 1
            continue
        new_argv.append(a)
        i += 1
    if len(new_argv) != len(argv):
        sys.argv[:] = new_argv

_extract_cli_flags()

core_path = Path(__file__).parent.parent / "core"
if getattr(sys, 'frozen', False):
    try:
        meipass = Path(sys._MEIPASS)
        core_path = meipass / "core"
        sys.path.insert(0, str(meipass.resolve()))
    except Exception:
        core_path = Path(__file__).parent.parent / "core"
        sys.path.insert(0, str(core_path.parent.resolve()))
else:
    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

import importlib
try:
    for _name in ("lexer", "flux_parser", "flux_ast"):
        try:
            core_mod = importlib.import_module(f"core.{_name}")
            sys.modules[_name] = core_mod
        except Exception:
            pass
except Exception:
    pass

from core.lexer import tokenize, TokenType
from core.flux_parser import parse
from core.flux_ast import (
    Program, FunctionDef, Return, BinaryOp, Variable, Literal,
    IfStmt, Assign, Compare, Call, WhileLoop, BreakStmt, ContinueStmt,
    StructDef, FieldAccess, ArrayAccess, ArrayLiteral, LogicalOp,
    PointerType, Dereference, InlineAsm, CastExpr, Decorator, ComptimeBlock
)
from core.flux_ast import MatchStmt, Case, ForLoop, EnumDef, AddressOf, SizeOf
from core.debugger import init_debugger, get_debugger, DebugLevel
# from core.type_checker import TypeChecker, SemanticError

class CCodeGenerator:
    def __init__(self, module_name: str = "cblerr_module"):
        self.module_name = module_name
        self.code_lines = []
        self.indent_level = 0
        self.struct_definitions = {}
        self.function_declarations = {}
        self.global_vars = {}
        self.string_constants = {}
        self.current_function = None
        self.break_stack = []
        self.continue_stack = []
        self.string_counter = 0
        self.local_vars_stack = []

    def generate(self, program: Program) -> str:
        self.emit_line("#include <stdio.h>")
        self.emit_line("#include <stdlib.h>")
        self.emit_line("#include <string.h>")
        self.emit_line("#include <stdint.h>")
        self.emit_line("#include <stdbool.h>")
        self.emit_line("#if defined(__has_include)")
        self.emit_line("#  if __has_include(<ncurses.h>)")
        self.emit_line("#    include <ncurses.h>")
        self.emit_line("#  elif __has_include(<curses.h>)")
        self.emit_line("#    include <curses.h>")
        self.emit_line("#  endif")
        self.emit_line("#else")
        self.emit_line("#  include <curses.h>")
        self.emit_line("#endif")
        self.emit_line("")
        self.emit_line("typedef struct { const char* data; int64_t length; } flux_string;")
        self.emit_line("")
        if program.structs:
            for struct_def in program.structs:
                if isinstance(struct_def, EnumDef):
                    continue
                self.emit_line(f"struct {struct_def.name};")
            self.emit_line("")
        if program.structs:
            for struct_def in program.structs:
                if isinstance(struct_def, EnumDef):
                    self.generate_enum(struct_def)
                else:
                    self.generate_struct_def(struct_def)
            self.emit_line("")
        if program.global_vars:
            for global_var in program.global_vars:
                self.generate_global_var(global_var)
            self.emit_line("")
        if program.functions:
            skip_std = {'malloc', 'free', 'memset', 'memcpy', 'printf', 'puts', 'putchar', 'scanf', 'exit',
                        'fopen', 'fgetc', 'feof', 'fclose', 'fputc', 'system'}
            for func_def in program.functions:
                if hasattr(func_def, 'is_extern') and func_def.is_extern:
                    if func_def.name in skip_std:
                        continue
                    sig = self.generate_function_signature(func_def)
                    self.emit_line(f"{sig};")
            for func_def in program.functions:
                if hasattr(func_def, 'is_extern') and func_def.is_extern:
                    continue
                sig = self.generate_function_signature(func_def)
                self.emit_line(f"{sig};")
            has_forwardes = any(
                not (hasattr(f, 'is_extern') and f.is_extern) for f in program.functions
            )
            if has_forwardes:
                self.emit_line("")
        if program.functions:
            for func_def in program.functions:
                if hasattr(func_def, 'is_extern') and func_def.is_extern:
                    continue
                self.generate_function_def(func_def)
                self.emit_line("")
        return "\n".join(self.code_lines)

    def emit_line(self, line: str = ""):
        if line:
            self.code_lines.append("    " * self.indent_level + line)
        else:
            self.code_lines.append("")

    def emit_block(self, lines: List[str]):
        for line in lines:
            self.emit_line(line)

    def _escape_string(self, s: str) -> str:
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        s = s.replace('\n', '\\n')
        s = s.replace('\r', '\\r')
        s = s.replace('\t', '\\t')
        return s

    def _emit_die_helper(self):
        return

    def generate_struct_def(self, struct_def):
        self.emit_line(f"struct {struct_def.name} {{")
        self.indent_level += 1
        if isinstance(struct_def.fields, dict):
            fields_items = struct_def.fields.items()
        else:
            fields_items = struct_def.fields
        for item in fields_items:
            if isinstance(item, tuple):
                field_name, field_type = item
            else:
                continue
            c_type = self.get_c_type(field_type)
            self.emit_line(f"{c_type} {field_name};")
        self.indent_level -= 1
        self.emit_line("};")

    def generate_global_var(self, global_var):
        c_type = self.get_c_type(global_var.var_type)
        if hasattr(global_var, 'var_type') and hasattr(global_var.var_type, 'name') and getattr(global_var.var_type, 'name', None) == 'array':
            inner = global_var.var_type.args[0] if getattr(global_var.var_type, 'args', None) else 'int'
            inner_c = self.get_c_type(inner)
            c_type = f"{inner_c}[]"
        self.global_vars[global_var.name] = global_var
        if hasattr(global_var, 'value') and global_var.value:
            value_code = self.generate_expression(global_var.value)
            if isinstance(c_type, str) and c_type.endswith('[]'):
                inner = c_type[:-2]
                self.emit_line(f"{inner} {global_var.name}[] = {value_code};")
            else:
                self.emit_line(f"{c_type} {global_var.name} = {value_code};")
        else:
            if isinstance(c_type, str) and c_type.endswith('[]'):
                inner = c_type[:-2]
                self.emit_line(f"{inner} {global_var.name}[];")
            else:
                self.emit_line(f"{c_type} {global_var.name};")

    def generate_function_signature(self, func_def) -> str:
        return_type = self.get_c_type(func_def.return_type)
        params = []
        if func_def.params:
            for param_tuple in func_def.params:
                if isinstance(param_tuple, tuple) and len(param_tuple) >= 2:
                    param_name, param_type = param_tuple[0], param_tuple[1]
                    param_c_type = self.get_c_type(param_type)
                    params.append(f"{param_c_type} {param_name}")
        params_str = ", ".join(params) if params else "void"
        return f"{return_type} {func_def.name}({params_str})"

    def generate_function_def(self, func_def):
        sig = self.generate_function_signature(func_def)
        if hasattr(func_def, 'is_extern') and func_def.is_extern:
            self.emit_line(f"{sig};")
            return
        
        self.emit_line(f"{sig} {{")
        self.indent_level += 1
        self.current_function = func_def.name
        self.local_vars_stack.append({})

        if func_def.params:
            for param_tuple in func_def.params:
                if isinstance(param_tuple, tuple) and len(param_tuple) >= 2:
                    pname, ptype = param_tuple[0], param_tuple[1]
                    try:
                        p_c = self.get_c_type(ptype)
                    except Exception:
                        p_c = None
                    if p_c:
                        self.local_vars_stack[-1][pname] = p_c

        if func_def.body:
            for stmt in func_def.body:
                self.generate_statement(stmt)
        if func_def.return_type != 'void' and func_def.return_type != None:
            if func_def.return_type in ['int', 'i32', 'int32']:
                self.emit_line("return 0;")
            else:
                self.emit_line(f"return ({self.get_c_type(func_def.return_type)})0;")
        self.indent_level -= 1
        self.emit_line("}")
        if self.local_vars_stack:
            self.local_vars_stack.pop()

    def generate_statement(self, stmt):
        if isinstance(stmt, Return):
            self.generate_return(stmt)
        elif isinstance(stmt, Assign):
            self.generate_assign(stmt)
        elif isinstance(stmt, IfStmt):
            self.generate_if(stmt)
        elif isinstance(stmt, WhileLoop):
            self.generate_while(stmt)
        elif isinstance(stmt, ForLoop):
            self.generate_for(stmt)
        elif isinstance(stmt, MatchStmt):
            self.generate_match(stmt)
        elif isinstance(stmt, EnumDef):
            self.generate_enum(stmt)
        elif isinstance(stmt, BreakStmt):
            self.emit_line("break;")
        elif isinstance(stmt, ContinueStmt):
            self.emit_line("continue;")
        elif isinstance(stmt, Call):
            expr = self.generate_expression(stmt)
            self.emit_line(f"{expr};")
        else:
            expr_code = self.generate_expression(stmt)
            if expr_code and expr_code != "0":
                self.emit_line(f"{expr_code};")

    def generate_return(self, ret_stmt):
        if ret_stmt.value:
            value_code = self.generate_expression(ret_stmt.value)
            self.emit_line(f"return {value_code};")
        else:
            self.emit_line("return;")

    def generate_assign(self, assign_stmt):
        if isinstance(assign_stmt.target, str):
            target = assign_stmt.target
            value = self.generate_expression(assign_stmt.value)
            if hasattr(assign_stmt, 'var_type') and assign_stmt.var_type:
                c_type = self.get_c_type(assign_stmt.var_type)
                self.emit_line(f"{c_type} {target} = {value};")
                if self.local_vars_stack:
                    self.local_vars_stack[-1][target] = c_type
            else:
                self.emit_line(f"{target} = {value};")
        else:
            target = self.generate_expression(assign_stmt.target)
            value = self.generate_expression(assign_stmt.value)
            self.emit_line(f"{target} = {value};")

    def generate_if(self, if_stmt):
        condition = self.generate_expression(if_stmt.condition)
        self.emit_line(f"if ({condition}) {{")
        self.indent_level += 1
        for stmt in if_stmt.then_body:
            self.generate_statement(stmt)
        self.indent_level -= 1
        if if_stmt.else_body:
            self.emit_line("} else {")
            self.indent_level += 1
            for stmt in if_stmt.else_body:
                self.generate_statement(stmt)
            self.indent_level -= 1
            self.emit_line("}")
        else:
            self.emit_line("}")

    def generate_while(self, while_stmt):
        condition = self.generate_expression(while_stmt.condition)
        self.emit_line(f"while ({condition}) {{")
        self.indent_level += 1
        for stmt in while_stmt.body:
            self.generate_statement(stmt)
        self.indent_level -= 1
        self.emit_line("}")

    def generate_for(self, for_stmt: ForLoop):
        if for_stmt.init or for_stmt.condition or for_stmt.post:
            init_code = ""
            if for_stmt.init:
                if isinstance(for_stmt.init, Assign):
                    if hasattr(for_stmt.init, 'var_type') and for_stmt.init.var_type:
                        ctype = self.get_c_type(for_stmt.init.var_type)
                        val = self.generate_expression(for_stmt.init.value)
                        init_code = f"{ctype} {for_stmt.init.target} = {val}"
                    else:
                        init_code = f"{for_stmt.init.target} = {self.generate_expression(for_stmt.init.value)}"
                else:
                    init_code = self.generate_expression(for_stmt.init)
            cond_code = self.generate_expression(for_stmt.condition) if for_stmt.condition else "1"
            post_code = self.generate_expression(for_stmt.post) if for_stmt.post else ""
            self.emit_line(f"for ({init_code}; {cond_code}; {post_code}) {{")
            self.indent_level += 1
            for stmt in for_stmt.body:
                self.generate_statement(stmt)
            self.indent_level -= 1
            self.emit_line("}")
            return

        if for_stmt.iter_var and for_stmt.iter_expr:
            ie = for_stmt.iter_expr
            if isinstance(ie, Call) and ie.func_name == 'range' and len(ie.args) >= 2:
                start = self.generate_expression(ie.args[0])
                end = self.generate_expression(ie.args[1])
                self.emit_line(f"for (int {for_stmt.iter_var} = {start}; {for_stmt.iter_var} < {end}; ++{for_stmt.iter_var}) {{")
                self.indent_level += 1
                for stmt in for_stmt.body:
                    self.generate_statement(stmt)
                self.indent_level -= 1
                self.emit_line("}")
                return

            iter_resolved = getattr(ie, 'resolved_type', None)
            if isinstance(ie, Variable) and iter_resolved and isinstance(iter_resolved, str) and iter_resolved.startswith('array<'):
                inner = iter_resolved[len('array<'):-1]
                elem_c = self.get_c_type(inner)
                arr_name = self.generate_expression(ie)
                idx_name = f"__idx_{for_stmt.iter_var}"
                len_expr = f"(sizeof({arr_name})/sizeof({arr_name}[0]))"
                self.emit_line(f"for (int {idx_name} = 0; {idx_name} < {len_expr}; ++{idx_name}) {{")
                self.indent_level += 1
                self.emit_line(f"{elem_c} {for_stmt.iter_var} = {arr_name}[{idx_name}];")
                for stmt in for_stmt.body:
                    self.generate_statement(stmt)
                self.indent_level -= 1
                self.emit_line("}")
                return

            self.emit_line(f"// Unsupported iterator-style for; falling back to block for {for_stmt.iter_var}")
            self.emit_line("{")
            self.indent_level += 1
            self.emit_line("TODO: implement generic iteration")
            for stmt in for_stmt.body:
                self.generate_statement(stmt)
            self.indent_level -= 1
            self.emit_line("}")

    def generate_match(self, match_stmt: MatchStmt):
        expr_code = self.generate_expression(match_stmt.expr)
        expr_type = getattr(match_stmt.expr, 'resolved_type', None)
        first = True
        for case in match_stmt.cases:
            if case.values is None:
                # default
                if first:
                    self.emit_line("if (1) {")
                else:
                    self.emit_line("else {")
                self.indent_level += 1
                for stmt in case.body:
                    self.generate_statement(stmt)
                self.indent_level -= 1
                self.emit_line("}")
                first = False
                continue

            conds = []
            for v in case.values:
                vcode = self.generate_expression(v)
                if expr_type == 'str' or getattr(v, 'resolved_type', None) == 'str':
                    conds.append(f"(strcmp({expr_code}.data, {vcode}.data) == 0)")
                else:
                    conds.append(f"({expr_code} == {vcode})")
            cond_code = " || ".join(conds)
            if first:
                self.emit_line(f"if ({cond_code}) {{")
            else:
                self.emit_line(f"else if ({cond_code}) {{")
            self.indent_level += 1
            for stmt in case.body:
                self.generate_statement(stmt)
            self.indent_level -= 1
            self.emit_line("}")
            first = False

    def generate_enum(self, enum_def: EnumDef):
        self.emit_line(f"typedef enum {{")
        self.indent_level += 1
        members_lines = []
        for name, val in enum_def.members:
            if val is not None:
                vcode = self.generate_expression(val)
                members_lines.append(f"{name} = {vcode},")
            else:
                members_lines.append(f"{name},")
        for line in members_lines:
            self.emit_line(line)
        self.indent_level -= 1
        self.emit_line(f"}} {enum_def.name};")
    
    def generate_expression(self, expr) -> str:
        if expr is None:
            return "0"
        
        if isinstance(expr, Literal):
            if isinstance(expr.value, str):
                escaped = self._escape_string(expr.value)
                length = len(expr.value)
                return f'(flux_string){{"{escaped}", {length}}}'
            elif isinstance(expr.value, float):
                return str(expr.value)
            elif isinstance(expr.value, bool):
                return "true" if expr.value else "false"
            else:
                return str(expr.value)
        
        elif isinstance(expr, Variable):
            return expr.name
        
        elif isinstance(expr, BinaryOp):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            op_map = {
                '+': '+', '-': '-', '*': '*', '/': '/',
                '%': '%', '&': '&', '|': '|', '^': '^',
                '<<': '<<', '>>': '>>'
            }
            op = op_map.get(expr.op, expr.op)
            return f"({left} {op} {right})"
        
        elif isinstance(expr, Compare):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            left_t = getattr(expr.left, 'resolved_type', None)
            right_t = getattr(expr.right, 'resolved_type', None)
            if left_t == 'str' or right_t == 'str':
                cmp_map = {
                    '==': '== 0',
                    '!=': '!= 0',
                    '<': '< 0',
                    '>': '> 0',
                    '<=': '<= 0',
                    '>=': '>= 0'
                }
                suffix = cmp_map.get(expr.op, f"== 0")
                return f"(strcmp({left}.data, {right}.data) {suffix})"
            else:
                op_map = {
                    '<': '<', '>': '>', '<=': '<=', '>=': '>=',
                    '==': '==', '!=': '!='
                }
                op = op_map.get(expr.op, expr.op)
                return f"({left} {op} {right})"
        
        elif isinstance(expr, LogicalOp):
            left = self.generate_expression(expr.left)
            right = self.generate_expression(expr.right)
            op = '&&' if expr.op == 'and' else '||'
            return f"({left} {op} {right})"
        
        elif isinstance(expr, Call):
            if expr.func_name == 'print':
                return self._generate_print_call(expr)
            if expr.func_name == 'len':
                if not expr.args or len(expr.args) != 1:
                    return '0'
                a = expr.args[0]
                a_code = self.generate_expression(a)
                a_t = getattr(a, 'resolved_type', None) or getattr(a, 'type', None)
                if a_t == 'str':
                    return f"({a_code}.length)"
                if isinstance(a, Variable) or (isinstance(a_t, str) and a_t.startswith('array')):
                    return f"(sizeof({a_code})/sizeof({a_code}[0]))"
                return f"(sizeof({a_code})/sizeof({a_code}[0]))"

            args = [self.generate_expression(arg) for arg in (expr.args or [])]
            args_str = ", ".join(args)
            return f"{expr.func_name}({args_str})"
        
        elif isinstance(expr, ArrayAccess):
            array = self.generate_expression(expr.arr)
            index = self.generate_expression(expr.index)
            return f"{array}[{index}]"
        
        elif isinstance(expr, FieldAccess):
            obj = self.generate_expression(expr.obj)
            obj_type = getattr(expr.obj, 'resolved_type', None)
            use_arrow = False
            if isinstance(obj_type, str) and (obj_type.startswith('*') or obj_type.startswith('ptr<')):
                use_arrow = True
            else:
                if self.local_vars_stack and hasattr(expr.obj, 'name'):
                    name = getattr(expr.obj, 'name')
                    try:
                        declared = self.local_vars_stack[-1].get(name)
                        if declared and ('*' in declared):
                            use_arrow = True
                    except Exception:
                        pass
            if use_arrow:
                return f"{obj}->{expr.field}"
            return f"{obj}.{expr.field}"
        
        elif isinstance(expr, Dereference):
            ptr = self.generate_expression(expr.ptr)
            return f"(*{ptr})"
        
        elif isinstance(expr, CastExpr):
            c_type = self.get_c_type(expr.target_type)
            value = self.generate_expression(expr.expr)   
            return f"(({c_type}){value})"
        elif isinstance(expr, ArrayLiteral):
            elems = [self.generate_expression(e) for e in expr.elements]
            if getattr(expr, 'is_struct_init', False):
                return "{" + ", ".join(elems) + "}"

            elem_c = None
            if getattr(expr, 'array_type', None):
                elem_c = self.get_c_type(expr.array_type)
            elif getattr(expr, 'resolved_type', None) and expr.resolved_type.startswith('array<'):
                inner = expr.resolved_type[len('array<'):-1]
                elem_c = self.get_c_type(inner)
            else:
                if expr.elements:
                    first = expr.elements[0]
                    ft = getattr(first, 'resolved_type', None) or getattr(first, 'type', None)
                    elem_c = self.get_c_type(ft) if ft else 'int32_t'
                else:
                    elem_c = 'int32_t'

            return f'({elem_c}[]){{' + ", ".join(elems) + '}'
        elif isinstance(expr, AddressOf):
            inner = self.generate_expression(expr.expr)
            return f"&{inner}"
        elif isinstance(expr, SizeOf):
            tgt = expr.target
            if isinstance(tgt, str):
                ctype = self.get_c_type(tgt)
                return f"sizeof({ctype})"
            elif hasattr(tgt, 'name'):
                return f"sizeof(struct {tgt.name})"
            else:
                inner = self.generate_expression(tgt)
                return f"sizeof({inner})"
        
        else:
            return "0"
    
    def _generate_print_call(self, expr) -> str:
        if not getattr(expr, 'args', None):
            return 'printf("\\n")'

        fmt_parts = []
        args_list = []

        for arg in expr.args:
            if isinstance(arg, Literal) and isinstance(arg.value, str):
                s = self._escape_string(arg.value)
                fmt_parts.append(s)
                continue

            t = getattr(arg, 'resolved_type', None)
            spec = "%d"
            if t in ('float', 'f32', 'f64', 'double'):
                spec = "%f"
            elif t == 'str':
                spec = "%s"
            elif isinstance(arg, Literal):
                v = arg.value
                if isinstance(v, float):
                    spec = "%f"
                elif isinstance(v, str):
                    spec = "%s"
                else:
                    spec = "%d"

            fmt_parts.append(spec)
            code = self.generate_expression(arg)
            if t == 'str':
                code = f"{code}.data"
            args_list.append(code)

        fmt = "".join(fmt_parts)
        if fmt and not fmt.endswith("\\n"):
            fmt += "\\n"
        elif not fmt:
            fmt = "\\n"

        fmt_escaped = self._escape_string(fmt)
        if args_list:
            return f'printf("{fmt_escaped}", {", ".join(args_list)})'
        return f'printf("{fmt_escaped}")'

    
    def get_c_type(self, flux_type) -> str:
        if flux_type is None or flux_type == 'void':
            return "void"
        
        type_map = {
            'int': 'int32_t',
            'i32': 'int32_t',
            'int32': 'int32_t',
            'int64': 'int64_t',
            'i64': 'int64_t',
            'i16': 'int16_t',
            'i8': 'int8_t',
            'u8': 'uint8_t',
            'u16': 'uint16_t',
            'u32': 'uint32_t',
            'u64': 'uint64_t',
            'float': 'float',
            'f32': 'float',
            'f64': 'double',
            'bool': 'bool',
            'str': 'flux_string',
        }
        if hasattr(flux_type, 'name') and hasattr(flux_type, 'args'):
            if flux_type.name == 'array':
                inner = flux_type.args[0] if flux_type.args else 'int'
                inner_c = self.get_c_type(inner)
                return f"{inner_c}*"
            if flux_type.args:
                return self.get_c_type(flux_type.args[0])
            return "int32_t"
        
        if flux_type in type_map:
            return type_map[flux_type]
        if isinstance(flux_type, str) and flux_type.startswith('*'):
            inner = flux_type[1:]
            inner_c_type = self.get_c_type(inner)
            return f"{inner_c_type}*"
        
        if isinstance(flux_type, str) and flux_type.startswith('ptr<'):
            inner = flux_type[4:-1]
            inner_c_type = self.get_c_type(inner)
            return f"{inner_c_type}*"
        
        # Структура
        if isinstance(flux_type, str) and flux_type not in type_map:
            return f"struct {flux_type}"
        
        return "int32_t"

class StandaloneCompiler:

    def __init__(self, source_file: str, output_exe: str, verbose: bool = True):
        self.source_file = Path(source_file)
        self.output_exe = Path(output_exe)
        self.verbose = verbose
        
        self.system = platform.system()
        self.is_windows = self.system == 'Windows'
        
        self.temp_dir = Path(tempfile.gettempdir()) / "cblerr_standalone"
        self.temp_dir.mkdir(exist_ok=True)
        
        self.c_file = self.temp_dir / f"{self.source_file.stem}.c"
        self.obj_file = self.temp_dir / f"{self.source_file.stem}.obj" if self.is_windows else self.temp_dir / f"{self.source_file.stem}.o"
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование"""
        if self.verbose:
            message = message.replace("✓", "[OK]").replace("✗", "[FAIL]")
            print(f"[{level}] {message}")
    
    def compile(self) -> bool:
        debugger = init_debugger(DebugLevel.INFO)
        try:
            debugger.log_info("Starting standalone compilation")
            self.log(f"CBlerr Compiler")
            self.log(f"Platform: {self.system}")
            self.log(f"Source: {self.source_file}")
            self.log(f"Output: {self.output_exe}")

            self.log("\n[1/4] Reading source file...")
            if not self.source_file.exists():
                self.log(f"File not found: {self.source_file}", "ERROR")
                return False

            with open(self.source_file, 'r', encoding='utf-8') as f:
                source = f.read()
            self.log(f"  Read {len(source)} bytes")

            self.log("\n[2/4] Tokenizing...")
            tokens = tokenize(source, str(self.source_file))
            self.log(f"  Generated {len(tokens)} tokens")

            self.log("\n[3/4] Parsing...")
            ast = parse(tokens)
            self.log(f"  AST created successfully")

            # skip semantic/type checking step
            # tc = TypeChecker(get_debugger())
            # tc.check(ast)

            self.log("\n[4/4] Generating C code...")
            generator = CCodeGenerator()
            c_code = generator.generate(ast)

            with open(self.c_file, 'w', encoding='utf-8') as f:
                f.write(c_code)
            self.log(f"  Generated {len(c_code)} bytes of C code")
            self.log(f"  C code saved to {self.c_file}")

            self.log("\n[5/5] Compiling C to executable...")
            success = self._compile_c_to_exe()
            if success:
                # Exact success message required by spec
                print("\033[92mCompilation completed!\033[0m")
            return success

        except (SyntaxError, NameError) as e:
            if DERR_FLAG:
                try:
                    debugger.critical_dump(e)
                except Exception:
                    pass
                import traceback
                traceback.print_exc()
                return False
            else:
                print(f"[ERROR] CODE ERROR: {e}")
                return False
        except Exception as e:
            try:
                debugger.critical_dump(e)
            except Exception:
                pass
            self.log(f"[FATAL] {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False
    
    def _compile_c_to_exe(self) -> bool:
        if self.is_windows:
            return self._compile_msvc() or self._compile_mingw()
        else:
            return self._compile_gcc() or self._compile_clang()
    
    def _compile_msvc(self) -> bool:
        self.log("Trying MSVC...")
        
        try:
            cl_exe = self._find_msvc_cl()
            if not cl_exe:
                self.log("  MSVC not found", "WARN")
                return False
            
            runtime_c = Path(__file__).parent.parent / 'lib' / 'cblerr_engine_runtime.c'
            srcs = [str(self.c_file)]
            if runtime_c.exists():
                srcs.append(str(runtime_c))

            cmd = [
                cl_exe,
            ] + srcs + [
                f'/Fe{self.output_exe}',
                '/link', '/INCREMENTAL:NO', '/OPT:REF', '/OPT:ICF',
                'kernel32.lib', 'user32.lib', 'winmm.lib', 'gdi32.lib', 'msvcrt.lib'
            ]
            
            self.log(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            exe_found = self.output_exe.exists() or (self.is_windows and self.output_exe.with_suffix('.exe').exists())

            if result.returncode == 0 and exe_found:
                self.log(f"  [OK] MSVC compilation successful!")
                try:
                    keep = SAVE_C_FLAG or os.getenv('CBLERR_KEEP_C', '0') == '1'
                    if keep:
                        self.log(f"  Keeping temporary files because -c or CBLERR_KEEP_C set: {self.c_file}")
                    else:
                        if self.c_file.exists():
                            os.remove(self.c_file)
                            self.log(f"  Removed temporary C file: {self.c_file}")
                        if self.obj_file.exists():
                            os.remove(self.obj_file)
                            self.log(f"  Removed temporary OBJ file: {self.obj_file}")
                except Exception as e:
                    self.log(f"  Cleanup error: {e}", "WARN")
                return True
            else:
                combined = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
                self.log(f"  MSVC compilation failed: {combined}", "WARN")
                return False
                
        except Exception as e:
            self.log(f"  MSVC error: {e}", "WARN")
            return False
    
    def _compile_mingw(self) -> bool:
        self.log("Trying MinGW (gcc.exe)...")
        
        try:
            runtime_c = Path(__file__).parent.parent / 'lib' / 'cblerr_engine_runtime.c'
            srcs = [str(self.c_file)]
            if runtime_c.exists():
                srcs.append(str(runtime_c))

            cmd = [
                'gcc.exe',
            ] + srcs + [
                '-o', str(self.output_exe),
                '-luser32', '-lkernel32', '-lwinmm', '-lgdi32', '-lncurses', '-lm'
            ]

            # Example: set CBLERR_CFLAGS=-std=c11 -O0 -s
            env_cflags = os.getenv('CBLERR_CFLAGS')
            if env_cflags:
                cmd += env_cflags.split()
            else:
                cmd += ['-std=c11', '-O2', '-s']
            
            self.log(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            exe_found = self.output_exe.exists() or (self.is_windows and self.output_exe.with_suffix('.exe').exists())

            if result.returncode == 0 and exe_found:
                self.log(f"  [OK] MinGW compilation successful!")
                try:
                    keep = SAVE_C_FLAG or os.getenv('CBLERR_KEEP_C', '0') == '1'
                    if keep:
                        self.log(f"  Keeping temporary files because -c or CBLERR_KEEP_C=1: {self.c_file}")
                    else:
                        if self.c_file.exists():
                            os.remove(self.c_file)
                            self.log(f"  Removed temporary C file: {self.c_file}")
                        if self.obj_file.exists():
                            os.remove(self.obj_file)
                            self.log(f"  Removed temporary OBJ file: {self.obj_file}")
                except Exception as e:
                    self.log(f"  Cleanup error: {e}", "WARN")
                return True
            else:
                combined = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
                self.log(f"  MinGW compilation failed: {combined}", "WARN")
                return False
                
        except FileNotFoundError:
            self.log("  MinGW not found", "WARN")
            return False
        except Exception as e:
            self.log(f"  MinGW error: {e}", "WARN")
            return False
    
    def _compile_gcc(self) -> bool:
        self.log("Trying GCC...")
        
        try:
            cmd = [
                'gcc',
                str(self.c_file),
                '-o', str(self.output_exe),
                '-lm', '-lc', '-O2', '-std=c11'
            ]
            
            self.log(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            exe_found = self.output_exe.exists() or (self.is_windows and self.output_exe.with_suffix('.exe').exists())

            if result.returncode == 0 and exe_found:
                self.log(f"  GCC compilation successful!")
                return True
            else:
                combined = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
                self.log(f"  GCC compilation failed: {combined}", "WARN")
                return False
                
        except FileNotFoundError:
            self.log("  GCC not found", "WARN")
            return False
        except Exception as e:
            self.log(f"  GCC error: {e}", "WARN")
            return False
    
    def _compile_clang(self) -> bool:
        self.log("Trying Clang...")
        
        try:
            cmd = [
                'clang',
                str(self.c_file),
                '-o', str(self.output_exe),
                '-lm', '-lc', '-O2', '-std=c11'
            ]
            
            self.log(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            exe_found = self.output_exe.exists() or (self.is_windows and self.output_exe.with_suffix('.exe').exists())

            if result.returncode == 0 and exe_found:
                self.log(f"  Clang compilation successful!")
                return True
            else:
                combined = (result.stdout or "") + ("\n" if result.stdout and result.stderr else "") + (result.stderr or "")
                self.log(f"  Clang compilation failed: {combined}", "WARN")
                return False
                
        except FileNotFoundError:
            self.log("  Clang not found", "WARN")
            return False
        except Exception as e:
            self.log(f"  Clang error: {e}", "WARN")
            return False
    
    def _find_msvc_cl(self) -> Optional[str]:
        common_paths = [
            r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\14.39.33519\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\VC\Tools\MSVC\14.29.30133\bin\Hostx64\x64\cl.exe",
            r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Tools\MSVC\14.39.33519\bin\Hostx64\x64\cl.exe",
        ]
        
        for path in common_paths:
            if Path(path).exists():
                return path
        
        try:
            result = subprocess.run(['where', 'cl.exe'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except:
            pass
        
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python build/builde.py <source.cbl> [options]")
        print("Options:")
        print("  -o <file>    Output executable path")
        print("  -t <target>  Target: windows (default) or linux")
        print("  --verbose    Show detailed output")
        print("  -c            Keep generated C file")
        sys.exit(1)
    
    source_file = sys.argv[1]
    output_exe = None
    target = "windows"
    verbose = True
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '-o' and i + 1 < len(sys.argv):
            output_exe = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '-t' and i + 1 < len(sys.argv):
            target = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--verbose':
            verbose = True
            i += 1
        else:
            i += 1
    
    if not output_exe:
        source_path = Path(source_file)
        exe_ext = '.exe' if target == 'windows' else ''
        output_exe = source_path.stem + exe_ext
    
    compiler = StandaloneCompiler(source_file, output_exe, verbose=verbose)
    success = compiler.compile()
    
    if success:
        print(f"\n[OK] Compilation successful!")
        print(f"Output: {compiler.output_exe}")
        sys.exit(0)
    else:
        print(f"\n[FAIL] Compilation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
