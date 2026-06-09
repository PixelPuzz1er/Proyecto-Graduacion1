import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui  import QPainter, QPen, QColor
from core.document import Document
from core.entities import ArcEntity
from core.geometry import parse_coord_input
from core.arc_geom import arc_from_csl
from core.commands.base_command import BaseCommand

class ArcCSLCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "CENTER"
        self._center: QPointF | None = None
        self._start: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self):
        if self._phase == "CENTER": return "ARCO-CSL ▶ Especifique centro:"
        elif self._phase == "START": return "ARCO-CSL ▶ Especifique inicio:"
        return "ARCO-CSL ▶ Especifique longitud de cuerda:"

    def on_mouse_move(self, world_pt): self._mouse = world_pt

    def on_left_click(self, world_pt):
        if self._phase == "CENTER":
            self._center = world_pt; self._phase = "START"
        elif self._phase == "START":
            self._start = world_pt; self._phase = "LENGTH"
        elif self._phase == "LENGTH":
            cl = math.hypot(world_pt.x() - self._center.x(), world_pt.y() - self._center.y())
            self._create(cl)

    def on_enter(self, text: str = ""):
        if self._phase == "CENTER":
            pt = parse_coord_input(text)
            if pt: self._center = pt; self._phase = "START"
        elif self._phase == "START":
            pt = parse_coord_input(text, self._center)
            if pt: self._start = pt; self._phase = "LENGTH"
        elif self._phase == "LENGTH":
            try: self._create(float(text))
            except ValueError: self.log("Longitud inválida.")

    def _create(self, chord_length: float):
        res = arc_from_csl(self._center, self._start, chord_length)
        if res:
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(*res))
            self.log(f"Arco CSL creado (cuerda={chord_length:.2f}).")
        else:
            self.log("Radio insuficiente para la cuerda.")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        if self._phase == "START" and self._center:
            cx, cy = viewport.world_to_screen(self._center.x(), self._center.y())
            painter.setPen(QPen(QColor("#FFFF00"), 2))
            painter.drawEllipse(QPointF(cx, cy), 3, 3)
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(cx, cy), QPointF(smx, smy))
        elif self._phase == "LENGTH" and self._center and self._start:
            r = math.hypot(self._start.x() - self._center.x(), self._start.y() - self._center.y())
            sa = math.degrees(math.atan2(self._start.y() - self._center.y(), self._start.x() - self._center.x()))
            cl = math.hypot(self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
            half_chord = cl / 2.0
            span = 2 * math.degrees(math.asin(min(half_chord / (r or 1), 1.0)))
            segments = 64; cx, cy = self._center.x(), self._center.y(); pts = []
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
