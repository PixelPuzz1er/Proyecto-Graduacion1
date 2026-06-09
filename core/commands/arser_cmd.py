import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt
from core.document import Document
from core.entities import ArcEntity
from core.geometry import parse_coord_input
from core.arc_geom import arc_from_ser
from core.commands.base_command import BaseCommand

def _mouse_to_ser_params(start: QPointF, end: QPointF, mouse: QPointF):
    """Compute radius and bulge direction from mouse via perpendicular bisector."""
    chord_dx = end.x() - start.x()
    chord_dy = end.y() - start.y()
    chord_len = math.hypot(chord_dx, chord_dy)
    if chord_len < 1e-8: return None, True
    mid_x = (start.x() + end.x()) / 2
    mid_y = (start.y() + end.y()) / 2
    perp_dx = -chord_dy
    perp_dy = chord_dx
    perp_len = math.hypot(perp_dx, perp_dy)
    if perp_len < 1e-8: return None, True
    h = ((mouse.x() - mid_x) * perp_dx + (mouse.y() - mid_y) * perp_dy) / perp_len
    radius = math.hypot(chord_len / 2.0, h)
    if radius < chord_len / 2.0: radius = chord_len / 2.0 + 0.001
    if radius < 0.001: radius = 0.001
    return radius, h >= 0

class ArcSERCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "START"
        self._start: QPointF | None = None
        self._end: QPointF | None = None
        self._mouse = QPointF(0, 0)
        self._bulge_up = True

    @property
    def prompt(self):
        if self._phase == "START": return "ARCO-SER ▶ Especifique punto inicial:"
        elif self._phase == "END": return "ARCO-SER ▶ Especifique punto final:"
        return "ARCO-SER ▶ Especifique radio:"

    def on_mouse_move(self, world_pt): self._mouse = world_pt

    def on_left_click(self, world_pt):
        if self._phase == "START":
            self._start = world_pt; self._phase = "END"
        elif self._phase == "END":
            self._end = world_pt; self._phase = "RADIUS"
        elif self._phase == "RADIUS":
            radius, bulge = _mouse_to_ser_params(self._start, self._end, self._mouse)
            if radius is not None:
                self._bulge_up = bulge
                self._create(radius)

    def on_enter(self, text: str = ""):
        if self._phase == "START":
            pt = parse_coord_input(text)
            if pt: self._start = pt; self._phase = "END"
        elif self._phase == "END":
            pt = parse_coord_input(text, self._start)
            if pt: self._end = pt; self._phase = "RADIUS"
        elif self._phase == "RADIUS":
            try:
                r = float(text)
                if r < 0: r = -r; self._bulge_up = False
                self._create(abs(r))
            except ValueError:
                self.log("Radio inválido.")

    def _create(self, radius: float):
        res = arc_from_ser(self._start, self._end, radius, self._bulge_up)
        if res:
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(*res))
            self.log(f"Arco SER creado (radio={radius:.2f}).")
        else:
            self.log("Radio insuficiente para la distancia entre puntos.")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "END" and self._start:
            sx, sy = viewport.world_to_screen(self._start.x(), self._start.y())
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawEllipse(QPointF(sx, sy), 3, 3)
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(sx, sy), QPointF(smx, smy))
        elif self._phase == "RADIUS" and self._start and self._end:
            radius, bulge = _mouse_to_ser_params(self._start, self._end, self._mouse)
            if radius is None: return
            res = arc_from_ser(self._start, self._end, radius, bulge)
            if res:
                cx, cy, _, sa, span = res
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
        if self._start: return (self._mouse.x() - self._start.x(), self._mouse.y() - self._start.y())
        return (1.0, 0.0)
