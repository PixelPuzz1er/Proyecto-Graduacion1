# -*- coding: utf-8 -*-
"""
core/commands/mirror_cmd.py — Comando ESPEJO (MI)
Fases: SELECT → P1 → P2 → ERASE_YN
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import (LineEntity, CircleEntity, ArcEntity,
                                    PolylineEntity, RectEntity,
                                    EllipseEntity, PolygonEntity)
from core.geometry          import parse_coord_input, mirror_point
from core.commands.base_command import BaseCommand


class MirrorCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"
        self._p1: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        if doc.has_selection:
            self._phase = "P1"
            self.log("ESPEJO ▶ Primer punto del eje:")

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            return "ESPEJO ▶ Seleccione objetos [Enter=conf]:"
        if self._phase == "P1":
            return "ESPEJO ▶ Primer punto del eje:"
        if self._phase == "P2":
            return "ESPEJO ▶ Segundo punto del eje:"
        return "ESPEJO ▶ Suprimir origen? [Sí/No] <N>:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "P1":
            self._p1 = world_pt
            self._phase = "P2"
            self.log(f"P1: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "P2":
            self._p2 = world_pt
            self._phase = "ERASE_YN"
            self.log("ESPEJO ▶ Suprimir origen? [Sí/No] <N>:")
        elif self._phase == "ERASE_YN":
            self._apply_mirror(self._p2, erase_src=True)

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if self._phase == "SELECT":
            self._selection_enter("ESPEJO", self._start_p1)
        elif self._phase == "P1":
            pt = parse_coord_input(text)
            if pt is not None:
                self._p1 = pt
                self._phase = "P2"
                self.log(f"P1: ({pt.x():.2f}, {pt.y():.2f})")
            else:
                self.log("Especifique punto haciendo clic o escriba X,Y")
        elif self._phase == "P2":
            cursor_dir = None
            if self._p1:
                cursor_dir = (self._mouse.x() - self._p1.x(),
                              self._mouse.y() - self._p1.y())
            pt = parse_coord_input(text, self._p1, cursor_dir)
            if pt is not None:
                self._p2 = pt
                self._phase = "ERASE_YN"
                self.log("ESPEJO ▶ Suprimir origen? [Sí/No] <N>:")
            elif not text:
                self._p2 = self._mouse
                self._phase = "ERASE_YN"
                self.log("ESPEJO ▶ Suprimir origen? [Sí/No] <N>:")
            else:
                self.log("Formato inválido.")
        elif self._phase == "ERASE_YN":
            if text in ("S", "SI", "Y", "YES"):
                self._apply_mirror(self._p2, erase_src=True)
            else:
                self._apply_mirror(self._p2, erase_src=False)

    def _make_mirrored(self, src, mx1, my1, mx2, my2):
        if isinstance(src, LineEntity):
            nx1, ny1 = mirror_point(src.x1, src.y1, mx1, my1, mx2, my2)
            nx2, ny2 = mirror_point(src.x2, src.y2, mx1, my1, mx2, my2)
            return LineEntity(nx1, ny1, nx2, ny2, color=src.color, layer=src.layer)

        if isinstance(src, CircleEntity):
            ncx, ncy = mirror_point(src.cx, src.cy, mx1, my1, mx2, my2)
            return CircleEntity(ncx, ncy, src.radius, color=src.color, layer=src.layer)

        if isinstance(src, ArcEntity):
            ncx, ncy = mirror_point(src.cx, src.cy, mx1, my1, mx2, my2)
            a_start_r = math.radians(src.start_angle)
            a_span_r  = math.radians(src.span_angle)
            sx = src.cx + src.radius * math.cos(a_start_r)
            sy = src.cy + src.radius * math.sin(a_start_r)
            ex = src.cx + src.radius * math.cos(a_start_r + a_span_r)
            ey = src.cy + src.radius * math.sin(a_start_r + a_span_r)
            nsx, nsy = mirror_point(sx, sy, mx1, my1, mx2, my2)
            nex, ney = mirror_point(ex, ey, mx1, my1, mx2, my2)
            n_start = math.degrees(math.atan2(nsy - ncy, nsx - ncx)) % 360
            n_end   = math.degrees(math.atan2(ney - ncy, nex - ncx)) % 360
            n_span = (n_end - n_start) % 360
            if n_span > 180:
                n_span -= 360
            return ArcEntity(ncx, ncy, src.radius, n_start, n_span,
                             color=src.color, layer=src.layer)

        if isinstance(src, RectEntity):
            x1, y1 = mirror_point(src.x1, src.y1, mx1, my1, mx2, my2)
            x2, y2 = mirror_point(src.x2, src.y2, mx1, my1, mx2, my2)
            return RectEntity(x1, y1, x2, y2, color=src.color, layer=src.layer)

        if isinstance(src, EllipseEntity):
            ncx, ncy = mirror_point(src.cx, src.cy, mx1, my1, mx2, my2)
            nmx, nmy = mirror_point(src.cx + src.major_x, src.cy + src.major_y,
                                    mx1, my1, mx2, my2)
            nmx -= ncx; nmy -= ncy
            return EllipseEntity(ncx, ncy, nmx, nmy, src.ratio,
                                 color=src.color, layer=src.layer)

        if isinstance(src, PolylineEntity):
            npts = [mirror_point(x, y, mx1, my1, mx2, my2) for x, y in src.points]
            return PolylineEntity(npts, closed=src.closed,
                                  color=src.color, layer=src.layer)

        if isinstance(src, PolygonEntity):
            return None

        return None

    def _apply_mirror(self, p2: QPointF, erase_src: bool):
        if self._p1 is None:
            return
        mx1, my1 = self._p1.x(), self._p1.y()
        mx2, my2 = p2.x(), p2.y()
        self.doc.push_undo()
        selected = list(self.doc.selected)
        for src in selected:
            dup = self._make_mirrored(src, mx1, my1, mx2, my2)
            if dup:
                self.doc.add_entity(dup)
            if erase_src:
                self.doc.remove_entity(src)
            src.selected = False
        self.doc.selected.clear()
        self.log(f"ESPEJO: {len(selected)} obj(s) reflejado(s)." +
                 (" (origen suprimido)" if erase_src else ""))
        self.is_done = True

    def _start_p1(self):
        self._phase = "P1"
        self.log("ESPEJO ▶ Primer punto del eje:")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase in ("P2", "ERASE_YN") and self._p1 is not None:
            self._draw_mirror_axis(painter, viewport)
            self._draw_mirrored_ghost(painter, viewport)

    def _draw_mirror_axis(self, painter, viewport):
        sx1, sy1 = viewport.world_to_screen(self._p1.x(), self._p1.y())
        sx2, sy2 = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
        painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.DashLine))
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def _draw_mirrored_ghost(self, painter, viewport):
        mx1, my1 = self._p1.x(), self._p1.y()
        mx2, my2 = self._mouse.x(), self._mouse.y()
        for src in self.doc.selected:
            dup = self._make_mirrored(src, mx1, my1, mx2, my2)
            if dup:
                dup.draw(painter, viewport, show_grips=False)
