# -*- coding: utf-8 -*-
"""
core/commands/base_command.py — Clase abstracta base para todos los comandos CAD.

Ciclo de vida:
  canvas → command.on_left_click(world_pt)
  canvas → command.on_mouse_move(world_pt)
  canvas → command.on_enter(text)          ← Enter o clic derecho
  canvas → command.on_escape()
  canvas → command.draw_preview(painter, viewport)
  canvas ← command.prompt                  ← texto para la consola
  canvas ← command.is_done                 ← True = comando terminó
"""
from abc import ABC, abstractmethod
from typing import Callable, List, Optional

from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document import Document
from core.entities  import Entity


class BaseCommand(ABC):
    """
    Comando CAD abstracto.
    Subclases implementan las operaciones específicas.
    """

    def __init__(self, doc: Document, log: Callable[[str], None]):
        self.doc    = doc
        self.log    = log          # fn(str) → añade línea al historial de consola
        self.is_done = False       # True → el canvas destruye el comando

    # ── Interfaz pública (eventos del canvas) ─────────────────────────────────

    @abstractmethod
    def on_left_click(self, world_pt: QPointF): ...

    @abstractmethod
    def on_mouse_move(self, world_pt: QPointF): ...

    @abstractmethod
    def on_enter(self, text: str = "") -> None:
        """Llamado cuando el usuario presiona Enter (con o sin texto en el buffer)."""
        ...

    def on_right_click(self, world_pt: QPointF):
        """Clic derecho = ENTER sin texto en casi todos los contextos."""
        self.on_enter("")

    def on_escape(self):
        """ESC → cancelar comando y limpiar selección."""
        self.doc.clear_selection()
        self.is_done = True

    @abstractmethod
    def draw_preview(self, painter: QPainter, viewport) -> None:
        """Dibuja rubber-band / ghost / caja de selección durante el comando."""
        ...

    @property
    @abstractmethod
    def prompt(self) -> str:
        """Texto que aparece como prefijo en la consola de comandos."""
        ...

    # ── Helpers de selección (comunes a comandos de edición) ──────────────────

    def _selection_enter(self, cmd_name: str, next_phase_fn: Callable):
        """Lógica estándar de confirmación de selección por Enter."""
        if not self.doc.selected:
            self.log(f"Sin selección. Cancelando {cmd_name}.")
            self.is_done = True
        else:
            self.log(f"{len(self.doc.selected)} obj. seleccionado(s).")
            next_phase_fn()

    def _draw_base_marker(self, painter: QPainter, viewport,
                          bx: float, by: float):
        """Cruz amarilla sobre el punto base activo."""
        from PySide6.QtCore import Qt, QPointF
        from PySide6.QtGui  import QPen, QColor
        sx, sy = viewport.world_to_screen(bx, by)
        painter.setPen(QPen(QColor("#FFFF00"), 2, Qt.SolidLine))
        painter.drawLine(QPointF(sx - 8, sy),     QPointF(sx + 8, sy))
        painter.drawLine(QPointF(sx,     sy - 8), QPointF(sx,     sy + 8))

    def _draw_vector_line(self, painter: QPainter, viewport,
                          bx: float, by: float, mouse_screen_pt: QPointF):
        """Línea guía blanca discontinua desde base hasta cursor."""
        from PySide6.QtCore import Qt
        from PySide6.QtGui  import QPen, QColor
        sx, sy = viewport.world_to_screen(bx, by)
        painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
        painter.drawLine(QPointF(sx, sy), mouse_screen_pt)
