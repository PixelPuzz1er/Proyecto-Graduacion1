# -*- coding: utf-8 -*-
"""
ui/canvas.py — CADCanvas (QWidget)
Implementación estricta de la Especificación AutoCAD 2026 para el Canvas.
"""
import math
from typing import Optional

from PySide6.QtWidgets import QWidget
from PySide6.QtCore    import Qt, QTimer, QPoint, QPointF, QRectF, Signal
from PySide6.QtGui     import (QPainter, QPainterPath, QColor, QPen, QBrush, QFont,
                                QPaintEvent, QKeyEvent, QMouseEvent, QWheelEvent)

from core.document import Document
from core.entities import Entity, LineEntity, CircleEntity, PolylineEntity
from core.geometry import point_to_segment_distance, segments_intersect

from core.command_registry import COMMAND_MAP, COMMAND_ALIASES, COMMAND_CLASS_MAP
from core.commands.base_command import BaseCommand

_SNAP_RANGE_PX = 8.0   # Atracción magnética OSNAP
_HIT_RANGE_PX  = 6.0    # Clic en entidad


class CADCanvas(QWidget):
    """
    Lienzo CAD interactivo.
    Emite state_changed(prompt, buffer, history) para actualizar consola.
    """

    state_changed = Signal(str, str, list)

    def __init__(self, doc: Document, parent=None):
        super().__init__(parent)
        self.doc = doc
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setCursor(Qt.BlankCursor)  # Reemplazado por dibujado custom

        # Cámara
        self.cam_x = 200.0
        self.cam_y = 200.0
        self.zoom  = 1.0

        # Estado del cursor y snappeo
        self._mouse_screen: QPointF = QPointF(0, 0)
        self._mouse_world:  QPointF = QPointF(0, 0)
        self._snap_point: Optional[QPointF] = None
        self._snap_type: str = "ENDPOINT"

        # Controles de Vista
        self._panning    = False
        self._pan_start  = QPoint(0, 0)

        # Selección (Window / Crossing)
        self._selecting        = False
        self._sel_start_screen = QPointF(0, 0)
        self._sel_end_screen   = QPointF(0, 0)

        # Máquina de estado (Comando activo)
        self._cmd: Optional[BaseCommand] = None

        # Hover entity (rollover highlight)
        self._hover_entity = None

        # ORTHO mode
        self._ortho_enabled = False
        self._ortho_angle = 90  # grados

        self.command_aliases = dict(COMMAND_ALIASES)

        self._history: list[str] = ["AutoCAD 2026 Engine iniciado."]
        self._buffer = ""

        # ── Dynamic Input state ────────────────────────────────────────────────
        self._dyn_active_field = 0       # 0=first, 1=second
        self._dyn_field_mode = None      # "xy", "dist_angle", "single", "prompt_only", "frozen"
        self._dyn_field_vals = ["", ""]  # values being typed in each field
        self._dyn_menu_active = False    # options dropdown visible?
        self._dyn_menu_index = 0
        self._dyn_menu_rects = []        # list of (QRectF, option_text) for hit testing

        # ORTHO mode

        # Loop a 60 FPS
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.update)
        self._timer.start(16)

        # AutoCAD 2026 Model Space Colors
        self._C_BG          = QColor("#212830")  # AutoCAD 2026 default dark model space
        self._C_CROSSHAIR   = QColor("#FFFFFF")
        self._C_SNAP        = QColor("#00FF00")
        self._C_SEL_W_BG    = QColor(0, 120, 212, 40)
        self._C_SEL_W_BD    = QColor("#0078D4")
        self._C_SEL_C_BG    = QColor(15, 123, 15, 40)
        self._C_SEL_C_BD    = QColor("#00FF00")

    # ══════════════════════════════════════════════════════════════════════════
    #  TRANSFORMACIONES DE CÁMARA
    # ══════════════════════════════════════════════════════════════════════════
    def world_to_screen(self, wx: float, wy: float) -> tuple:
        if self.zoom == 0.0: self.zoom = 0.0000001
        sx = wx * self.zoom + self.cam_x
        sy = self.height() - (wy * self.zoom + self.cam_y)
        return sx, sy

    def screen_to_world(self, sx: float, sy: float) -> tuple:
        if self.zoom == 0.0: self.zoom = 0.0000001
        wx = (sx - self.cam_x) / self.zoom
        wy = (self.height() - sy - self.cam_y) / self.zoom
        return wx, wy

    def constrain_ortho(self, target: QPointF, ref: QPointF) -> QPointF:
        """Returns the ortho-constrained point (for preview) without modifying canvas state."""
        dx = target.x() - ref.x()
        dy = target.y() - ref.y()
        angle = math.degrees(math.atan2(dy, dx))
        snapped = round(angle / self._ortho_angle) * self._ortho_angle
        dist = math.hypot(dx, dy)
        nx = ref.x() + dist * math.cos(math.radians(snapped))
        ny = ref.y() + dist * math.sin(math.radians(snapped))
        return QPointF(nx, ny)

    def _get_ortho_ref(self) -> QPointF | None:
        if not self._cmd:
            return None
        cmd = self._cmd
        phase = getattr(cmd, '_phase', '')
        for attr in ('_p1', '_base', '_first_pick', '_center', '_first', '_start'):
            val = getattr(cmd, attr, None)
            if val is not None:
                return val if isinstance(val, QPointF) else None
            if attr == '_first':
                val = getattr(cmd, attr, None)
                if val is not None and hasattr(val, 'x1'):
                    return QPointF(val.x1, val.y1)
        return None

    # ══════════════════════════════════════════════════════════════════════════
    #  OSNAP & HIT TESTING
    # ══════════════════════════════════════════════════════════════════════════
    def _compute_snap(self, sx: float, sy: float) -> tuple[Optional[QPointF], str]:
        best_d   = _SNAP_RANGE_PX
        best_pt  = None
        best_type = "ENDPOINT"
        
        for entity in self.doc.entities:
            if isinstance(entity, CircleEntity):
                svx, svy = self.world_to_screen(entity.cx, entity.cy)
                d = math.hypot(sx - svx, sy - svy)
                if d < best_d:
                    best_d, best_pt, best_type = d, QPointF(entity.cx, entity.cy), "CENTER"
                
                for vx, vy in entity.get_snap_points()[1:]:
                    svx, svy = self.world_to_screen(vx, vy)
                    d = math.hypot(sx - svx, sy - svy)
                    if d < best_d:
                        best_d, best_pt, best_type = d, QPointF(vx, vy), "QUADRANT"
            else:
                pts = entity.get_snap_points()
                if isinstance(entity, PolylineEntity):
                    num_endpoints = len(entity.points)
                elif isinstance(entity, CircleEntity):
                    num_endpoints = 0
                else:
                    num_endpoints = 2
                for i, (vx, vy) in enumerate(pts):
                    svx, svy = self.world_to_screen(vx, vy)
                    d = math.hypot(sx - svx, sy - svy)
                    if d < best_d:
                        best_d = d
                        best_pt = QPointF(vx, vy)
                        best_type = "ENDPOINT" if i < num_endpoints else "MIDPOINT"
                        
        if self._cmd and type(self._cmd).__name__ == "PolylineCommand" and len(getattr(self._cmd, '_points', [])) > 2:
            vx, vy = self._cmd._points[0].x(), self._cmd._points[0].y()
            svx, svy = self.world_to_screen(vx, vy)
            d = math.hypot(sx - svx, sy - svy)
            if d < best_d:
                best_d, best_pt, best_type = d, QPointF(vx, vy), "ENDPOINT"

        return best_pt, best_type

    def _find_entity_at(self, screen_pt: QPointF) -> Optional[Entity]:
        from core.entities import ArcEntity
        best_d  = _HIT_RANGE_PX
        best_e  = None
        for entity in self.doc.entities:
            if isinstance(entity, LineEntity):
                a = QPointF(*self.world_to_screen(entity.x1, entity.y1))
                b = QPointF(*self.world_to_screen(entity.x2, entity.y2))
                d = point_to_segment_distance(screen_pt, a, b)
            elif isinstance(entity, PolylineEntity):
                d = _HIT_RANGE_PX + 1
                for i in range(len(entity.points) - 1):
                    p1 = entity.points[i]
                    p2 = entity.points[i+1]
                    a = QPointF(*self.world_to_screen(p1[0], p1[1]))
                    b = QPointF(*self.world_to_screen(p2[0], p2[1]))
                    d_seg = point_to_segment_distance(screen_pt, a, b)
                    if d_seg < d: d = d_seg
                if getattr(entity, 'closed', False) and len(entity.points) > 2:
                    p1 = entity.points[-1]
                    p2 = entity.points[0]
                    a = QPointF(*self.world_to_screen(p1[0], p1[1]))
                    b = QPointF(*self.world_to_screen(p2[0], p2[1]))
                    d_seg = point_to_segment_distance(screen_pt, a, b)
                    if d_seg < d: d = d_seg
            elif isinstance(entity, ArcEntity):
                d = _HIT_RANGE_PX + 1
                segs = 32
                a_start = math.radians(entity.start_angle)
                a_span = math.radians(entity.span_angle)
                for i in range(segs):
                    a1 = a_start + a_span * i / segs
                    a2 = a_start + a_span * (i + 1) / segs
                    x1 = entity.cx + entity.radius * math.cos(a1)
                    y1 = entity.cy + entity.radius * math.sin(a1)
                    x2 = entity.cx + entity.radius * math.cos(a2)
                    y2 = entity.cy + entity.radius * math.sin(a2)
                    p1 = QPointF(*self.world_to_screen(x1, y1))
                    p2 = QPointF(*self.world_to_screen(x2, y2))
                    d_seg = point_to_segment_distance(screen_pt, p1, p2)
                    if d_seg < d: d = d_seg
            else:
                d = min(
                    math.hypot(screen_pt.x() - self.world_to_screen(vx, vy)[0],
                               screen_pt.y() - self.world_to_screen(vx, vy)[1])
                    for vx, vy in entity.get_snap_points()
                )
            if d < best_d:
                best_d, best_e = d, entity
        return best_e

    def _entities_in_window(self, s0: QPointF, s1: QPointF) -> list:
        is_window = s1.x() >= s0.x()
        wx0, wy0  = self.screen_to_world(s0.x(), s0.y())
        wx1, wy1  = self.screen_to_world(s1.x(), s1.y())
        rect_w    = QRectF(QPointF(wx0, wy0), QPointF(wx1, wy1)).normalized()
        tl, tr    = rect_w.topLeft(),    rect_w.topRight()
        bl, br    = rect_w.bottomLeft(), rect_w.bottomRight()

        result = []
        for entity in self.doc.entities:
            if entity in self.doc.selected: continue
                
            if isinstance(entity, CircleEntity):
                r = entity.radius
                bbox = QRectF(entity.cx - r, entity.cy - r, r * 2, r * 2)
                if is_window and rect_w.contains(bbox):
                    result.append(entity)
                elif not is_window:
                    closest_x = max(rect_w.left(), min(entity.cx, rect_w.right()))
                    closest_y = max(rect_w.top(), min(entity.cy, rect_w.bottom()))
                    if math.hypot(entity.cx - closest_x, entity.cy - closest_y) <= r:
                        result.append(entity)
            else:
                verts = entity.get_vertices()
                if is_window:
                    if all(rect_w.contains(QPointF(vx, vy)) for vx, vy in verts):
                        result.append(entity)
                else:
                    if any(rect_w.contains(QPointF(vx, vy)) for vx, vy in verts):
                        result.append(entity)
                    elif isinstance(entity, LineEntity):
                        p1 = QPointF(entity.x1, entity.y1)
                        p2 = QPointF(entity.x2, entity.y2)
                        if (segments_intersect(p1, p2, tl, tr) or
                            segments_intersect(p1, p2, tr, br) or
                            segments_intersect(p1, p2, br, bl) or
                            segments_intersect(p1, p2, bl, tl)):
                            result.append(entity)
                    elif isinstance(entity, PolylineEntity):
                        intersected = False
                        for i in range(len(entity.points) - 1):
                            p1 = QPointF(entity.points[i][0], entity.points[i][1])
                            p2 = QPointF(entity.points[i+1][0], entity.points[i+1][1])
                            if (segments_intersect(p1, p2, tl, tr) or
                                segments_intersect(p1, p2, tr, br) or
                                segments_intersect(p1, p2, br, bl) or
                                segments_intersect(p1, p2, bl, tl)):
                                intersected = True
                                break
                        if not intersected and getattr(entity, 'closed', False) and len(entity.points) > 2:
                            p1 = QPointF(entity.points[-1][0], entity.points[-1][1])
                            p2 = QPointF(entity.points[0][0], entity.points[0][1])
                            if (segments_intersect(p1, p2, tl, tr) or
                                segments_intersect(p1, p2, tr, br) or
                                segments_intersect(p1, p2, br, bl) or
                                segments_intersect(p1, p2, bl, tl)):
                                intersected = True
                        if intersected:
                            result.append(entity)
        return result

    # ══════════════════════════════════════════════════════════════════════════
    #  CONSOLA
    # ══════════════════════════════════════════════════════════════════════════
    def _log(self, msg: str):
        self._history.append(msg)
        if len(self._history) > 20: self._history.pop(0)
        self._emit_state()

    def _emit_state(self):
        prompt = self._cmd.prompt if self._cmd else "Comando: "
        self.state_changed.emit(prompt, self._buffer, self._history)

    def _check_done(self):
        if self._cmd and self._cmd.is_done:
            self._cmd = None
            self._selecting = False
            self._hover_entity = None
            self._reset_dyn_state()
            self._emit_state()
            self.update()

    def _reset_dyn_state(self):
        self._dyn_active_field = 0
        self._dyn_field_mode = None
        self._dyn_field_vals = ["", ""]
        self._dyn_menu_active = False
        self._dyn_menu_index = 0
        self._dyn_menu_rects = []

    # ══════════════════════════════════════════════════════════════════════════
    #  PARSEO Y COMANDOS
    # ══════════════════════════════════════════════════════════════════════════
    def _parse_idle_command(self, text: str):
        input_key = text.strip().upper()
        cmd_key = self.command_aliases.get(input_key, input_key)
        cls = COMMAND_MAP.get(cmd_key)
        if cls:
            self._cmd = cls(self.doc, self._log)
            self._log(f"Comando: {cmd_key}")
            self._check_done()
        else:
            self._log(f"Comando desconocido: '{text}'")

    def run_command(self, cmd_key: str):
        if self._cmd:
            self._cmd.on_escape()
            self._cmd = None
        self._buffer = ""
        self._selecting = False
        self._reset_dyn_state()
        self._parse_idle_command(cmd_key)
        self.setFocus()
        self.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  EVENTOS
    # ══════════════════════════════════════════════════════════════════════════
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()

        if key == Qt.Key_Escape:
            if self._cmd:
                self._cmd.on_escape()
                self._check_done()
            else:
                self.doc.clear_selection()
            self._buffer = ""
            self._dyn_field_vals = ["", ""]
            self._dyn_active_field = 0
            self._dyn_menu_active = False
            self._selecting = False
            self._emit_state()
            self.update()
            return
            
        if self._cmd and "[" in self._cmd.prompt:
            if key == Qt.Key_Down:
                if not self._dyn_menu_active:
                    self._dyn_menu_active = True
                    self._dyn_menu_index = 0
                else:
                    options = self._extract_dyn_options()
                    if options:
                        self._dyn_menu_index = (self._dyn_menu_index + 1) % len(options)
                self.update()
                return
            elif key == Qt.Key_Up and self._dyn_menu_active:
                options = self._extract_dyn_options()
                if options:
                    self._dyn_menu_index = (self._dyn_menu_index - 1) % len(options)
                self.update()
                return

        if key == Qt.Key_Z and (mods & Qt.ControlModifier):
            if self._cmd:
                self._cmd.on_escape()
                self._cmd = None
            self.doc.pop_undo()
            self._emit_state()
            self.update()
            return

        if key == Qt.Key_Delete:
            if self.doc.has_selection:
                self.doc.push_undo()
                self.doc.remove_selected()
                self._emit_state()
                self.update()
            return

        if key == Qt.Key_F8:
            self._ortho_enabled = not self._ortho_enabled
            self._emit_state()
            self.update()
            return

        if key == Qt.Key_Backspace:
            if self._dyn_field_mode in ("xy", "dist_angle") and self._dyn_field_vals[self._dyn_active_field]:
                self._dyn_field_vals[self._dyn_active_field] = self._dyn_field_vals[self._dyn_active_field][:-1]
                self._sync_buffer_from_fields()
            elif self._dyn_field_mode == "single" and self._dyn_field_vals[0]:
                self._dyn_field_vals[0] = self._dyn_field_vals[0][:-1]
                self._buffer = self._dyn_field_vals[0]
            else:
                self._buffer = self._buffer[:-1]
            self._emit_state()
            self.update()
            return

        if key == Qt.Key_Tab:
            self._dyn_active_field = 1 - self._dyn_active_field
            if self._dyn_field_mode in ("xy", "dist_angle"):
                self._sync_buffer_from_fields()
            self.update()
            return

        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self._dyn_menu_active:
                options = self._extract_dyn_options()
                if options and 0 <= self._dyn_menu_index < len(options):
                    self._buffer = options[self._dyn_menu_index]
                self._dyn_menu_active = False
            elif self._cmd:
                if self._dyn_field_mode in ("xy", "dist_angle", "single"):
                    self._sync_buffer_from_fields()
                self._cmd.on_enter(self._buffer)
                if self._buffer.strip() and not self._cmd.is_done:
                    self._sync_cursor_to_typed_coord()
                self._check_done()
                self._buffer = ""
                self._dyn_field_vals = ["", ""]
                self._dyn_active_field = 0
                self._dyn_menu_active = False
                self._emit_state()
                self.update()
                return
            else:
                if self._buffer.strip():
                    self._parse_idle_command(self._buffer)
            self._buffer = ""
            self._dyn_field_vals = ["", ""]
            self._dyn_active_field = 0
            self._dyn_menu_active = False
            self._emit_state()
            self.update()
            return

        ch = event.text()
        if ch and ch.isprintable():
            mode = self._get_dyn_field_mode()
            if mode in ("xy", "dist_angle"):
                # Si el usuario tipea el separador manualmente, cambia de campo (como Tab)
                sep = self._get_dyn_separator()
                if ch == sep:
                    self._dyn_active_field = 1 - self._dyn_active_field
                    self._sync_buffer_from_fields()
                else:
                    self._dyn_field_vals[self._dyn_active_field] += ch
                    self._sync_buffer_from_fields()
            elif mode == "single":
                if ch.isdigit() or ch in (".", "-"):
                    self._dyn_field_vals[0] += ch
                    self._buffer = self._dyn_field_vals[0]
                else:
                    self._buffer += ch
            else:
                self._buffer += ch
            self._emit_state()
            self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position()
        sx, sy = pos.x(), pos.y()

        if self._panning:
            pp = pos.toPoint()
            dx, dy = pp.x() - self._pan_start.x(), pp.y() - self._pan_start.y()
            self.cam_x += dx
            self.cam_y -= dy
            self._pan_start = pp
            self.update()
            return

        # OSNAP
        snap_res = self._compute_snap(sx, sy)
        self._snap_point = snap_res[0]
        self._snap_type  = snap_res[1]
        
        if self._snap_point:
            wx, wy = self._snap_point.x(), self._snap_point.y()
            sx, sy = self.world_to_screen(wx, wy)
        else:
            wx, wy = self.screen_to_world(sx, sy)

        # ORTHO: positional constraint during point specification (ref_pt exists)
        self._ortho_world = None
        self._ortho_screen = None
        if self._ortho_enabled and self._cmd:
            ref = self._get_ortho_ref()
            if ref:
                constrained = self.constrain_ortho(QPointF(wx, wy), ref)
                # Apply positional constraint - move cursor to ortho-aligned position
                wx, wy = constrained.x(), constrained.y()
                sx, sy = self.world_to_screen(wx, wy)
                # Recompute snap for constrained point
                snap_res = self._compute_snap(sx, sy)
                self._snap_point = snap_res[0]
                self._snap_type  = snap_res[1]

        self._mouse_screen = QPointF(sx, sy)
        self._mouse_world  = QPointF(wx, wy)

        # Hover entity (rollover highlight)
        self._hover_entity = self._find_entity_at(pos) if not self._selecting else None

        if self._selecting:
            self._sel_end_screen = pos

        if self._cmd:
            self._cmd.on_mouse_move(self._mouse_world)
            self._dyn_field_mode = self._get_dyn_field_mode()
            self._emit_state()
        else:
            self._dyn_field_mode = None

        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        pos = event.position()

        if event.button() == Qt.MiddleButton:
            self._panning   = True
            self._pan_start = pos.toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            return

        # Click on dropdown menu item
        if event.button() == Qt.LeftButton and self._dyn_menu_active:
            for rect, opt in self._dyn_menu_rects:
                if rect.contains(pos):
                    self._buffer = opt
                    self._dyn_menu_active = False
                    if self._cmd:
                        self._cmd.on_enter(self._buffer)
                        self._check_done()
                    self._buffer = ""
                    self._dyn_field_vals = ["", ""]
                    self._dyn_active_field = 0
                    self._emit_state()
                    self.update()
                    return

        if event.button() == Qt.RightButton:
            if self._cmd:
                self._cmd.on_right_click(self._mouse_world)
                self._check_done()
                self._emit_state()
                self.update()
            else:
                self._parse_idle_command("") # simulates "Enter" to repeat last cmd
            return

        if event.button() == Qt.LeftButton:
            # Use snap point if active, otherwise mouse world position
            pt = self._snap_point if self._snap_point is not None else self._mouse_world
            if self._cmd:
                cmd_in_select = (getattr(self._cmd, '_phase', "") == "SELECT")
                if cmd_in_select:
                    entity = self._find_entity_at(pos)
                    if entity: self.doc.toggle_select(entity)
                    else:
                        self._sel_start_screen = pos
                        self._sel_end_screen   = pos
                        self._selecting        = True
                else:
                    self._cmd.on_left_click(pt)
                    self._check_done()
            else:
                entity = self._find_entity_at(pos)
                if entity:
                    self.doc.toggle_select(entity)
                else:
                    self.doc.clear_selection()
                    self._sel_start_screen = pos
                    self._sel_end_screen   = pos
                    self._selecting        = True

            self._emit_state()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MiddleButton:
            self._panning = False
            self.setCursor(Qt.BlankCursor)
            return

        if event.button() == Qt.LeftButton and self._selecting:
            self._selecting       = False
            self._sel_end_screen  = event.position()

            entities = self._entities_in_window(self._sel_start_screen, self._sel_end_screen)
            for e in entities:
                self.doc.add_to_selection(e)

            self._emit_state()
            self.update()

    def wheelEvent(self, event: QWheelEvent):
        sx, sy = event.position().x(), event.position().y()
        wx, wy = self.screen_to_world(sx, sy)
        factor = 1.15 if event.angleDelta().y() > 0 else 0.85
        self.zoom  = self.zoom * factor
        if self.zoom == 0.0: self.zoom = 0.0000001
        self.cam_x = sx - wx * self.zoom
        self.cam_y = self.height() - sy - wy * self.zoom
        self.update()

    # ══════════════════════════════════════════════════════════════════════════
    #  RENDER (PAINT)
    # ══════════════════════════════════════════════════════════════════════════
    def paintEvent(self, _event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        try:
            # 1. Background
            painter.fillRect(self.rect(), self._C_BG)
    
            # UCS Icon — ejes infinitos estilo AutoCAD 2026
            ox, oy = self.world_to_screen(0, 0)
            # Eje X (rojo) — línea horizontal a lo ancho de la pantalla en Y=0
            painter.setPen(QPen(QColor(255, 0, 0, 80), 1, Qt.SolidLine))
            painter.drawLine(QPointF(0, oy), QPointF(self.width(), oy))
            # Eje Y (verde) — línea vertical a lo alto de la pantalla en X=0
            painter.setPen(QPen(QColor(0, 255, 0, 80), 1, Qt.SolidLine))
            painter.drawLine(QPointF(ox, 0), QPointF(ox, self.height()))
            # Flecha +X
            painter.setPen(QPen(QColor(255, 0, 0, 200), 2))
            painter.drawLine(QPointF(ox, oy), QPointF(ox + 40, oy))
            painter.drawLine(QPointF(ox + 40, oy), QPointF(ox + 30, oy - 5))
            painter.drawLine(QPointF(ox + 40, oy), QPointF(ox + 30, oy + 5))
            # Flecha +Y
            painter.setPen(QPen(QColor(0, 255, 0, 200), 2))
            painter.drawLine(QPointF(ox, oy), QPointF(ox, oy - 40))
            painter.drawLine(QPointF(ox, oy - 40), QPointF(ox - 5, oy - 30))
            painter.drawLine(QPointF(ox, oy - 40), QPointF(ox + 5, oy - 30))
            # Letras X y Y
            font = QFont("Segoe UI", 9, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QColor(255, 80, 80, 220))
            painter.drawText(int(ox + 42), int(oy + 4), "X")
            painter.setPen(QColor(80, 255, 80, 220))
            painter.drawText(int(ox - 14), int(oy - 42), "Y")
            # Cuadrado en el origen
            painter.setPen(QPen(QColor(255, 255, 255, 180), 1))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(QRectF(ox - 3, oy - 3, 6, 6))

            # 2. Entidades
            show_grips = True
            for entity in self.doc.entities:
                entity.draw(painter, self, show_grips=show_grips)

            # 2b. Hover highlight (rollover)
            if self._hover_entity and not self._hover_entity.selected:
                self._draw_hover_highlight(painter, self._hover_entity)

            # 3. Preview de comando (Rubber-band)
            if self._cmd:
                self._cmd.draw_preview(painter, self)
    
            # 4. Ventana de Selección
            if self._selecting:
                self._draw_selection_box(painter)
    
            # 5. Marcador OSNAP Magnético
            if self._snap_point:
                self._draw_osnap_marker(painter)

            # 6. Crosshairs y Pickbox (Lógica Estricta)
            self._draw_autocad_cursor(painter)

            # 6b. Cursor glyph for active command
            self._draw_cursor_glyph(painter)

            # 7. Dynamic Input
            self._draw_dynamic_tooltip(painter)
            
            # 8. Coordinate Bar
            self._draw_coord_bar(painter)
            
        except Exception as e:
            import traceback
            with open("crash_log.txt", "w") as f:
                traceback.print_exc(file=f)
        finally:
            # 9. Clean up
            painter.end()

    # ── Dynamic Input Field Helpers ──────────────────────────────────────────

    def _get_dyn_field_mode(self):
        """Determina el tipo de tooltip Dynamic Input a mostrar según la fase del comando.
        Retorna: 'xy', 'dist_angle', 'single', 'prompt_only', 'frozen', o None.
        """
        if not self._cmd:
            return None
        phase = getattr(self._cmd, '_phase', '')

        # Decision mode: no input fields, solo prompt
        if phase == "ERASE_YN":
            return "frozen"

        # Object selection phases: solo prompt
        if phase in ("SELECT", "TARGET", "WAIT_FIRST", "WAIT_SECOND"):
            return "prompt_only"

        # Single numeric/text value expected
        if phase in ("WAIT_RADIUS", "WAIT_DIAMETER", "WAIT_SIDES", "DRAG", "WAIT_INSCRIBED"):
            return "single"

        # Point specification: check for reference point
        ref = self._get_cmd_last_point()
        if ref is not None:
            return "dist_angle"

        # First point specification
        return "xy"

    def _get_dyn_separator(self):
        """Deriva el separador desde el modo de campo."""
        if self._dyn_field_mode == "dist_angle":
            return "<"
        elif self._dyn_field_mode == "xy":
            return ","
        return ""

    def _sync_buffer_from_fields(self):
        """Reconstruye _buffer desde _dyn_field_vals."""
        v0, v1 = self._dyn_field_vals
        if not v0 and not v1:
            self._buffer = ""
            return
        sep = self._get_dyn_separator()
        if sep and self._dyn_field_mode in ("xy", "dist_angle"):
            # Si solo hay un valor, no agregar separador (permite entrada de distancia simple)
            if v0 and v1:
                self._buffer = f"{v0}{sep}{v1}"
            elif v0:
                self._buffer = v0
            else:
                self._buffer = f"{sep}{v1}"
        elif self._dyn_field_mode == "single":
            self._buffer = v0 if v0 else ""
        else:
            self._buffer = v0 if v0 else ""

    # ── Helpers de cursor virtual (coordenadas tecleadas) ─────────────────────

    def _get_cmd_last_point(self):
        """Obtiene el último punto de referencia del comando activo, si existe."""
        if not self._cmd:
            return None
        if hasattr(self._cmd, '_points') and self._cmd._points:
            return self._cmd._points[-1]
        if hasattr(self._cmd, '_start_points') and self._cmd._start_points:
            return self._cmd._start_points[-1]
        if hasattr(self._cmd, '_p2') and self._cmd._p2:
            return self._cmd._p2
        if hasattr(self._cmd, '_p1') and self._cmd._p1:
            return self._cmd._p1
        if hasattr(self._cmd, '_center') and self._cmd._center:
            return self._cmd._center
        if hasattr(self._cmd, '_start') and self._cmd._start:
            return self._cmd._start
        if hasattr(self._cmd, '_base') and self._cmd._base:
            return self._cmd._base
        return None

    def _sync_cursor_to_typed_coord(self):
        """Después de teclear una coordenada, mueve el cursor virtual a esa posición (como AutoCAD DYN)."""
        from core.geometry import parse_coord_input as _parse
        text = self._buffer.strip()
        if not text:
            return
        # Intentar coordenada absoluta primero
        pt = _parse(text)
        if pt is None:
            # Intentar con punto de referencia del comando
            ref = self._get_cmd_last_point()
            if ref:
                pt = _parse(text, ref)
        if pt is not None:
            self._mouse_world = pt
            sx, sy = self.world_to_screen(pt.x(), pt.y())
            self._mouse_screen = QPointF(sx, sy)
            # Sincronizar también el _mouse del comando activo para que
            # la vista previa (rubber-band) se dibuje desde el punto tecleado
            if self._cmd and hasattr(self._cmd, '_mouse'):
                self._cmd._mouse = pt

    # ── Helpers Visuales ───────────────────────────────────────────────────────

    def _draw_osnap_marker(self, painter: QPainter):
        ssx, ssy = self.world_to_screen(self._snap_point.x(), self._snap_point.y())
        painter.setPen(QPen(self._C_SNAP, 2, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        
        if self._snap_type == "ENDPOINT":
            painter.drawRect(QRectF(ssx - 5, ssy - 5, 10, 10))
        elif self._snap_type == "MIDPOINT":
            painter.drawPolygon([QPointF(ssx, ssy - 6), QPointF(ssx - 6, ssy + 5), QPointF(ssx + 6, ssy + 5)])
        elif self._snap_type == "CENTER":
            painter.drawEllipse(QPointF(ssx, ssy), 6.0, 6.0)
        elif self._snap_type == "QUADRANT":
            painter.drawPolygon([QPointF(ssx, ssy - 6), QPointF(ssx + 6, ssy), QPointF(ssx, ssy + 6), QPointF(ssx - 6, ssy)])

    def _draw_cursor_glyph(self, painter: QPainter):
        if not self._cmd:
            return
        name = type(self._cmd).__name__
        glyphs = {
            "MoveCommand":      ["MOVER", ((5,-5),(8,-5),(8,5),(5,5),(5,-5))],
            "CopyCommand":      ["COPIAR", ((5,-5),(8,-5),(8,5),(5,5),(5,-5))],
            "RotateCommand":    ["ROTAR", None],
            "ScaleCommand":     ["ESCALA", None],
            "TrimCommand":      ["RECORTAR", None],
            "FilletCommand":    ["EMPALME", None],
            "MirrorCommand":    ["ESPEJO", None],
            "EraseCommand":     ["BORRAR", None],
            "StretchCommand":   ["ESTIRAR", None],
            "ArrayCommand":     ["ARRAY", None],
        }
        entry = glyphs.get(name)
        if entry is None:
            return
        label = entry[0]
        x, y = self._mouse_screen.x(), self._mouse_screen.y()
        font = QFont("Segoe UI", 7, QFont.Bold)
        painter.setFont(font)
        fm = painter.fontMetrics()
        tw = fm.horizontalAdvance(label)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 180))
        painter.drawRoundedRect(QRectF(x + 12, y - 10, tw + 8, fm.height() + 4), 3, 3)
        painter.setPen(QColor("#FFFFFF"))
        painter.drawText(int(x + 16), int(y - 10 + 2 + fm.ascent()), label)

    def _draw_autocad_cursor(self, painter: QPainter):
        """Cursor AutoCAD 2026 — cruces finitas, pickbox siempre visible, opaco."""
        if self._panning:
            return

        x, y = self._mouse_screen.x(), self._mouse_screen.y()

        pickbox_w = 4
        gap = 3
        crosshair_size = max(15, int(min(self.width(), self.height()) * 0.05))

        pen = QPen(QColor(255, 255, 255), 1, Qt.SolidLine)
        painter.setPen(pen)

        painter.drawLine(QPointF(x - crosshair_size, y), QPointF(x - gap, y))
        painter.drawLine(QPointF(x + gap, y), QPointF(x + crosshair_size, y))
        painter.drawLine(QPointF(x, y - crosshair_size), QPointF(x, y - gap))
        painter.drawLine(QPointF(x, y + gap), QPointF(x, y + crosshair_size))

        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(x - pickbox_w / 2, y - pickbox_w / 2,
                                pickbox_w, pickbox_w))

        # Decision-mode indicator: small "?" when command expects Yes/No
        if self._cmd:
            phase = getattr(self._cmd, '_phase', '')
            if phase == "ERASE_YN":
                font_q = QFont("Segoe UI", 9, QFont.Bold)
                painter.setFont(font_q)
                painter.setPen(QPen(QColor("#00BFFF"), 1))
                painter.setBrush(QColor("#00BFFF"))
                qx, qy = x + pickbox_w + 4, y - 12
                painter.drawEllipse(QPointF(qx + 6, qy + 2), 9, 9)
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(int(qx), int(qy + 7), "?")

        painter.setFont(QFont("Segoe UI", 9))  # reset

    def _draw_hover_highlight(self, painter, entity):
        from core.entities import (LineEntity, CircleEntity, ArcEntity,
                                   PolylineEntity, RectEntity, EllipseEntity)
        painter.save()
        glow = QColor("#0078D4")
        glow.setAlpha(60)
        pen = QPen(glow, 6, Qt.SolidLine)
        pen.setJoinStyle(Qt.RoundJoin)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        if isinstance(entity, LineEntity):
            sx1, sy1 = self.world_to_screen(entity.x1, entity.y1)
            sx2, sy2 = self.world_to_screen(entity.x2, entity.y2)
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        elif isinstance(entity, CircleEntity):
            sx, sy = self.world_to_screen(entity.cx, entity.cy)
            r = entity.radius * self.zoom
            painter.drawEllipse(QPointF(sx, sy), r, r)
        elif isinstance(entity, ArcEntity):
            segs = 48
            path = QPainterPath()
            first = True
            for i in range(segs + 1):
                a = math.radians(entity.start_angle + entity.span_angle * i / segs)
                wx = entity.cx + entity.radius * math.cos(a)
                wy = entity.cy + entity.radius * math.sin(a)
                sx, sy = self.world_to_screen(wx, wy)
                if first:
                    path.moveTo(sx, sy)
                    first = False
                else:
                    path.lineTo(sx, sy)
            painter.drawPath(path)
        elif isinstance(entity, RectEntity):
            sx1, sy1 = self.world_to_screen(entity.x1, entity.y1)
            sx2, sy2 = self.world_to_screen(entity.x2, entity.y2)
            painter.drawRect(QRectF(QPointF(sx1, sy1), QPointF(sx2, sy2)))
        elif isinstance(entity, PolylineEntity):
            path = QPainterPath()
            first = True
            for (wx, wy) in entity.points:
                sx, sy = self.world_to_screen(wx, wy)
                if first:
                    path.moveTo(sx, sy)
                    first = False
                else:
                    path.lineTo(sx, sy)
            if entity.closed and len(entity.points) > 2:
                x1, y1 = self.world_to_screen(entity.points[-1][0], entity.points[-1][1])
                x2, y2 = self.world_to_screen(entity.points[0][0], entity.points[0][1])
                painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))
            painter.drawPath(path)
        elif isinstance(entity, EllipseEntity):
            r_major = math.hypot(entity.major_x, entity.major_y)
            r_minor = r_major * entity.ratio
            angle_deg = math.degrees(math.atan2(entity.major_y, entity.major_x))
            scx, scy = self.world_to_screen(entity.cx, entity.cy)
            painter.save()
            painter.translate(scx, scy)
            painter.rotate(-angle_deg)
            painter.drawEllipse(QPointF(0, 0), r_major * self.zoom, r_minor * self.zoom)
            painter.restore()
        painter.restore()

    def _draw_selection_box(self, painter: QPainter):
        rect = QRectF(self._sel_start_screen, self._sel_end_screen).normalized()
        if self._sel_end_screen.x() >= self._sel_start_screen.x():
            painter.setPen(QPen(self._C_SEL_W_BD, 1, Qt.SolidLine))
            painter.setBrush(self._C_SEL_W_BG)
        else:
            painter.setPen(QPen(self._C_SEL_C_BD, 1, Qt.DashLine))
            painter.setBrush(self._C_SEL_C_BG)
        painter.drawRect(rect)

    def _extract_dyn_options(self):
        if self._cmd and self._cmd.prompt and "[" in self._cmd.prompt:
            p = self._cmd.prompt
            idx1 = p.find("[")
            idx2 = p.find("]")
            if idx2 > idx1:
                return [o.strip() for o in p[idx1+1:idx2].split("/")]
        return []

    def _draw_dyn_options_menu(self, painter: QPainter, rx: float, top_y: float, item_h: float):
        """Draw the options dropdown menu below the tooltip."""
        options = self._extract_dyn_options()
        if not options or not self._dyn_menu_active:
            return
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        fm = painter.fontMetrics()
        pad = 6

        # Compute menu dimensions
        max_w = max(fm.horizontalAdvance(o) for o in options) + pad * 2
        menu_x = rx
        menu_y = top_y + item_h + 4
        total_h = len(options) * (fm.height() + 6) + 4

        # Clamp to screen
        if menu_x + max_w > self.width():
            menu_x = self.width() - max_w - 10
        if menu_y + total_h > self.height():
            menu_y = top_y - total_h - 8

        # Background
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.setBrush(QColor(35, 35, 35, 235))
        painter.drawRect(QRectF(menu_x, menu_y, max_w, total_h))

        # Items
        self._dyn_menu_rects = []
        for i, opt in enumerate(options):
            iy = menu_y + 2 + i * (fm.height() + 6)
            item_rect = QRectF(menu_x + 2, iy, max_w - 4, fm.height() + 6)

            if i == self._dyn_menu_index:
                painter.fillRect(item_rect, QColor("#0078D4"))
            else:
                pass  # transparent background

            painter.setPen(QColor("#FFFFFF"))
            painter.drawText(int(menu_x + pad), int(iy + 3 + fm.ascent()), opt)

            self._dyn_menu_rects.append((item_rect, opt))

    def _draw_dynamic_tooltip(self, painter: QPainter):
        x, y = self._mouse_screen.x(), self._mouse_screen.y()
        mode = self._get_dyn_field_mode()
        if mode is None:
            return

        ref_pt = self._get_cmd_last_point()
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        fm = painter.fontMetrics()
        pad_x, pad_y = 8, 5

        # ── Build field display values ──────────────────────────────────────
        val1 = ""
        val2_str = None
        sep_display = ""
        field_mode = mode

        if mode == "frozen":
            # Only show prompt text, no input fields
            pass
        elif mode == "prompt_only":
            # Only show prompt text, no input fields
            pass
        elif mode == "single":
            # Single numeric field
            preview_val = None
            if self._dyn_field_vals[0]:
                val1 = self._dyn_field_vals[0]
            elif ref_pt:
                dx = self._mouse_world.x() - ref_pt.x()
                dy = self._mouse_world.y() - ref_pt.y()
                phase = getattr(self._cmd, '_phase', '')
                if phase == "WAIT_RADIUS":
                    preview_val = f"{math.hypot(dx, dy):.2f}"
                elif phase == "DRAG":
                    # Angle for rotate, distance for scale
                    cmd_name = type(self._cmd).__name__
                    if cmd_name == "RotateCommand":
                        deg = math.degrees(math.atan2(dy, dx)) % 360
                        preview_val = f"{deg:.1f}°"
                    else:
                        preview_val = f"{math.hypot(dx, dy):.2f}×"
                else:
                    preview_val = f"{math.hypot(dx, dy):.2f}"
                if preview_val:
                    val1 = preview_val
        elif mode in ("xy", "dist_angle"):
            # Two-field mode: X/Y or distance/angle
            v0 = self._dyn_field_vals[0]
            v1 = self._dyn_field_vals[1]

            if v0 or v1:
                val1 = v0 if v0 else "0"
                val2_str = v1 if v1 else ""
                sep_display = self._get_dyn_separator()
            elif ref_pt:
                dx = self._mouse_world.x() - ref_pt.x()
                dy = self._mouse_world.y() - ref_pt.y()
                if mode == "xy":
                    # Show absolute coordinates of cursor (from origin or relative to ref?)
                    # For first point: show cursor world position
                    val1 = f"{self._mouse_world.x():.2f}"
                    val2_str = f"{self._mouse_world.y():.2f}"
                    sep_display = ","
                else:
                    # dist_angle mode: distance and angle from reference
                    d = math.hypot(dx, dy)
                    a = math.degrees(math.atan2(dy, dx)) % 360
                    val1 = f"{d:.2f}"
                    val2_str = f"{a:.1f}°"
                    sep_display = "<"
            else:
                # No reference point, show cursor position
                val1 = f"{self._mouse_world.x():.2f}"
                val2_str = f"{self._mouse_world.y():.2f}"
                sep_display = ","

        # ── Compute layout ──────────────────────────────────────────────────
        has_fields = mode not in ("frozen", "prompt_only")

        # Prompt text
        prompt_text = ""
        if self._cmd and self._cmd.prompt:
            pt = self._cmd.prompt
            # Strip bracketed options from display (shown in dropdown instead)
            if "[" in pt and "]" in pt:
                prompt_text = pt[:pt.find("[")].strip()
                if prompt_text.endswith(":") or prompt_text.endswith(">"):
                    prompt_text = pt  # Keep full text if it ends with prompt char
            else:
                prompt_text = pt
        prompt_w = fm.horizontalAdvance(prompt_text) + pad_x * 2 if prompt_text else 0

        # Field sizes
        if has_fields and mode == "single":
            f1_w = fm.horizontalAdvance(val1 + "  ") if val1 else 60
            total_fields_w = f1_w + pad_x * 2
            sep_w = 0
            sep_display = ""
        elif has_fields and mode in ("xy", "dist_angle"):
            f1_w = fm.horizontalAdvance(val1 + "  ") if val1 else 60
            f2_w = fm.horizontalAdvance((val2_str or "  ") + "  ") + pad_x
            sep_w = fm.horizontalAdvance(sep_display) + 4 if sep_display else 0
            total_fields_w = f1_w + sep_w + f2_w + pad_x * 3
        else:
            total_fields_w = 0
            f1_w = 0
            sep_w = 0

        # Triangle indicator
        has_options = self._cmd and self._cmd.prompt and "[" in self._cmd.prompt and "]" in self._cmd.prompt
        tri_w = 10 if has_options else 0

        # Total tooltip width
        content_w = max(prompt_w, total_fields_w + tri_w)
        if content_w < 20:
            return

        # Position near cursor
        rx = x + 15
        ry = y + 20
        # Height: prompt line + fields line + gap
        prompt_h = fm.height() + pad_y * 2 if prompt_text else 0
        fields_h = fm.height() + pad_y * 2 if has_fields else 0
        gap = 4 if (prompt_text and has_fields) else 0
        total_h = prompt_h + gap + fields_h + 4

        # Clamp to screen
        if rx + content_w > self.width() - 10:
            rx = x - content_w - 15
        if ry + total_h > self.height() - 10:
            ry = y - total_h - 20
        if rx < 5:
            rx = 5
        if ry < 5:
            ry = 5

        painter.setRenderHint(QPainter.Antialiasing)

        # ── Draw background ────────────────────────────────────────────────
        bg_rect = QRectF(rx - 2, ry - 2, content_w + 4, total_h + 2)
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.setBrush(QColor(30, 30, 30, 230))
        painter.drawRoundedRect(bg_rect, 4, 4)

        curr_y = ry

        # ── Draw prompt text ────────────────────────────────────────────────
        if prompt_text:
            prompt_rect = QRectF(rx, curr_y, content_w - 4, prompt_h)
            painter.setPen(QColor("#CCCCCC"))
            painter.drawText(int(rx + pad_x), int(curr_y + pad_y + fm.ascent()), prompt_text)
            curr_y += prompt_h + gap

        # ── Draw input fields ───────────────────────────────────────────────
        if has_fields:
            curr_x = rx
            if mode == "single":
                is_active = (self._dyn_active_field == 0)
                fw = max(content_w - tri_w - 8, f1_w)
                rect1 = QRectF(curr_x, curr_y, fw + pad_x, fm.height() + pad_y * 2)
                painter.setPen(QPen(QColor("#0078D4"), 1.5) if is_active else QPen(QColor("#555555"), 1))
                painter.setBrush(QColor(255, 255, 255, 245) if is_active else QColor(255, 255, 255, 160))
                painter.drawRect(rect1)
                painter.setPen(QColor(0, 0, 0))
                if val1:
                    painter.drawText(int(curr_x + pad_x // 2), int(curr_y + pad_y + fm.ascent()), val1)
                curr_x += fw + pad_x

            elif mode in ("xy", "dist_angle"):
                # Field 1
                is_active_1 = (self._dyn_active_field == 0)
                fw1 = max(60, f1_w)
                rect1 = QRectF(curr_x, curr_y, fw1, fm.height() + pad_y * 2)
                painter.setPen(QPen(QColor("#0078D4"), 1.5) if is_active_1 else QPen(QColor("#555555"), 1))
                painter.setBrush(QColor(255, 255, 255, 245) if is_active_1 else QColor(255, 255, 255, 160))
                painter.drawRect(rect1)
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(int(curr_x + 3), int(curr_y + pad_y + fm.ascent()), val1)
                curr_x += fw1

                # Separator label ("," or "<")
                if sep_display:
                    x_sep = curr_x + 2
                    painter.setPen(QColor("#AAAAAA"))
                    painter.drawText(int(x_sep), int(curr_y + pad_y + fm.ascent()), sep_display)
                    curr_x += sep_w - 4

                # Field 2
                is_active_2 = (self._dyn_active_field == 1)
                fw2 = max(60, f2_w)
                rect2 = QRectF(curr_x, curr_y, fw2, fm.height() + pad_y * 2)
                painter.setPen(QPen(QColor("#0078D4"), 1.5) if is_active_2 else QPen(QColor("#555555"), 1))
                painter.setBrush(QColor(255, 255, 255, 245) if is_active_2 else QColor(255, 255, 255, 160))
                painter.drawRect(rect2)
                painter.setPen(QColor(0, 0, 0))
                if val2_str is not None:
                    painter.drawText(int(curr_x + 3), int(curr_y + pad_y + fm.ascent()), val2_str)
                curr_x += fw2

            # ── Options triangle indicator ──────────────────────────────────
            if has_options and not self._dyn_menu_active:
                tri_base_x = curr_x + 4
                tri_mid_y = curr_y + (fm.height() + pad_y * 2) // 2
                painter.setPen(QPen(QColor("#00BFFF"), 2))
                painter.drawLine(QPointF(tri_base_x, curr_y + 4),
                                 QPointF(tri_base_x + 5, tri_mid_y))
                painter.drawLine(QPointF(tri_base_x + 5, tri_mid_y),
                                 QPointF(tri_base_x, curr_y + fm.height() + pad_y * 2 - 4))

            # ── Options dropdown menu ───────────────────────────────────────
            if self._dyn_menu_active:
                self._draw_dyn_options_menu(painter, rx, curr_y, fm.height() + pad_y * 2)

    def _draw_coord_bar(self, painter: QPainter):
        wx, wy   = self._mouse_world.x(), self._mouse_world.y()
        zp       = self.zoom * 100.0
        n_e, n_s = len(self.doc.entities), len(self.doc.selected)
        state_s  = getattr(self._cmd, '_phase', "IDLE")

        top  = f"X: {wx:>10.3f}    Y: {wy:>10.3f}    Zoom: {zp:.0f}%"
        bot  = f"Entidades: {n_e}    Sel: {n_s}    [{state_s}]"
        if self._ortho_enabled:
            bot += "    ORTO: ON"

        font = QFont("Consolas", 9)
        painter.setFont(font)
        fm   = painter.fontMetrics()
        mw   = max(fm.horizontalAdvance(top), fm.horizontalAdvance(bot))
        pad  = 8
        rw   = mw + pad * 2
        rh   = fm.height() * 2 + pad * 2
        rx   = self.width() - rw - 10
        ry   = 10

        painter.setPen(QPen(QColor("#3C3C3C"), 1))
        painter.setBrush(QColor(22, 24, 28, 200))
        painter.drawRect(QRectF(rx, ry, rw, rh))
        painter.setPen(QColor("#00D4FF"))
        painter.drawText(int(rx + pad), int(ry + pad + fm.ascent()), top)
        painter.setPen(QColor("#8A8A8A"))
        painter.drawText(int(rx + pad), int(ry + pad + fm.height() + fm.ascent()), bot)
