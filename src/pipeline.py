"""Run the whole pipeline: fetch -> load -> classify -> verify."""
import sys

from classify import classify
from fetch import fetch
from load import load

STEPS = [("fetch", fetch), ("load", load), ("classify", classify)]


def main():
    for name, fn in STEPS:
        print(f"\n{'=' * 62}\n{name}\n{'=' * 62}")
        fn()

    print(f"\n{'=' * 62}\nverify\n{'=' * 62}")
    import verify

    verify.main()


if __name__ == "__main__":
    sys.exit(main())
