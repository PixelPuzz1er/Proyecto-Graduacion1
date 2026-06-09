import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui  import QPainter, QPen, QColor

from core.document          import Document
from core.entities          import HatchEntity
from core.commands.base_command import BaseCommand

HATCH_COLOR = "#88CCFF"

class HatchCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "PICK_INTERIOR"
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "PICK_INTERIOR":
            return "SOMBREADO ▶ Haga clic en el interior de un área cerrada [Seleccionar]:"
        return "SOMBREADO ▶ Seleccione objetos (Enter=confirmar):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "PICK_INTERIOR":
            self._try_hatch_at(world_pt)
        elif self._phase == "SELECT":
            self.doc.select_at(world_pt.x(), world_pt.y())

    def on_right_click(self, world_pt: QPointF):
        if self._phase == "PICK_INTERIOR":
            self._phase = "SELECT"
        else:
            self.on_escape()

    def on_enter(self, text: str = ""):
        if self._phase == "PICK_INTERIOR":
            self._try_hatch_at(self._mouse)
        elif self._phase == "SELECT":
            self._selection_enter("SOMBREADO", self._hatch_selected)

    def _try_hatch_at(self, pt: QPointF):
        boundary = self._find_closest_boundary(pt.x(), pt.y())
        if boundary and len(boundary) >= 3:
            self.doc.push_undo()
            hatch = HatchEntity(boundary, pattern="SOLID", color=HATCH_COLOR)
            self.doc.add_entity(hatch)
            self.log(f"Sombreado aplicado en ({pt.x():.2f}, {pt.y():.2f}).")
            self.is_done = True
        else:
            self.log("No se encontró un área cerrada. Clic derecho = seleccionar objetos.")

    def _find_closest_boundary(self, px: float, py: float):
        best = None
        best_dist = float('inf')
        for e in self.doc.entities:
            pts = e.get_vertices()
            if len(pts) >= 3:
                cx = sum(p[0] for p in pts) / len(pts)
                cy = sum(p[1] for p in pts) / len(pts)
                d = math.hypot(cx - px, cy - py)
                if d < best_dist:
                    best_dist = d
                    best = pts
        if best_dist < 100:
            return [(p[0], p[1]) for p in best]
        return None

    def _hatch_selected(self):
        if not self.doc.selected:
            self.log("Sin selección. Cancelando.")
            self.is_done = True
            return
        self.doc.push_undo()
        for e in self.doc.selected:
            pts = e.get_vertices()
            if len(pts) >= 3:
                self.doc.add_entity(HatchEntity(
                    [(p[0], p[1]) for p in pts], pattern="SOLID", color=HATCH_COLOR))
        n = len(self.doc.selected)
        self.doc.clear_selection()
        self.log(f"Sombreado aplicado a {n} entidad(es).")
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        from PySide6.QtCore import QPointF
        from PySide6.QtGui import QBrush, QColor, QPen, QPolygonF
        if self._phase == "PICK_INTERIOR":
            boundary = self._find_closest_boundary(self._mouse.x(), self._mouse.y())
            if boundary and len(boundary) >= 3:
                screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in boundary]
                poly = QPolygonF(screen_pts)
                painter.setPen(QPen(QColor(HATCH_COLOR), 1, Qt.DashLine))
                painter.setBrush(QBrush(QColor(136, 204, 255, 40)))
                painter.drawPolygon(poly)
