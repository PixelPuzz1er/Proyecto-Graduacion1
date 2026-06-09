# -*- coding: utf-8 -*-
"""
core/document.py — Modelo de datos del CAD (entidades, selección, undo).
Sin dependencias de UI ni de coordenadas de pantalla.
"""
import copy
from typing import List

from core.entities import Entity


class Document:
    """
    Modelo central: guarda las entidades, el set de selección y la pila de undo.
    No sabe nada de coordenadas de pantalla ni de Qt widgets.
    """

    MAX_UNDO = 50

    def __init__(self):
        self.entities: List[Entity] = []
        self.selected: List[Entity] = []
        self._undo_stack: List[List[Entity]] = []

    # ══════════════════════════════════════════════════════════════════════════
    #  Gestión de Entidades
    # ══════════════════════════════════════════════════════════════════════════

    def add_entity(self, entity: Entity):
        self.entities.append(entity)

    def remove_entity(self, entity: Entity):
        if entity in self.entities:
            self.entities.remove(entity)

    def remove_selected(self):
        """Borra todas las entidades seleccionadas del documento."""
        for e in list(self.selected):
            self.remove_entity(e)
        self.clear_selection()

    # ══════════════════════════════════════════════════════════════════════════
    #  Gestión de Selección
    # ══════════════════════════════════════════════════════════════════════════

    def toggle_select(self, entity: Entity):
        if entity in self.selected:
            self.selected.remove(entity)
            entity.selected = False
        else:
            self.selected.append(entity)
            entity.selected = True

    def add_to_selection(self, entity: Entity):
        if entity not in self.selected:
            self.selected.append(entity)
            entity.selected = True

    def clear_selection(self):
        for e in self.selected:
            e.selected = False
        self.selected.clear()

    @property
    def has_selection(self) -> bool:
        return len(self.selected) > 0

    # ══════════════════════════════════════════════════════════════════════════
    #  Undo / Redo
    # ══════════════════════════════════════════════════════════════════════════

    def push_undo(self):
        """Guarda un snapshot profundo del estado actual antes de mutarlo."""
        snapshot = copy.deepcopy(self.entities)
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > self.MAX_UNDO:
            self._undo_stack.pop(0)

    def pop_undo(self) -> bool:
        """Restaura el estado anterior. Retorna True si se aplicó undo."""
        if not self._undo_stack:
            return False
        self.clear_selection()
        self.entities = self._undo_stack.pop()
        return True

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0
