"""Run lint, type-checking, and unit tests."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    ("Ruff (lint)", ["-m", "ruff", "check", "app.py", "src", "tests"]),
    ("mypy (types)", ["-m", "mypy", "--check-untyped-defs", "app.py", "src"]),
    (
        "unittest (tests)",
        ["-m", "unittest", "discover", "-s", "tests", "-v"],
    ),
)


def main() -> int:
    failed_checks = []

    for name, arguments in CHECKS:
        print(f"\n==> {name}", flush=True)
        try:
            result = subprocess.run(
                [sys.executable, *arguments],
                cwd=PROJECT_ROOT,
                check=False,
            )
        except OSError as error:
            print(f"Não foi possível iniciar {name}: {error}", file=sys.stderr)
            failed_checks.append(name)
            continue

        if result.returncode:
            failed_checks.append(name)

    if failed_checks:
        print(
            "\nScanner de qualidade encontrou falhas ou ferramentas indisponíveis: "
            + ", ".join(failed_checks),
            file=sys.stderr,
        )
        return 1

    print("\nScanner de qualidade concluído sem achados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
