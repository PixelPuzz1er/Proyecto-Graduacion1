# -*- coding: utf-8 -*-
"""
core/commands/scale_cmd.py — Comando SCALE (SC)  ← El más delicado
Fases: SELECT → BASE_POINT → DRAG_FACTOR

REGLAS ESTRICTAS:
  - Factor numérico ingresado <= 0  → cancelar con mensaje de error
  - Factor calculado por arrastre   → clampear a mínimo 0.01 (nunca negativo)
  - Fórmula: nuevo = base + (viejo - base) * factor

Entrada numérica en DRAG:
  2      → escala exacta ×2
  0.5    → reduce a la mitad
  0      → ERROR: "El factor de escala debe ser positivo"
  -1     → ERROR: "El factor de escala debe ser positivo"
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.commands.base_command import BaseCommand

MIN_SCALE_FACTOR = 0.01   # Factor mínimo permitido en arrastre de ratón


class ScaleCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase        = "SELECT"
        self._base:  QPointF | None = None
        self._mouse: QPointF        = QPointF(0, 0)
        self._ref_dist: float | None = None   # Distancia inicial de referencia

        if doc.has_selection:
            self._start_base_phase()

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "ESCALA ▶ Seleccione objetos (Enter/clic der. = confirmar):"
        if self._phase == "BASE":
            return "ESCALA ▶ Especifique punto base:"
        f = self._current_factor()
        return f"ESCALA ▶ Factor: {f:.3f}×  (clic=aplicar | tipee N + Enter):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt
        # Capturar distancia de referencia en el primer movimiento tras fijar base
        if self._phase == "DRAG" and self._base is not None and self._ref_dist is None:
            d = math.hypot(world_pt.x() - self._base.x(),
                           world_pt.y() - self._base.y())
            if d > 0.001:
                self._ref_dist = d

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "BASE":
            self._base      = world_pt
            self._ref_dist  = None
            self._phase     = "DRAG"
            self.log(f"Base escala: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "DRAG":
            factor = self._current_factor()
            self._apply_scale(factor)

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self._selection_enter("ESCALAR", self._start_base_phase)
        elif self._phase == "BASE":
            self.log("Haga clic para definir el punto base de escala.")
        elif self._phase == "DRAG":
            if text:
                import re
                m = re.match(r'^(-?\d+(?:\.\d+)?)$', text.strip())
                if m:
                    factor = float(m.group(1))
                    # ── REGLA ESTRICTA: factor debe ser positivo ──────────────
                    if factor <= 0:
                        self.log("⚠ El factor de escala debe ser positivo (> 0).")
                        return
                    self._apply_scale(factor)
                else:
                    self.log("Factor inválido. Escriba un número positivo (ej: 2 o 0.5).")
            else:
                factor = self._current_factor()
                self._apply_scale(factor)

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "DRAG" and self._base is not None:
            ms = QPointF(*viewport.world_to_screen(self._mouse.x(), self._mouse.y()))
            self._draw_vector_line(painter, viewport,
                                   self._base.x(), self._base.y(), ms)
            self._draw_base_marker(painter, viewport,
                                   self._base.x(), self._base.y())
            f = self._current_factor()
            for e in self.doc.selected:
                e.draw_ghost_scaled(painter, viewport,
                                    self._base.x(), self._base.y(), f)

    # ── Private ───────────────────────────────────────────────────────────────
    def _start_base_phase(self):
        self._phase = "BASE"
        self.log("ESCALA ▶ Especifique punto base:")

    def _current_factor(self) -> float:
        """
        Calcula el factor de escala actual por arrastre.
        REGLA: mínimo siempre 0.01 (nunca 0 ni negativo).
        """
        if self._base is None:
            return 1.0
        dist = math.hypot(self._mouse.x() - self._base.x(),
                          self._mouse.y() - self._base.y())
        if self._ref_dist and self._ref_dist > 0.001:
            factor = dist / self._ref_dist
        else:
            factor = max(dist, 0.001)
        return max(factor, MIN_SCALE_FACTOR)  # Nunca baja de 0.01

    def _apply_scale(self, factor: float):
        if factor <= 0:
            self.log("⚠ El factor de escala debe ser positivo (> 0).")
            return
        self.doc.push_undo()
        for e in self.doc.selected:
            e.scale(self._base.x(), self._base.y(), factor)
            e.selected = False
        self.doc.selected.clear()
        self.log(f"Escala ×{factor:.3f} aplicada.")
        self.is_done = True
