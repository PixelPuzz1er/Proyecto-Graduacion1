# -*- coding: utf-8 -*-
"""
core/commands/erase_cmd.py — Comando ERASE (E)
Fases: SELECT → confirmar con Enter/clic der.
Si hay pre-selección, borra directamente.
"""
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter

from core.document          import Document
from core.commands.base_command import BaseCommand


class EraseCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        if doc.has_selection:
            # PICKFIRST: ya hay selección → borrar inmediatamente
            self._do_erase()
        else:
            self._phase = "SELECT"
            self.log("BORRAR ▶ Seleccione objetos (Enter/clic der. = confirmar):")

    @property
    def prompt(self) -> str:
        return "BORRAR ▶ Seleccione objetos (Enter/clic der. = confirmar):"

    def on_mouse_move(self, world_pt: QPointF): pass

    def on_left_click(self, world_pt: QPointF):
        # La selección la maneja el canvas; aquí no se necesita nada
        pass

    def on_enter(self, text: str = ""):
        self._selection_enter("BORRAR", self._do_erase)

    def draw_preview(self, painter: QPainter, viewport): pass

    # ── Private ───────────────────────────────────────────────────────────────
    def _do_erase(self):
        n = len(self.doc.selected)
        self.doc.push_undo()
        self.doc.remove_selected()
        self.log(f"{n} entidad(es) borrada(s).")
        self.is_done = True
