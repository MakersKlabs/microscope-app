"""Load Qt's own translations for the active language.

Qt widgets such as :class:`QFileDialog` and :class:`QMessageBox` ship their
strings in compiled ``.qm`` files distributed by Qt. This module installs the
right catalog so that standard dialogs follow the language chosen in the app
(instead of the system locale).
"""

from __future__ import annotations

from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

_translator: QTranslator | None = None


def install_qt_translator(language: str) -> bool:
    """Install the Qt translation catalog for ``language``.

    Returns ``True`` if a catalog was loaded. Missing catalogs are not an
    error: the custom translations of the app keep working regardless.
    """
    global _translator

    app = QApplication.instance()
    if app is None:
        return False

    if _translator is not None:
        app.removeTranslator(_translator)
        _translator = None

    directory = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    locale = QLocale(language)

    for catalog in ("qtbase", "qt"):
        translator = QTranslator(app)
        if translator.load(locale, catalog, "_", directory):
            app.installTranslator(translator)
            _translator = translator
            return True
    return False
