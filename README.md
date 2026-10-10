# Microscope

Desktop application for Ubuntu to capture images and videos from a
high-resolution USB camera attached to a microscope.

> 🇮🇹 Italian version: [README.it.md](README.it.md)

## Features

- **Camera selection** among the connected ones (name and `/dev/videoN` path).
- **Resolution and frame rate selection** from the camera capabilities.
- **Rotation** 0°/90°/180°/270° and **mirroring** on both axes, with
  **settings remembered per camera**.
- **Image navigation**:
  - zoom with the **mouse wheel**;
  - pan by dragging with the **left button**;
  - **fit** to the window with the **right click** (or double click, or `Ctrl+0`).
- **PNG photographs** (also JPEG/TIFF), remembering the last used folder.
- **Compressed video recording** (H.264 x264, with MPEG-4 fallback),
  remembering the last used folder.
- **Bilingual interface** (English / Italian) with a language selector
  (System / English / Italiano).

All preferences are stored in `~/.config/microscope-app/settings.json`.

## Language

The interface language can be changed in **Settings → Language**. The default
`System` option follows the operating system locale (`LANG`, `LC_ALL`,
`LANGUAGE`). The change is applied immediately, without restarting the app.

## Installation

The `.deb` package does not bundle the Python libraries: it declares them as
dependencies and downloads them from the Ubuntu repositories.

```bash
# 1. Build the package (root is not required)
make deb

# 2. Install it (apt resolves the dependencies)
sudo apt install ./dist/microscope-app_*_all.deb
```

The application then appears in the application menu as **Microscope** and can
also be started from a terminal with:

```bash
microscope-app
```

### Uninstall

```bash
sudo apt remove microscope-app
# or, to also remove system-wide configuration:
sudo apt purge microscope-app
```

The per-user file `~/.config/microscope-app/settings.json` is left untouched
(remove it with `rm -rf ~/.config/microscope-app`).

## Dependencies

Installed automatically as package dependencies:

| Package | Purpose |
|---|---|
| `python3-pyside6.qtwidgets` | Qt graphical interface |
| `python3-opencv` | camera capture |
| `python3-numpy` | image processing |
| `python3-av` | video compression (FFmpeg) |
| `python3-gi`, `gir1.2-gstreamer-1.0` | camera enumeration |
| `gstreamer1.0-plugins-base`, `gstreamer1.0-plugins-good` | V4L2 provider |

## Development

```bash
make dev    # create .venv and install the development dependencies
make run    # run the app from source
make clean  # remove build artifacts and caches
```

## Project structure

```
bin/microscope-app              launcher installed in /usr/bin
src/microscope_app/             application code
src/microscope_app/i18n.py      English / Italian translations
packaging/                      files for the .deb package
build-deb.sh                    creates dist/microscope-app_<ver>_all.deb
Makefile                        build/install/run shortcuts
```

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Ctrl+S` | save photo |
| `Ctrl+R` | start/stop recording |
| `Ctrl+0` / `F` | fit the image to the window |
| `+` / `-` | zoom in / out |
