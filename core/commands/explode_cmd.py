from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter
from core.document import Document
from core.commands.base_command import BaseCommand
from core.entities import RectEntity, PolylineEntity, LineEntity


class ExplodeCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._mouse: QPointF = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "DESCOMPONER ▶ Seleccione objetos a descomponer (Enter/clic der. = ejecutar):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        entity = None
        if hasattr(self, '_find_entity_at'):
            entity = self._find_entity_at(world_pt)
        if entity:
            if isinstance(entity, (RectEntity, PolylineEntity)):
                self.doc.toggle_select(entity)
            else:
                self.log("El objeto seleccionado no se puede descomponer.")

    def on_enter(self, text: str = ""):
        if not self.doc.selected:
            self.log("Sin selección. Cancelando DESCOMPONER.")
            self.is_done = True
            return
        self.doc.push_undo()
        new_entities = []
        for e in self.doc.selected:
            decomposed = _explode(e)
            if decomposed:
                new_entities.extend(decomposed)
                self.doc.remove_entity(e)
        for ne in new_entities:
            self.doc.add_entity(ne)
        self.doc.clear_selection()
        self.log(f"{len(new_entities)} entidad(es) generada(s) al descomponer.")
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport):
        pass


def _explode(entity):
    if isinstance(entity, RectEntity):
        x1, y1 = entity.x1, entity.y1
        x2, y2 = entity.x2, entity.y2
        return [
            LineEntity(x1, y1, x2, y1, color=entity.color, layer=entity.layer),
            LineEntity(x2, y1, x2, y2, color=entity.color, layer=entity.layer),
            LineEntity(x2, y2, x1, y2, color=entity.color, layer=entity.layer),
            LineEntity(x1, y2, x1, y1, color=entity.color, layer=entity.layer),
        ]
    if isinstance(entity, PolylineEntity):
        pts = entity.points
        lines = []
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            lines.append(LineEntity(x1, y1, x2, y2, color=entity.color, layer=entity.layer))
        if entity.closed and len(pts) > 2:
            x1, y1 = pts[-1]
            x2, y2 = pts[0]
            lines.append(LineEntity(x1, y1, x2, y2, color=entity.color, layer=entity.layer))
        return lines
    return None
