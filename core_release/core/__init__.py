import importlib, sys
_names = ['compiler','debugger','flux_ast','flux_parser','lexer']
for n in _names:
    try:
        mod = importlib.import_module(n)
        globals()[n] = mod
        sys.modules[f'core.{n}'] = mod
    except Exception:
        # ignore; module may be loaded later or not present
        pass
