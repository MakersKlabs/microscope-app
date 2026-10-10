"""Settings dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
)

from .i18n import tr
from .recorder import CODEC_LABELS

PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"]


def _rotation_options() -> list:
    return [
        (0, tr("rotation_0")),
        (90, tr("rotation_90")),
        (180, tr("rotation_180")),
        (270, tr("rotation_270")),
    ]


class SettingsDialog(QDialog):
    """Image and recording settings dialog.

    Rotation and mirror changes are applied live (see :attr:`transformChanged`),
    while the video options are read on confirmation.
    """

    transformChanged = Signal(int, bool, bool)

    def __init__(
        self,
        parent,
        camera_settings: dict,
        video: dict,
        encoders: list,
        language: str = "system",
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setModal(True)

        root = QVBoxLayout(self)

        # -- Language ------------------------------------------------------
        language_group = QGroupBox(tr("group_language"))
        language_form = QFormLayout(language_group)
        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("language_system"), "system")
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Italiano", "it")
        self._select_data(self.language_combo, language)
        language_form.addRow(tr("language_label"), self.language_combo)
        root.addWidget(language_group)

        # -- Image ---------------------------------------------------------
        image_group = QGroupBox(tr("group_image"))
        image_form = QFormLayout(image_group)

        self.rotation_combo = QComboBox()
        for value, label in _rotation_options():
            self.rotation_combo.addItem(label, value)
        self._select_data(self.rotation_combo, int(camera_settings.get("rotation", 0)))
        image_form.addRow(tr("rotation_label"), self.rotation_combo)

        flips = QHBoxLayout()
        self.flip_h_check = QCheckBox(tr("mirror_horizontal"))
        self.flip_v_check = QCheckBox(tr("mirror_vertical"))
        self.flip_h_check.setChecked(bool(camera_settings.get("flip_h", False)))
        self.flip_v_check.setChecked(bool(camera_settings.get("flip_v", False)))
        flips.addWidget(self.flip_h_check)
        flips.addWidget(self.flip_v_check)
        image_form.addRow(tr("mirror_label"), flips)
        root.addWidget(image_group)

        # -- Recording -----------------------------------------------------
        video_group = QGroupBox(tr("group_video"))
        video_form = QFormLayout(video_group)

        self.codec_combo = QComboBox()
        for codec in encoders or ["mpeg4"]:
            self.codec_combo.addItem(CODEC_LABELS.get(codec, codec), codec)
        self._select_data(self.codec_combo, video.get("codec", "libx264"))
        video_form.addRow(tr("encoder_label"), self.codec_combo)

        quality_row = QHBoxLayout()
        self.crf_slider = QSlider(Qt.Orientation.Horizontal)
        self.crf_slider.setRange(15, 35)
        self.crf_slider.setValue(int(video.get("crf", 23)))
        self.crf_value = QLabel(str(self.crf_slider.value()))
        self.crf_slider.valueChanged.connect(
            lambda value: self.crf_value.setText(str(value))
        )
        quality_row.addWidget(self.crf_slider, 1)
        quality_row.addWidget(self.crf_value)
        video_form.addRow(tr("quality_label"), quality_row)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESETS)
        preset = video.get("preset", "veryfast")
        if preset in PRESETS:
            self.preset_combo.setCurrentText(preset)
        video_form.addRow(tr("speed_label"), self.preset_combo)
        root.addWidget(video_group)

        hint = QLabel(tr("video_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: palette(mid);")
        root.addWidget(hint)

        # -- Buttons -------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText(tr("ok"))
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(tr("cancel"))
        self.reset_button = QPushButton(tr("reset_camera"))
        buttons.addButton(self.reset_button, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        # Live application of the image geometry.
        self.rotation_combo.currentIndexChanged.connect(self._emit_transform)
        self.flip_h_check.toggled.connect(self._emit_transform)
        self.flip_v_check.toggled.connect(self._emit_transform)

    # -- Utilities ---------------------------------------------------------
    @staticmethod
    def _select_data(combo: QComboBox, value) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _emit_transform(self) -> None:
        self.transformChanged.emit(*self.transform_values())

    def reset_to_defaults(self) -> None:
        """Restore rotation and mirroring to their default values."""
        self._select_data(self.rotation_combo, 0)
        self.flip_h_check.setChecked(False)
        self.flip_v_check.setChecked(False)
        self._emit_transform()

    # -- Results -----------------------------------------------------------
    def transform_values(self) -> tuple[int, bool, bool]:
        return (
            int(self.rotation_combo.currentData() or 0),
            self.flip_h_check.isChecked(),
            self.flip_v_check.isChecked(),
        )

    def video_values(self) -> dict:
        return {
            "codec": self.codec_combo.currentData() or "mpeg4",
            "crf": int(self.crf_slider.value()),
            "preset": self.preset_combo.currentText(),
        }

    def language_value(self) -> str:
        return self.language_combo.currentData() or "system"
