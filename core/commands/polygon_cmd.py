# -*- coding: utf-8 -*-
"""
core/commands/polygon_cmd.py — Comando POLÍGONO (POL) - AutoCAD 2026 Spec
Fases:
- WAIT_SIDES: Indique número de lados <4>:
- WAIT_CENTER: Precise centro de polígono o [Lado]:
- WAIT_INSCRIBED: Indique una opción [Inscrito en el círculo/Circunscrito alrededor del círculo] <I>:
- WAIT_RADIUS: Precise radio de círculo:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import PolygonEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class PolygonCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._sides: int = 4
        self._center: QPointF | None = None
        self._inscribed: bool = True
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_CENTER"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_CENTER":
            return "Precise centro de polígono:"
        elif self._phase == "WAIT_SIDES":
            return f"Indique número de lados <{self._sides}>:"
        elif self._phase == "WAIT_INSCRIBED":
            return "Indique una opción [Inscrito en el círculo/Circunscrito alrededor del círculo] <I>:"
        elif self._phase == "WAIT_RADIUS":
            return "Precise radio de círculo:"
        return ""

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_CENTER":
            self._center = world_pt
            self._phase = "WAIT_SIDES"
            self.log(f"Centro: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_RADIUS":
            self._commit(world_pt)

    def on_right_click(self, world_pt: QPointF):
        if self._phase == "WAIT_CENTER":
            self._phase = "WAIT_SIDES"
        elif self._phase == "WAIT_SIDES":
            self._phase = "WAIT_INSCRIBED"
        elif self._phase == "WAIT_INSCRIBED":
            self._phase = "WAIT_RADIUS"
        else:
            self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        
        if self._phase == "WAIT_CENTER":
            if not text: return
            pt = parse_coord_input(text)
            if pt is not None:
                self.on_left_click(pt)
            else:
                self.log("Punto inválido.")
                
        elif self._phase == "WAIT_SIDES":
            if not text:
                self._phase = "WAIT_INSCRIBED"
            else:
                try:
                    s = int(text)
                    if s >= 3:
                        self._sides = s
                        self._phase = "WAIT_INSCRIBED"
                    else:
                        self.log("Requiere un entero entre 3 y 1024.")
                except ValueError:
                    self.log("Requiere un entero válido.")
                    
        elif self._phase == "WAIT_INSCRIBED":
            if not text or text.startswith("I") or text == "INSCRITO":
                self._inscribed = True
                self._phase = "WAIT_RADIUS"
            elif text.startswith("C") or text == "CIRCUNSCRITO":
                self._inscribed = False
                self._phase = "WAIT_RADIUS"
            else:
                self.log("Opción inválida.")
                
        elif self._phase == "WAIT_RADIUS":
            if not text: return
            pt = parse_coord_input(text, self._center, self._cursor_dir())
            if pt is not None:
                self.on_left_click(pt)
            else:
                try:
                    r = float(text)
                    if r > 0:
                        self._commit_radius(r, 0.0)
                except ValueError:
                    self.log("Requiere distancia numérica o punto.")

    def on_escape(self):
        self.is_done = True
        self.log("Comando POLÍGONO finalizado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_RADIUS" and self._center:
            dx = self._mouse.x() - self._center.x()
            dy = self._mouse.y() - self._center.y()
            r = math.hypot(dx, dy)
            if r > 0:
                angle_rad = math.atan2(dy, dx)
                
                # Crear entidad temporal para preview
                temp_poly = PolygonEntity(self._center.x(), self._center.y(), r, self._sides, self._inscribed, angle_rad)
                
                # Dibujar el círculo de referencia en naranja (solo vista previa)
                painter.setPen(QPen(QColor("#FF8C00"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                scx, scy = viewport.world_to_screen(self._center.x(), self._center.y())
                sr = r * viewport.zoom
                painter.drawEllipse(QPointF(scx, scy), sr, sr)
                
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
                painter.setBrush(Qt.NoBrush)
                
                screen_pts = [QPointF(*viewport.world_to_screen(p.x(), p.y())) for p in temp_poly._get_vertices()]
                from PySide6.QtGui import QPolygonF
                if screen_pts:
                    painter.drawPolygon(QPolygonF(screen_pts))

    def _commit(self, p2: QPointF):
        dx = p2.x() - self._center.x()
        dy = p2.y() - self._center.y()
        r = math.hypot(dx, dy)
        angle_rad = math.atan2(dy, dx)
        self._commit_radius(r, angle_rad)

    def _commit_radius(self, r: float, angle_rad: float):
        if r > 0:
            self.doc.push_undo()
            self.doc.add_entity(PolygonEntity(self._center.x(), self._center.y(), r, self._sides, self._inscribed, angle_rad))
            self.log("Polígono creado.")
        self.is_done = True

    def _cursor_dir(self):
        if self._phase == "WAIT_RADIUS" and self._center:
            return (self._mouse.x() - self._center.x(), self._mouse.y() - self._center.y())
        return (1.0, 0.0)
