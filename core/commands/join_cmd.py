import math
from PySide6.QtCore import QPointF
from PySide6.QtGui import QPainter
from core.document import Document
from core.commands.base_command import BaseCommand
from core.entities import LineEntity, ArcEntity


class JoinCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT_SOURCE"
        self._source = None
        self._mouse: QPointF = QPointF(0, 0)

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT_SOURCE":
            return "JUNTAR ▶ Seleccione entidad de origen:"
        return "JUNTAR ▶ Seleccione entidades a unir (Enter/clic der. = ejecutar):"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT_SOURCE":
            entity = None
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            if entity is None:
                self.log("No se detectó ninguna entidad.")
                return
            if not isinstance(entity, (LineEntity, ArcEntity)):
                self.log("Solo se pueden unir líneas y arcos.")
                return
            self._source = entity
            self._phase = "SELECT_TARGETS"
            self.log(f"Origen: {type(entity).__name__}. Seleccione entidades a unir:")
        elif self._phase == "SELECT_TARGETS":
            entity = None
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            if entity and entity is not self._source:
                if isinstance(entity, (LineEntity, ArcEntity)):
                    self.doc.toggle_select(entity)

    def on_right_click(self, world_pt: QPointF):
        if self._phase == "SELECT_TARGETS":
            self._apply_join()
        else:
            self.on_enter("")

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT_SOURCE":
            self.log("Seleccione una línea o arco con clic izquierdo.")
        elif self._phase == "SELECT_TARGETS":
            self._apply_join()

    def draw_preview(self, painter: QPainter, viewport):
        pass

    def _apply_join(self):
        source = self._source
        targets = list(self.doc.selected)
        if not targets:
            self.log("No hay entidades para unir. Cancelando.")
            self.is_done = True
            return

        self.doc.push_undo()
        joined = False

        if isinstance(source, LineEntity):
            xs, ys = source.x2, source.y2
            for t in targets:
                if isinstance(t, LineEntity) and _lines_collinear(source, t):
                    if _points_close(xs, ys, t.x1, t.y1):
                        source.x2, source.y2 = t.x2, t.y2
                        self.doc.remove_entity(t)
                        joined = True
                    elif _points_close(xs, ys, t.x2, t.y2):
                        source.x2, source.y2 = t.x1, t.y1
                        self.doc.remove_entity(t)
                        joined = True

        elif isinstance(source, ArcEntity):
            for t in targets:
                if isinstance(t, ArcEntity) and _arcs_compatible(source, t):
                    if _points_close(
                        source.cx + source.radius * math.cos(math.radians(source.start_angle + source.span_angle)),
                        source.cy + source.radius * math.sin(math.radians(source.start_angle + source.span_angle)),
                        t.cx + t.radius * math.cos(math.radians(t.start_angle)),
                        t.cy + t.radius * math.sin(math.radians(t.start_angle)),
                    ):
                        new_span = t.start_angle + t.span_angle - source.start_angle
                        source.span_angle = new_span
                        self.doc.remove_entity(t)
                        joined = True

        self.doc.clear_selection()
        if joined:
            self.log("Entidades unidas correctamente.")
        else:
            self.log("No se pudieron unir las entidades (no son colineales o compatibles).")
        self.is_done = True


def _points_close(x1, y1, x2, y2, tol=0.01):
    return math.hypot(x2 - x1, y2 - y1) < tol


def _lines_collinear(l1, l2, tol=0.01):
    v1x = l1.x2 - l1.x1
    v1y = l1.y2 - l1.y1
    v2x = l2.x2 - l2.x1
    v2y = l2.y2 - l2.y1
    cross = abs(v1x * v2y - v1y * v2x)
    if cross > tol:
        return False
    cx = l2.x1 - l1.x1
    cy = l2.y1 - l1.y1
    cross2 = abs(v1x * cy - v1y * cx)
    return cross2 < tol


def _arcs_compatible(a1, a2, tol=1.0):
    dc = math.hypot(a2.cx - a1.cx, a2.cy - a1.cy)
    if dc > tol:
        return False
    dr = abs(a2.radius - a1.radius)
    return dr < tol
