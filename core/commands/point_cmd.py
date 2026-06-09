# -*- coding: utf-8 -*-
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.entities          import PointEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class PointCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "PLACE"
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        return "PUNTO ▶ Especifique ubicación del punto (clic o X,Y):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        self._create_point(world_pt)

    def on_enter(self, text: str = ""):
        if text:
            pt = parse_coord_input(text)
            if pt is not None:
                self._create_point(pt)
            else:
                self.log("Haga clic o escriba X,Y.")
        else:
            self._create_point(self._mouse)

    def _create_point(self, pt: QPointF):
        self.doc.push_undo()
        p = PointEntity(pt.x(), pt.y(), color="#FFFFFF")
        self.doc.add_entity(p)
        self.log(f"Punto en ({pt.x():.2f}, {pt.y():.2f}).")
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtGui import QPen, QColor
        sx, sy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
        painter.setPen(QPen(QColor("#00FF00"), 1, Qt.DashLine))
        painter.drawLine(QPointF(sx - 5, sy), QPointF(sx + 5, sy))
        painter.drawLine(QPointF(sx, sy - 5), QPointF(sx, sy + 5))
