"""Backward-compatible entry point (``python -m androguard``)."""

from androguard.cli.main import app

if __name__ == "__main__":
    raise SystemExit(app())
