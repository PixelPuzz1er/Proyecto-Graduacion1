# -*- coding: utf-8 -*-
"""
core/commands/fillet_cmd.py — Comando EMPALME (F) - AutoCAD 2026 Spec
Fases:
- WAIT_RADIUS: Indique radio de empalme <0.0000>:
- WAIT_FIRST: Seleccione primer objeto o [Deshacer/Polilínea/Radio]:
- WAIT_SECOND: Seleccione segundo objeto:
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import LineEntity, ArcEntity
from core.geometry          import (compute_fillet, parse_factor,
                                    line_line_intersection,
                                    point_to_segment_distance,
                                    get_line_parameter)
from core.commands.base_command import BaseCommand


class FilletCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._radius: float = 0.0
        self._first: LineEntity | None = None
        self._first_pick: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_RADIUS"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_RADIUS":
            return f"Indique radio de empalme <{self._radius:.4f}>:"
        if self._phase == "WAIT_FIRST":
            return "Seleccione primer objeto o [Deshacer/Polilínea/Radio]:"
        return "Seleccione segundo objeto:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_FIRST":
            ent = self._find_line_at(world_pt)
            if ent:
                self._first = ent
                self._first_pick = world_pt
                self.log("Primer objeto seleccionado.")
                self._phase = "WAIT_SECOND"
            else:
                self.log("No se detectó ninguna línea. Intente de nuevo.")
        elif self._phase == "WAIT_SECOND":
            ent = self._find_line_at(world_pt)
            if ent is None:
                self.log("No se detectó ninguna línea.")
            elif ent is self._first:
                self.log("Seleccione un objeto diferente.")
            else:
                self._apply_fillet(self._first, ent, self._first_pick, world_pt)

    def on_right_click(self, world_pt: QPointF):
        self.on_enter("")

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            self.is_done = True
            self.log("Comando EMPALME finalizado.")
            return
        if self._phase == "WAIT_RADIUS":
            r = parse_factor(text)
            if r is not None and r >= 0:
                self._radius = r
                self.log(f"Radio: {self._radius:.4f}")
                self._phase = "WAIT_FIRST"
            else:
                self.log("Requiere un número positivo.")
        elif self._phase == "WAIT_FIRST":
            if text in ("R", "RADIO"):
                self._phase = "WAIT_RADIUS"
            elif text in ("D", "DESHACER"):
                self.log("Nada que deshacer.")
            elif text in ("P", "POLILINEA"):
                self.log("Empalme en polilínea no implementado aún.")
            else:
                self.log("Opción no reconocida.")
        elif self._phase == "WAIT_SECOND":
            self.log("Haga clic en el segundo objeto.")

    def on_escape(self):
        self.is_done = True
        self.log("Comando EMPALME cancelado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_FIRST":
            self._draw_hover(painter, viewport)
        elif self._phase == "WAIT_SECOND" and self._first:
            self._draw_highlight_first(painter, viewport)
            self._draw_preview(painter, viewport)

    # ── Private ───────────────────────────────────────────────────────────────

    def _find_line_at(self, world_pt: QPointF, viewport=None) -> LineEntity | None:
        if viewport is not None:
            best_d = 6.0 / max(viewport.zoom, 1e-9)
        else:
            best_d = 3.0
        best_e = None
        for ent in self.doc.entities:
            if isinstance(ent, LineEntity):
                a = QPointF(ent.x1, ent.y1)
                b = QPointF(ent.x2, ent.y2)
                d = point_to_segment_distance(world_pt, a, b)
                if d < best_d:
                    best_d = d
                    best_e = ent
        return best_e

    def _draw_hover(self, painter, viewport):
        tol = 6.0 / viewport.zoom
        for ent in self.doc.entities:
            if isinstance(ent, LineEntity):
                a = QPointF(ent.x1, ent.y1)
                b = QPointF(ent.x2, ent.y2)
                if point_to_segment_distance(self._mouse, a, b) < tol:
                    sx1, sy1 = viewport.world_to_screen(ent.x1, ent.y1)
                    sx2, sy2 = viewport.world_to_screen(ent.x2, ent.y2)
                    painter.setPen(QPen(QColor("#00FFFF"), 3, Qt.SolidLine))
                    painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _draw_highlight_first(self, painter, viewport):
        if not self._first:
            return
        sx1, sy1 = viewport.world_to_screen(self._first.x1, self._first.y1)
        sx2, sy2 = viewport.world_to_screen(self._first.x2, self._first.y2)
        painter.setPen(QPen(QColor(100, 180, 255), 3, Qt.SolidLine))
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _draw_preview(self, painter, viewport):
        second = self._find_line_at(self._mouse, viewport)
        if second and second is not self._first and isinstance(second, LineEntity):
            res = compute_fillet(self._first, second, self._radius,
                                 self._first_pick, self._mouse)
            if res:
                cx, cy, r, a_start, span, t1, t2, _, _ = res
                segs = 48
                pts = []
                for i in range(segs + 1):
                    a = math.radians(a_start + span * i / segs)
                    spx, spy = viewport.world_to_screen(
                        cx + r * math.cos(a), cy + r * math.sin(a))
                    pts.append(QPointF(spx, spy))
                painter.setPen(QPen(QColor("#00FFFF"), 2, Qt.SolidLine))
                painter.setBrush(Qt.NoBrush)
                for i in range(len(pts) - 1):
                    painter.drawLine(pts[i], pts[i + 1])
                tx1 = self._first.x1 + t1 * (self._first.x2 - self._first.x1)
                ty1 = self._first.y1 + t1 * (self._first.y2 - self._first.y1)
                tx2 = second.x1 + t2 * (second.x2 - second.x1)
                ty2 = second.y1 + t2 * (second.y2 - second.y1)
                painter.setPen(QPen(QColor("#FFD700"), 1, Qt.DashLine))
                for (wx, wy) in [(tx1, ty1), (tx2, ty2)]:
                    sx, sy = viewport.world_to_screen(wx, wy)
                    painter.drawEllipse(QPointF(sx, sy), 4, 4)

    def _apply_fillet(self, line1, line2, pick1, pick2):
        if self._radius < 1e-9:
            self._sharp_corner(line1, line2, pick1, pick2)
            return
        res = compute_fillet(line1, line2, self._radius, pick1, pick2)
        if res is None:
            self.log("No se puede calcular el empalme (líneas paralelas?).")
            return
        cx, cy, r, a_start, span, t1, t2, _, _ = res
        self.doc.push_undo()

        tx1 = line1.x1 + t1 * (line1.x2 - line1.x1)
        ty1 = line1.y1 + t1 * (line1.y2 - line1.y1)
        tx2 = line2.x1 + t2 * (line2.x2 - line2.x1)
        ty2 = line2.y1 + t2 * (line2.y2 - line2.y1)

        p1 = QPointF(line1.x1, line1.y1)
        p2 = QPointF(line1.x2, line1.y2)
        int_pt, t_int1 = line_line_intersection(p1, p2,
                          QPointF(line2.x1, line2.y1),
                          QPointF(line2.x2, line2.y2))
        if int_pt is None:
            return

        t_pk1 = get_line_parameter(p1, p2, pick1)
        if t_pk1 < t_int1:
            line1.x2, line1.y2 = tx1, ty1
        else:
            line1.x1, line1.y1 = tx1, ty1

        p3 = QPointF(line2.x1, line2.y1)
        p4 = QPointF(line2.x2, line2.y2)
        t_pk2 = get_line_parameter(p3, p4, pick2)
        _, t_int2 = line_line_intersection(p3, p4, p1, p2)
        if t_pk2 < t_int2:
            line2.x2, line2.y2 = tx2, ty2
        else:
            line2.x1, line2.y1 = tx2, ty2

        self.doc.add_entity(ArcEntity(cx, cy, r, a_start, span,
                                       color=line1.color))
        self.log(f"Empalme creado. Radio: {r:.4f}")
        self.is_done = True

    def _sharp_corner(self, line1, line2, pick1, pick2):
        p1 = QPointF(line1.x1, line1.y1)
        p2 = QPointF(line1.x2, line1.y2)
        p3 = QPointF(line2.x1, line2.y1)
        p4 = QPointF(line2.x2, line2.y2)
        res = line_line_intersection(p1, p2, p3, p4)
        if res is None:
            self.log("Líneas paralelas, no se puede crear esquina.")
            return
        int_pt, t_int1 = res
        _, t_int2 = line_line_intersection(p3, p4, p1, p2)
        self.doc.push_undo()
        t_pk1 = get_line_parameter(p1, p2, pick1)
        t_pk2 = get_line_parameter(p3, p4, pick2)
        if t_pk1 < t_int1:
            line1.x2, line1.y2 = int_pt.x(), int_pt.y()
        else:
            line1.x1, line1.y1 = int_pt.x(), int_pt.y()
        if t_pk2 < t_int2:
            line2.x2, line2.y2 = int_pt.x(), int_pt.y()
        else:
            line2.x1, line2.y1 = int_pt.x(), int_pt.y()
        self.log("Esquina creada (radio 0).")
        self.is_done = True
