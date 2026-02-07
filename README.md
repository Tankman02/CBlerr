[README.md](https://github.com/user-attachments/files/25149812/README.md)
# CBlerr / Руководство / README

CBlerr — экспериментальный язык системного программирования, сочетающий читаемость Python с контролем и производительностью C. Этот репозиторий содержит исходный компилятор (`core/`) и обфусцированную сборку компилятора в `Release/core_release/`.

---

## Русский — Краткое руководство

### Статус

- Компилятор полностью работает и может собирать программы `.cbl` в standalone-исполняемые файлы.
- В `Release/core_release/` находятся обфусцированные версии ключевых модулей и PyArmor runtime, готовые для распространения.

### Быстрый старт (Windows)

Требования:
- Python 3.9.13 (x86_64) — ABI-совместим с поставленным PyArmor runtime.
- MinGW-w64 (gcc) для компиляции сгенерированного C-кода.

Примеры команд:

```powershell
py -3.9 fix_and_build.py
# или
python build/build_standalone.py examples/test_gui_and_die.cbl -o hello.exe
```

Если вы используете обфусцированную сборку в `Release/core_release/`, запускайте Python именно той версии, для которой собран `pyarmor_runtime.pyd` (по умолчанию в релизе — Python 3.9.13).

### Linux / macOS — Быстрый старт

Требования:
- Python 3.9.13 (x86_64) — рекомендуется для совместимости с готовыми PyArmor runtime-библиотеками.
- GCC (или Clang на macOS) — на Linux обычно пакет `build-essential` / `gcc`, на macOS — Xcode Command Line Tools.

Установка инструментов (примеры):

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y build-essential python3.9 python3.9-venv

# Fedora
sudo dnf install -y @development-tools python39

# macOS (Homebrew)
brew install python@3.9
# Установите Xcode Command Line Tools, если ещё не установлены
xcode-select --install
```

Пример сборки программы на Linux/macOS:

```bash
python3.9 build/build_linux.py hello.cbl -o hello
```

Если вы планируете использовать обфусцированную папку `Release/core_release/` на Linux/macOS, убедитесь, что в ней присутствует подходящая версия PyArmor runtime (обычно это нативная библиотека `.so` для Linux или `.dylib` для macOS). Релизный набор в этом репозитории может содержать только Windows-версию `pyarmor_runtime.pyd` — в этом случае нужно заново сгенерировать runtime для целевой платформы с помощью PyArmor.

### Обфусцированный компилятор

- Все возможности исходного компилятора доступны в обфусцированной версии: лексер, парсер, генерация C, интеграция с Win32/C, сборка GUI-приложений и т.д.
- Обфусцированный код защищён от статического анализа — поведение и API эквивалентны исходному.

Особенность: PyArmor runtime (`pyarmor_runtime_000000/pyarmor_runtime.pyd` или соответствующая нативная библиотека) привязан к конкретной версии Python. При попытке запускать релизную папку с другой версией Python вы получите ошибку вида `RuntimeError: unauthorized use of script` или несовместимость бинарного runtime.

### Как заново обфусцировать (для владельца проекта)

1. Установите PyArmor.
2. Выполните (пример):

```powershell
pyarmor gen -O Release/core_release core\\compiler.py core\\debugger.py core\\flux_ast.py core\\flux_parser.py core\\lexer.py
# Переместите/проверьте файлы в Release/core_release (без вложенной папки core\\)
```

3. Сгенерируйте или скопируйте `pyarmor_runtime` для целевой платформы и версии Python (см. документацию PyArmor).

### Отладка и типичные проблемы

- "unauthorized use of script": означает несоответствие PyArmor header/runtime — не пытайтесь заменять обфусцированные файлы их неподзащищёнными исходниками; нужно регенерировать через PyArmor.
- Если сборка C не проходит — проверьте доступность `gcc`/`clang` и переменные `PATH`.

### Тесты и примеры

- В `examples/` есть тестовые программы, например `test_gui_and_die.cbl`. В ходе валидации был создан рабочий пример `Release/core_release/test_gui_and_die_via_obf.exe`.

---

## English — Quick Start & Notes

CBlerr is an experimental systems programming language combining Python-like readability with C-level control and performance. This repository contains the compiler source (`core/`) and an obfuscated compiler build in `Release/core_release/`.

### Status

- The compiler is fully functional and can compile `.cbl` programs to standalone executables.
- `Release/core_release/` contains obfuscated core modules and the PyArmor runtime suitable for distribution.

### Quick start (Windows)

Requirements:
- Python 3.9.13 (x86_64) — ABI-compatible with the bundled PyArmor runtime.
- MinGW-w64 (gcc) to compile generated C code.

Example commands:

```powershell
py -3.9 fix_and_build.py
# or
python build/build_standalone.py examples/test_gui_and_die.cbl -o hello.exe
```

When using the obfuscated build in `Release/core_release/`, run Python matching the `pyarmor_runtime` ABI (by default the release includes Python 3.9.13-compatible runtime).

### Linux / macOS Quick start

Requirements:
- Python 3.9.13 (x86_64) recommended.
- GCC (or Clang on macOS). On Linux, install `build-essential` / `gcc`; on macOS, install Xcode Command Line Tools.

Install examples:

```bash
# Debian/Ubuntu
sudo apt update
sudo apt install -y build-essential python3.9 python3.9-venv

# Fedora
sudo dnf install -y @development-tools python39

# macOS (Homebrew)
brew install python@3.9
# Install Xcode Command Line Tools if needed:
xcode-select --install
```

Build example on Linux/macOS:

```bash
python3.9 build/build_linux.py hello.cbl -o hello
```

If you intend to use the obfuscated `Release/core_release/` on Linux or macOS, make sure the folder includes a platform-appropriate PyArmor runtime (`.so` for Linux, `.dylib` for macOS). The release included here may only contain the Windows `pyarmor_runtime.pyd`; in that case, re-generate the runtime for the target platform using PyArmor.

### Obfuscated compiler notes

- The obfuscated build exposes the same functionality as the source compiler: lexer, parser, C generation, FFI/C integration, GUI builds, etc.
- Obfuscation only protects source readability — runtime behavior and public API remain the same.

Important: PyArmor runtime is tied to a specific Python ABI version. Running the release with a different Python version can cause `RuntimeError: unauthorized use of script` or native library incompatibilities.

### Re-obfuscation (for project owners)

1. Install PyArmor.
2. Example command:

```bash
pyarmor gen -O Release/core_release core\\compiler.py core\\debugger.py core\\flux_ast.py core\\flux_parser.py core\\lexer.py
```

3. Generate or copy an appropriate `pyarmor_runtime` for the platform and Python version you plan to support.

### Troubleshooting

- `unauthorized use of script`: the PyArmor header/runtime do not match — do not try to patch obfuscated files with plain `.py` files; regenerate using PyArmor.
- C compilation fails: verify `gcc`/`clang` availability and `PATH`.

---

If you'd like, I can add CI snippets to automatically validate that `pyarmor_runtime` matches a given Python interpreter, or add platform-specific reobfuscation commands.

---

## Release / Obfuscated Compiler (details)

The `Release/core_release/` folder contains the obfuscated compiler core modules and the PyArmor runtime intended for distribution. This section summarizes release-specific usage and notes (Russian and English follow).

### Русский — Быстрое использование (Release)

1. Установите Python 3.9.13 (x86_64) — версия критична для совместимости с `pyarmor_runtime.pyd`.
2. Установите MinGW-w64 (gcc) и добавьте `gcc` в `PATH`.
3. Запустите сборку примера через корень проекта:

```powershell
py -3.9 fix_and_build.py
```

`fix_and_build.py` настроен так, чтобы при наличии `Release/core_release/` использовать обфусцированные модули автоматически.

Ограничения:

- PyArmor runtime привязан к версии Python и платформе. Для Linux/macOS требуется соответствующая нативная библиотека (`.so`/`.dylib`).
- Нельзя просто заменить обфусцированные файлы на `.py` — PyArmor проверяет подписи и выдаст ошибку.

### English — Quick usage (Release)

The `Release/core_release/` folder contains obfuscated core modules (`compiler.py`, `debugger.py`, `flux_ast.py`, `flux_parser.py`, `lexer.py`) and the PyArmor runtime (`pyarmor_runtime_000000/`). Use the release as follows:

1. Install Python 3.9.13 (x86_64) — the included runtime targets this ABI.
2. Install MinGW-w64 (gcc) and ensure `gcc` is on `PATH`.
3. From the project root run:

```powershell
py -3.9 fix_and_build.py
```

Notes:

- PyArmor runtime is platform- and Python-version-specific. For Linux/macOS you need a platform-appropriate runtime (`.so` / `.dylib`).
- Do not attempt to replace obfuscated modules with plain `.py` files — regenerate the release via PyArmor.
