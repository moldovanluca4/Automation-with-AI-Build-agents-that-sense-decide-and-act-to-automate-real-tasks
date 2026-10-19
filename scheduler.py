import sys

from run import main


if __name__ == "__main__":
    raise SystemExit(main(["scheduler.py", *sys.argv[1:]]))
