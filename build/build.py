import sys
import subprocess
import os
from pathlib import Path

def main():
    current_dir = Path(__file__).parent.resolve()
    target_script = current_dir / "build_standalone.py" #chito meowly fazber? Idk 

    command = [sys.executable, str(target_script)] + sys.argv[1:]

    try:
        result = subprocess.run(command, check=False)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\nСборка прервана пользователем.")
        sys.exit(130)
    except Exception as e:
        print(f"Не удалось запустить компилятор: {e} (возможно, он не установлен или не найден в папке со скриптом)")
        sys.exit(1)

if __name__ == "__main__":
    main()
