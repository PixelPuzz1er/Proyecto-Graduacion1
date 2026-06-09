# -*- coding: utf-8 -*-
"""
core/commands/trim_cmd.py — Comandos TRIM (TR) y EXTEND (EX) unificados.

Paradigma AutoCAD 2026:
  1. Segmentado Secuencial y Ordenamiento Vectorial por Parámetro T.
  2. Hibridación completa mediante la tecla SHIFT (TRIM <-> EXTEND).
  3. Edición en base de datos: Recorte en extremos o división física de la entidad (split) en dos nuevas líneas.
"""
import math
from PySide6.QtCore import QPointF
from PySide6.QtGui  import QPainter, QPen, QColor, QGuiApplication
from PySide6.QtCore import Qt

from core.document          import Document
from core.entities          import LineEntity, CircleEntity
from core.geometry          import (get_entities_intersection, point_to_segment_distance,
                                    get_line_parameter)
from core.commands.base_command import BaseCommand


class TrimCommand(BaseCommand):

    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._phase = "SELECT"              # "SELECT" | "TARGET"
        self._edges = []                    # Bordes de corte / límite
        self._mouse = QPointF(0, 0)
        self._default_mode = "TRIM"         # "TRIM" en TrimCommand, "EXTEND" en ExtendCommand

        # Hover states
        self._hovered_entity = None
        self._t_segments = []               # Parámetros t ordenados para segmentado
        self._selected_segment_idx = -1    # Segmento bajo el ratón
        self._extend_p1 = True              # Extremo a extender
        self._extend_intersection = None    # Intersección virtual calculada

        if doc.has_selection:
            self._start_target_phase()

    @property
    def prompt(self) -> str:
        if self._phase == "SELECT":
            if self._default_mode == "TRIM":
                return "RECORTAR ▶ Seleccione bordes de corte (Enter para <seleccionar todo>):"
            else:
                return "EXTENDER ▶ Seleccione bordes límite (Enter para <seleccionar todo>):"
        
        # Fase TARGET
        if self._default_mode == "TRIM":
            return "RECORTAR ▶ Seleccione objeto a recortar o [Shift+Clic para Extender]:"
        else:
            return "EXTENDER ▶ Seleccione objeto a extender o [Shift+Clic para Recortar]:"

    def on_mouse_move(self, world_pt: QPointF):
        self._mouse = world_pt

    def on_left_click(self, world_pt: QPointF):
        if self._phase == "SELECT":
            pass
        elif self._phase == "TARGET":
            is_shift = bool(QGuiApplication.keyboardModifiers() & Qt.ShiftModifier)
            
            # Determinar modo efectivo
            if self._default_mode == "TRIM":
                effective_mode = "EXTEND" if is_shift else "TRIM"
            else:
                effective_mode = "TRIM" if is_shift else "EXTEND"

            if self._hovered_entity:
                if effective_mode == "TRIM":
                    if len(self._t_segments) >= 2 and self._selected_segment_idx != -1:
                        self._apply_trim()
                else:
                    if self._extend_intersection:
                        self._apply_extend()

    def on_enter(self, text: str = "") -> None:
        if self._phase == "SELECT":
            self._start_target_phase()
        elif self._phase == "TARGET":
            if text.upper() in ("D", "DESHACER"):
                if self.doc.pop_undo():
                    self.log("Deshecho el último cambio.")
                else:
                    self.log("Nada que deshacer.")
            else:
                self.is_done = True
                self.log(f"Comando {self._default_mode} terminado.")

    def on_escape(self):
        self.doc.clear_selection()
        self.is_done = True

    def draw_preview(self, painter: QPainter, viewport) -> None:
        if self._phase == "TARGET":
            is_shift = bool(QGuiApplication.keyboardModifiers() & Qt.ShiftModifier)
            
            # Determinar modo efectivo
            if self._default_mode == "TRIM":
                effective_mode = "EXTEND" if is_shift else "TRIM"
            else:
                effective_mode = "TRIM" if is_shift else "EXTEND"

            self._update_hover(viewport, effective_mode)

            if self._hovered_entity:
                ent = self._hovered_entity
                
                if effective_mode == "TRIM":
                    # ── PREVIEW DE RECORTAR ──
                    if len(self._t_segments) >= 2 and self._selected_segment_idx != -1:
                        dx, dy = ent.x2 - ent.x1, ent.y2 - ent.y1
                        
                        for idx in range(len(self._t_segments) - 1):
                            t_start = self._t_segments[idx]
                            t_end = self._t_segments[idx + 1]
                            
                            # Obtener coordenadas mundo de este tramo
                            w_start = QPointF(ent.x1 + t_start * dx, ent.y1 + t_start * dy)
                            w_end = QPointF(ent.x1 + t_end * dx, ent.y1 + t_end * dy)
                            
                            # Pasar a coordenadas de pantalla
                            sx_start, sy_start = viewport.world_to_screen(w_start.x(), w_start.y())
                            sx_end, sy_end = viewport.world_to_screen(w_end.x(), w_end.y())
                            
                            if idx == self._selected_segment_idx:
                                # Segmento a borrar: DashedLine y Gris claro (#888888)
                                painter.setPen(QPen(QColor("#888888"), 2.0, Qt.DashLine))
                            else:
                                # Segmentos que permanecen: Color sólido normal de la entidad
                                color = QColor("#00FFFF") if ent.selected else QColor(ent.color)
                                painter.setPen(QPen(color, 2.0, Qt.SolidLine))
                                
                            painter.drawLine(QPointF(sx_start, sy_start), QPointF(sx_end, sy_end))
                else:
                    # ── PREVIEW DE EXTENDER ──
                    # Dibuja la línea original normal + una extensión sólida hasta la intersección virtual
                    if self._extend_intersection:
                        six, siy = viewport.world_to_screen(self._extend_intersection.x(), self._extend_intersection.y())
                        if self._extend_p1:
                            sx_start, sy_start = viewport.world_to_screen(ent.x1, ent.y1)
                        else:
                            sx_start, sy_start = viewport.world_to_screen(ent.x2, ent.y2)
                            
                        # Dibujar extensión sólida (Cyan #00FFFF o color de la línea)
                        painter.setPen(QPen(QColor("#00FFFF"), 2.0, Qt.SolidLine))
                        painter.drawLine(QPointF(sx_start, sy_start), QPointF(six, siy))
                        
                        # Dibujar línea original en su color normal
                        sx1, sy1 = viewport.world_to_screen(ent.x1, ent.y1)
                        sx2, sy2 = viewport.world_to_screen(ent.x2, ent.y2)
                        color = QColor("#00FFFF") if ent.selected else QColor(ent.color)
                        painter.setPen(QPen(color, 2.0, Qt.SolidLine))
                        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    # ── Private ───────────────────────────────────────────────────────────────

    def _start_target_phase(self):
        if not self.doc.selected:
            self._edges = list(self.doc.entities)
            self.log("Todos los objetos del dibujo seleccionados como bordes.")
        else:
            self._edges = list(self.doc.selected)
            self.log(f"{len(self._edges)} objetos seleccionados como bordes.")

        self.doc.clear_selection()
        self._phase = "TARGET"

    def _update_hover(self, viewport, effective_mode: str):
        self._hovered_entity = None
        self._t_segments = []
        self._selected_segment_idx = -1
        self._extend_intersection = None

        # 1. Encontrar la línea objetivo bajo el cursor (Hit test 8px)
        best_dist = 8.0
        best_e = None

        msx, msy = viewport.world_to_screen(self._mouse.x(), self._mouse.y())
        mouse_screen = QPointF(msx, msy)

        for ent in self.doc.entities:
            if isinstance(ent, LineEntity):
                sx1, sy1 = viewport.world_to_screen(ent.x1, ent.y1)
                sx2, sy2 = viewport.world_to_screen(ent.x2, ent.y2)
                p1 = QPointF(sx1, sy1)
                p2 = QPointF(sx2, sy2)

                d = point_to_segment_distance(mouse_screen, p1, p2)
                if d < best_dist:
                    best_dist = d
                    best_e = ent

        if best_e:
            self._hovered_entity = best_e

            if effective_mode == "TRIM":
                # ── CÁLCULO DE RECORTE SECUENCIAL ──
                t_vals = {0.0, 1.0}
                
                for edge in self._edges:
                    if edge is not best_e:
                        ipts = get_entities_intersection(best_e, edge)
                        for ipt, t in ipts:
                            # Sólo considerar intersecciones dentro del segmento físico del target
                            if 0.0 <= t <= 1.0:
                                # Si el borde es otra línea, verificar cruce físico (EDGEMODE = 0 por defecto)
                                if isinstance(edge, LineEntity):
                                    t_edge = get_line_parameter(QPointF(edge.x1, edge.y1), QPointF(edge.x2, edge.y2), ipt)
                                    if 0.0 <= t_edge <= 1.0:
                                        t_vals.add(t)
                                else:
                                    # Círculos u otras entidades
                                    t_vals.add(t)
                                    
                sorted_t = sorted(list(t_vals))
                
                # Consolidar parámetros t duplicados o muy pegados
                consolidated = []
                for val in sorted_t:
                    if not consolidated or abs(val - consolidated[-1]) > 1e-5:
                        consolidated.append(val)
                self._t_segments = consolidated
                
                # Calcular t_cursor
                t_cursor = get_line_parameter(QPointF(best_e.x1, best_e.y1), QPointF(best_e.x2, best_e.y2), self._mouse)
                
                # Determinar en qué segmento cae t_cursor
                if len(self._t_segments) >= 2:
                    if t_cursor < self._t_segments[0]:
                        self._selected_segment_idx = 0
                    elif t_cursor > self._t_segments[-1]:
                        self._selected_segment_idx = len(self._t_segments) - 2
                    else:
                        for idx in range(len(self._t_segments) - 1):
                            if self._t_segments[idx] <= t_cursor <= self._t_segments[idx + 1]:
                                self._selected_segment_idx = idx
                                break
            else:
                # ── CÁLCULO DE EXTENSIÓN VIRTUAL ──
                # Detección del extremo más cercano
                d1 = math.hypot(self._mouse.x() - best_e.x1, self._mouse.y() - best_e.y1)
                d2 = math.hypot(self._mouse.x() - best_e.x2, self._mouse.y() - best_e.y2)
                self._extend_p1 = (d1 < d2)
                
                # Dirección del rayo infinitamente hacia afuera
                if self._extend_p1:
                    vx, vy = best_e.x1 - best_e.x2, best_e.y1 - best_e.y2
                    px_ref, py_ref = best_e.x2, best_e.y2
                    px_start, py_start = best_e.x1, best_e.y1
                else:
                    vx, vy = best_e.x2 - best_e.x1, best_e.y2 - best_e.y1
                    px_ref, py_ref = best_e.x1, best_e.y1
                    px_start, py_start = best_e.x2, best_e.y2
                    
                valid_intersections = []
                for edge in self._edges:
                    if edge is not best_e:
                        ipts = get_entities_intersection(best_e, edge)
                        for ipt, t in ipts:
                            length_sq = vx*vx + vy*vy
                            if length_sq > 1e-9:
                                t_ray = ((ipt.x() - px_ref) * vx + (ipt.y() - py_ref) * vy) / length_sq
                                # t_ray > 1.0 indica proyección externa
                                if t_ray > 1.001:
                                    # Verificar si la intersección virtual toca físicamente el borde límite (si es línea)
                                    if isinstance(edge, LineEntity):
                                        t_edge = get_line_parameter(QPointF(edge.x1, edge.y1), QPointF(edge.x2, edge.y2), ipt)
                                        if 0.0 <= t_edge <= 1.0:
                                            dist = math.hypot(ipt.x() - px_start, ipt.y() - py_start)
                                            valid_intersections.append((ipt, dist))
                                    else:
                                        # Círculo
                                        dist = math.hypot(ipt.x() - px_start, ipt.y() - py_start)
                                        valid_intersections.append((ipt, dist))
                                        
                if valid_intersections:
                    self._extend_intersection = min(valid_intersections, key=lambda item: item[1])[0]

    def _apply_trim(self):
        ent = self._hovered_entity
        t_points = self._t_segments
        idx = self._selected_segment_idx
        
        dx, dy = ent.x2 - ent.x1, ent.y2 - ent.y1
        self.doc.push_undo()

        if idx == 0:
            # Corte al extremo inicial P1
            t_cut = t_points[1]
            ent.x1, ent.y1 = ent.x1 + t_cut * dx, ent.y1 + t_cut * dy
            self.log("Línea recortada en el extremo inicial.")
        elif idx == len(t_points) - 2:
            # Corte al extremo final P2
            t_cut = t_points[-2]
            ent.x2, ent.y2 = ent.x1 + t_cut * dx, ent.y1 + t_cut * dy
            self.log("Línea recortada en el extremo final.")
        else:
            # Corte en medio -> Eliminar entidad original y crear DOS LineEntity nuevas
            t_left = t_points[idx]
            t_right = t_points[idx + 1]
            
            ipt_left = QPointF(ent.x1 + t_left * dx, ent.y1 + t_left * dy)
            ipt_right = QPointF(ent.x1 + t_right * dx, ent.y1 + t_right * dy)
            
            # Crear nuevas líneas segmentadas
            line_left = LineEntity(ent.x1, ent.y1, ipt_left.x(), ipt_left.y(), color=ent.color, layer=ent.layer)
            line_right = LineEntity(ipt_right.x(), ipt_right.y(), ent.x2, ent.y2, color=ent.color, layer=ent.layer)
            
            # Mutar base de datos
            self.doc.remove_entity(ent)
            self.doc.add_entity(line_left)
            self.doc.add_entity(line_right)
            self.log("Segmento intermedio recortado. Línea dividida en dos partes.")

        self._hovered_entity = None
        self._selected_segment_idx = -1

    def _apply_extend(self):
        ent = self._hovered_entity
        ix, iy = self._extend_intersection.x(), self._extend_intersection.y()
        
        self.doc.push_undo()
        if self._extend_p1:
            ent.x1, ent.y1 = ix, iy
        else:
            ent.x2, ent.y2 = ix, iy
            
        self.log(f"Línea extendida hasta el borde límite en ({ix:.1f}, {iy:.1f}).")
        self._hovered_entity = None
        self._extend_intersection = None


class ExtendCommand(TrimCommand):
    """
    Comando EXTEND (EX).
    Es la imagen especular de TRIM. Comparte el 100% de la lógica y cálculo vectorial,
    invirtiendo únicamente el modo de acción por defecto.
    """
    def __init__(self, doc: Document, log):
        super().__init__(doc, log)
        self._default_mode = "EXTEND"
