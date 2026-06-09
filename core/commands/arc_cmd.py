# -*- coding: utf-8 -*-
"""
core/commands/arc_cmd.py — Comando ARCO (A) - AutoCAD 2026 Spec
Fases (3 Puntos):
- WAIT_P1: Precise punto inicial de arco o [Centro]:
- WAIT_P2: Precise segundo punto de arco o [Centro/Fin]:
- WAIT_P3: Precise punto final de arco:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import ArcEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

def _calculate_arc_3p(p1: QPointF, p2: QPointF, p3: QPointF):
    """Calcula el centro, radio, start_angle y span_angle dados 3 puntos en 2D."""
    # Determinante
    temp = p2.x()**2 + p2.y()**2
    bc = (p1.x()**2 + p1.y()**2 - temp) / 2.0
    cd = (temp - p3.x()**2 - p3.y()**2) / 2.0
    det = (p1.x() - p2.x()) * (p2.y() - p3.y()) - (p2.x() - p3.x()) * (p1.y() - p2.y())
    
    if abs(det) < 1e-6:
        return None # Colineales

    # Centro
    cx = (bc * (p2.y() - p3.y()) - cd * (p1.y() - p2.y())) / det
    cy = ((p1.x() - p2.x()) * cd - (p2.x() - p3.x()) * bc) / det
    radius = math.hypot(cx - p1.x(), cy - p1.y())
    
    # Angulos
    a1 = math.degrees(math.atan2(p1.y() - cy, p1.x() - cx)) % 360
    a2 = math.degrees(math.atan2(p2.y() - cy, p2.x() - cx)) % 360
    a3 = math.degrees(math.atan2(p3.y() - cy, p3.x() - cx)) % 360
    
    # Span angle (dirección que pasa por a2)
    # Forma sencilla: medir desde a1 hacia a3. Si a2 no está dentro, invertir.
    span = (a3 - a1) % 360
    
    # Verificar si a2 está en el recorrido CCW de a1 a a3
    # Relativo a a1:
    rel_a2 = (a2 - a1) % 360
    rel_a3 = span
    
    if rel_a2 > rel_a3:
        # Significa que el camino más corto no pasa por a2, debemos ir por el otro lado (CW)
        span = span - 360
        
    return cx, cy, radius, a1, span

class ArcCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._p1: QPointF | None = None
        self._p2: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_P1"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_P1":
            return "Precise punto inicial de arco o [Centro]:"
        elif self._phase == "WAIT_P2":
            return "Precise segundo punto de arco o [Centro/Fin]:"
        elif self._phase == "WAIT_P3":
            return "Precise punto final de arco:"
        return ""

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_P1":
            self._p1 = world_pt
            self._phase = "WAIT_P2"
            self.log(f"Punto inicial: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_P2":
            self._p2 = world_pt
            self._phase = "WAIT_P3"
            self.log(f"Segundo punto: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_P3":
            self._commit(world_pt)

    def on_right_click(self, world_pt: QPointF):
        self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            self.on_escape()
            return
            
        # TODO: Implementar sub-opciones como Centro, Fin, etc.
        # Por ahora solo leer coordenadas.
        ref_pt = None
        if self._phase == "WAIT_P2": ref_pt = self._p1
        if self._phase == "WAIT_P3": ref_pt = self._p2
        
        pt = parse_coord_input(text, ref_pt, self._cursor_dir() if ref_pt else None)
        if pt is not None:
            self.on_left_click(pt)
        else:
            self.log("Se requiere un punto (Ej: 10,20 o @5<45).")

    def on_escape(self):
        self.is_done = True
        self.log("Comando ARCO finalizado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_P2" and self._p1:
            # Rubber-band line from P1 to mouse
            sx1, sy1 = viewport.world_to_screen(self._p1.x(), self._p1.y())
            smx, smy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(smx, smy))
            
        elif self._phase == "WAIT_P3" and self._p1 and self._p2:
            res = _calculate_arc_3p(self._p1, self._p2, self._mouse)
            if res:
                cx, cy, r, a1, span = res
                
                # Render using a calculated polyline to ensure 100% visibility 
                # and bypass any platform specific drawArc issues.
                segments = 64
                pts = []
                for i in range(segments + 1):
                    angle_deg = a1 + (span * i / segments)
                    rad = math.radians(angle_deg)
                    px = cx + r * math.cos(rad)
                    py = cy + r * math.sin(rad)
                    spx, spy = viewport.world_to_screen(px, py)
                    pts.append(QPointF(spx, spy))
                
                painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                painter.drawPolyline(pts)

    def _commit(self, p3: QPointF):
        res = _calculate_arc_3p(self._p1, self._p2, p3)
        if res:
            cx, cy, r, a1, span = res
            self.doc.push_undo()
            self.doc.add_entity(ArcEntity(cx, cy, r, a1, span))
            self.log("Arco creado.")
        else:
            self.log("Puntos colineales. No se puede crear el arco.")
        self.is_done = True

    def _cursor_dir(self):
        if self._phase == "WAIT_P2" and self._p1:
            return (self._mouse.x() - self._p1.x(), self._mouse.y() - self._p1.y())
        if self._phase == "WAIT_P3" and self._p2:
            return (self._mouse.x() - self._p2.x(), self._mouse.y() - self._p2.y())
        return (1.0, 0.0)
