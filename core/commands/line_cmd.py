# -*- coding: utf-8 -*-
"""
core/commands/line_cmd.py — Comando LÍNEA (L) - AutoCAD 2026 Spec
Fases:
- WAIT_START: Espera el P1 (Clic o teclado)
- WAIT_NEXT: Espera P2 (Dibuja rubber-band, acepta D para deshacer, C para cerrar)
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import LineEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class LineCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._start_points: list[QPointF] = []  # Para deshacer segmentos y cerrar polígonos
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_START"
        self._is_active = True

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_START":
            return "Precise primer punto:"
        elif len(self._start_points) > 1:
            return "Precise punto siguiente o [Cerrar/Deshacer]:"
        else:
            return "Precise punto siguiente o [Deshacer]:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        self._apply_point(world_pt)

    def on_right_click(self, world_pt: QPointF):
        # Click derecho en AutoCAD termina el comando Línea
        self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            # Enter vacío = finalizar
            self.on_escape()
            return

        if text in ["C", "CERRAR"] and len(self._start_points) > 1:
            # Cerrar
            last_pt = self._start_points[-1]
            first_pt = self._start_points[0]
            self.doc.push_undo()
            self.doc.add_entity(LineEntity(last_pt.x(), last_pt.y(), first_pt.x(), first_pt.y()))
            self.log(f"Línea cerrada.")
            self.on_escape()
            return
            
        if text in ["D", "DESHACER"] and len(self._start_points) > 0:
            if len(self._start_points) == 1:
                self._start_points.pop()
                self._phase = "WAIT_START"
                self.log("Deshacer punto inicial.")
            else:
                self.doc.pop_undo()  # Borra la entidad física
                self._start_points.pop()
                self.log("Segmento deshecho.")
            return

        # Intentar parsear coordenada
        ref_pt = self._start_points[-1] if self._start_points else None
        pt = parse_coord_input(text, ref_pt, self._cursor_dir() if ref_pt else None)
        
        if pt is not None:
            self._apply_point(pt)
        else:
            self.log("Se requiere un punto (Ej: 10,20 o @5<45) o una opción.")

    def on_escape(self):
        self._start_points.clear()
        self._is_active = False
        self.is_done = True
        self.log("Comando finalizado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_NEXT" and self._start_points:
            p1 = self._start_points[-1]
            sx1, sy1 = viewport.world_to_screen(p1.x(), p1.y())
            sx2, sy2 = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            
            # AutoCAD usa una línea punteada o sólida tenue para el rubber-band
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    # ── Private ───────────────────────────────────────────────────────────────

    def _apply_point(self, pt: QPointF):
        if self._phase == "WAIT_START":
            self._start_points.append(pt)
            self._phase = "WAIT_NEXT"
        else:
            last_pt = self._start_points[-1]
            self.doc.push_undo()
            self.doc.add_entity(LineEntity(last_pt.x(), last_pt.y(), pt.x(), pt.y()))
            self._start_points.append(pt)

    def _cursor_dir(self):
        if not self._start_points:
            return (1.0, 0.0)
        p1 = self._start_points[-1]
        return (self._mouse.x() - p1.x(), self._mouse.y() - p1.y())
