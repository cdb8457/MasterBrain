"""Allow ``python -m masterbrain <command>`` to drive the CLI."""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
