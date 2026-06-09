# -*- coding: utf-8 -*-
"""
core/commands/rotate_cmd.py — Comando ROTATE (RO)
Fases: SELECT → BASE_POINT → DRAG_ANGLE

Entrada numérica en DRAG_ANGLE:
  45    → rotar exactamente 45° en sentido antihorario
  -90   → rotar -90°  (sentido horario)
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.geometry          import parse_angle
from core.commands.base_command import BaseCommand


class RotateCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase   = "SELECT"
        self._base:  QPointF | None = None
        self._mouse: QPointF        = QPointF(0, 0)

        if doc.has_selection:
            self._start_base_phase()

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "ROTAR ▶ Seleccione objetos (Enter/clic der. = confirmar):"
        if self._phase == "BASE":
            return "ROTAR ▶ Especifique punto base (eje de rotación):"
        deg = self._current_angle_deg()
        return f"ROTAR ▶ Ángulo: {deg:.1f}°  (clic=fijar | tipee N° + Enter):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "BASE":
            self._base  = world_pt
            self._phase = "DRAG"
            self.log(f"Base rotación: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "DRAG":
            self._apply_rotate(self._current_angle_rad())

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self._selection_enter("ROTAR", self._start_base_phase)
        elif self._phase == "BASE":
            self.log("Haga clic para definir el eje de rotación.")
        elif self._phase == "DRAG":
            if text:
                # Intento de parseo con signo para ángulos negativos
                import re
                m = re.match(r'^(-?\d+(?:\.\d+)?)$', text.strip())
                if m:
                    angle_rad = math.radians(float(m.group(1)))
                    self._apply_rotate(angle_rad)
                else:
                    self.log("Ángulo inválido. Escriba un número (ej: 45 o -90).")
            else:
                self._apply_rotate(self._current_angle_rad())

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "DRAG" and self._base is not None:
            ms = QPointF(*viewport.world_to_screen(self._mouse.x(), self._mouse.y()))
            self._draw_vector_line(painter, viewport,
                                   self._base.x(), self._base.y(), ms)
            self._draw_base_marker(painter, viewport,
                                   self._base.x(), self._base.y())
            angle = self._current_angle_rad()
            for e in self.doc.selected:
                e.draw_ghost_rotated(painter, viewport,
                                     self._base.x(), self._base.y(), angle)

    # ── Private ───────────────────────────────────────────────────────────────
    def _start_base_phase(self):
        self._phase = "BASE"
        self.log("ROTAR ▶ Especifique eje de rotación (punto base):")

    def _current_angle_rad(self) -> float:
        if self._base is None:
            return 0.0
        return math.atan2(self._mouse.y() - self._base.y(),
                          self._mouse.x() - self._base.x())

    def _current_angle_deg(self) -> float:
        return (math.degrees(self._current_angle_rad()) % 360.0)

    def _apply_rotate(self, angle_rad: float):
        self.doc.push_undo()
        for e in self.doc.selected:
            e.rotate(self._base.x(), self._base.y(), angle_rad)
            e.selected = False
        self.doc.selected.clear()
        self.log(f"Rotación {math.degrees(angle_rad):.1f}° aplicada.")
        self.is_done = True
