from __future__ import annotations

from pathlib import Path
import runpy
import sys
import types


def main() -> None:
    """Compatibility entrypoint forwarding to package main."""
    package_path = Path(__file__).with_name("bot")
    package_module = types.ModuleType("bot")
    package_module.__path__ = [str(package_path)]  # type: ignore[attr-defined]
    sys.modules["bot"] = package_module

    module_path = package_path / "main.py"
    namespace = runpy.run_path(str(module_path), run_name="bot.main")
    namespace["main"]()


if __name__ == "__main__":
    main()
