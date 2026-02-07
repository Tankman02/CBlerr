"""
🎉 Парсер (Recursive Descent Parser) для языка CBlerr
Превращает скучные токены в красивое дерево синтаксиса (AST)
Потому что токены - это просто беспорядок

Версия 4.0: OSDev & Low-Level Features
(т.е. теперь вы можете писать код, который сломает компьютер)
"""
from typing import List, Optional
from core.lexer import Token, TokenType
from core.flux_ast import (
    Program, FunctionDef, Return, BinaryOp, Variable, Literal,
    IfStmt, Assign, Compare, Call, WhileLoop, BreakStmt, ContinueStmt,
    StructDef, FieldAccess, ArrayAccess, ArrayLiteral, LogicalOp,
    # v4.0: новые AST узлы
    PointerType, Dereference, InlineAsm, CastExpr, Decorator, ComptimeBlock,
    # v4.0: модульная система
    ImportStmt, FromImportStmt, GlobalVariable
)


class Parser:
    """
    Recursive Descent Parser для CBlerr
    (recursion - потому что мы в начале 2000х и любим гримасы)
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def current_token(self) -> Optional[Token]:
        """Возвращает текущий токен (или None если конец файла - грустно 😢)"""
        if self.pos >= len(self.tokens):
            return None
        return self.tokens[self.pos]
    
    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """Просматривает токен на offset позиций вперед"""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]
    
    def parse_import(self) -> ImportStmt:
        """v4.0: Парсит: import module_name"""
        self.expect(TokenType.IMPORT, "Ожидалось 'import'")
        
        module_name_token = self.expect(TokenType.NAME, "Ожидалось имя модуля")
        module_name = module_name_token.value
        
        # import module as alias (опционально)
        if self.current_token() and self.current_token().type == TokenType.AS:
            self.advance()
            alias_token = self.expect(TokenType.NAME, "Ожидалось имя alias")
            # TODO: обрабатывать alias
        
        return ImportStmt(module_name)
    
    def parse_from_import(self) -> FromImportStmt:
        """v4.0: Парсит: from module import X, Y, Z"""
        self.expect(TokenType.FROM, "Ожидалось 'from'")
        
        module_name_token = self.expect(TokenType.NAME, "Ожидалось имя модуля")
        module_name = module_name_token.value
        
        self.expect(TokenType.IMPORT, "Ожидалось 'import' после имени модуля")
        
        # Парсим список импортируемых имен
        items = []
        while True:
            name_token = self.expect(TokenType.NAME, "Ожидалось имя для импорта")
            items.append(name_token.value)
            
            # Проверяем запятую
            if self.current_token() and self.current_token().type == TokenType.COMMA:
                self.advance()
            else:
                break
        
        return FromImportStmt(module_name, items)
    
    def advance(self) -> Optional[Token]:
        """Перемещается на следующий токен"""
        if self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            self.pos += 1
            return token
        return None
    
    def expect(self, token_type: TokenType, error_msg: str = None, strict: bool = False):
        """Проверяет, что текущий токен имеет ожидаемый тип, и продвигается вперед
        
        Args:
            token_type: ожидаемый тип токена
            error_msg: пользовательское сообщение об ошибке
            strict: если True, выбрасывает исключение при несовпадении (старое поведение)
                   если False (default), пытается продолжить парсинг
        """
        token = self.current_token()
        if not token or token.type != token_type:
            msg = error_msg or f"Ожидался {token_type}, получен {token.type if token else 'EOF'}"
            if strict:
                raise SyntaxError(f"{msg} на строке {token.line if token else '?'}")
            else:
                # Толерантный режим: логируем предупреждение и продолжаем
                print(f"⚠️  WARNING: {msg} на строке {token.line if token else '?'}")
                # Не продвигаемся, чтобы парсер мог попытаться восстановиться
                return token
        return self.advance()
    
    def skip_newlines(self):
        """Пропускает токены NEWLINE"""
        while self.current_token() and self.current_token().type == TokenType.NEWLINE:
            self.advance()
    
    def parse_decorators(self) -> List[Decorator]:
        """
        v4.2: Парсит декораторы: @name или @name(arg1, arg2, ...)
        
        ✨ УЛУЧШЕНИЯ v4.2:
          - Принимает COMPTIME, PACKED и другие ключевые слова как валидные декораторы
          - Тихо обрабатывает неизвестные декораторы (логирует в лог, не падает)
          - Поддерживает вложенные декораторы
          - Обработка ошибок не прерывает парсинг
        """
        decorators = []
        while self.current_token() and self.current_token().type == TokenType.AT:
            self.advance()  # пропускаем @
            
            token = self.current_token()
            if not token:
                # Тихая обработка ошибки
                print(f"⚠️  WARNING: Ожидалось имя декоратора после @ на строке {self.current_token().line if self.current_token() else '?'}")
                break
            
            # ✨ КЛЮЧЕВОЕ УЛУЧШЕНИЕ: принимаем не только NAME, но и ключевые слова
            if token.type == TokenType.NAME:
                dec_name = token.value
                self.advance()
            elif token.type in (TokenType.COMPTIME, TokenType.PACKED, TokenType.ASM, 
                               TokenType.INLINE, TokenType.EXTERN):
                # ✨ v4.2: Расширенный список ключевых слов как декораторы
                dec_name = token.value
                self.advance()
            else:
                # ✨ v4.2: Неизвестный декоратор - логируем и продолжаем (ТИХО)
                dec_name = token.value if hasattr(token, 'value') else f"unknown_{token.type.name}"
                if not dec_name.startswith('unknown_'):
                    print(f"⚠️  WARNING: Неизвестный декоратор @{dec_name} на строке {token.line}")
                self.advance()
            
            # Аргументы (опционально)
            dec_args = []
            if self.current_token() and self.current_token().type == TokenType.LPAREN:
                self.advance()  # пропускаем (
                if self.current_token() and self.current_token().type != TokenType.RPAREN:
                    while True:
                        arg_token = self.current_token()
                        if arg_token and arg_token.type == TokenType.NAME:
                            dec_args.append(arg_token.value)
                            self.advance()
                        else:
                            break
                        
                        if self.current_token() and self.current_token().type == TokenType.COMMA:
                            self.advance()
                        else:
                            break
                
                if self.current_token() and self.current_token().type == TokenType.RPAREN:
                    self.advance()  # пропускаем )
            
            decorators.append(Decorator(dec_name, dec_args if dec_args else None))
            self.skip_newlines()
        
        return decorators if decorators else None

    def parse_type(self) -> str:
        """
        Читает имя типа: NAME, INT, STR или v4.2:
          - ptr<Type> - простые указатели
          - ptr<ptr<u8>> - вложенные указатели
          - u8, u16, u32, u64 - беззнаковые целые
          - i8, i16, i32, i64 - знаковые целые
          
        ✨ v4.2: Тихая обработка неизвестных типов (логирует warning)
        """
        token = self.current_token()

        # New v5.0: support '*' pointer style (e.g. *i32, **void)
        if token and token.type == TokenType.MULTIPLY:
            star_count = 0
            while self.current_token() and self.current_token().type == TokenType.MULTIPLY:
                star_count += 1
                self.advance()

            base = self.parse_type()
            # wrap base in ptr<> star_count times
            for _ in range(star_count):
                base = f"ptr<{base}>"
            return base

        # v4.0: also accept ptr<...> legacy syntax
        if token and (token.type == TokenType.NAME and token.value == 'ptr' or
                      token.type == TokenType.LT):
            if token.type == TokenType.NAME and token.value == 'ptr':
                self.advance()  # пропускаем 'ptr'
            
            if self.current_token() and self.current_token().type == TokenType.LT:
                self.advance()  # пропускаем '<'
                base_type = self.parse_type()  # рекурсивный вызов (поддерживает вложенность)
                
                if self.current_token() and self.current_token().type == TokenType.GT:
                    self.advance()  # пропускаем '>'
                    return f"ptr<{base_type}>"
                else:
                    print(f"⚠️  WARNING: Ожидалась '>' после типа в ptr<> на строке {token.line}")
                    return f"ptr<{base_type}>"
        
        # v4.0: Фиксированные типы целых чисел
        if token and token.type in (TokenType.U8, TokenType.U16, TokenType.U32, TokenType.U64,
                                     TokenType.I8, TokenType.I16, TokenType.I32, TokenType.I64):
            type_name = token.value
            self.advance()
            return type_name
        
        # Стандартные типы
        if token and token.type in (TokenType.NAME, TokenType.INT, TokenType.STR, 
                                    TokenType.BOOL, TokenType.FLOAT, TokenType.VOID):
            self.advance()
            return token.value
        
        # ✨ v4.2: Тихая обработка - логируем и возвращаем неизвестный тип
        if token:
            print(f"⚠️  WARNING: Неизвестный тип {token.value} на строке {token.line}")
            self.advance()
            return token.value if hasattr(token, 'value') else "unknown"
        
        raise SyntaxError(
            f"Ожидался тип на строке {token.line if token else '?'}"
        )
    
    def parse_global_var(self) -> GlobalVariable:
        """Парсит глобальную переменную: const name: type = value или name: type = value"""
        is_const = False
        
        # Проверяем const
        if self.current_token().type == TokenType.CONST:
            is_const = True
            self.advance()  # пропускаем const
        
        # name
        name_token = self.expect(TokenType.NAME, "Ожидалось имя переменной")
        name = name_token.value
        
        # : type
        self.expect(TokenType.COLON, "Ожидалось ':' после имени переменной")
        var_type = self.parse_type()
        
        # = value (опционально)
        value = None
        if self.current_token().type == TokenType.ASSIGN:
            self.advance()  # пропускаем =
            value = self.parse_expression()
        
        self.skip_newlines()
        
        return GlobalVariable(name, var_type, value, is_const)
    
    def parse(self) -> Program:
        """Парсит программу (корневой метод)"""
        functions = []
        structs = []
        imports = []
        global_vars = []
        
        # Пропускаем начальные переносы строк
        self.skip_newlines()
        
        # v4.0: Парсим импорты в начале файла
        while self.current_token() and self.current_token().type in (TokenType.IMPORT, TokenType.FROM):
            if self.current_token().type == TokenType.IMPORT:
                import_stmt = self.parse_import()
                imports.append(import_stmt)
            elif self.current_token().type == TokenType.FROM:
                from_import_stmt = self.parse_from_import()
                imports.append(from_import_stmt)
            
            self.skip_newlines()
        
        # Парсим функции, структуры, глобальные переменные и блоки comptime до конца файла
        while self.current_token() and self.current_token().type != TokenType.EOF:
            # Пропускаем NEWLINE между элементами
            if self.current_token().type == TokenType.NEWLINE:
                self.skip_newlines()
                continue
            
            # Пропускаем DEDENT (может быть в конце файла)
            if self.current_token().type == TokenType.DEDENT:
                self.advance()
                continue

            # v4.0: Проверяем на comptime блок
            if self.current_token().type == TokenType.COMPTIME:
                comptime_block = self.parse_comptime()
                # В программе выполняем comptime блок и добавляем результаты
                # (реализуется в компиляторе)
                continue
            
            # v4.0: Парсим глобальные переменные и константы (только const явно)
            if self.current_token().type == TokenType.CONST:
                global_var = self.parse_global_var()
                global_vars.append(global_var)
                continue
            
            # Пробуем распарсить глобальную переменную (без const): name: type = value
            # Проверяем паттерн в начале: NAME : TYPE ASSIGN
            # Это безопасно, т.к. функции начинаются с DEF/EXTERN, а структуры с STRUCT
            if self.current_token().type == TokenType.NAME and self.peek_token(1) and self.peek_token(1).type == TokenType.COLON:
                # Имеет формат name:..., проверяем не это ли функция
                # Функции начинаются с def/extern или декоратора, поэтому это не может быть функцией
                # Структуры начинаются с struct или декоратора 
                # Значит, это глобальная переменная!
                saved_pos = self.pos
                try:
                    name_token = self.current_token()
                    name = name_token.value
                    self.advance()
                    self.expect(TokenType.COLON, "Ожидалось ':'")
                    var_type = self.parse_type()
                    
                    value = None
                    if self.current_token() and self.current_token().type == TokenType.ASSIGN:
                        self.advance()
                        value = self.parse_expression()
                    
                    self.skip_newlines()
                    global_vars.append(GlobalVariable(name, var_type, value, is_const=False))
                    continue
                except Exception as e:
                    # Если что-то пошло не так, откатываемся
                    self.pos = saved_pos
            
            # v4.0: Парсим декораторы перед структурой или функцией
            decorators = self.parse_decorators()
            
            if self.current_token().type == TokenType.STRUCT:
                # Парсим определение структуры
                struct = self.parse_struct_def(decorators)
                structs.append(struct)
            elif self.current_token().type in (TokenType.DEF, TokenType.EXTERN):
                func = self.parse_function(decorators)
                functions.append(func)
            else:
                raise SyntaxError(f"Неожиданный токен {self.current_token().type} на строке {self.current_token().line}")
        
        # v4.0: Возвращаем Program с импортами и глобальными переменными
        program = Program(
            imports=imports if imports else [],
            global_vars=global_vars if global_vars else [],
            functions=functions if functions else [],
            structs=structs if structs else []
        )
        return program
    def parse_function(self, decorators: List[Decorator] = None) -> FunctionDef:
        """Парсит определение функции: [extern] def name(params) [->] return_type: body"""
        # extern (опционально)
        is_extern = False
        if self.current_token().type == TokenType.EXTERN:
            is_extern = True
            self.advance()  # пропускаем extern
        
        # def
        self.expect(TokenType.DEF, "Ожидалось ключевое слово 'def'")
        
        # name
        name_token = self.expect(TokenType.NAME, "Ожидалось имя функции")
        name = name_token.value
        
        # (
        self.expect(TokenType.LPAREN, "Ожидалась '(' после имени функции")
        
        # params: список параметров (с поддержкой varargs)
        params = []
        is_vararg = False  # ✨ НОВОЕ: флаг для varargs
        
        if self.current_token().type != TokenType.RPAREN:
            # Есть хотя бы один параметр
            while True:
                # ✨ НОВОЕ: Проверяем на varargs (...)
                if self.current_token() and self.current_token().type == TokenType.ELLIPSIS:
                    is_vararg = True
                    self.advance()  # пропускаем ...
                    break
                
                # param_name: type
                # Note: параметр может быть именем, но также и ключевым словом типа (str, int, etc.)
                param_name_token = self.current_token()
                
                # Разрешаем использовать токены как имена параметров
                if param_name_token and param_name_token.type in (TokenType.NAME, TokenType.STR, TokenType.INT, 
                                                                    TokenType.BOOL, TokenType.FLOAT,
                                                                    TokenType.U8, TokenType.U16, TokenType.U32, TokenType.U64,
                                                                    TokenType.I8, TokenType.I16, TokenType.I32, TokenType.I64):
                    param_name = param_name_token.value
                    self.advance()
                else:
                    raise SyntaxError(f"Ожидалось имя параметра на строке {param_name_token.line if param_name_token else '?'}")
                
                self.expect(TokenType.COLON, "Ожидалось ':' после имени параметра")
                
                param_type = self.parse_type()
                
                params.append((param_name, param_type))
                
                # Проверяем, есть ли еще параметры (может быть varargs)
                if self.current_token() and self.current_token().type == TokenType.COMMA:
                    self.advance()  # пропускаем запятую
                else:
                    break
        
        # )
        self.expect(TokenType.RPAREN, "Ожидалась ')' после параметров")
        
        # -> return_type (опционально) или просто return_type
        # Поддерживаем оба синтаксиса:
        # - def f() -> int:
        # - extern def f() int
        return_type = None
        if self.current_token().type == TokenType.ARROW:
            self.advance()  # пропускаем ->
            return_type = self.parse_type()
        elif self.current_token().type != TokenType.COLON and self.current_token().type != TokenType.EOF and not self._is_keyword_or_dedent():
            # Если нет ARROW и не двоеточие, пробуем распарсить тип (C-style синтаксис)
            return_type = self.parse_type()
        
        # Для extern функций тела нет, двоеточие опционально
        if is_extern:
            # Если есть двоеточие — пропускаем, если нет — тоже ок
            if self.current_token() and self.current_token().type == TokenType.COLON:
                self.advance()
            self.skip_newlines()
            func_def = FunctionDef(name, params, return_type, [], is_extern=True, is_vararg=is_vararg)
            func_def.decorators = decorators
            return func_def

        # : (обязательно для обычных функций)
        self.expect(TokenType.COLON, "Ожидалось ':' после сигнатуры функции")
        
        # body: список statements (с учетом отступов)
        self.skip_newlines()

        # Ожидаем INDENT
        body = []
        if self.current_token() and self.current_token().type == TokenType.INDENT:
            self.advance()
            # Парсим statements до DEDENT
            while True:
                self.skip_newlines()
                token = self.current_token()
                if not token or token.type == TokenType.EOF:
                    break
                if token.type == TokenType.DEDENT:
                    self.advance()
                    break
                stmt = self.parse_statement()
                if stmt:
                    body.append(stmt)
        else:
            # Тело функции может быть в одну строку (нечастый случай) — парсим single statement
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)

        func_def = FunctionDef(name, params, return_type, body, is_extern=False, is_vararg=is_vararg)
        func_def.decorators = decorators
        return func_def

    def parse_statement(self):
        """Парсит statement (оператор)"""
        token = self.current_token()
        if not token:
            return None

        # v4.0: asm() блок
        if token.type == TokenType.ASM:
            self.advance()  # пропускаем 'asm'
            self.expect(TokenType.LPAREN, "Ожидалась '(' после 'asm'")

            # Asm код в строке
            asm_token = self.expect(TokenType.STRING, "Ожидалась строка с asm кодом")
            asm_code = asm_token.value

            self.expect(TokenType.RPAREN, "Ожидалась ')' после asm кода")
            return InlineAsm(asm_code)

        if token.type == TokenType.RETURN:
            return self.parse_return()
        elif token.type == TokenType.IF:
            return self.parse_if_stmt()
        elif token.type == TokenType.WHILE:
            return self.parse_while_stmt()
        elif token.type == TokenType.BREAK:
            self.advance()
            return BreakStmt()
        elif token.type == TokenType.CONTINUE:
            self.advance()
            return ContinueStmt()
        elif token.type == TokenType.LET:
            # let name = expr
            self.advance()
            name_token = self.expect(TokenType.NAME, "Ожидалось имя переменной после 'let'")
            name = name_token.value
            if self.current_token() and self.current_token().type == TokenType.ASSIGN:
                self.advance()
                value = self.parse_expression()
                return Assign(name, value)
            else:
                raise SyntaxError("Ожидалось '=' после имени в 'let' объявлении")
        elif token.type == TokenType.NAME:
            # Проверяем варианты:
            # 1. name: type = expr (объявление переменной)
            # 2. name := expr (walrus)
            # 3. name = expr или obj.field = expr (присваивание)
            # 4. Просто выражение
            
            if self.peek_token() and self.peek_token().type == TokenType.COLON:
                return self.parse_var_decl()
            
            # Пробуем распарсить как выражение с доступом
            # и проверяем, есть ли знак присваивания
            saved_pos = self.pos
            try:
                # Попробуем распарсить левую часть с доступом к полям
                left_expr = self.parse_atom_or_access_simple()
                
                # Проверяем на присваивание
                if self.current_token() and self.current_token().type == TokenType.ASSIGN:
                    self.advance()  # пропускаем =
                    value = self.parse_expression()
                    if isinstance(left_expr, Variable):
                        return Assign(left_expr.name, value)
                    else:
                        return Assign(left_expr, value)
                elif self.current_token() and self.current_token().type == TokenType.WALRUS:
                    # name := expr (walrus)
                    if isinstance(left_expr, Variable):
                        self.advance()  # пропускаем :=
                        value = self.parse_expression()
                        return Assign(left_expr.name, value)
                    else:
                        raise SyntaxError("Только простые переменные поддерживают :=")
                else:
                    # Это просто выражение
                    return left_expr
            except:
                # В случае ошибки вернемся и распарсим как выражение
                self.pos = saved_pos
                return self.parse_expression()
        else:
            # Пробуем распарсить как выражение и проверяем на присваивание
            # (например, для *ptr = value)
            saved_pos = self.pos
            try:
                # Попытка распарсить как левая часть присваивания
                # Используем parse_unary чтобы обработать *ptr, &var, итд.
                left_expr = self.parse_unary()
                
                # Проверяем на присваивание
                if self.current_token() and self.current_token().type == TokenType.ASSIGN:
                    self.advance()  # пропускаем =
                    value = self.parse_expression()
                    if isinstance(left_expr, Variable):
                        return Assign(left_expr.name, value)
                    else:
                        return Assign(left_expr, value)
                else:
                    # Это просто выражение
                    return left_expr
            except:
                # В случае ошибки вернемся и распарсим как обычное выражение
                self.pos = saved_pos
                return self.parse_expression()
    
    def _is_keyword_or_dedent(self) -> bool:
        """Проверяет, является ли текущий токен ключевым словом или DEDENT"""
        token = self.current_token()
        if not token:
            return True
        return token.type in (TokenType.DEDENT, TokenType.EOF, TokenType.NEWLINE)

    def parse_struct_def(self, decorators: List[Decorator] = None) -> StructDef:
        """Парсит определение структуры: struct Name: field1: type1, field2: type2, ..."""
        # struct
        self.expect(TokenType.STRUCT, "Ожидалось ключевое слово 'struct'")
        
        # name
        name_token = self.expect(TokenType.NAME, "Ожидалось имя структуры")
        name = name_token.value
        
        # :
        self.expect(TokenType.COLON, "Ожидалось ':' после имени структуры")
        
        # fields
        self.skip_newlines()
        
        # Ожидаем INDENT
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        else:
            raise SyntaxError("Ожидался отступ после ':' на строке struct")
        
        fields = []
        # Парсим поля до DEDENT
        while True:
            self.skip_newlines()
            token = self.current_token()
            if not token:
                break
            if token.type == TokenType.DEDENT:
                self.advance()
                break
            if token.type == TokenType.EOF:
                break
            
            # Парсим поле: name: type
            field_name_token = self.expect(TokenType.NAME, "Ожидалось имя поля")
            field_name = field_name_token.value
            
            self.expect(TokenType.COLON, "Ожидалось ':' после имени поля")
            
            field_type = self.parse_type()
            
            fields.append((field_name, field_type))
            
            # Пропускаем NEWLINE после каждого поля
            self.skip_newlines()
        
        struct_def = StructDef(name, fields)
        struct_def.decorators = decorators
        return struct_def
    
    def parse_comptime(self) -> ComptimeBlock:
        """v4.0: Парсит блок compile-time: comptime { ... }"""
        self.expect(TokenType.COMPTIME, "Ожидалось ключевое слово 'comptime'")
        
        self.skip_newlines()
        
        # Читаем код Python до конца блока (между { и })
        code_lines = []
        
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        
        while True:
            token = self.current_token()
            if not token or token.type == TokenType.EOF:
                break
            if token.type == TokenType.DEDENT:
                self.advance()
                break
            
            # Собираем все токены как строку (упрощение)
            if token.type == TokenType.NEWLINE:
                code_lines.append('\n')
                self.advance()
            else:
                code_lines.append(token.value or str(token.type.value))
                self.advance()
        
        code = ''.join(code_lines)
        return ComptimeBlock(code)
        """Парсит statement (оператор)"""
        token = self.current_token()
        if not token:
            return None
        
        # v4.0: asm() блок
        if token.type == TokenType.ASM:
            self.advance()  # пропускаем 'asm'
            self.expect(TokenType.LPAREN, "Ожидалась '(' после 'asm'")
            
            # Asm код в строке
            asm_token = self.expect(TokenType.STRING, "Ожидалась строка с asm кодом")
            asm_code = asm_token.value
            
            self.expect(TokenType.RPAREN, "Ожидалась ')' после asm кода")
            return InlineAsm(asm_code)
        
        if token.type == TokenType.RETURN:
            return self.parse_return()
        elif token.type == TokenType.IF:
            return self.parse_if_stmt()
        elif token.type == TokenType.WHILE:  # while loop
            return self.parse_while_stmt()
        elif token.type == TokenType.BREAK:  # break statement
            self.advance()
            return BreakStmt()
        elif token.type == TokenType.CONTINUE:  # continue statement
            self.advance()
            return ContinueStmt()
        elif token.type == TokenType.NAME:
            # Может быть присваивание, объявление переменной или выражение
            # Проверяем, есть ли после имени: двоеточие или оператор присваивания
            if self.peek_token() and self.peek_token().type == TokenType.COLON:
                # Объявление переменной с типом: name: type = expr
                return self.parse_var_decl()
            elif self.peek_token() and self.peek_token().type == TokenType.ASSIGN:
                # Присваивание: name = expr
                return self.parse_assign()
            else:
                # Это выражение
                return self.parse_expression()
        else:
            # Выражение
            return self.parse_expression()
    
    def parse_return(self) -> Return:
        """Парсит оператор return"""
        self.expect(TokenType.RETURN, "Ожидалось 'return'")
        
        # return может быть с выражением или без
        if self.current_token() and self.current_token().type not in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            value = self.parse_expression()
        else:
            value = None
        
        return Return(value)
    
    def parse_assign(self) -> Assign:
        """Парсит присваивание: name = expression или obj.field = expression или arr[idx] = expression
        
        v4.3: Поддержка присваивания к полям структур и элементам массивов
        """
        # Прочитаем левую часть как выражение (переменная, поле, элемент массива)
        left_expr = self.parse_atom_or_access()
        
        # =
        self.expect(TokenType.ASSIGN, "Ожидалось '=' после переменной или поля")
        
        # Выражение справа
        value = self.parse_expression()
        
        # Преобразуем для совместимости: если левая часть - просто переменная, используем старый синтаксис
        if isinstance(left_expr, Variable):
            return Assign(left_expr.name, value)
        else:
            # Для полей и элементов массива - используем расширенное присваивание
            # (требует поддержки в компиляторе)
            return Assign(left_expr, value)
    
    def parse_atom_or_access_simple(self):
        """Парсит атомарное выражение с поддержкой доступа к полям и элементам
        
        v4.3: Поддержка для присваивания к полям структур
        """
        token = self.current_token()
        if not token or token.type != TokenType.NAME:
            raise SyntaxError(f"Ожидалось имя переменной на строке {token.line if token else '?'}")
        
        name = token.value
        self.advance()
        
        # Проверяем на вызов функции
        if self.current_token() and self.current_token().type == TokenType.LPAREN:
            expr = self.parse_call(name)
        else:
            expr = Variable(name)
        
        # Обработка доступа к полям и элементам
        while self.current_token():
            if self.current_token().type == TokenType.DOT:
                self.advance()  # пропускаем .
                field_name_token = self.expect(TokenType.NAME, "Ожидалось имя поля после '.'")
                expr = FieldAccess(expr, field_name_token.value)
            elif self.current_token().type == TokenType.LBRACKET:
                self.advance()  # пропускаем [
                index = self.parse_expression()
                self.expect(TokenType.RBRACKET, "Ожидалась ']'")
                expr = ArrayAccess(expr, index)
            else:
                break
        
        return expr
    
    def parse_atom_or_access(self):
        """Алиас для parse_atom_or_access_simple для обратной совместимости"""
        return self.parse_atom_or_access_simple()
    
    def parse_var_decl(self) -> Assign:
        """Парсит объявление переменной: name: type = expression"""
        # name
        name_token = self.expect(TokenType.NAME, "Ожидалось имя переменной")
        name = name_token.value
        
        # :
        self.expect(TokenType.COLON, "Ожидалось ':' после имени переменной")
        
        # type (используем parse_type чтобы поддержать *i32)
        type_name = self.parse_type()
        
        # = (опционально)
        if self.current_token() and self.current_token().type == TokenType.ASSIGN:
            self.advance()
            # Выражение
            value = self.parse_expression()
            return Assign(name, value, type_name)
        else:
            # Просто объявление без инициализации
            # Возвращаем Assign с нулевым значением по умолчанию и указанным типом
            return Assign(name, Literal(0, 'int'), type_name)
    
    def parse_if_stmt(self) -> IfStmt:
        """Парсит условный оператор: if condition: ... else: ..."""
        # if
        self.expect(TokenType.IF, "Ожидалось ключевое слово 'if'")
        
        # condition
        condition = self.parse_expression()
        
        # :
        self.expect(TokenType.COLON, "Ожидалось ':' после условия")
        
        # then body: список statements (с учетом отступов)
        self.skip_newlines()
        
        # Ожидаем INDENT для then блока
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        else:
            # Тело может быть на той же строке (для простоты не поддерживаем)
            raise SyntaxError("Ожидался отступ после ':' на строке if")
        
        then_body = []
        # Парсим statements до DEDENT или else
        while True:
            self.skip_newlines()
            token = self.current_token()
            if not token:
                break
            if token.type == TokenType.DEDENT:
                # Пропускаем DEDENT и проверяем, не идет ли else
                self.advance()
                # Пропускаем возможные NEWLINE после DEDENT
                self.skip_newlines()
                # Проверяем, есть ли else на том же уровне
                if self.current_token() and self.current_token().type == TokenType.ELSE:
                    # Есть else блок
                    break
                # Нет else, просто выходим
                break
            if token.type == TokenType.EOF:
                break
            
            stmt = self.parse_statement()
            if stmt:
                then_body.append(stmt)
        
        # Проверяем, есть ли else
        else_body = None
        if self.current_token() and self.current_token().type == TokenType.ELSE:
            # else
            self.expect(TokenType.ELSE, "Ожидалось 'else'")
            
            # :
            self.expect(TokenType.COLON, "Ожидалось ':' после 'else'")
            
            # else body: список statements (с учетом отступов)
            self.skip_newlines()
            
            # Ожидаем INDENT для else блока
            if self.current_token().type == TokenType.INDENT:
                self.advance()
            else:
                raise SyntaxError("Ожидался отступ после ':' на строке else")
            
            else_body = []
            # Парсим statements до DEDENT
            while True:
                self.skip_newlines()
                token = self.current_token()
                if not token:
                    break
                if token.type == TokenType.DEDENT:
                    self.advance()
                    break
                if token.type == TokenType.EOF:
                    break
                
                stmt = self.parse_statement()
                if stmt:
                    else_body.append(stmt)
        
        return IfStmt(condition, then_body, else_body)
    
    def parse_while_stmt(self) -> WhileLoop:
        """NEW: Парсит цикл while: while condition: body"""
        # while
        self.expect(TokenType.WHILE, "Ожидалось ключевое слово 'while'")
        
        # condition
        condition = self.parse_expression()
        
        # :
        self.expect(TokenType.COLON, "Ожидалось ':' после условия")
        
        # body: список statements (с учетом отступов)
        self.skip_newlines()
        
        # Ожидаем INDENT
        if self.current_token().type == TokenType.INDENT:
            self.advance()
        else:
            raise SyntaxError("Ожидался отступ после ':' на строке while")
        
        body = []
        # Парсим statements до DEDENT
        while True:
            self.skip_newlines()
            token = self.current_token()
            if not token:
                break
            if token.type == TokenType.DEDENT:
                self.advance()
                break
            if token.type == TokenType.EOF:
                break
            
            stmt = self.parse_statement()
            if stmt:
                body.append(stmt)
        
        return WhileLoop(condition, body)
    
    def parse_expression(self):
        """Парсит выражение (с учетом приоритета операторов)"""
        # Логические операции (or) имеют самый низкий приоритет
        return self.parse_logical_or()
    
    def parse_logical_or(self):
        """NEW: Парсит логические операции 'or'"""
        left = self.parse_logical_and()
        
        while self.current_token() and self.current_token().type == TokenType.OR:
            op_token = self.advance()
            right = self.parse_logical_and()
            left = LogicalOp('or', left, right)
        
        return left
    
    def parse_logical_and(self):
        """NEW: Парсит логические операции 'and'"""
        left = self.parse_logical_not()
        
        while self.current_token() and self.current_token().type == TokenType.AND:
            op_token = self.advance()
            right = self.parse_logical_not()
            left = LogicalOp('and', left, right)
        
        return left
    
    def parse_logical_not(self):
        """NEW: Парсит унарный логический оператор 'not'"""
        if self.current_token() and self.current_token().type == TokenType.NOT:
            self.advance()
            expr = self.parse_logical_not()
            return LogicalOp('not', expr)
        
        return self.parse_comparison()
    
    def parse_comparison(self):
        """Парсит операции сравнения (==, !=, <, >, <=, >=)"""
        left = self.parse_additive()
        
        # Операторы сравнения
        comparison_ops = (TokenType.EQ, TokenType.NE, TokenType.LT, TokenType.GT, TokenType.LE, TokenType.GE)
        
        while self.current_token() and self.current_token().type in comparison_ops:
            op_token = self.advance()
            right = self.parse_additive()
            # Преобразуем токен в строку оператора
            op_map = {
                TokenType.EQ: '==',
                TokenType.NE: '!=',
                TokenType.LT: '<',
                TokenType.GT: '>',
                TokenType.LE: '<=',
                TokenType.GE: '>=',
            }
            left = Compare(op_map[op_token.type], left, right)
        
        return left
    
    def parse_additive(self):
        """Парсит аддитивные операции (+, -)"""
        left = self.parse_multiplicative()
        
        while self.current_token() and self.current_token().type in (TokenType.PLUS, TokenType.MINUS):
            op_token = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(op_token.value, left, right)
        
        return left
    
    def parse_multiplicative(self):
        """Парсит мультипликативные операции (*, /)"""
        left = self.parse_unary()
        
        while self.current_token() and self.current_token().type in (TokenType.MULTIPLY, TokenType.DIVIDE):
            op_token = self.advance()
            right = self.parse_unary()
            left = BinaryOp(op_token.value, left, right)
        
        return left
    
    def parse_unary(self):
        """Парсит унарные операции и атомарные выражения"""
        token = self.current_token()
        
        # v4.0: Разыменование указателя: *ptr
        if token and token.type == TokenType.MULTIPLY:
            self.advance()  # пропускаем *
            ptr_expr = self.parse_unary()
            return Dereference(ptr_expr)
        
        # v4.0: Адрес переменной: &var (уже поддерживается как AMP)
        if token and token.type == TokenType.AMP:
            self.advance()  # пропускаем &
            var_expr = self.parse_unary()
            # Возвращаем как приведение типа к ptr<expr>
            # (точная типизация происходит в компиляторе)
            return var_expr  # Упрощение: пока просто переменная
        
        # v4.0: Унарный минус: -expr (представляем как 0 - expr)
        if token and token.type == TokenType.MINUS:
            self.advance()  # пропускаем -
            expr = self.parse_unary()
            # Создаем BinaryOp: 0 - expr
            return BinaryOp('-', Literal(0, 'int'), expr)
        
        return self.parse_atom()
    
    def parse_atom(self):
        """Парсит атомарное выражение (литерал, переменная, вызов функции, скобки)"""
        token = self.current_token()
        if not token:
            raise SyntaxError("Неожиданный конец файла")
        
        # Строковый литерал
        if token.type == TokenType.STRING:
            self.advance()
            return Literal(token.value, 'str')
        
        # Число
        if token.type == TokenType.NUMBER:
            self.advance()
            # Determine if it's int or float
            if '.' in token.value:
                return Literal(float(token.value), 'float')
            else:
                return Literal(int(token.value), 'int')
        
        # Идентификатор (переменная или вызов функции)
        if token.type == TokenType.NAME:
            name = token.value
            self.advance()
            
            # Проверяем, не вызов ли это функции
            if self.current_token() and self.current_token().type == TokenType.LPAREN:
                # Вызов функции: func_name(arg1, arg2, ...)
                expr = self.parse_call(name)
            else:
                expr = Variable(name)
            
            # Проверяем field access (obj.field) и array access (arr[index])
            while self.current_token():
                if self.current_token().type == TokenType.DOT:
                    # Field access: obj.field
                    self.advance()  # пропускаем .
                    field_name_token = self.expect(TokenType.NAME, "Ожидалось имя поля после '.'")
                    expr = FieldAccess(expr, field_name_token.value)
                elif self.current_token().type == TokenType.LBRACKET:
                    # Array access or pointer deref: arr[index]
                    self.advance()  # пропускаем [
                    index = self.parse_expression()
                    self.expect(TokenType.RBRACKET, "Ожидалась ']'")
                    expr = Dereference(expr, index)
                else:
                    break
            
            # v4.0: Проверяем на приведение типа: expr as Type
            if self.current_token() and self.current_token().type == TokenType.AS:
                self.advance()  # пропускаем 'as'
                target_type = self.parse_type()
                expr = CastExpr(expr, target_type)
            
            return expr
        
        # Скобки
        if token.type == TokenType.LPAREN:
            self.advance()  # пропускаем (
            expr = self.parse_expression()
            self.expect(TokenType.RPAREN, "Ожидалась ')'")
            
            # Проверяем на приведение типа после скобок
            if self.current_token() and self.current_token().type == TokenType.AS:
                self.advance()  # пропускаем 'as'
                target_type = self.parse_type()
                expr = CastExpr(expr, target_type)
            
            return expr
        
        # Массивы [1, 2, 3]
        if token.type == TokenType.LBRACKET:
            self.advance()  # пропускаем [
            elements = []
            if self.current_token().type != TokenType.RBRACKET:
                while True:
                    elem = self.parse_expression()
                    elements.append(elem)
                    if self.current_token().type == TokenType.COMMA:
                        self.advance()
                    else:
                        break
            self.expect(TokenType.RBRACKET, "Ожидалась ']'")
            return ArrayLiteral(elements)
        
        raise SyntaxError(f"Неожиданный токен {token.type} на строке {token.line}")
    
    def parse_call(self, func_name: str) -> Call:
        """Парсит вызов функции: func_name(arg1, arg2, ...)"""
        # (
        self.expect(TokenType.LPAREN, "Ожидалась '(' после имени функции")
        
        # args: список аргументов
        args = []
        if self.current_token() and self.current_token().type != TokenType.RPAREN:
            # Есть хотя бы один аргумент
            while True:
                arg = self.parse_expression()
                args.append(arg)
                
                # Проверяем, есть ли еще аргументы
                if self.current_token() and self.current_token().type == TokenType.COMMA:
                    self.advance()  # пропускаем запятую
                else:
                    break
        
        # )
        self.expect(TokenType.RPAREN, "Ожидалась ')' после аргументов")
        
        return Call(func_name, args)


def parse(tokens: List[Token]) -> Program:
    """Удобная функция для парсинга"""
    parser = Parser(tokens)
    return parser.parse()

