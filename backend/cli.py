import os
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    sys.path.insert(0, str(root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

    from django.core.management import execute_from_command_line

    args = sys.argv[1:]
    if not args:
        execute_from_command_line([sys.argv[0], "wait_for_db"])
        execute_from_command_line([sys.argv[0], "migrate", "--noinput"])
        execute_from_command_line([sys.argv[0], "seed_demo"])
        execute_from_command_line([sys.argv[0], "runserver"])
    else:
        execute_from_command_line([sys.argv[0], *args])


if __name__ == "__main__":
    main()
