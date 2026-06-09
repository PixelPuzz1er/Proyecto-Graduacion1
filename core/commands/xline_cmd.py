# -*- coding: utf-8 -*-
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.entities          import XLineEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class XLineCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "FIRST"
        self._p1: QPointF | None = None
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "FIRST":
            return "XLÍNEA ▶ Especifique primer punto de la línea auxiliar:"
        return "XLÍNEA ▶ Especifique segundo punto de la línea auxiliar:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "FIRST":
            self._p1 = world_pt
            self._phase = "SECOND"
            self.log(f"Primer punto: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "SECOND":
            self._create_xline(world_pt)

    def on_enter(self, text: str = ""):
        if self._phase == "FIRST":
            pt = parse_coord_input(text)
            if pt is not None:
                self._p1 = pt
                self._phase = "SECOND"
            else:
                self.log("Haga clic o escriba X,Y para el primer punto.")
        elif self._phase == "SECOND":
            if text:
                pt = parse_coord_input(text, self._p1)
                if pt is not None:
                    self._create_xline(pt)
                else:
                    self.log("Haga clic o escriba coordenadas.")
            else:
                self.log("Especifique segundo punto.")

    def _create_xline(self, p2: QPointF):
        dx = p2.x() - self._p1.x()
        dy = p2.y() - self._p1.y()
        self.doc.push_undo()
        xline = XLineEntity(self._p1.x(), self._p1.y(), dx, dy, color="#FFAA00")
        self.doc.add_entity(xline)
        self.log("Línea auxiliar creada.")
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "SECOND" and self._p1 is not None:
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QPen, QColor
            dx = self._mouse.x() - self._p1.x()
            dy = self._mouse.y() - self._p1.y()
            diag = math.hypot(viewport.width(), viewport.height())
            x1 = self._p1.x() - dx * diag
            y1 = self._p1.y() - dy * diag
            x2 = self._p1.x() + dx * diag
            y2 = self._p1.y() + dy * diag
            sx1, sy1 = viewport.world_to_screen(x1, y1)
            sx2, sy2 = viewport.world_to_screen(x2, y2)
            painter.setPen(QPen(QColor("#FFAA00"), 1, Qt.DashDotLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
