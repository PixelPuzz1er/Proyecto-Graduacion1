import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui  import QPainter, QPen, QColor

from core.document          import Document
from core.entities          import ArcEntity
from core.geometry          import parse_coord_input
from core.arc_geom          import arc_from_sca
from core.commands.base_command import BaseCommand

class ArcSCACommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "START"
        self._start: QPointF | None = None
        self._center: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "START":
            return "ARCO-SCA ▶ Especifique punto inicial:"
        elif self._phase == "CENTER":
            return "ARCO-SCA ▶ Especifique centro:"
        return "ARCO-SCA ▶ Especifique ángulo incluido:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "START":
            self._start = world_pt; self._phase = "CENTER"
        elif self._phase == "CENTER":
            self._center = world_pt; self._phase = "ANGLE"
        elif self._phase == "ANGLE":
            ea = math.degrees(math.atan2(world_pt.y() - self._center.y(), world_pt.x() - self._center.x()))
            sa = math.degrees(math.atan2(self._start.y() - self._center.y(), self._start.x() - self._center.x()))
            included = (ea - sa) % 360
            if included > 180:
                included -= 360
            self._create(included)

    def on_enter(self, text: str = ""):
        text = text.strip()
        if self._phase == "START":
            pt = parse_coord_input(text)
            if pt is not None:
                self._start = pt; self._phase = "CENTER"
        elif self._phase == "CENTER":
            pt = parse_coord_input(text, self._start)
            if pt is not None:
                self._center = pt; self._phase = "ANGLE"
        elif self._phase == "ANGLE":
            try:
                included = float(text)
                self._create(included)
            except ValueError:
                self.log("Ángulo inválido. Ingrese un número (ej: 90).")

    def _create(self, included_angle: float):
        res = arc_from_sca(self._start, self._center, included_angle)
        if res:
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(*res))
            self.log(f"Arco SCA creado (ángulo={included_angle:.2f}°).")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "CENTER" and self._start:
            sx, sy = viewport.world_to_screen(self._start.x(), self._start.y())
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawEllipse(QPointF(sx, sy), 3, 3)
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(sx, sy), QPointF(smx, smy))
        elif self._phase == "ANGLE" and self._start and self._center:
            res = arc_from_sca(self._start, self._center, 90.0)
            if res:
                _, _, r, sa, _ = res
                cx, cy = self._center.x(), self._center.y()
                ea = math.degrees(math.atan2(self._mouse.y() - cy, self._mouse.x() - cx))
                included = (ea - sa) % 360
                if included > 180:
                    included -= 360
                segments = 64
                pts = []
                for i in range(segments + 1):
                    a_deg = sa + included * i / segments
                    a_rad = math.radians(a_deg)
                    wx = cx + r * math.cos(a_rad)
                    wy = cy + r * math.sin(a_rad)
                    sx, sy = viewport.world_to_screen(wx, wy)
                    pts.append(QPointF(sx, sy))
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(pts)

    def _cursor_dir(self):
        if self._center:
            return (self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
        return (1.0, 0.0)
