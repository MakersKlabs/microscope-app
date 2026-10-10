"""Gestione della persistenza delle impostazioni.

Le impostazioni sono salvate in ``~/.config/microscope-app/settings.json`` e
includono le preferenze specifiche per ogni telecamera (rotazione, specchiature,
risoluzione e frame rate), oltre all'ultima cartella usata per foto e video.
"""

from __future__ import annotations

import copy
import json
import os
import tempfile
from pathlib import Path

APP_ID = "microscope-app"

#: Impostazioni predefinite di una singola telecamera.
DEFAULT_CAMERA_SETTINGS = {
    "rotation": 0,        # 0, 90, 180, 270 (senso orario)
    "flip_h": False,      # specchiatura asse orizzontale
    "flip_v": False,      # specchiatura asse verticale
    "width": None,
    "height": None,
    "fps": None,
}

#: Impostazioni globali predefinite.
def _guess_dir(candidates: list) -> str:
    for name in candidates:
        path = Path.home() / name
        if path.is_dir():
            return str(path)
    return str(Path.home())


DEFAULTS = {
    "cameras": {},
    "selected_camera": None,
    "last_image_dir": _guess_dir(["Immagini", "Pictures"]),
    "last_video_dir": _guess_dir(["Video", "Videos"]),
    "video_codec": "libx264",
    "video_crf": 23,
    "video_preset": "veryfast",
    "window_geometry": None,
    "window_state": None,
    "fit_on_start": True,
}


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / APP_ID


def config_path() -> Path:
    return config_dir() / "settings.json"


def _ensure_dir_for(directory: str) -> str:
    """Restituisce una directory esistente, ricadendo sulla home."""
    try:
        p = Path(directory)
        if p.is_dir():
            return str(p)
    except (OSError, TypeError):
        pass
    return str(Path.home())


class SettingsStore:
    """Contenitore JSON con salvataggio atomico."""

    def __init__(self, path: str | os.PathLike | None = None) -> None:
        self._path = Path(path) if path is not None else config_path()
        self._data = copy.deepcopy(DEFAULTS)
        self.load()

    # -- I/O ---------------------------------------------------------------
    def load(self) -> None:
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        except FileNotFoundError:
            return
        except (OSError, ValueError):
            return
        if isinstance(data, dict):
            self._merge(self._data, data)

    @staticmethod
    def _merge(base: dict, incoming: dict) -> None:
        for key, value in incoming.items():
            if key == "cameras" and isinstance(value, dict):
                base["cameras"] = value
            elif key in base:
                base[key] = value

    def save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp = tempfile.mkstemp(
                dir=str(self._path.parent), prefix=".settings-", suffix=".json"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as fh:
                    json.dump(self._data, fh, indent=2, ensure_ascii=False)
                os.replace(tmp, self._path)
            except BaseException:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise
        except OSError:
            # Non bloccare mai l'applicazione per un errore di scrittura.
            pass

    # -- Accesso generico --------------------------------------------------
    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value

    def image_dir(self) -> str:
        return _ensure_dir_for(self._data.get("last_image_dir"))

    def video_dir(self) -> str:
        return _ensure_dir_for(self._data.get("last_video_dir"))

    # -- Impostazioni per telecamera --------------------------------------
    def camera_settings(self, camera_key: str) -> dict:
        settings = copy.deepcopy(DEFAULT_CAMERA_SETTINGS)
        stored = self._data.get("cameras", {}).get(camera_key)
        if isinstance(stored, dict):
            settings.update(stored)
        return settings

    def set_camera_settings(self, camera_key: str, values: dict) -> None:
        cameras = self._data.setdefault("cameras", {})
        cameras[camera_key] = dict(values)
