"""Finestra di dialogo delle impostazioni."""

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

from .recorder import CODEC_LABELS

PRESETS = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"]

ROTATIONS = [(0, "0°"), (90, "90° (orario)"), (180, "180°"), (270, "270° (antiorario)")]


class SettingsDialog(QDialog):
    """Dialogo impostazioni immagine e registrazione.

    I cambi di rotazione e specchiatura vengono applicati in tempo reale
    (segui :attr:`transformChanged`), mentre le opzioni video vengono lette
    alla conferma.
    """

    transformChanged = Signal(int, bool, bool)

    def __init__(self, parent, camera_settings: dict, video: dict, encoders: list):
        super().__init__(parent)
        self.setWindowTitle("Impostazioni")
        self.setModal(True)

        root = QVBoxLayout(self)

        # -- Immagine ------------------------------------------------------
        image_group = QGroupBox("Immagine")
        image_form = QFormLayout(image_group)

        self.rotation_combo = QComboBox()
        for value, label in ROTATIONS:
            self.rotation_combo.addItem(label, value)
        self._select_data(self.rotation_combo, int(camera_settings.get("rotation", 0)))
        image_form.addRow("Rotazione:", self.rotation_combo)

        flips = QHBoxLayout()
        self.flip_h_check = QCheckBox("Orizzontale")
        self.flip_v_check = QCheckBox("Verticale")
        self.flip_h_check.setChecked(bool(camera_settings.get("flip_h", False)))
        self.flip_v_check.setChecked(bool(camera_settings.get("flip_v", False)))
        flips.addWidget(self.flip_h_check)
        flips.addWidget(self.flip_v_check)
        image_form.addRow("Specchia:", flips)
        root.addWidget(image_group)

        # -- Registrazione -------------------------------------------------
        video_group = QGroupBox("Registrazione video")
        video_form = QFormLayout(video_group)

        self.codec_combo = QComboBox()
        for codec in encoders or ["mpeg4"]:
            self.codec_combo.addItem(CODEC_LABELS.get(codec, codec), codec)
        self._select_data(self.codec_combo, video.get("codec", "libx264"))
        video_form.addRow("Codificatore:", self.codec_combo)

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
        video_form.addRow("Qualità (CRF):", quality_row)

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESETS)
        preset = video.get("preset", "veryfast")
        if preset in PRESETS:
            self.preset_combo.setCurrentText(preset)
        video_form.addRow("Velocità:", self.preset_combo)
        root.addWidget(video_group)

        hint = QLabel(
            "CRF più basso = qualità migliore e file più grandi. "
            "La velocità influisce solo sul tempo di codifica."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: palette(mid);")
        root.addWidget(hint)

        # -- Pulsanti ------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.reset_button = QPushButton("Ripristina camera")
        buttons.addButton(self.reset_button, QDialogButtonBox.ButtonRole.ResetRole)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

        # Applicazione in tempo reale della geometria immagine.
        self.rotation_combo.currentIndexChanged.connect(self._emit_transform)
        self.flip_h_check.toggled.connect(self._emit_transform)
        self.flip_v_check.toggled.connect(self._emit_transform)

    # -- Utility -----------------------------------------------------------
    @staticmethod
    def _select_data(combo: QComboBox, value) -> None:
        index = combo.findData(value)
        combo.setCurrentIndex(index if index >= 0 else 0)

    def _emit_transform(self) -> None:
        self.transformChanged.emit(*self.transform_values())

    def reset_to_defaults(self) -> None:
        """Ripristina rotazione e specchiature ai valori predefiniti."""
        self._select_data(self.rotation_combo, 0)
        self.flip_h_check.setChecked(False)
        self.flip_v_check.setChecked(False)
        self._emit_transform()

    # -- Risultati ---------------------------------------------------------
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
