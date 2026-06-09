import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui  import QPainter, QPen, QColor
from core.document import Document
from core.entities import ArcEntity, LineEntity
from core.geometry import parse_coord_input
from core.commands.base_command import BaseCommand

class ArcContinueCommand(BaseCommand):
    """Continúa desde el último arco o línea, tangente al segmento anterior."""

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._prev_is_arc = False
        self._prev_tan_angle = 0.0
        self._prev_end = QPointF(0, 0)
        self._prev_start = QPointF(0, 0)
        self._mouse = QPointF(0, 0)

    def _init_from_last(self):
        """Busca la última entidad para obtener dirección tangente."""
        for e in reversed(self.doc.entities):
            if isinstance(e, ArcEntity):
                self._prev_is_arc = True
                self._prev_end = QPointF(e.cx + e.radius * math.cos(math.radians(e.start_angle + e.span_angle)),
                                          e.cy + e.radius * math.sin(math.radians(e.start_angle + e.span_angle)))
                self._prev_tan_angle = math.radians(e.start_angle + e.span_angle + 90)
                return True
            elif isinstance(e, LineEntity):
                self._prev_is_arc = False
                self._prev_end = QPointF(e.x2, e.y2)
                self._prev_start = QPointF(e.x1, e.y1)
                self._prev_tan_angle = math.atan2(e.y2 - e.y1, e.x2 - e.x1)
                return True
        return False

    @property
    def prompt(self):
        return "ARCO-CONT ▶ Especifique punto final:"

    def on_mouse_move(self, world_pt): self._mouse = world_pt

    def on_left_click(self, world_pt):
        self._create(world_pt)

    def on_enter(self, text: str = ""):
        pt = parse_coord_input(text, self._prev_end)
        if pt: self._create(pt)

    def _create(self, end: QPointF):
        if not self._init_from_last():
            self.log("No hay entidad previa para continuar.")
            self.is_done = True
            return
        dx = end.x() - self._prev_end.x()
        dy = end.y() - self._prev_end.y()
        d = math.hypot(dx, dy)
        if d == 0:
            self.is_done = True
            return
        # Encontrar centro en la perpendicular a la tangente
        tx = math.cos(self._prev_tan_angle)
        ty = math.sin(self._prev_tan_angle)
        # Vector del extremo al punto final
        chord_mid = QPointF((self._prev_end.x() + end.x()) / 2, (self._prev_end.y() + end.y()) / 2)
        chord_angle = math.atan2(dy, dx)
        diff = (chord_angle - self._prev_tan_angle) % math.pi
        if abs(diff) < 0.001:
            self.log("Puntos colineales con la tangente.")
            self.is_done = True
            return
        r = d / (2 * abs(math.sin(diff)))
        # Normal perpendicular a la tangente
        nx = -ty
        ny = tx
        cx = self._prev_end.x() + nx * r
        cy = self._prev_end.y() + ny * r
        sa = math.degrees(math.atan2(self._prev_end.y() - cy, self._prev_end.x() - cx))
        ea = math.degrees(math.atan2(end.y() - cy, end.x() - cx))
        span = (ea - sa) % 360
        if span > 180: span -= 360
        if diff < 0: span = -abs(span)
        else: span = abs(span)
        if r > 0:
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(cx, cy, r, sa, span))
            self.log("Arco continuado creado.")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._init_from_last():
            ex, ey = viewport.world_to_screen(self._prev_end.x(), self._prev_end.y())
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawEllipse(QPointF(ex, ey), 3, 3)
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(ex, ey), QPointF(smx, smy))
            # Preview con radio calculado
            dx = self._mouse.x() - self._prev_end.x()
            dy = self._mouse.y() - self._prev_end.y()
            d = math.hypot(dx, dy)
            if d > 0:
                tx = math.cos(self._prev_tan_angle)
                ty = math.sin(self._prev_tan_angle)
                chord_angle = math.atan2(dy, dx)
                diff = (chord_angle - self._prev_tan_angle) % math.pi
                if abs(diff) > 0.001:
                    r = d / (2 * abs(math.sin(diff)))
                    nx, ny = -ty, tx
                    cx = self._prev_end.x() + nx * r
                    cy = self._prev_end.y() + ny * r
                    sa = math.degrees(math.atan2(self._prev_end.y() - cy, self._prev_end.x() - cx))
                    ea = math.degrees(math.atan2(self._mouse.y() - cy, self._mouse.x() - cx))
                    span = (ea - sa) % 360
                    if span > 180: span -= 360
                    if diff < 0: span = -abs(span)
                    else: span = abs(span)
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

    def on_escape(self):
        self.is_done = True
        self.log("Arco continuado cancelado.")
