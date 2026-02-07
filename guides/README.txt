Гайд: как компилировать с помощью обфусцированного компилятора CBlerr

1) Требования
- Windows x86_64.
- Python 3.9.13 (обязательное требование для включённого нативного рантайма `pyarmor_runtime.pyd`).
- MinGW (`gcc`) или MSVC в PATH для финальной компиляции C->EXE.
- Папка релиза: `Release/` (содержит `core_release/` и `examples/`).

2) Быстрая проверка лексера
```powershell
Release\core_release\lexer.exe Release\examples\test_simple.cbl > Release\core_release\last_lexer_output.jsonl
```
Результат: `Release/core_release/last_lexer_output.jsonl` — список токенов.

3) Сборка одного примера (рекомендуемый способ)
- Из корня репозитория выполните команду через Python 3.9:
```powershell
py -3.9 build.py --input Release\examples\test_simple.cbl --output Release\core_release\
```
- Что происходит:
  - Скрипт использует обфусцированные модули из `Release/core_release/`.
  - Генерирует временный C-файл, компилирует его (MSVC или MinGW) и записывает exe в указанную папку.

4) Альтернативный запуск (если скрипт недоступен)
- Запускать `build/build_standalone.py` напрямую, указав абсолютные пути и добавив `Release/core_release` в `PYTHONPATH` или `sys.path`:
```powershell
py -3.9 -c "import sys; sys.path.insert(0, r'C:\Users\User\Desktop\CBlerr\Release\core_release'); import runpy; sys.argv=['build_standalone.py', r'C:\Users\User\Desktop\CBlerr\Release\examples\test_simple.cbl','-o', r'C:\Users\User\Desktop\CBlerr\Release\core_release\test_simple.exe']; runpy.run_path(r'C:\Users\User\Desktop\CBlerr\build\build_standalone.py', run_name='__main__')"
```

5) Сохранение промежуточного C-файла (для отладки)
- Чтобы не удалялись временные C/OBJ файлы, установите переменную окружения `CBLERR_KEEP_C=1` перед запуском сборки:
```powershell
$env:CBLERR_KEEP_C='1'
py -3.9 build.py --input Release\examples\test_simple.cbl --output Release\core_release\
```
Сгенерированный C-файл будет находиться в папке временных файлов (см. вывод сборщика) — можно скопировать его в `Release/core_release/` для правок/анализа.

6) Где искать результат
- По умолчанию output — имя исходного файла с расширением `.exe` в указанной папке. Пример: `Release/core_release/test_simple.exe`.

7) Отладка проблем с GUI или CreateWindow
- Если exe «вылетает» или не показывает окно, сохраните вывод программы в файл и пришлите его: команда запуска с логом:
```powershell
& 'C:\Users\User\Desktop\CBlerr\Release\core_release\test_simple.exe' > C:\Users\User\Desktop\CBlerr\Release\core_release\test_simple.out.txt 2>&1
Get-Content C:\Users\User\Desktop\CBlerr\Release\core_release\test_simple.out.txt -Tail 200
```
- Для детальной диагностики установите `CBLERR_KEEP_C=1`, найдите сгенерированный C-файл, проверьте, как он создаёт окно (вызовы `CreateWindowEx`/`RegisterClassEx`) и при необходимости исправьте генератор в `build/build_standalone.py`.

8) Советы и ограничения
- Всегда запускайте сборку через `py -3.9` при работе с обфусцированными модулями (иначе нативный рантайм может не загрузиться).
- Не удаляйте и не изменяйте файлы в `Release/core_release/` (обфусцированные модули и `pyarmor_runtime.pyd`).
- Если нужен массовый прогон примеров — могу написать простой скрипт, который пройдёт по `Release/examples/` и попытается собрать каждый пример, логируя результаты.

9) Пример автоматической проверки всех примеров (одна строка)
```powershell
Get-ChildItem -Path Release\examples -Filter *.cbl | ForEach-Object { py -3.9 build.py --input $_.FullName --output Release\core_release\ }
```

Если хотите, я добавлю:
- скрипт для массовой сборки примеров и журналирования, или
- встраивание корректной регистрации окон в генератор `build/build_standalone.py` (чтобы GUI-примеры работали «из коробки").

Файл: [Release/COMPILING.md](Release/COMPILING.md)
