# -*- coding: utf-8 -*-
"""
core/commands/ellipse_cmd.py — Comando ELIPSE (EL) - AutoCAD 2026 Spec
Fases:
- WAIT_P1: Precise punto final de eje de elipse o [Arco/Centro]:
- WAIT_P2: Precise otro punto final de eje:
- WAIT_P3: Precise distancia a otro eje o [Rotación]:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import EllipseEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class EllipseCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._p1: QPointF | None = None
        self._p2: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_P1"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_P1":
            return "Precise punto final de eje de elipse o [Arco/Centro]:"
        elif self._phase == "WAIT_P2":
            return "Precise otro punto final de eje:"
        elif self._phase == "WAIT_P3":
            return "Precise distancia a otro eje o [Rotación]:"
        return ""

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_P1":
            self._p1 = world_pt
            self._phase = "WAIT_P2"
            self.log(f"Eje 1 P1: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_P2":
            self._p2 = world_pt
            self._phase = "WAIT_P3"
            self.log(f"Eje 1 P2: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_P3":
            self._commit(world_pt)

    def on_right_click(self, world_pt: QPointF):
        self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            self.on_escape()
            return
            
        ref_pt = None
        if self._phase == "WAIT_P2": ref_pt = self._p1
        elif self._phase == "WAIT_P3":
            # El centro es el punto de referencia para la distancia
            ref_pt = QPointF((self._p1.x() + self._p2.x()) / 2.0, (self._p1.y() + self._p2.y()) / 2.0)
            
        pt = parse_coord_input(text, ref_pt, self._cursor_dir() if ref_pt else None)
        
        if pt is not None:
            self.on_left_click(pt)
        else:
            self.log("Se requiere un punto numérico o de clic.")

    def on_escape(self):
        self.is_done = True
        self.log("Comando ELIPSE finalizado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_P2" and self._p1:
            sx1, sy1 = viewport.world_to_screen(self._p1.x(), self._p1.y())
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(smx, smy))
            
        elif self._phase == "WAIT_P3" and self._p1 and self._p2:
            cx = (self._p1.x() + self._p2.x()) / 2.0
            cy = (self._p1.y() + self._p2.y()) / 2.0
            
            major_x = (self._p2.x() - self._p1.x()) / 2.0
            major_y = (self._p2.y() - self._p1.y()) / 2.0
            r_major = math.hypot(major_x, major_y)
            
            if r_major > 0:
                # Distancia del mouse al centro es el semi-eje menor
                r_minor = math.hypot(self._mouse.x() - cx, self._mouse.y() - cy)
                ratio = r_minor / r_major
                
                scx, scy = viewport.world_to_screen(cx, cy)
                angle_deg = math.degrees(math.atan2(major_y, major_x))
                
                painter.save()
                painter.translate(scx, scy)
                painter.rotate(-angle_deg)
                
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                
                sm_major = r_major * viewport.zoom
                sm_minor = r_minor * viewport.zoom
                painter.drawEllipse(QPointF(0, 0), sm_major, sm_minor)
                
                painter.restore()
                
                # Linea fantasma del eje menor
                smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.drawLine(QPointF(scx, scy), QPointF(smx, smy))

    def _commit(self, p3: QPointF):
        cx = (self._p1.x() + self._p2.x()) / 2.0
        cy = (self._p1.y() + self._p2.y()) / 2.0
        
        major_x = (self._p2.x() - self._p1.x()) / 2.0
        major_y = (self._p2.y() - self._p1.y()) / 2.0
        r_major = math.hypot(major_x, major_y)
        
        if r_major > 0:
            r_minor = math.hypot(p3.x() - cx, p3.y() - cy)
            ratio = r_minor / r_major
            
            self.doc.push_undo()
            self.doc.add_entity(EllipseEntity(cx, cy, major_x, major_y, ratio))
            self.log("Elipse creada.")
        else:
            self.log("El eje mayor es 0. Cancelado.")
            
        self.is_done = True

    def _cursor_dir(self):
        if self._phase == "WAIT_P2" and self._p1:
            return (self._mouse.x() - self._p1.x(), self._mouse.y() - self._p1.y())
        if self._phase == "WAIT_P3" and self._p2:
            cx = (self._p1.x() + self._p2.x()) / 2.0
            cy = (self._p1.y() + self._p2.y()) / 2.0
            return (self._mouse.x() - cx, self._mouse.y() - cy)
        return (1.0, 0.0)
