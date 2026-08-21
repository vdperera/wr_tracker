"""
Packaging entry point: run from the project root (`python app.py`) so
that `src` resolves as a package without relying on PYTHONPATH, and
so PyInstaller/nicegui-pack can build against a stable entry file.
"""

from src import main_ui  # noqa: F401  (import triggers ui.run())
