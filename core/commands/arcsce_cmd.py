import math
from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import ArcEntity
from core.geometry          import parse_coord_input
from core.arc_geom          import arc_from_sce
from core.commands.base_command import BaseCommand

class ArcSCECommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "START"
        self._start: QPointF | None = None
        self._center: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "START":
            return "ARCO-SCE ▶ Especifique punto inicial:"
        elif self._phase == "CENTER":
            return "ARCO-SCE ▶ Especifique centro:"
        return "ARCO-SCE ▶ Especifique fin:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "START":
            self._start = world_pt; self._phase = "CENTER"
        elif self._phase == "CENTER":
            self._center = world_pt; self._phase = "END"
        elif self._phase == "END":
            self._create(world_pt)

    def on_enter(self, text: str = ""):
        if self._phase == "START":
            pt = parse_coord_input(text)
            if pt is not None:
                self._start = pt; self._phase = "CENTER"
        elif self._phase == "CENTER":
            pt = parse_coord_input(text, self._start)
            if pt is not None:
                self._center = pt; self._phase = "END"
        elif self._phase == "END":
            pt = parse_coord_input(text, self._center, self._cursor_dir())
            if pt is not None:
                self._create(pt)

    def _create(self, end: QPointF):
        res = arc_from_sce(self._start, self._center, end)
        if res:
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(*res))
            self.log("Arco SCE creado.")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "CENTER" and self._start:
            sx, sy = viewport.world_to_screen(self._start.x(), self._start.y())
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawEllipse(QPointF(sx, sy), 3, 3)
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(sx, sy), QPointF(smx, smy))
        elif self._phase == "END" and self._start and self._center:
            res = arc_from_sce(self._start, self._center, self._mouse)
            if res:
                _, _, r, sa, span = res
                cx, cy = self._center.x(), self._center.y()
                segments = 64
                pts = []
                for i in range(segments + 1):
                    a_deg = sa + span * i / segments
                    a_rad = math.radians(a_deg)
                    wx = cx + r * math.cos(a_rad)
                    wy = cy + r * math.sin(a_rad)
                    sx, sy = viewport.world_to_screen(wx, wy)
                    pts.append(QPointF(sx, sy))
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(pts)

    def _cursor_dir(self):
        if self._center:
            return (self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
        return (1.0, 0.0)
