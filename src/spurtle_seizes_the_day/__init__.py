import sys

from . import spurtle


def main():
    spurtle.main()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback

        traceback.print_exception(sys.exception(), colorize=True)
        sys.exit(1)
