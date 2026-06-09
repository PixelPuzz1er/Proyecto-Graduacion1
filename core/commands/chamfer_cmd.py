import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from core.document import Document
from core.commands.base_command import BaseCommand
from core.entities import LineEntity
from core.geometry import line_line_intersection, get_line_parameter


class ChamferCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT_FIRST"
        self._first_line = None
        self._first_pick: QPointF | None = None
        self._second_pick: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._dist1: float = 10.0
        self._dist2: float = 10.0
        self._preview_line = None
        self._preview_valid = False

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT_FIRST":
            return "CHAFÁN ▶ Seleccione primera línea:"
        if self._phase == "SELECT_SECOND":
            return "CHAFÁN ▶ Seleccione segunda línea:"
        return "CHAFÁN ▶ Usando D1={d1:.1f} D2={d2:.1f}. Clic para aceptar."

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT_FIRST":
            self._first_pick = world_pt
            self._first_line = self._pick_line(world_pt)
            if self._first_line is None:
                self.log("No se detectó ninguna línea. Intente de nuevo.")
                return
            self._phase = "SELECT_SECOND"
            self.log("Primera línea seleccionada. Seleccione segunda línea:")
        elif self._phase == "SELECT_SECOND":
            self._second_pick = world_pt
            line2 = self._pick_line(world_pt)
            if line2 is None or line2 is self._first_line:
                self.log("Seleccione una línea diferente.")
                return
            self._compute_chamfer(line2)
            if self._preview_valid:
                self._apply_chamfer(line2)
            else:
                self.log("No se pudo calcular el chafán.")

    def on_enter(self, text: str = ""):
        if text and self._phase == "SELECT_FIRST":
            try:
                parts = text.strip().split()
                if len(parts) == 1:
                    self._dist1 = self._dist2 = float(parts[0])
                elif len(parts) == 2:
                    self._dist1 = float(parts[0])
                    self._dist2 = float(parts[1])
                self.log(f"D1={self._dist1:.1f} D2={self._dist2:.1f}")
            except ValueError:
                self.log("Use: 'dist' o 'dist1 dist2'")
        elif self._phase == "SELECT_FIRST":
            self.log("Seleccione la primera línea con clic izquierdo.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._preview_valid and self._preview_line:
            sx1, sy1 = viewport.world_to_screen(self._preview_line.x1, self._preview_line.y1)
            sx2, sy2 = viewport.world_to_screen(self._preview_line.x2, self._preview_line.y2)
            painter.setPen(QPen(QColor("#00FFFF"), 2, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _pick_line(self, pt: QPointF):
        best_d = 10.0
        best = None
        for e in self.doc.entities:
            if isinstance(e, LineEntity):
                p1 = QPointF(e.x1, e.y1)
                p2 = QPointF(e.x2, e.y2)
                from core.geometry import point_to_segment_distance
                d = point_to_segment_distance(pt, p1, p2)
                if d < best_d:
                    best_d = d
                    best = e
        return best

    def _compute_chamfer(self, line2):
        l1 = self._first_line
        l2 = line2
        if l1 is None or l2 is None:
            self._preview_valid = False
            return

        p1 = QPointF(l1.x1, l1.y1)
        p2 = QPointF(l1.x2, l1.y2)
        p3 = QPointF(l2.x1, l2.y1)
        p4 = QPointF(l2.x2, l2.y2)

        res = line_line_intersection(p1, p2, p3, p4)
        if res is None:
            self._preview_valid = False
            return
        int_pt, _ = res

        t1 = get_line_parameter(p1, p2, self._first_pick)
        t2 = get_line_parameter(p3, p4, self._second_pick)

        d1 = self._dist1
        d2 = self._dist2

        dx1, dy1 = p2.x() - p1.x(), p2.y() - p1.y()
        len1 = math.hypot(dx1, dy1)
        u1x, u1y = dx1 / len1, dy1 / len1

        dx2, dy2 = p4.x() - p3.x(), p4.y() - p3.y()
        len2 = math.hypot(dx2, dy2)
        u2x, u2y = dx2 / len2, dy2 / len2

        dir1 = 1.0 if t1 >= 0.5 else -1.0
        dir2 = 1.0 if t2 >= 0.5 else -1.0

        tx1 = int_pt.x() + u1x * d1 * dir1
        ty1 = int_pt.y() + u1y * d1 * dir1
        tx2 = int_pt.x() + u2x * d2 * dir2
        ty2 = int_pt.y() + u2y * d2 * dir2

        self._chamfer_pts = (tx1, ty1, tx2, ty2, u1x, u1y, u2x, u2y, dir1, dir2)
        self._preview_line = LineEntity(tx1, ty1, tx2, ty2, color="#00FFFF")
        self._preview_valid = True

    def _apply_chamfer(self, line2):
        l1 = self._first_line
        l2 = line2
        if not self._preview_valid or self._chamfer_pts is None:
            return
        tx1, ty1, tx2, ty2, u1x, u1y, u2x, u2y, dir1, dir2 = self._chamfer_pts
        self.doc.push_undo()

        p1 = QPointF(l1.x1, l1.y1)
        p2 = QPointF(l1.x2, l1.y2)

        t_start_new1 = get_line_parameter(p1, p2, QPointF(tx1, ty1))
        if t_start_new1 < 0.5:
            l1.x1, l1.y1 = tx1, ty1
        else:
            l1.x2, l1.y2 = tx1, ty1

        p3 = QPointF(l2.x1, l2.y1)
        p4 = QPointF(l2.x2, l2.y2)
        t_start_new2 = get_line_parameter(p3, p4, QPointF(tx2, ty2))
        if t_start_new2 < 0.5:
            l2.x1, l2.y1 = tx2, ty2
        else:
            l2.x2, l2.y2 = tx2, ty2

        chamfer_line = LineEntity(tx1, ty1, tx2, ty2, color=l1.color, layer=l1.layer)
        self.doc.add_entity(chamfer_line)
        self.doc.clear_selection()
        self.log(f"Chafán aplicado (D1={self._dist1:.1f}, D2={self._dist2:.1f}).")
        self.is_done = True
