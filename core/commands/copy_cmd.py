# -*- coding: utf-8 -*-
"""
core/commands/copy_cmd.py — Comando COPY (CO)
Fases: SELECT → BASE_POINT → DESTINATION (loop, ESC/clic der. = salir)

El bucle de copiado NO termina con clic — solo con ESC o clic derecho en DESTINATION.
Entrada numérica igual que MOVE.
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand


class CopyCommand(BaseCommand):

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
            return "COPIAR ▶ Seleccione objetos (Enter/clic der. = confirmar):"
        if self._phase == "BASE":
            return "COPIAR ▶ Especifique punto base:"
        return "COPIAR ▶ Punto de inserción (clic der. = salir)  [@dx,dy | dist]:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "BASE":
            self._base  = world_pt
            self._phase = "DESTINATION"
            self.log(f"Base: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "DESTINATION":
            self._place_copy(world_pt)

    def on_right_click(self, world_pt: QPointF):
        if self._phase == "DESTINATION":
            # Clic derecho en fase de destino → salir del modo copia
            self.doc.clear_selection()
            self.log("Modo COPIAR terminado.")
            self.is_done = True
        else:
            self.on_enter("")

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self._selection_enter("COPIAR", self._start_base_phase)
        elif self._phase == "BASE":
            pt = parse_coord_input(text)
            if pt is not None:
                self._base  = pt
                self._phase = "DESTINATION"
            else:
                self.log("Haga clic o escriba X,Y para el punto base.")
        elif self._phase == "DESTINATION":
            if text:
                cursor_dir = (self._mouse.x() - self._base.x(),
                              self._mouse.y() - self._base.y())
                pt = parse_coord_input(text, self._base, cursor_dir)
                if pt is not None:
                    self._place_copy(pt)
                else:
                    self.log("Formato inválido. Use @dx,dy | @d<ang | X,Y | dist")
            else:
                # Enter vacío en DESTINATION = salir del modo copia
                self.doc.clear_selection()
                self.log("Modo COPIAR terminado.")
                self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "DESTINATION" and self._base is not None:
            ms = QPointF(*viewport.world_to_screen(self._mouse.x(), self._mouse.y()))
            self._draw_vector_line(painter, viewport,
                                   self._base.x(), self._base.y(), ms)
            self._draw_base_marker(painter, viewport,
                                   self._base.x(), self._base.y())
            vx = self._mouse.x() - self._base.x()
            vy = self._mouse.y() - self._base.y()
            for e in self.doc.selected:
                e.draw_ghost_offset(painter, viewport, vx, vy)

    # ── Private ───────────────────────────────────────────────────────────────
    def _start_base_phase(self):
        self._phase = "BASE"
        self.log("COPIAR ▶ Especifique punto base:")

    def _place_copy(self, dest: QPointF):
        vx = dest.x() - self._base.x()
        vy = dest.y() - self._base.y()
        self.doc.push_undo()
        for e in self.doc.selected:
            self.doc.add_entity(e.copy_at_offset(vx, vy))
        n = len(self.doc.selected)
        self.log(f"{n} copia(s) colocada(s). Siguiente punto o clic der. para salir.")
        # NO termina → sigue en DESTINATION para múltiples copias
