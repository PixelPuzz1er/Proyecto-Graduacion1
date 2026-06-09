# -*- coding: utf-8 -*-
"""
core/commands/move_cmd.py — Comando MOVE (M)
Fases: SELECT → BASE_POINT → DESTINATION

Entrada numérica en DESTINATION:
  @dx,dy       → vector relativo exacto
  @dist<angle  → polar relativo
  x,y          → coordenada absoluta
  dist         → distancia en dirección actual del cursor desde base
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand


class MoveCommand(BaseCommand):

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
            return "MOVER ▶ Seleccione objetos (Enter/clic der. = confirmar):"
        if self._phase == "BASE":
            return "MOVER ▶ Especifique punto base:"
        return "MOVER ▶ Segundo punto  (@dx,dy | @dist<ang | X,Y | dist):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "BASE":
            self._base  = world_pt
            self._phase = "DESTINATION"
            self.log(f"Base: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "DESTINATION":
            self._apply_move(world_pt)

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self._selection_enter("MOVER", self._start_base_phase)
        elif self._phase == "BASE":
            pt = parse_coord_input(text)
            if pt is not None:
                self._base  = pt
                self._phase = "DESTINATION"
                self.log(f"Base: ({pt.x():.2f}, {pt.y():.2f})")
            else:
                self.log("Especifique punto base haciendo clic o escriba X,Y")
        elif self._phase == "DESTINATION":
            if text:
                cursor_dir = (self._mouse.x() - self._base.x(),
                              self._mouse.y() - self._base.y())
                pt = parse_coord_input(text, self._base, cursor_dir)
                if pt is not None:
                    self._apply_move(pt)
                else:
                    self.log("Formato inválido. Use @dx,dy | @d<ang | X,Y | dist")
            else:
                # Enter vacío = usar posición actual del cursor
                self._apply_move(self._mouse)

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "DESTINATION" and self._base is not None:
            self._draw_vector_line(painter, viewport,
                                   self._base.x(), self._base.y(),
                                   QPointF(*viewport.world_to_screen(
                                       self._mouse.x(), self._mouse.y())))
            self._draw_base_marker(painter, viewport,
                                   self._base.x(), self._base.y())
            vx = self._mouse.x() - self._base.x()
            vy = self._mouse.y() - self._base.y()
            for e in self.doc.selected:
                e.draw_ghost_offset(painter, viewport, vx, vy)

    # ── Private ───────────────────────────────────────────────────────────────
    def _start_base_phase(self):
        self._phase = "BASE"
        self.log("MOVER ▶ Especifique punto base:")

    def _apply_move(self, dest: QPointF):
        vx = dest.x() - self._base.x()
        vy = dest.y() - self._base.y()
        self.doc.push_undo()
        for e in self.doc.selected:
            e.move(vx, vy)
            e.selected = False
        self.doc.selected.clear()
        self.log(f"Mover Δ({vx:.2f}, {vy:.2f}) aplicado.")
        self.is_done = True
