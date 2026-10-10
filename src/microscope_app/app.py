"""Qt application entry point."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from . import __app_name__, __version__
from .main_window import MainWindow


def _application_icon() -> QIcon:
    icon = QIcon.fromTheme("microscope-app")
    if not icon.isNull():
        return icon
    fallback = Path(__file__).resolve().parent / "resources" / "microscope-app.svg"
    if fallback.exists():
        return QIcon(str(fallback))
    return QIcon()


def main(argv=None) -> int:
    argv = list(sys.argv if argv is None else argv)
    app = QApplication(argv)
    app.setApplicationName(__app_name__)
    app.setApplicationDisplayName(__app_name__)
    app.setApplicationVersion(__version__)
    app.setOrganizationName("Microscope")
    app.setDesktopFileName("microscope-app")
    app.setWindowIcon(_application_icon())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
