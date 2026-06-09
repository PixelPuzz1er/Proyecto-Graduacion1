import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from core.document import Document
from core.commands.base_command import BaseCommand
from core.entities import LineEntity, CircleEntity, ArcEntity


class OffsetCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._dist: float | None = None
        self._source = None
        self._mouse: QPointF = QPointF(0, 0)
        self._preview_valid = False
        self._preview_entity = None

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "DESFASE ▶ Seleccione objeto a desfasar:"
        if self._phase == "DISTANCE":
            return "DESFASE ▶ Especifique distancia de desfase:"
        return "DESFASE ▶ Especifique lado para desfasar:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt
        if self._phase == "SIDE" and self._source is not None and self._dist is not None:
            self._compute_preview()

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            else:
                entity = None
            if entity is None:
                self.log("Ningún objeto seleccionado.")
                return
            if not _is_offsetable(entity):
                self.log("El objeto seleccionado no se puede desfasar.")
                return
            self._source = entity
            self._phase = "DISTANCE"
            self.log(f"Objeto seleccionado. Especifique distancia:")
        elif self._phase == "DISTANCE":
            d = math.hypot(world_pt.x(), world_pt.y())
            if d < 0.001:
                self.log("Distancia demasiado pequeña.")
                return
            self._dist = d
            self._phase = "SIDE"
            self.log(f"Distancia: {d:.2f}. Seleccione lado:")
            self._compute_preview()
        elif self._phase == "SIDE":
            self._apply_offset()

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self.log("Seleccione un objeto con clic izquierdo.")
        elif self._phase == "DISTANCE":
            if text:
                try:
                    d = float(text.strip())
                    if d <= 0:
                        self.log("La distancia debe ser positiva.")
                        return
                    self._dist = d
                    self._phase = "SIDE"
                    self.log(f"Distancia: {d:.2f}. Seleccione lado:")
                    self._compute_preview()
                except ValueError:
                    self.log("Distancia inválida.")
            else:
                self.log("Especifique una distancia numérica.")
        elif self._phase == "SIDE":
            self._apply_offset()

    def draw_preview(self, painter: QPainter, viewport):
        if self._preview_valid and self._preview_entity:
            self._preview_entity.draw(painter, viewport, show_grips=False)
            painter.setPen(QPen(QColor("#00FFFF"), 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            if isinstance(self._preview_entity, LineEntity):
                sx1, sy1 = viewport.world_to_screen(self._preview_entity.x1, self._preview_entity.y1)
                sx2, sy2 = viewport.world_to_screen(self._preview_entity.x2, self._preview_entity.y2)
                painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
            elif isinstance(self._preview_entity, CircleEntity):
                scx, scy = viewport.world_to_screen(self._preview_entity.cx, self._preview_entity.cy)
                sr = self._preview_entity.radius * viewport.zoom
                painter.drawEllipse(QPointF(scx, scy), sr, sr)
            elif isinstance(self._preview_entity, ArcEntity):
                segs = 48
                pts = []
                sa_rad = math.radians(self._preview_entity.start_angle)
                span_rad = math.radians(self._preview_entity.span_angle)
                for i in range(segs + 1):
                    a = sa_rad + span_rad * i / segs
                    wx = self._preview_entity.cx + self._preview_entity.radius * math.cos(a)
                    wy = self._preview_entity.cy + self._preview_entity.radius * math.sin(a)
                    sx, sy = viewport.world_to_screen(wx, wy)
                    pts.append(QPointF(sx, sy))
                painter.drawPolyline(pts)

    def _compute_preview(self):
        ent = self._source
        d = self._dist
        mouse = self._mouse
        c = _offset_entity(ent, d, mouse)
        self._preview_entity = c
        self._preview_valid = c is not None

    def _apply_offset(self):
        if not self._preview_valid or self._preview_entity is None:
            self.log("No se pudo calcular el desfase.")
            return
        self.doc.push_undo()
        self.doc.add_entity(self._preview_entity)
        self.log("Desfase aplicado.")
        self.is_done = True


def _is_offsetable(entity) -> bool:
    return isinstance(entity, (LineEntity, CircleEntity, ArcEntity))


def _offset_entity(entity, dist: float, pick: QPointF):
    if isinstance(entity, LineEntity):
        dx = entity.x2 - entity.x1
        dy = entity.y2 - entity.y1
        length = math.hypot(dx, dy)
        if length < 1e-9:
            return None
        nx = -dy / length
        ny = dx / length
        cx = (entity.x1 + entity.x2) / 2.0
        cy = (entity.y1 + entity.y2) / 2.0
        mid_to_pick = math.hypot(pick.x() - cx, pick.y() - cy)
        sign = 1.0
        if mid_to_pick > 0:
            dot = (pick.x() - cx) * nx + (pick.y() - cy) * ny
            sign = 1.0 if dot >= 0 else -1.0
        ox1 = entity.x1 + nx * dist * sign
        oy1 = entity.y1 + ny * dist * sign
        ox2 = entity.x2 + nx * dist * sign
        oy2 = entity.y2 + ny * dist * sign
        return LineEntity(ox1, oy1, ox2, oy2, color=entity.color, layer=entity.layer)

    if isinstance(entity, CircleEntity):
        d = math.hypot(pick.x() - entity.cx, pick.y() - entity.cy)
        r = entity.radius + dist if d >= 0 else entity.radius - dist
        if r <= 0:
            return None
        return CircleEntity(entity.cx, entity.cy, r, color=entity.color, layer=entity.layer)

    if isinstance(entity, ArcEntity):
        d = math.hypot(pick.x() - entity.cx, pick.y() - entity.cy)
        r = entity.radius + dist if d >= entity.radius else entity.radius - dist
        if r <= 0:
            return None
        return ArcEntity(entity.cx, entity.cy, r, entity.start_angle, entity.span_angle, color=entity.color, layer=entity.layer)

    return None
