# -*- coding: utf-8 -*-
"""
core/commands/circle_cmd.py — Comando CIRCULO (C) - AutoCAD 2026 Spec
Fases:
- WAIT_CENTER: Precise punto central para círculo o [3P/2P/Ttr (tangente tangente radio)]:
- WAIT_RADIUS: Precise radio de círculo o [Diámetro]:
- WAIT_DIAMETER: Precise diámetro de círculo:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import CircleEntity
from core.geometry          import parse_coord_input, parse_factor
from core.commands.base_command import BaseCommand

class CircleCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._center: QPointF | None = None
        self._mouse: QPointF         = QPointF(0, 0)
        self._phase = "WAIT_CENTER"
        self._mode = "RADIUS"  # o "DIAMETER"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_CENTER":
            return "Precise punto central para círculo o [3P/2P/Ttr (tangente tangente radio)]:"
        elif self._phase == "WAIT_RADIUS":
            return "Precise radio de círculo o [Diámetro]:"
        elif self._phase == "WAIT_DIAMETER":
            return "Precise diámetro de círculo:"
        return ""

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_CENTER":
            self._center = world_pt
            self._phase  = "WAIT_RADIUS"
            self.log(f"Centro: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        else:
            d = math.hypot(world_pt.x() - self._center.x(), world_pt.y() - self._center.y())
            if self._phase == "WAIT_DIAMETER":
                self._commit(d / 2.0)
            else:
                self._commit(d)

    def on_right_click(self, world_pt: QPointF):
        self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            # Enter vacío en círculo puede repetir comando previo, pero aquí cancela/termina
            self.on_escape()
            return

        if self._phase == "WAIT_CENTER":
            pt = parse_coord_input(text)
            if pt is not None:
                self._center = pt
                self._phase  = "WAIT_RADIUS"
                self.log(f"Centro: ({pt.x():.2f}, {pt.y():.2f})")
            else:
                self.log("Especifique centro haciendo clic o escriba X,Y")
        
        elif self._phase == "WAIT_RADIUS":
            if text in ["D", "DIAMETRO", "DIÁMETRO"]:
                self._phase = "WAIT_DIAMETER"
                return
                
            dx = self._mouse.x() - self._center.x()
            dy = self._mouse.y() - self._center.y()
            pt = parse_coord_input(text, ref=self._center, cursor_dir=(dx, dy))
            if pt is not None:
                r = math.hypot(pt.x() - self._center.x(), pt.y() - self._center.y())
                self._commit(r)
            else:
                r = parse_factor(text)
                if r and r > 0:
                    self._commit(r)
                else:
                    self.log("Requiere radio numérico válido.")

        elif self._phase == "WAIT_DIAMETER":
            dx = self._mouse.x() - self._center.x()
            dy = self._mouse.y() - self._center.y()
            pt = parse_coord_input(text, ref=self._center, cursor_dir=(dx, dy))
            if pt is not None:
                d = math.hypot(pt.x() - self._center.x(), pt.y() - self._center.y())
                self._commit(d / 2.0)
            else:
                d = parse_factor(text)
                if d and d > 0:
                    self._commit(d / 2.0)
                else:
                    self.log("Requiere diámetro numérico válido.")

    def on_escape(self):
        self.is_done = True
        self.log("Comando cancelado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._center is not None:
            scx, scy = viewport.world_to_screen(self._center.x(), self._center.y())
            d = math.hypot(self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
            
            if self._phase == "WAIT_DIAMETER":
                # La distancia al ratón representa el diámetro completo
                r_world = d / 2.0
            else:
                r_world = d
                
            r_screen = r_world * viewport.zoom
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(scx, scy), r_screen, r_screen)
            
            # Dibujar la línea de radio fantasma
            if self._phase == "WAIT_DIAMETER":
                # Draw line to actual radius point for visualization
                dx = self._mouse.x() - self._center.x()
                dy = self._mouse.y() - self._center.y()
                if d > 0:
                    ux, uy = dx/d, dy/d
                    px, py = self._center.x() + ux*r_world, self._center.y() + uy*r_world
                    spx, spy = viewport.world_to_screen(px, py)
                    painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                    painter.drawLine(QPointF(scx, scy), QPointF(spx, spy))
            else:
                smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.drawLine(QPointF(scx, scy), QPointF(smx, smy))

    def _commit(self, radius: float):
        if radius > 0:
            self.doc.push_undo()
            self.doc.add_entity(CircleEntity(self._center.x(), self._center.y(), radius))
            self.log(f"Círculo creado. Radio: {radius:.4f}")
        self.is_done = True
