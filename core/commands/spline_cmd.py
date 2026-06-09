# -*- coding: utf-8 -*-
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor

from core.document          import Document
from core.entities          import SplineEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class SplineCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "POINTS"
        self._points: list[QPointF] = []
        self._mouse = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if not self._points:
            return "SPLINE ▶ Especifique primer punto de ajuste:"
        return f"SPLINE ▶ Especifique siguiente punto ({len(self._points)} pts, Enter=fin):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        self._points.append(world_pt)
        self.log(f"Punto {len(self._points)}: ({world_pt.x():.2f}, {world_pt.y():.2f})")

    def on_enter(self, text: str = ""):
        if not self._points:
            if text:
                pt = parse_coord_input(text)
                if pt is not None:
                    self._points.append(pt)
                    self.log(f"Punto 1: ({pt.x():.2f}, {pt.y():.2f})")
                else:
                    self.log("Haga clic o escriba X,Y para el primer punto.")
            return
        if text:
            pt = parse_coord_input(text, self._points[-1] if self._points else None)
            if pt is not None:
                self._points.append(pt)
                self.log(f"Punto {len(self._points)}: ({pt.x():.2f}, {pt.y():.2f})")
                return
        if len(self._points) >= 2:
            self._finalize()
        else:
            self.log("Se necesitan al menos 2 puntos para la spline.")

    def on_right_click(self, world_pt: QPointF):
        if len(self._points) >= 2:
            self._finalize()
        else:
            self.log("Se necesitan al menos 2 puntos.")

    def _finalize(self):
        pts = [(p.x(), p.y()) for p in self._points]
        self.doc.push_undo()
        spline = SplineEntity(pts, closed=False, color="#00D4FF")
        self.doc.add_entity(spline)
        self.log(f"Spline creada ({len(pts)} puntos de ajuste).")
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        if not self._points:
            return
        from PySide6.QtCore import Qt, QPointF
        all_pts = [(p.x(), p.y()) for p in self._points]
        all_pts.append((self._mouse.x(), self._mouse.y()))
        if len(all_pts) >= 2:
            temp = SplineEntity(all_pts, closed=False)
            temp.color = "#00D4FF"
            screen_pts = []
            samples = temp._sample_points()
            for x, y in samples:
                sx, sy = viewport.world_to_screen(x, y)
                screen_pts.append(QPointF(sx, sy))
            painter.setPen(QPen(QColor("#00D4FF"), 1, Qt.DashLine))
            painter.drawPolyline(screen_pts)
        for p in self._points:
            sx, sy = viewport.world_to_screen(p.x(), p.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1))
            painter.drawEllipse(QPointF(sx, sy), 3, 3)
