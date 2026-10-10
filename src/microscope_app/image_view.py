"""Image view widget with zoom, pan and fit."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView

MIN_SCALE = 0.02
MAX_SCALE = 60.0


class ImageView(QGraphicsView):
    """Interactive image view.

    * mouse wheel: zoom towards the pointer;
    * left button dragged: pan;
    * right click: fit the image to the window.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)

        self._item = QGraphicsPixmapItem()
        self._item.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
        self._scene.addItem(self._item)

        self.setRenderHints(
            QPainter.RenderHint.SmoothPixmapTransform
            | QPainter.RenderHint.Antialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setBackgroundBrush(QColor("#101216"))
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._has_image = False
        self._fit_mode = True

    # -- Content -----------------------------------------------------------
    def has_image(self) -> bool:
        return self._has_image

    def set_image(self, qimage) -> None:
        size_changed = (
            not self._has_image
            or qimage.size() != self._item.pixmap().size()
        )
        self._item.setPixmap(QPixmap.fromImage(qimage))
        if not self._has_image:
            self._has_image = True
        if size_changed:
            self._scene.setSceneRect(self._item.boundingRect())
            if self._fit_mode:
                self.fit()

    def clear(self) -> None:
        self._item.setPixmap(QPixmap())
        self._has_image = False
        self._fit_mode = True

    # -- Navigation --------------------------------------------------------
    def fit(self) -> None:
        if not self._has_image:
            return
        self._scene.setSceneRect(self._item.boundingRect())
        self.resetTransform()
        self.fitInView(self._item, Qt.AspectRatioMode.KeepAspectRatio)
        self._fit_mode = True

    def _scale(self) -> float:
        return self.transform().m11()

    def zoom(self, factor: float) -> None:
        if not self._has_image:
            return
        new_scale = self._scale() * factor
        if new_scale < MIN_SCALE or new_scale > MAX_SCALE:
            return
        self.scale(factor, factor)
        self._fit_mode = False

    def zoom_in(self) -> None:
        self.zoom(1.25)

    def zoom_out(self) -> None:
        self.zoom(1 / 1.25)

    # -- Events ------------------------------------------------------------
    def wheelEvent(self, event) -> None:  # noqa: N802 (Qt API)
        delta = event.angleDelta().y()
        if delta == 0:
            super().wheelEvent(event)
            return
        self.zoom(1.25 if delta > 0 else 1 / 1.25)
        event.accept()

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        if event.button() == Qt.MouseButton.RightButton:
            self.fit()
            event.accept()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self._fit_mode = False
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802 (Qt API)
        self.fit()
        event.accept()

    def keyPressEvent(self, event) -> None:  # noqa: N802 (Qt API)
        key = event.key()
        if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
            self.zoom_in()
            event.accept()
            return
        if key in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
            self.zoom_out()
            event.accept()
            return
        if key == Qt.Key.Key_F:
            self.fit()
            event.accept()
            return
        super().keyPressEvent(event)
