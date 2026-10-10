"""Main application window."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QByteArray, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from . import __app_name__
from .cameras import (
    CameraInfo,
    enumerate_cameras,
    normalize_framerates,
    normalize_resolutions,
)
from .capture import CaptureThread
from .i18n import get_language, set_language, tr
from .image_view import ImageView
from .recorder import VideoRecorder, available_encoders
from .settings_dialog import SettingsDialog
from .settings_store import SettingsStore

IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg", ".tif", ".tiff"]
VIDEO_EXTENSIONS = [".mp4", ".mkv", ".mov"]


def _themed_icon(*names: str) -> QIcon:
    for name in names:
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            return icon
    return QIcon()


def _record_icon(color: str = "#e74c3c", size: int = 16) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(color))
    margin = 2
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.end()
    return QIcon(pixmap)


class MainWindow(QMainWindow):
    """Main window with the toolbar and the image view."""

    def __init__(self, settings: SettingsStore | None = None) -> None:
        super().__init__()
        self.settings = settings or SettingsStore()
        set_language(self.settings.get("language", "system"))

        self._cameras: list[CameraInfo] = []
        self._camera: CameraInfo | None = None
        self._capture: CaptureThread | None = None
        self._camera_settings: dict = {}
        self._rotation = 0
        self._last_frame = None
        self._current_fps = 0.0
        self._actual_resolution = (0, 0)

        self._recorder: VideoRecorder | None = None
        self._record_guard = False
        self._record_seconds = 0

        self._video_encoders = available_encoders()
        self._populating = False

        self.setWindowTitle("Microscope")
        self.resize(1200, 800)

        self._build_ui()
        self._wire_shortcuts()
        self._restore_geometry()
        self.refresh_cameras()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QToolBar("Commands", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(18, 18))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout.addWidget(toolbar)

        # Camera selection ---------------------------------------------
        self.camera_label = QLabel(self)
        toolbar.addWidget(self.camera_label)
        self.camera_combo = QComboBox()
        self.camera_combo.setMinimumWidth(230)
        self.camera_combo.currentIndexChanged.connect(self._on_camera_combo)
        toolbar.addWidget(self.camera_combo)

        self.refresh_action = QAction(
            _themed_icon("view-refresh", "reload"), "", self
        )
        self.refresh_action.triggered.connect(self.refresh_cameras)
        toolbar.addAction(self.refresh_action)
        toolbar.addSeparator()

        # Resolution and frame rate ------------------------------------
        self.resolution_label = QLabel(self)
        toolbar.addWidget(self.resolution_label)
        self.resolution_combo = QComboBox()
        self.resolution_combo.setMinimumWidth(140)
        self.resolution_combo.currentIndexChanged.connect(self._on_resolution_changed)
        toolbar.addWidget(self.resolution_combo)

        self.fps_label = QLabel(self)
        toolbar.addWidget(self.fps_label)
        self.fps_combo = QComboBox()
        self.fps_combo.currentIndexChanged.connect(self._on_fps_changed)
        toolbar.addWidget(self.fps_combo)
        toolbar.addSeparator()

        # Rotation / mirroring -----------------------------------------
        self.rotate_action = QAction("", self)
        self.rotate_action.triggered.connect(self._rotate)
        toolbar.addAction(self.rotate_action)

        self.flip_h_action = QAction("", self)
        self.flip_h_action.setCheckable(True)
        self.flip_h_action.toggled.connect(self._on_flip_toggled)
        toolbar.addAction(self.flip_h_action)

        self.flip_v_action = QAction("", self)
        self.flip_v_action.setCheckable(True)
        self.flip_v_action.toggled.connect(self._on_flip_toggled)
        toolbar.addAction(self.flip_v_action)
        toolbar.addSeparator()

        # Main actions -------------------------------------------------
        self.fit_action = QAction(_themed_icon("zoom-fit-best", "zoom-original"), "", self)
        self.fit_action.triggered.connect(self.image_view_fit)
        toolbar.addAction(self.fit_action)

        self.photo_action = QAction(_themed_icon("camera-photo", "camera"), "", self)
        self.photo_action.triggered.connect(self.save_photo)
        toolbar.addAction(self.photo_action)

        self.record_action = QAction(_record_icon(), "", self)
        self.record_action.setCheckable(True)
        self.record_action.toggled.connect(self._on_record_toggled)
        toolbar.addAction(self.record_action)

        self.settings_action = QAction(
            _themed_icon("preferences-system", "emblem-system"), "", self
        )
        self.settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(self.settings_action)

        self.image_view = ImageView(central)
        self.image_view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self.image_view, 1)
        self.setCentralWidget(central)

        # Status bar ---------------------------------------------------
        self.status_camera = QLabel(tr("searching"))
        self.status_info = QLabel("")
        self.status_recording = QLabel("")
        self.statusBar().addWidget(self.status_camera, 1)
        self.statusBar().addPermanentWidget(self.status_info)
        self.statusBar().addPermanentWidget(self.status_recording)

        self._record_timer = QTimer(self)
        self._record_timer.setInterval(1000)
        self._record_timer.timeout.connect(self._on_record_tick)

        self.retranslate_ui()

    def retranslate_ui(self) -> None:
        """Refresh every translatable text for the active language."""
        self.camera_label.setText(tr("camera"))
        self.resolution_label.setText(tr("resolution"))
        self.fps_label.setText(tr("fps"))

        self.refresh_action.setText(tr("refresh"))
        self.refresh_action.setToolTip(tr("refresh_tip"))

        self.rotate_action.setToolTip(tr("rotate_tip"))
        self._update_rotate_label()

        self.flip_h_action.setText(tr("mirror_h"))
        self.flip_h_action.setToolTip(tr("mirror_h_tip"))
        self.flip_v_action.setText(tr("mirror_v"))
        self.flip_v_action.setToolTip(tr("mirror_v_tip"))

        self.fit_action.setText(tr("fit"))
        self.fit_action.setToolTip(tr("fit_tip"))
        self.photo_action.setText(tr("photo"))
        self.photo_action.setToolTip(tr("photo_tip"))
        self.record_action.setText(
            tr("stop") if self.record_action.isChecked() else tr("record")
        )
        self.record_action.setToolTip(tr("record_tip"))
        self.settings_action.setText(tr("settings"))
        self.settings_action.setToolTip(tr("settings_tip"))

        if self._camera is None and not self._cameras:
            self.status_camera.setText(tr("no_camera"))
        if self.record_action.isChecked():
            self._on_record_tick()

    def _wire_shortcuts(self) -> None:
        self.photo_action.setShortcut("Ctrl+S")
        self.record_action.setShortcut("Ctrl+R")
        self.fit_action.setShortcut("Ctrl+0")
        self.addAction(self.photo_action)
        self.addAction(self.record_action)
        self.addAction(self.fit_action)

    def _restore_geometry(self) -> None:
        geometry = self.settings.get("window_geometry")
        if geometry:
            try:
                self.restoreGeometry(QByteArray.fromBase64(geometry.encode("ascii")))
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Camera handling
    # ------------------------------------------------------------------
    def refresh_cameras(self) -> None:
        selected_key = self._camera.key if self._camera else self.settings.get(
            "selected_camera"
        )
        self._cameras = enumerate_cameras()

        self._populating = True
        self.camera_combo.blockSignals(True)
        self.camera_combo.clear()
        for camera in self._cameras:
            self.camera_combo.addItem(camera.label, camera.key)
        index = 0
        if selected_key:
            found = self.camera_combo.findData(selected_key)
            if found >= 0:
                index = found
        if self._cameras:
            self.camera_combo.setCurrentIndex(index)
        self.camera_combo.blockSignals(False)
        self._populating = False

        self._on_camera_combo(index if self._cameras else -1)

    def _on_camera_combo(self, index: int) -> None:
        if self._populating:
            return
        camera = self._cameras[index] if 0 <= index < len(self._cameras) else None
        self.settings.set("selected_camera", camera.key if camera else None)
        self._start_camera(camera)

    def _start_camera(self, camera: CameraInfo | None) -> None:
        self._stop_recording(silent=True)
        self._stop_capture()
        self._camera = camera

        if camera is None:
            self._camera_settings = {}
            self._set_controls_enabled(False)
            self.image_view.clear()
            self.status_camera.setText(tr("no_camera"))
            self.status_info.setText("")
            return

        self._set_controls_enabled(True)
        self._camera_settings = self.settings.camera_settings(camera.key)
        self._populate_resolution(camera, self._camera_settings)
        self._populate_framerates(camera, self._camera_settings)
        self._apply_transform_ui(self._camera_settings)
        self._launch_capture()

    def _populate_resolution(self, camera: CameraInfo, settings: dict) -> None:
        self._populating = True
        self.resolution_combo.blockSignals(True)
        self.resolution_combo.clear()
        for width, height in normalize_resolutions(camera):
            self.resolution_combo.addItem(f"{width} × {height}", (width, height))
        want = (settings.get("width"), settings.get("height"))
        index = self.resolution_combo.findData(want) if want[0] and want[1] else -1
        self.resolution_combo.setCurrentIndex(index if index >= 0 else 0)
        self.resolution_combo.blockSignals(False)
        self._populating = False

    def _populate_framerates(self, camera: CameraInfo, settings: dict) -> None:
        self._populating = True
        self.fps_combo.blockSignals(True)
        self.fps_combo.clear()
        for fps in normalize_framerates(camera):
            self.fps_combo.addItem(f"{fps:g} fps", float(fps))
        want = settings.get("fps")
        index = self.fps_combo.findData(want) if want else -1
        self.fps_combo.setCurrentIndex(index if index >= 0 else 0)
        self.fps_combo.blockSignals(False)
        self._populating = False

    def _apply_transform_ui(self, settings: dict) -> None:
        self._rotation = int(settings.get("rotation", 0)) % 360
        self.flip_h_action.blockSignals(True)
        self.flip_v_action.blockSignals(True)
        self.flip_h_action.setChecked(bool(settings.get("flip_h", False)))
        self.flip_v_action.setChecked(bool(settings.get("flip_v", False)))
        self.flip_h_action.blockSignals(False)
        self.flip_v_action.blockSignals(False)
        self._update_rotate_label()

    def _launch_capture(self) -> None:
        self._stop_capture()
        if self._camera is None:
            return

        width, height = self.resolution_combo.currentData() or (None, None)
        fps = self.fps_combo.currentData()

        self._capture = CaptureThread(self._camera, width, height, fps, parent=self)
        self._capture.set_transform(
            self._rotation,
            self.flip_h_action.isChecked(),
            self.flip_v_action.isChecked(),
        )
        self._capture.frameReady.connect(self._on_frame)
        self._capture.stats.connect(self._on_stats)
        self._capture.opened.connect(self._on_opened)
        self._capture.error.connect(self._on_capture_error)
        self._capture.start()

        self.status_camera.setText(f"{self._camera.name} — {self._camera.path}")
        self._store_camera_settings()

    def _stop_capture(self) -> None:
        if self._capture is not None:
            self._capture.request_stop()
            self._capture.stop()
            self._capture = None

    # ------------------------------------------------------------------
    # Acquisition slots
    # ------------------------------------------------------------------
    def _on_frame(self, qimage, frame, index: int) -> None:
        self._last_frame = frame
        self.image_view.set_image(qimage)

    def _on_opened(self, width: int, height: int) -> None:
        self._actual_resolution = (width, height)
        self._refresh_info()

    def _on_stats(self, fps: float) -> None:
        self._current_fps = fps
        self._refresh_info()

    def _refresh_info(self) -> None:
        width, height = self._actual_resolution
        parts = []
        if width and height:
            parts.append(f"{width} × {height}")
        if self._current_fps:
            parts.append(f"{self._current_fps:.1f} fps")
        self.status_info.setText("   ".join(parts))

    def _on_capture_error(self, message: str) -> None:
        self.statusBar().showMessage(message, 10000)
        QMessageBox.warning(self, __app_name__, message)

    # ------------------------------------------------------------------
    # Rotation / mirroring
    # ------------------------------------------------------------------
    def _update_rotate_label(self) -> None:
        self.rotate_action.setText(tr("rotate", degrees=self._rotation))

    def _rotate(self) -> None:
        self._rotation = (self._rotation + 90) % 360
        self._update_rotate_label()
        self._apply_transform_runtime()

    def _on_flip_toggled(self, _checked: bool) -> None:
        self._apply_transform_runtime()

    def _apply_transform_runtime(self) -> None:
        if self._capture is not None:
            self._capture.set_transform(
                self._rotation,
                self.flip_h_action.isChecked(),
                self.flip_v_action.isChecked(),
            )
        self._store_camera_settings()

    # ------------------------------------------------------------------
    # Resolution / fps changes
    # ------------------------------------------------------------------
    def _on_resolution_changed(self, _index: int) -> None:
        if self._populating or self._camera is None:
            return
        self._launch_capture()

    def _on_fps_changed(self, _index: int) -> None:
        if self._populating or self._camera is None:
            return
        self._launch_capture()

    # ------------------------------------------------------------------
    # Camera settings persistence
    # ------------------------------------------------------------------
    def _store_camera_settings(self) -> None:
        if self._camera is None:
            return
        width, height = self.resolution_combo.currentData() or (None, None)
        self._camera_settings = {
            "rotation": self._rotation,
            "flip_h": self.flip_h_action.isChecked(),
            "flip_v": self.flip_v_action.isChecked(),
            "width": width,
            "height": height,
            "fps": self.fps_combo.currentData(),
        }
        self.settings.set_camera_settings(self._camera.key, self._camera_settings)
        self.settings.save()

    # ------------------------------------------------------------------
    # Photos
    # ------------------------------------------------------------------
    def save_photo(self) -> None:
        if self._last_frame is None:
            self.statusBar().showMessage(tr("no_image_to_save"), 4000)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = str(Path(self.settings.image_dir()) / f"microscope_{timestamp}.png")
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_image_title"), default_path, tr("filter_images")
        )
        if not path:
            return

        path = self._ensure_extension(path, IMAGE_EXTENSIONS, ".png")
        import cv2

        extension = Path(path).suffix.lower()
        if extension == ".png":
            params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
        elif extension in (".jpg", ".jpeg"):
            params = [cv2.IMWRITE_JPEG_QUALITY, 95]
        else:
            params = []

        if cv2.imwrite(path, self._last_frame, params):
            self.settings.set("last_image_dir", str(Path(path).parent))
            self.settings.save()
            self.statusBar().showMessage(tr("image_saved", path=path), 6000)
        else:
            QMessageBox.warning(self, __app_name__, tr("save_failed", path=path))

    # ------------------------------------------------------------------
    # Video recording
    # ------------------------------------------------------------------
    def _on_record_toggled(self, checked: bool) -> None:
        if self._record_guard:
            return
        if checked:
            self._start_recording()
        else:
            self._stop_recording()

    def _start_recording(self) -> None:
        if self._capture is None or self._last_frame is None:
            self.statusBar().showMessage(tr("no_video_stream"), 4000)
            self._set_record_checked(False)
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = str(Path(self.settings.video_dir()) / f"microscope_{timestamp}.mp4")
        path, _ = QFileDialog.getSaveFileName(
            self, tr("save_video_title"), default_path, tr("filter_videos")
        )
        if not path:
            self._set_record_checked(False)
            return

        path = self._ensure_extension(path, VIDEO_EXTENSIONS, ".mp4")
        height, width = self._last_frame.shape[:2]
        fps = self._current_fps or self.fps_combo.currentData() or 30.0

        recorder = VideoRecorder(
            path,
            width,
            height,
            fps=fps,
            codec=self.settings.get("video_codec", "libx264"),
            crf=self.settings.get("video_crf", 23),
            preset=self.settings.get("video_preset", "veryfast"),
        )
        recorder.start()
        self._recorder = recorder
        self._capture.recorder = recorder.submit

        self._record_seconds = 0
        self._record_timer.start()
        self._set_record_checked(True)
        self.record_action.setText(tr("stop"))
        self._set_controls_enabled(False)
        self.statusBar().showMessage(tr("recording_started", path=path), 5000)
        self._on_record_tick()

    def _stop_recording(self, silent: bool = False) -> None:
        recorder = self._recorder
        self._recorder = None
        if self._capture is not None:
            self._capture.recorder = None
        self._record_timer.stop()
        self._set_record_checked(False)
        self.record_action.setText(tr("record"))
        if self._camera is not None:
            self._set_controls_enabled(True)

        if recorder is None:
            self.status_recording.setText("")
            return

        recorder.close()
        self.status_recording.setText("")
        if recorder.error:
            QMessageBox.warning(self, __app_name__, recorder.error)
        else:
            self.settings.set("last_video_dir", str(Path(recorder.path).parent))
            self.settings.save()
            if not silent:
                self.statusBar().showMessage(
                    tr(
                        "video_saved",
                        path=recorder.path,
                        frames=recorder.frames_written,
                        dropped=recorder.frames_dropped,
                    ),
                    8000,
                )

    def _on_record_tick(self) -> None:
        self._record_seconds += 1
        minutes, seconds = divmod(self._record_seconds, 60)
        hours, minutes = divmod(minutes, 60)
        stamp = (
            f"{hours:d}:{minutes:02d}:{seconds:02d}"
            if hours
            else f"{minutes:02d}:{seconds:02d}"
        )
        self.status_recording.setText(tr("recording_status", time=stamp))

    def _set_record_checked(self, checked: bool) -> None:
        self._record_guard = True
        self.record_action.setChecked(checked)
        self._record_guard = False

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def open_settings(self) -> None:
        original = (
            self._rotation,
            self.flip_h_action.isChecked(),
            self.flip_v_action.isChecked(),
        )
        video = {
            "codec": self.settings.get("video_codec", "libx264"),
            "crf": self.settings.get("video_crf", 23),
            "preset": self.settings.get("video_preset", "veryfast"),
        }
        dialog = SettingsDialog(
            self,
            self._camera_settings,
            video,
            self._video_encoders,
            language=self.settings.get("language", "system"),
        )
        dialog.transformChanged.connect(self._on_transform_from_dialog)
        dialog.reset_button.clicked.connect(dialog.reset_to_defaults)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            values = dialog.video_values()
            self.settings.set("video_codec", values["codec"])
            self.settings.set("video_crf", values["crf"])
            self.settings.set("video_preset", values["preset"])

            language = dialog.language_value()
            if language != self.settings.get("language"):
                self.settings.set("language", language)
                set_language(language)
                self.retranslate_ui()
            self.settings.save()
            self._store_camera_settings()
        else:
            # Cancel: restore the previous transform.
            self._rotation = original[0]
            self.flip_h_action.blockSignals(True)
            self.flip_v_action.blockSignals(True)
            self.flip_h_action.setChecked(original[1])
            self.flip_v_action.setChecked(original[2])
            self.flip_h_action.blockSignals(False)
            self.flip_v_action.blockSignals(False)
            self._update_rotate_label()
            self._apply_transform_runtime()

    def _on_transform_from_dialog(
        self, rotation: int, flip_h: bool, flip_v: bool
    ) -> None:
        self._rotation = int(rotation) % 360
        self.flip_h_action.blockSignals(True)
        self.flip_v_action.blockSignals(True)
        self.flip_h_action.setChecked(flip_h)
        self.flip_v_action.setChecked(flip_v)
        self.flip_h_action.blockSignals(False)
        self.flip_v_action.blockSignals(False)
        self._update_rotate_label()
        self._apply_transform_runtime()

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def image_view_fit(self) -> None:
        self.image_view.fit()

    def _set_controls_enabled(self, enabled: bool) -> None:
        self.camera_combo.setEnabled(enabled)
        self.resolution_combo.setEnabled(enabled)
        self.fps_combo.setEnabled(enabled)
        self.refresh_action.setEnabled(enabled)
        self.rotate_action.setEnabled(enabled)
        self.flip_h_action.setEnabled(enabled)
        self.flip_v_action.setEnabled(enabled)
        self.settings_action.setEnabled(enabled)

    @staticmethod
    def _ensure_extension(path: str, extensions: list, default: str) -> str:
        if Path(path).suffix.lower() in extensions:
            return path
        return path + default

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self._stop_recording(silent=True)
        self._stop_capture()
        self._store_camera_settings()
        try:
            self.settings.set(
                "window_geometry",
                bytes(self.saveGeometry().toBase64()).decode("ascii"),
            )
        except Exception:
            pass
        self.settings.save()
        super().closeEvent(event)
