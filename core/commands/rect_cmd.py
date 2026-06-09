# -*- coding: utf-8 -*-
"""
core/commands/rect_cmd.py — Comando RECTANG (REC) - AutoCAD 2026 Spec
Fases:
- WAIT_P1: Precise primer punto de esquina o [Chaflán/Elevación/Empalme/Altura de objeto/Grosor]:
- WAIT_P2: Precise esquina opuesta o [Área/Cotas/Rotación]:
"""
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, Qt

from core.document          import Document
from core.entities          import RectEntity
from core.geometry          import parse_coord_input
from core.commands.base_command import BaseCommand

class RectCommand(BaseCommand):
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._p1: QPointF | None = None
        self._mouse: QPointF = QPointF(0, 0)
        self._phase = "WAIT_P1"

    @property
    def prompt(self) -> str:
        if self._phase == "WAIT_P1":
            return "Precise primer punto de esquina o [Chaflán/Elevación/Empalme/Altura de objeto/Grosor]:"
        elif self._phase == "WAIT_P2":
            return "Precise esquina opuesta o [Área/Cotas/Rotación]:"
        return ""

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "WAIT_P1":
            self._p1 = world_pt
            self._phase = "WAIT_P2"
            self.log(f"Esquina 1: ({world_pt.x():.2f}, {world_pt.y():.2f})")
        elif self._phase == "WAIT_P2":
            self._commit(world_pt)

    def on_right_click(self, world_pt: QPointF):
        self.on_escape()

    def on_enter(self, text: str = ""):
        text = text.strip().upper()
        if not text:
            self.on_escape()
            return
            
        ref_pt = self._p1 if self._phase == "WAIT_P2" else None
        pt = parse_coord_input(text, ref_pt, self._cursor_dir() if ref_pt else None)
        
        if pt is not None:
            self.on_left_click(pt)
        else:
            self.log("Se requiere un punto (Ej: 10,20 o @5<45).")

    def on_escape(self):
        self.is_done = True
        self.log("Comando RECTANG finalizado.")

    def draw_preview(self, painter: QPainter, viewport):
        if self._phase == "WAIT_P2" and self._p1:
            sx1, sy1 = viewport.world_to_screen(self._p1.x(), self._p1.y())
            sx2, sy2 = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
            painter.setPen(QPen(QColor("#FFFFFF"), 1, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            from PySide6.QtCore import QRectF
            painter.drawRect(QRectF(QPointF(sx1, sy1), QPointF(sx2, sy2)).normalized())

    def _commit(self, p2: QPointF):
        self.doc.push_undo()
        self.doc.add_entity(RectEntity(self._p1.x(), self._p1.y(), p2.x(), p2.y()))
        self.log("Rectángulo creado.")
        self.is_done = True

    def _cursor_dir(self):
        if self._phase == "WAIT_P2" and self._p1:
            return (self._mouse.x() - self._p1.x(), self._mouse.y() - self._p1.y())
        return (1.0, 0.0)
