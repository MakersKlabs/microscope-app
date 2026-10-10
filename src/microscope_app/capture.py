"""Thread di acquisizione dei frame dalla telecamera."""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import QMutex, QMutexLocker, QThread, Signal
from PySide6.QtGui import QImage


class CaptureThread(QThread):
    """Legge in continuazione i frame dalla telecamera e li trasforma.

    I frame vengono emessi già ruotati/specchiati verso il thread grafico sotto
    forma di :class:`QImage`; lo stesso array NumPy (BGR) viene inoltrato al
    registratore video, se attivo, tramite il callback :attr:`recorder`.
    """

    frameReady = Signal(QImage, object, int)   # immagine, array BGR, indice
    stats = Signal(float)                       # frame per secondo reali
    opened = Signal(int, int)                   # larghezza, altezza reali
    error = Signal(str)

    def __init__(self, camera, width=None, height=None, fps=None, parent=None):
        super().__init__(parent)
        self.camera = camera
        self._width = width
        self._height = height
        self._fps = fps
        self._rotation = 0
        self._flip_h = False
        self._flip_v = False
        self._running = False
        self._lock = QMutex()
        #: callback opzionale ``callable(frame)`` richiamato con il frame BGR
        self.recorder = None

    # -- Configurazione ---------------------------------------------------
    def set_transform(self, rotation: int, flip_h: bool, flip_v: bool) -> None:
        with QMutexLocker(self._lock):
            self._rotation = int(rotation) % 360
            self._flip_h = bool(flip_h)
            self._flip_v = bool(flip_v)

    def _current_transform(self) -> tuple[int, bool, bool]:
        with QMutexLocker(self._lock):
            return self._rotation, self._flip_h, self._flip_v

    def request_stop(self) -> None:
        self._running = False

    def stop(self, timeout_ms: int = 3000) -> None:
        self._running = False
        if self.isRunning():
            self.wait(timeout_ms)

    # -- Loop --------------------------------------------------------------
    def run(self) -> None:  # noqa: C901 - flusso lineare ma con più controlli
        import cv2

        capture = cv2.VideoCapture(self.camera.index, cv2.CAP_V4L2)
        if not capture.isOpened():
            self.error.emit(
                f"Impossibile aprire la telecamera {self.camera.path}."
            )
            return

        try:
            capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
            if self._width and self._height:
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, float(self._width))
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, float(self._height))
            if self._fps:
                capture.set(cv2.CAP_PROP_FPS, float(self._fps))
            try:
                capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass

            ok, frame = capture.read()
            if not ok or frame is None:
                self.error.emit(
                    f"Nessun frame dalla telecamera {self.camera.path}. "
                    "Verifica che non sia usata da un altro programma."
                )
                return

            height, width = frame.shape[:2]
            self.opened.emit(width, height)

            self._running = True
            count = 0
            started = time.monotonic()
            failures = 0

            while self._running:
                ok, frame = capture.read()
                if not ok or frame is None:
                    failures += 1
                    if failures > 60:
                        self.error.emit("Flusso video interrotto.")
                        break
                    time.sleep(0.01)
                    continue
                failures = 0

                rotation, flip_h, flip_v = self._current_transform()
                image = frame
                if rotation == 90:
                    image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                elif rotation == 180:
                    image = cv2.rotate(image, cv2.ROTATE_180)
                elif rotation == 270:
                    image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                if flip_h:
                    image = cv2.flip(image, 1)
                if flip_v:
                    image = cv2.flip(image, 0)

                if not image.flags["C_CONTIGUOUS"]:
                    image = np.ascontiguousarray(image)

                img_h, img_w = image.shape[:2]
                qimage = QImage(
                    image.data,
                    img_w,
                    img_h,
                    image.strides[0],
                    QImage.Format.Format_BGR888,
                ).copy()

                self.frameReady.emit(qimage, image, count)

                callback = self.recorder
                if callback is not None:
                    try:
                        callback(image)
                    except Exception:
                        pass

                count += 1
                now = time.monotonic()
                if now - started >= 1.0:
                    self.stats.emit(count / (now - started))
                    count = 0
                    started = now
        finally:
            capture.release()
