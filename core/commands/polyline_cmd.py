# -*- coding: utf-8 -*-
"""
core/commands/polyline_cmd.py — Comando POLILÍNEA (PL) - AutoCAD 2026 Spec
Fases:
- WAIT_START: Precise punto inicial:
- WAIT_NEXT: Precise punto siguiente o [Deshacer/Cerrar]:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import LineEntity  # Para esta versión simplificada usamos líneas
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class PolylineCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._points: list[QPointF] = []
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_START"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_START":
            return "Precise punto inicial:"
        elif len(self._points) > 2:
            return "Precise punto siguiente o [Deshacer/Cerrar]:"
        else:
            return "Precise punto siguiente o [Deshacer]:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        self._apply_point(world_pt)

    def on_right_click(self, world_pt: QPointF):
        self.on_escape()

    # Duplicate methods removed

    def _apply_point(self, pt: QPointF):
        if self._phase == "WAIT_START":
            self._points.append(pt)
            self._phase = "WAIT_NEXT"
        else:
            # We add it to points but we DON'T commit to document until Enter/Escape!
            # BUT AutoCAD draws the segments immediately.
            # However, if we want it to be a single entity, we should commit the entire Polyline on enter.
            # In AutoCAD, while drawing a polyline, the segments are part of the active command preview, 
            # and they commit as one object when done.
            self._points.append(pt)

    def draw_preview(self, painter: QPainter, viewport):
        if len(self._points) > 0:
            # Draw all segments so far
            painter.setPen(QPen(QColor("#FFFFFF"), 2.0, Qt.SolidLine))
            pts_screen = [QPointF(*viewport.world_to_screen(p.x(), p.y())) for p in self._points]
            painter.drawPolyline(pts_screen)
            
            # Draw rubber band to mouse if WAIT_NEXT
            if self._phase == "WAIT_NEXT":
                p1 = self._points[-1]
                sx1, sy1 = viewport.world_to_screen(p1.x(), p1.y())
                sx2, sy2 = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
                painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            self._commit_polyline()
            return

        if text in ["C", "CERRAR"] and len(self._points) > 2:
            self._commit_polyline(closed=True)
            return
            
        if text in ["D", "DESHACER"] and len(self._points) > 0:
            if len(self._points) == 1:
                self._points.pop()
                self._phase = "WAIT_START"
                self.log("Deshacer punto inicial.")
            else:
                self._points.pop()
                self.log("Segmento deshecho.")
            return

        ref_pt = self._points[-1] if self._points else None
        pt = parse_coord_input(text, ref_pt, self._cursor_dir() if ref_pt else None)
        
        if pt is not None:
            self._apply_point(pt)
        else:
            self.log("Se requiere un punto o una opción.")

    def on_escape(self):
        self._commit_polyline()

    def _commit_polyline(self, closed=False):
        if len(self._points) > 1:
            from core.entities import PolylineEntity
            self.doc.push_undo()
            pts_tuples = [(p.x(), p.y()) for p in self._points]
            self.doc.add_entity(PolylineEntity(pts_tuples, closed=closed))
            self.log("Polilínea creada.")
        
        self._points.clear()
        self.is_done = True
        self.log("Comando POLILÍNEA finalizado.")

    def _cursor_dir(self):
        if not self._points:
            return (1.0, 0.0)
        p1 = self._points[-1]
        return (self._mouse.x() - p1.x(), self._mouse.y() - p1.y())
