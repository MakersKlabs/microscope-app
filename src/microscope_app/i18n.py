"""Minimal built-in internationalization (English / Italian).

The application ships with its own translation table so it does not depend on
compiled Qt ``.qm`` files. Use :func:`tr` to translate a key at runtime; the
active language can be changed with :func:`set_language`.
"""

from __future__ import annotations

import locale
import os

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        # Toolbar
        "camera": "Camera",
        "camera_fallback": "Camera {index}",
        "resolution": "Resolution",
        "fps": "FPS",
        "refresh": "Refresh",
        "refresh_tip": "Search again for connected cameras",
        "rotate": "Rotate {degrees}\u00b0",
        "rotate_tip": "Rotate the image by 90\u00b0 (clockwise)",
        "mirror_h": "Mirror H",
        "mirror_h_tip": "Mirror on the horizontal axis",
        "mirror_v": "Mirror V",
        "mirror_v_tip": "Mirror on the vertical axis",
        "fit": "Fit",
        "fit_tip": "Fit the image to the window (also right click)",
        "photo": "Photo",
        "photo_tip": "Save the current image as PNG (Ctrl+S)",
        "record": "Record",
        "stop": "Stop",
        "record_tip": "Start/stop video recording (Ctrl+R)",
        "settings": "Settings",
        "settings_tip": "Image and video settings",
        # Status bar
        "searching": "Searching for cameras\u2026",
        "no_camera": "No camera available",
        "no_image_to_save": "No image to save.",
        "no_video_stream": "No video stream to record.",
        "image_saved": "Image saved: {path}",
        "save_failed": "Saving failed:\n{path}",
        "video_saved": "Video saved: {path} ({frames} frames, {dropped} dropped)",
        "recording_started": "Recording started: {path}",
        "recording_status": "\u25cf REC  {time}   ",
        # File dialogs
        "save_image_title": "Save image",
        "save_video_title": "Save video",
        "filter_images": "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff)",
        "filter_videos": "Video MP4 (*.mp4);;Matroska (*.mkv);;QuickTime (*.mov)",
        # Errors
        "error_open_camera": "Cannot open camera {path}.",
        "error_no_frame": "No frame from camera {path}. "
                          "Check that it is not in use by another program.",
        "error_stream_interrupted": "Video stream interrupted.",
        "error_pyav_missing": "PyAV not available: {error}",
        "error_recording": "Recording error: {error}",
        # Settings dialog
        "settings_title": "Settings",
        "group_language": "Language",
        "language_label": "Language:",
        "language_system": "System",
        "group_image": "Image",
        "rotation_label": "Rotation:",
        "rotation_0": "0\u00b0",
        "rotation_90": "90\u00b0 (clockwise)",
        "rotation_180": "180\u00b0",
        "rotation_270": "270\u00b0 (counter-clockwise)",
        "mirror_label": "Mirror:",
        "mirror_horizontal": "Horizontal",
        "mirror_vertical": "Vertical",
        "group_video": "Video recording",
        "encoder_label": "Encoder:",
        "quality_label": "Quality (CRF):",
        "speed_label": "Speed:",
        "video_hint": "Lower CRF = better quality and larger files. "
                      "Speed only affects encoding time.",
        "ok": "OK",
        "cancel": "Cancel",
        "reset_camera": "Reset camera",
        # x264 encoder speed presets
        "preset_ultrafast": "Ultrafast",
        "preset_superfast": "Superfast",
        "preset_veryfast": "Very fast",
        "preset_faster": "Faster",
        "preset_fast": "Fast",
        "preset_medium": "Medium",
        "preset_slow": "Slow",
    },
    "it": {
        # Barra strumenti
        "camera": "Camera",
        "camera_fallback": "Camera {index}",
        "resolution": "Risoluzione",
        "fps": "FPS",
        "refresh": "Aggiorna",
        "refresh_tip": "Cerca di nuovo le telecamere collegate",
        "rotate": "Ruota {degrees}\u00b0",
        "rotate_tip": "Ruota l'immagine di 90\u00b0 (senso orario)",
        "mirror_h": "Specchia H",
        "mirror_h_tip": "Specchia sull'asse orizzontale",
        "mirror_v": "Specchia V",
        "mirror_v_tip": "Specchia sull'asse verticale",
        "fit": "Adatta",
        "fit_tip": "Adatta l'immagine alla finestra (anche click destro)",
        "photo": "Foto",
        "photo_tip": "Salva l'immagine corrente in PNG (Ctrl+S)",
        "record": "Registra",
        "stop": "Ferma",
        "record_tip": "Avvia/ferma la registrazione video (Ctrl+R)",
        "settings": "Impostazioni",
        "settings_tip": "Impostazioni immagine e video",
        # Barra di stato
        "searching": "Ricerca telecamere\u2026",
        "no_camera": "Nessuna telecamera disponibile",
        "no_image_to_save": "Nessuna immagine da salvare.",
        "no_video_stream": "Nessun flusso video da registrare.",
        "image_saved": "Immagine salvata: {path}",
        "save_failed": "Salvataggio non riuscito:\n{path}",
        "video_saved": "Video salvato: {path} ({frames} frame, {dropped} scartati)",
        "recording_started": "Registrazione avviata: {path}",
        "recording_status": "\u25cf REC  {time}   ",
        # Finestre di dialogo file
        "save_image_title": "Salva immagine",
        "save_video_title": "Salva video",
        "filter_images": "PNG (*.png);;JPEG (*.jpg *.jpeg);;TIFF (*.tif *.tiff)",
        "filter_videos": "Video MP4 (*.mp4);;Matroska (*.mkv);;QuickTime (*.mov)",
        # Errori
        "error_open_camera": "Impossibile aprire la telecamera {path}.",
        "error_no_frame": "Nessun frame dalla telecamera {path}. "
                          "Verifica che non sia usata da un altro programma.",
        "error_stream_interrupted": "Flusso video interrotto.",
        "error_pyav_missing": "PyAV non disponibile: {error}",
        "error_recording": "Errore di registrazione: {error}",
        # Finestra impostazioni
        "settings_title": "Impostazioni",
        "group_language": "Lingua",
        "language_label": "Lingua:",
        "language_system": "Sistema",
        "group_image": "Immagine",
        "rotation_label": "Rotazione:",
        "rotation_0": "0\u00b0",
        "rotation_90": "90\u00b0 (orario)",
        "rotation_180": "180\u00b0",
        "rotation_270": "270\u00b0 (antiorario)",
        "mirror_label": "Specchia:",
        "mirror_horizontal": "Orizzontale",
        "mirror_vertical": "Verticale",
        "group_video": "Registrazione video",
        "encoder_label": "Codificatore:",
        "quality_label": "Qualit\u00e0 (CRF):",
        "speed_label": "Velocit\u00e0:",
        "video_hint": "CRF pi\u00f9 basso = qualit\u00e0 migliore e file pi\u00f9 grandi. "
                      "La velocit\u00e0 influisce solo sul tempo di codifica.",
        "ok": "OK",
        "cancel": "Annulla",
        "reset_camera": "Ripristina camera",
        # Preset di velocit\u00e0 x264
        "preset_ultrafast": "Ultra veloce",
        "preset_superfast": "Super veloce",
        "preset_veryfast": "Molto veloce",
        "preset_faster": "Pi\u00f9 veloce",
        "preset_fast": "Veloce",
        "preset_medium": "Medio",
        "preset_slow": "Lento",
    },
}

_current = "en"


def available_languages() -> list[str]:
    """Return the language codes that have a translation table."""
    return list(TRANSLATIONS.keys())


def system_language() -> str:
    """Best-effort detection of the user's preferred language."""
    for var in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG"):
        value = os.environ.get(var)
        if not value:
            continue
        code = value.split(":")[0].split(".")[0].split("_")[0].lower()
        if code in TRANSLATIONS:
            return code
    try:
        code = (locale.getlocale()[0] or "").split("_")[0].lower()
        if code in TRANSLATIONS:
            return code
    except Exception:
        pass
    return "en"


def set_language(language: str | None) -> str:
    """Activate a language. ``"system"``/``None`` follows the OS locale.

    Returns the language code that was actually activated.
    """
    global _current
    if not language or language == "system":
        language = system_language()
    if language not in TRANSLATIONS:
        language = "en"
    _current = language
    return _current


def get_language() -> str:
    """Return the active language code."""
    return _current


def tr(key: str, **kwargs) -> str:
    """Translate ``key`` into the active language, with optional formatting."""
    table = TRANSLATIONS.get(_current, TRANSLATIONS["en"])
    text = table.get(key) or TRANSLATIONS["en"].get(key, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            pass
    return text
