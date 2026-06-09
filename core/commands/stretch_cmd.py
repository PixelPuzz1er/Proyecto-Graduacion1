import math
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from core.document import Document
from core.commands.base_command import BaseCommand


class StretchCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._base: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._sel_start: QPointF | None = None
        self._sel_end: QPointF | None = None

        if doc.has_selection:
            self._start_base_phase()

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "ESTIRAR ▶ Seleccione objetos con ventana de cruce (clic der. = confirmar):"
        if self._phase == "BASE":
            return "ESTIRAR ▶ Especifique punto base:"
        return "ESTIRAR ▶ Segundo punto (@dx,dy | X,Y | dist):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            entity = None
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            if entity:
                self.doc.toggle_select(entity)
            else:
                self._sel_start = world_pt
                self._sel_end = world_pt
        elif self._phase == "BASE":
            self._base = world_pt
            self._phase = "DESTINATION"
            self.log(f"Base: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "DESTINATION":
            self._apply_stretch(world_pt)

    def on_right_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            self._selection_enter("ESTIRAR", self._start_base_phase)
        else:
            self.on_enter("")

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self._selection_enter("ESTIRAR", self._start_base_phase)
        elif self._phase == "BASE":
            pt = self._parse_point(text)
            if pt is not None:
                self._base = pt
                self._phase = "DESTINATION"
                self.log(f"Base: ({pt.x():.2f}, {pt.y():.2f})")
            else:
                self.log("Especifique punto base haciendo clic o escriba X,Y")
        elif self._phase == "DESTINATION":
            if text:
                pt = self._parse_point(text, self._base)
                if pt is not None:
                    self._apply_stretch(pt)
                else:
                    self.log("Formato inválido. Use @dx,dy | X,Y | dist")
            else:
                self._apply_stretch(self._mouse)

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "SELECT" and self._sel_start is not None and self._sel_end is not None:
            sx1, sy1 = viewport.world_to_screen(self._sel_start.x(), self._sel_start.y())
            sx2, sy2 = viewport.world_to_screen(self._sel_end.x(), self._sel_end.y())
            rect = QRectF(sx1, sy1, sx2 - sx1, sy2 - sy1).normalized()
            painter.setPen(QPen(QColor("#00FF00"), 1, Qt.DashLine))
            painter.setBrush(QColor(15, 123, 15, 40))
            painter.drawRect(rect)

        if self._phase == "DESTINATION" and self._base is not None:
            ms = QPointF(*viewport.world_to_screen(self._mouse.x(), self._mouse.y()))
            self._draw_vector_line(painter, viewport, self._base.x(), self._base.y(), ms)
            self._draw_base_marker(painter, viewport, self._base.x(), self._base.y())
            vx = self._mouse.x() - self._base.x()
            vy = self._mouse.y() - self._base.y()
            for e in self.doc.selected:
                e.draw_ghost_offset(painter, viewport, vx, vy)

    def _start_base_phase(self):
        self._phase = "BASE"
        self.log("ESTIRAR ▶ Especifique punto base:")

    def _apply_stretch(self, dest: QPointF):
        vx = dest.x() - self._base.x()
        vy = dest.y() - self._base.y()
        self.doc.push_undo()
        for e in self.doc.selected:
            e.move(vx, vy)
            e.selected = False
        self.doc.selected.clear()
        self.log(f"Estirar Δ({vx:.2f}, {vy:.2f}) aplicado.")
        self.is_done = True

    def _parse_point(self, text: str, ref: QPointF = None):
        from core.geometry import parse_coord_input
        if ref is not None:
            cursor_dir = (self._mouse.x() - ref.x(), self._mouse.y() - ref.y())
            return parse_coord_input(text, ref, cursor_dir)
        return parse_coord_input(text)
