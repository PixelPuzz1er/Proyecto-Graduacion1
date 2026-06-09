from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter
from core.document import Document
from core.commands.base_command import BaseCommand


class ArrayCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._mouse: QPointF = QPointF(0, 0)
        self._rows: int = 3
        self._cols: int = 3
        self._row_dist: float = 50.0
        self._col_dist: float = 50.0

        if doc.has_selection:
            self._phase = "ROWS"

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "ARRAY ▶ Seleccione objetos (Enter/clic der. = confirmar):"
        if self._phase == "ROWS":
            return f"ARRAY ▶ Número de filas <{self._rows}>:"
        if self._phase == "COLS":
            return f"ARRAY ▶ Número de columnas <{self._cols}>:"
        if self._phase == "ROW_DIST":
            return f"ARRAY ▶ Distancia entre filas <{self._row_dist:.1f}>:"
        return f"ARRAY ▶ Distancia entre columnas <{self._col_dist:.1f}>:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            entity = None
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            if entity:
                self.doc.toggle_select(entity)

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            if not self.doc.selected:
                self.log("Sin selección. Cancelando ARRAY.")
                self.is_done = True
            else:
                self._phase = "ROWS"
                self.log(f"{len(self.doc.selected)} obj. seleccionado(s). Filas [{self._rows}]:")
        elif self._phase == "ROWS":
            if text:
                try:
                    v = int(text.strip())
                    if v < 1: raise ValueError
                    self._rows = v
                except ValueError:
                    self.log("Número inválido. Use un entero positivo.")
                    return
            self._phase = "COLS"
            self.log(f"Columnas [{self._cols}]:")
        elif self._phase == "COLS":
            if text:
                try:
                    v = int(text.strip())
                    if v < 1: raise ValueError
                    self._cols = v
                except ValueError:
                    self.log("Número inválido. Use un entero positivo.")
                    return
            self._phase = "ROW_DIST"
            self.log(f"Distancia entre filas [{self._row_dist:.1f}]:")
        elif self._phase == "ROW_DIST":
            if text:
                try:
                    v = float(text.strip())
                    if v <= 0: raise ValueError
                    self._row_dist = v
                except ValueError:
                    self.log("Distancia inválida.")
                    return
            self._phase = "COL_DIST"
            self.log(f"Distancia entre columnas [{self._col_dist:.1f}]:")
        elif self._phase == "COL_DIST":
            if text:
                try:
                    v = float(text.strip())
                    if v <= 0: raise ValueError
                    self._col_dist = v
                except ValueError:
                    self.log("Distancia inválida.")
                    return
            self._apply_array()

    def draw_preview(self, painter: QPainter, viewport):
        pass

    def _apply_array(self):
        self.doc.push_undo()
        new_ents = []
        for e in self.doc.selected:
            for r in range(self._rows):
                for c in range(self._cols):
                    if r == 0 and c == 0:
                        continue
                    dx = c * self._col_dist
                    dy = r * self._row_dist
                    new_ents.append(e.copy_at_offset(dx, dy))
        for ne in new_ents:
            self.doc.add_entity(ne)
        n = len(new_ents)
        self.doc.clear_selection()
        self.log(f"Array: {n} copia(s) creada(s) ({self._rows}×{self._cols}).")
        self.is_done = True
