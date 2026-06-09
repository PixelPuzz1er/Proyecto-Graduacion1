import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui  import QPainter, QPen, QColor
from core.document import Document
from core.entities import ArcEntity
from core.geometry import parse_coord_input
from core.arc_geom import arc_from_cse
from core.commands.base_command import BaseCommand

class ArcCSECommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "CENTER"
        self._center: QPointF | None = None
        self._start: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self):
        if self._phase == "CENTER": return "ARCO-CSE ▶ Especifique centro:"
        elif self._phase == "START": return "ARCO-CSE ▶ Especifique inicio:"
        return "ARCO-CSE ▶ Especifique fin:"

    def on_mouse_move(self, world_pt): self._mouse = world_pt

    def on_left_click(self, world_pt):
        if self._phase == "CENTER":
            self._center = world_pt; self._phase = "START"
        elif self._phase == "START":
            self._start = world_pt; self._phase = "END"
        elif self._phase == "END":
            res = arc_from_cse(self._center, self._start, world_pt)
            if res:
                self.doc.push_undo()
                self.doc.add_entity(ArcEntity(*res))
                self.log("Arco CSE creado.")
            self.is_done = True

    def on_enter(self, text: str = ""):
        if self._phase == "CENTER":
            pt = parse_coord_input(text)
            if pt: self._center = pt; self._phase = "START"
        elif self._phase == "START":
            pt = parse_coord_input(text, self._center)
            if pt: self._start = pt; self._phase = "END"
        elif self._phase == "END":
            pt = parse_coord_input(text, self._center, self._cursor_dir())
            if pt:
                res = arc_from_cse(self._center, self._start, pt)
                if res:
                    self.doc.push_undo()
                    self.doc.add_entity(ArcEntity(*res))
                    self.log("Arco CSE creado.")
                self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "START" and self._center:
            cx, cy = viewport.world_to_screen(self._center.x(), self._center.y())
            painter.setPen(QPen(QColor("#FFFF00"), 2))
            painter.drawEllipse(QPointF(cx, cy), 3, 3)
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(cx, cy), QPointF(smx, smy))
        elif self._phase == "END" and self._center and self._start:
            res = arc_from_cse(self._center, self._start, self._mouse)
            if res:
                cx, cy, r, sa, span = res
                segments = 64; pts = []
                for i in range(segments + 1):
                    a_deg = sa + span * i / segments
                    a_rad = math.radians(a_deg)
                    wx = cx + r * math.cos(a_rad); wy = cy + r * math.sin(a_rad)
                    sx, sy = viewport.world_to_screen(wx, wy)
                    pts.append(QPointF(sx, sy))
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(pts)

    def _cursor_dir(self):
        if self._center: return (self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
        return (1.0, 0.0)
