import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import CircleEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

def _circle_from_3p(p1, p2, p3):
    ax, ay = p1.x(), p1.y()
    bx, by = p2.x(), p2.y()
    cx, cy = p3.x(), p3.y()
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    ux = ((ax*ax + ay*ay) * (by - cy) + (bx*bx + by*by) * (cy - ay) + (cx*cx + cy*cy) * (ay - by)) / d
    uy = ((ax*ax + ay*ay) * (cx - bx) + (bx*bx + by*by) * (ax - cx) + (cx*cx + cy*cy) * (bx - ax)) / d
    r = math.hypot(ux - ax, uy - ay)
    return ux, uy, r

class Circle3PCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "P1"
        self._points: list[QPointF] = []
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        phases = {0: "primer", 1: "segundo", 2: "tercer"}
        return f"CÍRCULO-3P ▶ Especifique {phases.get(len(self._points), 'siguiente')} punto:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        self._points.append(world_pt)
        if len(self._points) == 3:
            self._create()

    def on_enter(self, text: str = ""):
        if not self._points:
            pt = parse_coord_input(text)
            if pt is not None:
                self._points.append(pt)
                return
        ref = self._points[-1] if self._points else None
        pt = parse_coord_input(text, ref, self._cursor_dir())
        if pt is not None:
            self._points.append(pt)
            if len(self._points) == 3:
                self._create()
        else:
            self.log("Punto inválido.")

    def _create(self):
        result = _circle_from_3p(self._points[0], self._points[1], self._points[2])
        if result:
            cx, cy, r = result
            self.doc.push_undo()
            self.doc.add_entity(CircleEntity(cx, cy, r))
            self.log(f"Círculo 3P creado (r={r:.2f}).")
        else:
            self.log("Los puntos son colineales.")
        self.is_done = True

    def draw_preview(self, painter, viewport):
        from PySide6.QtCore import QPointF
        pts = [QPointF(p.x(), p.y()) for p in self._points]
        pts.append(self._mouse)
        for p in pts[:-1]:
            sx, sy = viewport.world_to_screen(p.x(), p.y())
            painter.setPen(QPen(QColor("#00FF00"), 2))
            painter.drawEllipse(QPointF(sx, sy), 3, 3)
        if len(pts) == 3:
            result = _circle_from_3p(pts[0], pts[1], pts[2])
            if result:
                cx, cy, r = result
                scx, scy = viewport.world_to_screen(cx, cy)
                sr = r * viewport.zoom
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawEllipse(QPointF(scx, scy), sr, sr)

    def _cursor_dir(self):
        if self._points:
            return (self._mouse.x() - self._points[-1].x(), self._mouse.y() - self._points[-1].y())
        return (1.0, 0.0)
