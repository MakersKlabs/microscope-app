"""Discovery of the cameras connected to the system.

GStreamer's ``GstDeviceMonitor`` is used (when available) to obtain the device
name, its ``/dev/videoN`` path and its capabilities (resolutions and frame
rates). If GStreamer is missing we fall back to a plain scan of
``/sys/class/video4linux``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

#: Frame rates used as a fallback when the camera reports none.
DEFAULT_FRAMERATES = [30.0, 15.0, 10.0, 5.0, 1.0]


@dataclass
class CameraInfo:
    """Description of a usable camera."""

    index: int                  # OpenCV index (the N of /dev/videoN)
    path: str                   # /dev/videoN
    name: str                   # human readable name
    resolutions: list = field(default_factory=list)  # list of (w, h)
    framerates: list = field(default_factory=list)   # list of float

    @property
    def key(self) -> str:
        """Stable key used to store the per-camera settings."""
        return self.name.strip() or self.path

    @property
    def label(self) -> str:
        return f"{self.name}  ({self.path})"


# ---------------------------------------------------------------------------
# GStreamer capability parsing
# ---------------------------------------------------------------------------
def _extract_ints(value: str) -> list:
    return [int(x) for x in re.findall(r"\d+", value)]


_NUM_OR_LIST = r"(\[[^\]]*\]|\{[^}]*\}|\d+)"


def _parse_structure(structure) -> tuple[list, list, list]:
    """Extract (widths, heights, framerates) from a Gst.Structure."""
    text = structure.to_string()
    widths: list = []
    heights: list = []
    framerates: list = []

    match = re.search(r"width=\(int\)" + _NUM_OR_LIST, text)
    if match:
        widths = _extract_ints(match.group(1))
    match = re.search(r"height=\(int\)" + _NUM_OR_LIST, text)
    if match:
        heights = _extract_ints(match.group(1))
    match = re.search(
        r"framerate=\(fraction\)(\[[^\]]*\]|\{[^}]*\}|\d+/\d+)", text
    )
    if match:
        for num, den in re.findall(r"(\d+)/(\d+)", match.group(1)):
            if int(den):
                framerates.append(round(int(num) / int(den), 3))
    return widths, heights, framerates


def _caps_to_options(caps) -> tuple[list, list]:
    resolutions: set = set()
    framerates: set = set()
    try:
        size = caps.get_size()
    except Exception:
        return [], []

    for i in range(size):
        try:
            structure = caps.get_structure(i)
        except Exception:
            continue
        if structure.get_name() in (None, ""):
            continue
        widths, heights, rates = _parse_structure(structure)
        for width in widths:
            for height in heights:
                if 0 < width <= 20000 and 0 < height <= 20000:
                    resolutions.add((width, height))
        framerates.update(rates)

    res_list = sorted(resolutions, key=lambda wh: wh[0] * wh[1], reverse=True)
    fps_list = sorted(framerates, reverse=True)
    return res_list, fps_list


# ---------------------------------------------------------------------------
# Enumeration
# ---------------------------------------------------------------------------
def _enumerate_gst() -> list:
    try:
        import gi

        gi.require_version("Gst", "1.0")
        from gi.repository import Gst
    except Exception:
        return []

    try:
        if not Gst.is_initialized():
            Gst.init(None)
        monitor = Gst.DeviceMonitor.new()
        monitor.add_filter("Video/Source", None)
        devices = monitor.get_devices()
    except Exception:
        return []

    cameras: list = []
    seen: set = set()
    for device in devices:
        path = None
        try:
            props = device.get_properties()
            if props is not None:
                try:
                    path = props.get_string("device.path")
                except Exception:
                    path = None
        except Exception:
            path = None

        # Skip duplicates (providers without a path) and repeated entries.
        if not path or path in seen:
            continue
        match = re.search(r"(\d+)$", path)
        if not match:
            continue
        seen.add(path)
        index = int(match.group(1))
        name = (device.get_display_name() or f"Camera {index}").strip()
        try:
            resolutions, framerates = _caps_to_options(device.get_caps())
        except Exception:
            resolutions, framerates = [], []
        cameras.append(CameraInfo(index, path, name, resolutions, framerates))

    cameras.sort(key=lambda cam: cam.index)
    return cameras


def _enumerate_sysfs() -> list:
    base = Path("/sys/class/video4linux")
    cameras: list = []
    if not base.is_dir():
        return cameras
    for entry in sorted(base.glob("video*")):
        try:
            index = int(entry.name[len("video"):])
        except ValueError:
            continue
        name_file = entry / "name"
        try:
            name = name_file.read_text(encoding="utf-8").strip()
        except OSError:
            name = f"Camera {index}"
        cameras.append(CameraInfo(index, f"/dev/{entry.name}", name, [], []))
    cameras.sort(key=lambda cam: cam.index)
    return cameras


def enumerate_cameras() -> list:
    """Return the list of available cameras."""
    cameras = _enumerate_gst()
    if not cameras:
        cameras = _enumerate_sysfs()
    return cameras


def normalize_resolutions(camera: CameraInfo) -> list:
    if camera.resolutions:
        return list(camera.resolutions)
    return [(640, 480)]


def normalize_framerates(camera: CameraInfo) -> list:
    if camera.framerates:
        return list(camera.framerates)
    return list(DEFAULT_FRAMERATES)
