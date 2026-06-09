import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import CircleEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class Circle2PCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "P1"
        self._p1: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "P1":
            return "CÍRCULO-2P ▶ Especifique primer extremo del diámetro:"
        return "CÍRCULO-2P ▶ Especifique segundo extremo del diámetro:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "P1":
            self._p1 = world_pt
            self._phase = "P2"
        elif self._phase == "P2":
            self._create(world_pt)

    def on_enter(self, text: str = ""):
        if self._phase == "P1":
            pt = parse_coord_input(text)
            if pt is not None:
                self._p1 = pt; self._phase = "P2"
        elif self._phase == "P2":
            pt = parse_coord_input(text, self._p1, self._cursor_dir())
            if pt is not None:
                self._create(pt)

    def _create(self, p2: QPointF):
        cx = (self._p1.x() + p2.x()) / 2
        cy = (self._p1.y() + p2.y()) / 2
        r = math.hypot(p2.x() - self._p1.x(), p2.y() - self._p1.y()) / 2
        if r > 0:
            self.doc.push_undo()
            self.doc.add_entity(CircleEntity(cx, cy, r))
            self.log(f"Círculo 2P creado (r={r:.2f}).")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "P2" and self._p1:
            from PySide6.QtCore import QPointF
            cx = (self._p1.x() + self._mouse.x()) / 2
            cy = (self._p1.y() + self._mouse.y()) / 2
            r = math.hypot(self._mouse.x() - self._p1.x(), self._mouse.y() - self._p1.y()) / 2
            scx, scy = viewport.world_to_screen(cx, cy)
            sr = r * viewport.zoom
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(scx, scy), sr, sr)

    def _cursor_dir(self):
        if self._p1:
            return (self._mouse.x() - self._p1.x(), self._mouse.y() - self._p1.y())
        return (1.0, 0.0)
