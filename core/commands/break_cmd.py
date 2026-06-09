import math
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QPainter, QPen, QColor
from core.document import Document
from core.commands.base_command import BaseCommand
from core.entities import LineEntity, ArcEntity, CircleEntity
from core.geometry import point_to_segment_distance


class BreakCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._entity = None
        self._p1: QPointF | None = None
        self._p2: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._preview_p1: QPointF | None = None

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "PARTIR ▶ Seleccione entidad a partir:"
        if self._phase == "FIRST_POINT":
            return "PARTIR ▶ Especifique primer punto de rotura:"
        return "PARTIR ▶ Especifique segundo punto de rotura:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt
        if self._phase == "FIRST_POINT":
            self._preview_p1 = world_pt
        elif self._phase == "SECOND_POINT" and self._entity is not None:
            self._preview_p1 = None

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            entity = None
            if hasattr(self, '_find_entity_at'):
                entity = self._find_entity_at(world_pt)
            if entity is None:
                self.log("No se detectó ninguna entidad.")
                return
            if not isinstance(entity, (LineEntity, CircleEntity, ArcEntity)):
                self.log("Solo se pueden partir líneas, círculos y arcos.")
                return
            self._entity = entity
            self._p1 = _project_point(entity, world_pt)
            self._phase = "SECOND_POINT"
            tp = type(entity).__name__
            self.log(f"{tp} seleccionado. Especifique segundo punto de rotura:")
        elif self._phase == "SECOND_POINT":
            self._p2 = _project_point(self._entity, world_pt)
            self._apply_break()

    def on_enter(self, text: str = ""):
        if self._phase == "SELECT":
            self.log("Seleccione una entidad con clic izquierdo.")
        elif self._phase == "SECOND_POINT":
            self._p2 = _project_point(self._entity, self._mouse)
            self._apply_break()

    def draw_preview(self, painter: QPainter, viewport):
        if self._entity is not None and self._p2 is None and self._preview_p1 is not None:
            pt = _project_point(self._entity, self._preview_p1)
            sx, sy = viewport.world_to_screen(pt.x(), pt.y())
            painter.setPen(QPen(QColor("#00FF00"), 2, Qt.SolidLine))
            painter.drawLine(QPointF(sx - 5, sy), QPointF(sx + 5, sy))
            painter.drawLine(QPointF(sx, sy - 5), QPointF(sx, sy + 5))

        if self._entity is not None and self._p1 is not None and self._p2 is not None:
            p1 = _project_point(self._entity, self._p1)
            p2 = _project_point(self._entity, self._p2)
            sx1, sy1 = viewport.world_to_screen(p1.x(), p1.y())
            sx2, sy2 = viewport.world_to_screen(p2.x(), p2.y())
            painter.setPen(QPen(QColor("#FF4444"), 2, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _apply_break(self):
        ent = self._entity
        p1, p2 = self._p1, self._p2
        if p1 is None or p2 is None or ent is None:
            return
        self.doc.push_undo()

        if isinstance(ent, LineEntity):
            t1 = _line_param(ent, p1)
            t2 = _line_param(ent, p2)
            t_min = min(t1, t2)
            t_max = max(t1, t2)
            if t_min <= 0 and t_max >= 1:
                self.doc.remove_entity(ent)
            elif t_min <= 0:
                ent.x1, ent.y1 = ent.x2 + (ent.x2 - ent.x1) * (t_max - 1), ent.y2 + (ent.y2 - ent.y1) * (t_max - 1)
                ent.x1, ent.y1 = _point_on_line(ent, t_max)
            elif t_max >= 1:
                ent.x2, ent.y2 = _point_on_line(ent, t_min)
            else:
                mid = _point_on_line(ent, t_max)
                ent.x2, ent.y2 = _point_on_line(ent, t_min)
                seg2 = LineEntity(mid.x(), mid.y(), _point_on_line(ent, t_max).x(), _point_on_line(ent, t_max).y(),
                                  color=ent.color, layer=ent.layer)

        elif isinstance(ent, CircleEntity):
            a1 = math.atan2(p1.y() - ent.cy, p1.x() - ent.cx)
            a2 = math.atan2(p2.y() - ent.cy, p2.x() - ent.cx)
            sa = math.degrees(a1)
            ea = math.degrees(a2)
            span = (ea - sa) % 360
            arc1 = ArcEntity(ent.cx, ent.cy, ent.radius, sa, span, color=ent.color, layer=ent.layer)
            arc2 = ArcEntity(ent.cx, ent.cy, ent.radius, sa + span, 360 - span, color=ent.color, layer=ent.layer)
            self.doc.remove_entity(ent)
            self.doc.add_entity(arc1)
            self.doc.add_entity(arc2)

        elif isinstance(ent, ArcEntity):
            a1 = math.degrees(math.atan2(p1.y() - ent.cy, p1.x() - ent.cx))
            a2 = math.degrees(math.atan2(p2.y() - ent.cy, p2.x() - ent.cx))
            sa = ent.start_angle
            span = ent.span_angle
            ea = sa + span
            t1 = (a1 - sa) / span if span != 0 else 0
            t2 = (a2 - sa) / span if span != 0 else 0
            if t1 > t2:
                t1, t2 = t2, t1
            if t1 <= 0 and t2 >= 1:
                self.doc.remove_entity(ent)
            elif t1 <= 0:
                ent.start_angle = sa + t2 * span
                ent.span_angle = span - t2 * span
            elif t2 >= 1:
                ent.span_angle = t1 * span
            else:
                ent.span_angle = (t1 - t2) * span

        self.doc.clear_selection()
        self.log("Entidad partida.")
        self.is_done = True


def _project_point(entity, pt: QPointF):
    if isinstance(entity, LineEntity):
        return _closest_on_line(entity, pt)
    if isinstance(entity, (CircleEntity, ArcEntity)):
        a = math.atan2(pt.y() - entity.cy, pt.x() - entity.cx)
        return QPointF(entity.cx + entity.radius * math.cos(a),
                       entity.cy + entity.radius * math.sin(a))
    return pt


def _closest_on_line(line, pt):
    dx = line.x2 - line.x1
    dy = line.y2 - line.y1
    if dx == 0 and dy == 0:
        return QPointF(line.x1, line.y1)
    t = ((pt.x() - line.x1) * dx + (pt.y() - line.y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return QPointF(line.x1 + t * dx, line.y1 + t * dy)


def _point_on_line(line, t):
    return QPointF(line.x1 + t * (line.x2 - line.x1),
                   line.y1 + t * (line.y2 - line.y1))


def _line_param(line, pt):
    dx = line.x2 - line.x1
    dy = line.y2 - line.y1
    if dx == 0 and dy == 0:
        return 0.0
    return ((pt.x() - line.x1) * dx + (pt.y() - line.y1) * dy) / (dx * dx + dy * dy)
