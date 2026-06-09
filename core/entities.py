# -*- coding: utf-8 -*-
"""
core/entities.py — Clases de entidades CAD en Espacio Mundo (Y-Up).
Sin dependencias de estado de UI. Solo geometría y renderizado.
"""
import math
from abc import ABC, abstractmethod

from PySide6.QtCore  import Qt, QPointF, QRectF
from PySide6.QtGui   import QPainter, QPen, QColor, QBrush

from core.geometry import rotate_point, scale_point


# ──────────────────────────────────────────────────────────────────────────────
#  Helpers de renderizado compartidos
# ──────────────────────────────────────────────────────────────────────────────

SEL_COLOR = "#0078D4"  # AutoCAD 2026 selection highlight blue (vivid)

def _draw_grips(painter: QPainter, screen_pts: list):
    """Dibuja grips sólidos azul #0078D4 con contorno blanco en cada punto."""
    painter.setPen(QPen(QColor("#FFFFFF"), 1))
    painter.setBrush(QBrush(QColor("#0078D4")))
    for sx, sy in screen_pts:
        painter.drawRect(QRectF(sx - 4.0, sy - 4.0, 8.0, 8.0))


def _ghost_pen() -> QPen:
    return QPen(QColor("#00FFFF"), 1, Qt.DashLine)


# ══════════════════════════════════════════════════════════════════════════════
#  Clase Abstracta Base
# ══════════════════════════════════════════════════════════════════════════════

class Entity(ABC):
    """Entidad geométrica base. Vive en Espacio Mundo (Y-Up, floats)."""

    def __init__(self, color: str = "#FFFFFF", layer: str = "0"):
        self.color    = color
        self.layer    = layer
        self.selected = False

    # ── Transformaciones in-place ──────────────────────────────────────────────
    @abstractmethod
    def move(self, dx: float, dy: float): ...

    @abstractmethod
    def rotate(self, bx: float, by: float, angle_rad: float): ...

    @abstractmethod
    def scale(self, bx: float, by: float, factor: float): ...

    # ── Consultas ─────────────────────────────────────────────────────────────
    @abstractmethod
    def get_snap_points(self) -> list:
        """Retorna [[wx, wy], ...] de puntos clave para OSNAP."""
        ...

    def get_vertices(self) -> list:
        """
        Alias canónico de get_snap_points().
        Retorna [[wx, wy], ...] de los vértices definidores de la entidad.
        Usado por el ghost-drawing y por la evaluación de ventanas de selección.
        """
        return self.get_snap_points()

    @abstractmethod
    def copy_at_offset(self, dx: float, dy: float) -> "Entity":
        """Crea una copia desplazada sin modificar self."""
        ...

    # ── Renderizado ───────────────────────────────────────────────────────────
    @abstractmethod
    def draw(self, painter: QPainter, viewport, show_grips: bool = True): ...

    @abstractmethod
    def draw_ghost_offset(self, p: QPainter, v, dx: float, dy: float): ...

    @abstractmethod
    def draw_ghost_rotated(self, p: QPainter, v,
                           bx: float, by: float, angle_rad: float): ...

    @abstractmethod
    def draw_ghost_scaled(self, p: QPainter, v,
                          bx: float, by: float, factor: float): ...


# ══════════════════════════════════════════════════════════════════════════════
#  LineEntity
# ══════════════════════════════════════════════════════════════════════════════

class LineEntity(Entity):
    """Segmento de recta definido por dos vértices en Espacio Mundo."""

    def __init__(self, x1: float, y1: float,
                 x2: float, y2: float, **kw):
        super().__init__(**kw)
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    # ── Transforms ────────────────────────────────────────────────────────────
    def move(self, dx, dy):
        self.x1 += dx; self.y1 += dy
        self.x2 += dx; self.y2 += dy

    def rotate(self, bx, by, angle_rad):
        self.x1, self.y1 = rotate_point(self.x1, self.y1, bx, by, angle_rad)
        self.x2, self.y2 = rotate_point(self.x2, self.y2, bx, by, angle_rad)

    def scale(self, bx, by, factor):
        self.x1, self.y1 = scale_point(self.x1, self.y1, bx, by, factor)
        self.x2, self.y2 = scale_point(self.x2, self.y2, bx, by, factor)

    def copy_at_offset(self, dx, dy):
        return LineEntity(self.x1 + dx, self.y1 + dy,
                          self.x2 + dx, self.y2 + dy,
                          color=self.color, layer=self.layer)

    def get_snap_points(self):
        mx, my = (self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0
        return [[self.x1, self.y1], [self.x2, self.y2], [mx, my]]

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        sx1, sy1 = viewport.world_to_screen(self.x1, self.y1)
        sx2, sy2 = viewport.world_to_screen(self.x2, self.y2)
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        if self.selected and show_grips:
            _draw_grips(painter, [(sx1, sy1), (sx2, sy2)])

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        sx1, sy1 = viewport.world_to_screen(self.x1 + dx, self.y1 + dy)
        sx2, sy2 = viewport.world_to_screen(self.x2 + dx, self.y2 + dy)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_rotated(self, painter: QPainter, viewport,
                           bx: float, by: float, angle_rad: float):
        rx1, ry1 = rotate_point(self.x1, self.y1, bx, by, angle_rad)
        rx2, ry2 = rotate_point(self.x2, self.y2, bx, by, angle_rad)
        sx1, sy1 = viewport.world_to_screen(rx1, ry1)
        sx2, sy2 = viewport.world_to_screen(rx2, ry2)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_scaled(self, painter: QPainter, viewport,
                          bx: float, by: float, factor: float):
        nx1, ny1 = scale_point(self.x1, self.y1, bx, by, factor)
        nx2, ny2 = scale_point(self.x2, self.y2, bx, by, factor)
        sx1, sy1 = viewport.world_to_screen(nx1, ny1)
        sx2, sy2 = viewport.world_to_screen(nx2, ny2)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))


# ══════════════════════════════════════════════════════════════════════════════
#  PolylineEntity
# ══════════════════════════════════════════════════════════════════════════════
class PolylineEntity(Entity):
    def __init__(self, points: list[tuple[float, float]], closed: bool = False, color: str = "#FFFFFF", layer: str = "0"):
        super().__init__(color, layer)
        self.points = list(points)
        self.closed = closed

    # ── Transformaciones ──────────────────────────────────────────────────────
    def move(self, dx: float, dy: float):
        self.points = [(x + dx, y + dy) for x, y in self.points]

    def rotate(self, bx: float, by: float, angle_rad: float):
        self.points = [rotate_point(x, y, bx, by, angle_rad) for x, y in self.points]

    def scale(self, bx: float, by: float, factor: float):
        self.points = [scale_point(x, y, bx, by, factor) for x, y in self.points]

    def copy_at_offset(self, dx: float, dy: float) -> "Entity":
        pts = [(x + dx, y + dy) for x, y in self.points]
        return PolylineEntity(pts, closed=self.closed, color=self.color, layer=self.layer)

    # ── Hit Test ──────────────────────────────────────────────────────────────
    def get_snap_points(self) -> list[list[float]]:
        pts = []
        for x, y in self.points:
            pts.append([x, y])
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i+1]
            mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
            pts.append([mx, my])
        if self.closed and len(self.points) > 2:
            p1 = self.points[-1]
            p2 = self.points[0]
            mx, my = (p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0
            pts.append([mx, my])
        return pts

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        if not self.points: return
        pts_screen = [QPointF(*viewport.world_to_screen(x, y)) for x, y in self.points]

        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.drawPolyline(pts_screen)
            if self.closed and len(pts_screen) > 2:
                painter.drawLine(pts_screen[-1], pts_screen[0])

        painter.setPen(QPen(QColor(self.color), 2.0, Qt.SolidLine))
        painter.drawPolyline(pts_screen)
        if self.closed and len(pts_screen) > 2:
            painter.drawLine(pts_screen[-1], pts_screen[0])

        if self.selected and show_grips:
            _draw_grips(painter, [(pt.x(), pt.y()) for pt in pts_screen])

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        if not self.points: return
        pts_screen = [QPointF(*viewport.world_to_screen(x + dx, y + dy)) for x, y in self.points]
        painter.setPen(_ghost_pen())
        painter.drawPolyline(pts_screen)
        if self.closed and len(pts_screen) > 2:
            painter.drawLine(pts_screen[-1], pts_screen[0])

    def draw_ghost_rotated(self, painter: QPainter, viewport, bx: float, by: float, angle_rad: float):
        if not self.points: return
        pts_screen = []
        for x, y in self.points:
            rx, ry = rotate_point(x, y, bx, by, angle_rad)
            pts_screen.append(QPointF(*viewport.world_to_screen(rx, ry)))
        painter.setPen(_ghost_pen())
        painter.drawPolyline(pts_screen)
        if self.closed and len(pts_screen) > 2:
            painter.drawLine(pts_screen[-1], pts_screen[0])

    def draw_ghost_scaled(self, painter: QPainter, viewport, bx: float, by: float, factor: float):
        if not self.points: return
        pts_screen = []
        for x, y in self.points:
            rx, ry = scale_point(x, y, bx, by, factor)
            pts_screen.append(QPointF(*viewport.world_to_screen(rx, ry)))
        painter.setPen(_ghost_pen())
        painter.drawPolyline(pts_screen)
        if self.closed and len(pts_screen) > 2:
            painter.drawLine(pts_screen[-1], pts_screen[0])


# ══════════════════════════════════════════════════════════════════════════════
#  CircleEntity
# ══════════════════════════════════════════════════════════════════════════════

class CircleEntity(Entity):
    """Círculo definido por centro y radio en Espacio Mundo."""

    def __init__(self, cx: float, cy: float, radius: float, **kw):
        super().__init__(**kw)
        self.cx, self.cy = cx, cy
        self.radius = radius

    # ── Transforms ────────────────────────────────────────────────────────────
    def move(self, dx, dy):
        self.cx += dx; self.cy += dy

    def rotate(self, bx, by, angle_rad):
        self.cx, self.cy = rotate_point(self.cx, self.cy, bx, by, angle_rad)

    def scale(self, bx, by, factor):
        if factor <= 0:
            return
        self.cx, self.cy = scale_point(self.cx, self.cy, bx, by, factor)
        self.radius *= factor

    def copy_at_offset(self, dx, dy):
        return CircleEntity(self.cx + dx, self.cy + dy, self.radius,
                            color=self.color, layer=self.layer)

    def get_snap_points(self):
        r = self.radius
        return [
            [self.cx,     self.cy    ],
            [self.cx + r, self.cy    ],
            [self.cx - r, self.cy    ],
            [self.cx,     self.cy + r],
            [self.cx,     self.cy - r],
        ]

    # ── Draw ──────────────────────────────────────────────────────────────────
    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        scx, scy = viewport.world_to_screen(self.cx, self.cy)
        sr = self.radius * viewport.zoom
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(scx, scy), sr, sr)
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(scx, scy), sr, sr)
        if self.selected and show_grips:
            pts = [viewport.world_to_screen(vx, vy)
                   for vx, vy in self.get_snap_points()[1:]]
            _draw_grips(painter, pts)

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        scx, scy = viewport.world_to_screen(self.cx + dx, self.cy + dy)
        sr = self.radius * viewport.zoom
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(scx, scy), sr, sr)

    def draw_ghost_rotated(self, painter: QPainter, viewport,
                           bx: float, by: float, angle_rad: float):
        ncx, ncy = rotate_point(self.cx, self.cy, bx, by, angle_rad)
        scx, scy = viewport.world_to_screen(ncx, ncy)
        sr = self.radius * viewport.zoom
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(scx, scy), sr, sr)

    def draw_ghost_scaled(self, painter: QPainter, viewport,
                          bx: float, by: float, factor: float):
        ncx, ncy = scale_point(self.cx, self.cy, bx, by, factor)
        scx, scy = viewport.world_to_screen(ncx, ncy)
        sr = self.radius * abs(factor) * viewport.zoom
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(scx, scy), sr, sr)

# ══════════════════════════════════════════════════════════════════════════════
#  ArcEntity
# ══════════════════════════════════════════════════════════════════════════════

class ArcEntity(Entity):
    """Arco definido por centro, radio, ángulo de inicio y ángulo de extensión."""
    def __init__(self, cx: float, cy: float, radius: float, start_angle: float, span_angle: float, **kw):
        super().__init__(**kw)
        self.cx, self.cy = cx, cy
        self.radius = radius
        self.start_angle = start_angle # en grados (0 es 3 en punto)
        self.span_angle = span_angle   # en grados (positivo es CCW)

    def move(self, dx, dy):
        self.cx += dx; self.cy += dy

    def rotate(self, bx, by, angle_rad):
        self.cx, self.cy = rotate_point(self.cx, self.cy, bx, by, angle_rad)
        self.start_angle = (self.start_angle + math.degrees(angle_rad)) % 360

    def scale(self, bx, by, factor):
        if factor <= 0: return
        self.cx, self.cy = scale_point(self.cx, self.cy, bx, by, factor)
        self.radius *= factor

    def copy_at_offset(self, dx, dy):
        return ArcEntity(self.cx + dx, self.cy + dy, self.radius, self.start_angle, self.span_angle,
                         color=self.color, layer=self.layer)

    def get_snap_points(self):
        r = self.radius
        sa_rad = math.radians(self.start_angle)
        ea_rad = math.radians(self.start_angle + self.span_angle)
        return [
            [self.cx, self.cy],
            [self.cx + r * math.cos(sa_rad), self.cy + r * math.sin(sa_rad)],
            [self.cx + r * math.cos(ea_rad), self.cy + r * math.sin(ea_rad)]
        ]

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        segments = 64
        pts = []
        sa_rad = math.radians(self.start_angle)
        span_rad = math.radians(self.span_angle)
        for i in range(segments + 1):
            a = sa_rad + span_rad * i / segments
            wx = self.cx + self.radius * math.cos(a)
            wy = self.cy + self.radius * math.sin(a)
            sx, sy = viewport.world_to_screen(wx, wy)
            pts.append(QPointF(sx, sy))

        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawPolyline(pts)

        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(pts)

        if self.selected and show_grips:
            grip_pts = [viewport.world_to_screen(vx, vy) for vx, vy in self.get_snap_points()[1:]]
            _draw_grips(painter, grip_pts)

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        segments = 64
        pts = []
        sa_rad = math.radians(self.start_angle)
        span_rad = math.radians(self.span_angle)
        for i in range(segments + 1):
            a = sa_rad + span_rad * i / segments
            wx = self.cx + dx + self.radius * math.cos(a)
            wy = self.cy + dy + self.radius * math.sin(a)
            sx, sy = viewport.world_to_screen(wx, wy)
            pts.append(QPointF(sx, sy))
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawPolyline(pts)

    def draw_ghost_rotated(self, painter: QPainter, viewport, bx: float, by: float, angle_rad: float):
        pass

    def draw_ghost_scaled(self, painter: QPainter, viewport, bx: float, by: float, factor: float):
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  RectEntity (Polilínea cerrada simple)
# ══════════════════════════════════════════════════════════════════════════════
class RectEntity(Entity):
    def __init__(self, x1: float, y1: float, x2: float, y2: float, **kw):
        super().__init__(**kw)
        self.x1, self.y1 = x1, y1
        self.x2, self.y2 = x2, y2

    def move(self, dx, dy):
        self.x1 += dx; self.y1 += dy
        self.x2 += dx; self.y2 += dy

    def rotate(self, bx, by, angle_rad):
        pass # Por simplicidad

    def scale(self, bx, by, factor):
        self.x1, self.y1 = scale_point(self.x1, self.y1, bx, by, factor)
        self.x2, self.y2 = scale_point(self.x2, self.y2, bx, by, factor)

    def copy_at_offset(self, dx, dy):
        return RectEntity(self.x1 + dx, self.y1 + dy, self.x2 + dx, self.y2 + dy, color=self.color, layer=self.layer)

    def get_snap_points(self):
        return [
            [self.x1, self.y1],
            [self.x2, self.y1],
            [self.x2, self.y2],
            [self.x1, self.y2],
            [(self.x1 + self.x2)/2, (self.y1 + self.y2)/2]
        ]

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        sx1, sy1 = viewport.world_to_screen(self.x1, self.y1)
        sx2, sy2 = viewport.world_to_screen(self.x2, self.y2)
        rect = QRectF(QPointF(sx1, sy1), QPointF(sx2, sy2)).normalized()
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(vx, vy) for vx, vy in self.get_snap_points()[:4]])

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        sx1, sy1 = viewport.world_to_screen(self.x1 + dx, self.y1 + dy)
        sx2, sy2 = viewport.world_to_screen(self.x2 + dx, self.y2 + dy)
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(QRectF(QPointF(sx1, sy1), QPointF(sx2, sy2)).normalized())

    def draw_ghost_rotated(self, painter: QPainter, viewport, bx: float, by: float, angle_rad: float):
        pass

    def draw_ghost_scaled(self, painter: QPainter, viewport, bx: float, by: float, factor: float):
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  EllipseEntity
# ══════════════════════════════════════════════════════════════════════════════
class EllipseEntity(Entity):
    """Elipse definida por su centro, y los vectores de su eje mayor y menor."""
    def __init__(self, cx: float, cy: float, major_x: float, major_y: float, ratio: float, **kw):
        super().__init__(**kw)
        self.cx, self.cy = cx, cy
        self.major_x = major_x # Vector del centro al fin del eje mayor
        self.major_y = major_y
        self.ratio = ratio # radio menor / radio mayor

    def move(self, dx, dy):
        self.cx += dx; self.cy += dy

    def rotate(self, bx, by, angle_rad):
        self.cx, self.cy = rotate_point(self.cx, self.cy, bx, by, angle_rad)
        nx, ny = rotate_point(self.cx + self.major_x, self.cy + self.major_y, self.cx, self.cy, angle_rad)
        self.major_x, self.major_y = nx - self.cx, ny - self.cy

    def scale(self, bx, by, factor):
        self.cx, self.cy = scale_point(self.cx, self.cy, bx, by, factor)
        self.major_x *= factor
        self.major_y *= factor

    def copy_at_offset(self, dx, dy):
        return EllipseEntity(self.cx + dx, self.cy + dy, self.major_x, self.major_y, self.ratio, color=self.color, layer=self.layer)

    def get_snap_points(self):
        r_major = math.hypot(self.major_x, self.major_y)
        if r_major == 0: return [[self.cx, self.cy]]
        
        ux, uy = self.major_x / r_major, self.major_y / r_major
        vx, vy = -uy, ux
        r_minor = r_major * self.ratio
        
        return [
            [self.cx, self.cy],
            [self.cx + self.major_x, self.cy + self.major_y],
            [self.cx - self.major_x, self.cy - self.major_y],
            [self.cx + vx * r_minor, self.cy + vy * r_minor],
            [self.cx - vx * r_minor, self.cy - vy * r_minor]
        ]

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        import math
        from PySide6.QtCore import QPointF, Qt
        from PySide6.QtGui import QColor, QPen
        scx, scy = viewport.world_to_screen(self.cx, self.cy)
        r_major = math.hypot(self.major_x, self.major_y)
        r_minor = r_major * self.ratio
        angle_deg = math.degrees(math.atan2(self.major_y, self.major_x))

        painter.save()
        painter.translate(scx, scy)
        painter.rotate(-angle_deg)

        sm_major = r_major * viewport.zoom
        sm_minor = r_minor * viewport.zoom

        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(QPointF(0, 0), sm_major, sm_minor)

        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), sm_major, sm_minor)
        painter.restore()

        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(vx, vy) for vx, vy in self.get_snap_points()[1:]])

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        scx, scy = viewport.world_to_screen(self.cx + dx, self.cy + dy)
        r_major = math.hypot(self.major_x, self.major_y)
        r_minor = r_major * self.ratio
        angle_deg = math.degrees(math.atan2(self.major_y, self.major_x))
        
        painter.save()
        painter.translate(scx, scy)
        painter.rotate(-angle_deg)
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(0, 0), r_major * viewport.zoom, r_minor * viewport.zoom)
        painter.restore()

    def draw_ghost_rotated(self, painter: QPainter, viewport, bx: float, by: float, angle_rad: float):
        pass

    def draw_ghost_scaled(self, painter: QPainter, viewport, bx: float, by: float, factor: float):
        pass

# ══════════════════════════════════════════════════════════════════════════════
#  PolygonEntity
# ══════════════════════════════════════════════════════════════════════════════
class PolygonEntity(Entity):
    """Polígono regular definido por su centro, radio, número de lados, y si está inscrito o circunscrito."""
    def __init__(self, cx: float, cy: float, radius: float, sides: int, inscribed: bool, rotation: float = 0.0, **kw):
        super().__init__(**kw)
        self.cx, self.cy = cx, cy
        self.radius = radius
        self.sides = sides
        self.inscribed = inscribed
        self.rotation = rotation # radianes

    def move(self, dx, dy):
        self.cx += dx; self.cy += dy

    def rotate(self, bx, by, angle_rad):
        self.cx, self.cy = rotate_point(self.cx, self.cy, bx, by, angle_rad)
        self.rotation += angle_rad

    def scale(self, bx, by, factor):
        self.cx, self.cy = scale_point(self.cx, self.cy, bx, by, factor)
        self.radius *= abs(factor)

    def copy_at_offset(self, dx, dy):
        return PolygonEntity(self.cx + dx, self.cy + dy, self.radius, self.sides, self.inscribed, self.rotation, color=self.color, layer=self.layer)

    def _get_vertices(self):
        pts = []
        if self.inscribed:
            r = self.radius
            start_angle = self.rotation
        else:
            r = self.radius / math.cos(math.pi / self.sides)
            start_angle = self.rotation - (math.pi / self.sides)
            
        for i in range(self.sides):
            a = start_angle + i * (2 * math.pi / self.sides)
            pts.append(QPointF(self.cx + r * math.cos(a), self.cy + r * math.sin(a)))
        return pts

    def get_snap_points(self):
        pts = [[p.x(), p.y()] for p in self._get_vertices()]
        pts.insert(0, [self.cx, self.cy]) # centro
        return pts

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        screen_pts = [QPointF(*viewport.world_to_screen(p.x(), p.y())) for p in self._get_vertices()]
        if not screen_pts:
            return
        from PySide6.QtGui import QPolygonF
        poly = QPolygonF(screen_pts)
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(poly)
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(poly)

        if self.selected and show_grips:
            _draw_grips(painter, [(p.x(), p.y()) for p in screen_pts])

    def draw_ghost_offset(self, painter: QPainter, viewport, dx: float, dy: float):
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        pts = self._get_vertices()
        screen_pts = [QPointF(*viewport.world_to_screen(p.x() + dx, p.y() + dy)) for p in pts]
        from PySide6.QtGui import QPolygonF
        painter.drawPolygon(QPolygonF(screen_pts))

    def draw_ghost_rotated(self, painter: QPainter, viewport, bx: float, by: float, angle_rad: float):
        pass

    def draw_ghost_scaled(self, painter: QPainter, viewport, bx: float, by: float, factor: float):
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  PointEntity
# ══════════════════════════════════════════════════════════════════════════════

class PointEntity(Entity):
    """Single point marker drawn as a small cross (+)."""

    def __init__(self, x: float, y: float, **kw):
        super().__init__(**kw)
        self.x, self.y = x, y

    def move(self, dx, dy):
        self.x += dx; self.y += dy

    def rotate(self, bx, by, angle_rad):
        self.x, self.y = rotate_point(self.x, self.y, bx, by, angle_rad)

    def scale(self, bx, by, factor):
        self.x, self.y = scale_point(self.x, self.y, bx, by, factor)

    def copy_at_offset(self, dx, dy):
        return PointEntity(self.x + dx, self.y + dy, color=self.color, layer=self.layer)

    def get_snap_points(self):
        return [[self.x, self.y]]

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        sx, sy = viewport.world_to_screen(self.x, self.y)
        size = 5
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 2, Qt.SolidLine))
            painter.drawLine(QPointF(sx - size, sy), QPointF(sx + size, sy))
            painter.drawLine(QPointF(sx, sy - size), QPointF(sx, sy + size))
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.drawLine(QPointF(sx - size, sy), QPointF(sx + size, sy))
        painter.drawLine(QPointF(sx, sy - size), QPointF(sx, sy + size))
        if self.selected and show_grips:
            _draw_grips(painter, [(sx, sy)])

    def draw_ghost_offset(self, painter, viewport, dx, dy):
        sx, sy = viewport.world_to_screen(self.x + dx, self.y + dy)
        size = 5
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx - size, sy), QPointF(sx + size, sy))
        painter.drawLine(QPointF(sx, sy - size), QPointF(sx, sy + size))

    def draw_ghost_rotated(self, painter, viewport, bx, by, angle_rad):
        rx, ry = rotate_point(self.x, self.y, bx, by, angle_rad)
        self.draw_ghost_offset(painter, viewport, rx - self.x, ry - self.y)

    def draw_ghost_scaled(self, painter, viewport, bx, by, factor):
        nx, ny = scale_point(self.x, self.y, bx, by, factor)
        sx, sy = viewport.world_to_screen(nx, ny)
        size = 5
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx - size, sy), QPointF(sx + size, sy))
        painter.drawLine(QPointF(sx, sy - size), QPointF(sx, sy + size))


# ══════════════════════════════════════════════════════════════════════════════
#  XLineEntity  (Construction Line)
# ══════════════════════════════════════════════════════════════════════════════

class XLineEntity(Entity):
    """Infinite construction line through origin with direction vector."""

    def __init__(self, ox: float, oy: float, dx: float, dy: float, **kw):
        super().__init__(**kw)
        self.ox, self.oy = ox, oy
        self.dx, self.dy = dx, dy
        self._normalize()

    def _normalize(self):
        d = math.hypot(self.dx, self.dy)
        if d > 1e-12:
            self.dx /= d
            self.dy /= d
        else:
            self.dx, self.dy = 1.0, 0.0

    def move(self, dx, dy):
        self.ox += dx; self.oy += dy

    def rotate(self, bx, by, angle_rad):
        self.ox, self.oy = rotate_point(self.ox, self.oy, bx, by, angle_rad)
        ex, ey = rotate_point(self.ox + self.dx, self.oy + self.dy, self.ox, self.oy, angle_rad)
        self.dx, self.dy = ex - self.ox, ey - self.oy
        self._normalize()

    def scale(self, bx, by, factor):
        self.ox, self.oy = scale_point(self.ox, self.oy, bx, by, factor)

    def copy_at_offset(self, dx, dy):
        return XLineEntity(self.ox + dx, self.oy + dy, self.dx, self.dy,
                           color=self.color, layer=self.layer)

    def get_snap_points(self):
        return [[self.ox, self.oy]]

    def _viewport_diagonal(self, viewport):
        x1, y1 = viewport.screen_to_world(0, 0)
        x2, y2 = viewport.screen_to_world(viewport.width(), viewport.height())
        return math.hypot(x2 - x1, y2 - y1)

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        diag = self._viewport_diagonal(viewport)
        x1 = self.ox - self.dx * diag
        y1 = self.oy - self.dy * diag
        x2 = self.ox + self.dx * diag
        y2 = self.oy + self.dy * diag
        sx1, sy1 = viewport.world_to_screen(x1, y1)
        sx2, sy2 = viewport.world_to_screen(x2, y2)
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(self.ox, self.oy)])

    def draw_ghost_offset(self, painter, viewport, dx, dy):
        diag = self._viewport_diagonal(viewport)
        ox, oy = self.ox + dx, self.oy + dy
        sx1, sy1 = viewport.world_to_screen(ox - self.dx * diag, oy - self.dy * diag)
        sx2, sy2 = viewport.world_to_screen(ox + self.dx * diag, oy + self.dy * diag)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_rotated(self, painter, viewport, bx, by, angle_rad):
        diag = self._viewport_diagonal(viewport)
        ox, oy = rotate_point(self.ox, self.oy, bx, by, angle_rad)
        ex, ey = rotate_point(self.ox + self.dx, self.oy + self.dy, bx, by, angle_rad)
        ndx, ndy = ex - ox, ey - oy
        d = math.hypot(ndx, ndy)
        if d > 1e-12:
            ndx /= d; ndy /= d
        sx1, sy1 = viewport.world_to_screen(ox - ndx * diag, oy - ndy * diag)
        sx2, sy2 = viewport.world_to_screen(ox + ndx * diag, oy + ndy * diag)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_scaled(self, painter, viewport, bx, by, factor):
        self.draw_ghost_offset(painter, viewport, 0, 0)


# ══════════════════════════════════════════════════════════════════════════════
#  RayEntity
# ══════════════════════════════════════════════════════════════════════════════

class RayEntity(Entity):
    """Semi-infinite line from origin through direction point."""

    def __init__(self, ox: float, oy: float, dx: float, dy: float, **kw):
        super().__init__(**kw)
        self.ox, self.oy = ox, oy
        self.dx, self.dy = dx, dy
        self._normalize()

    def _normalize(self):
        d = math.hypot(self.dx, self.dy)
        if d > 1e-12:
            self.dx /= d
            self.dy /= d
        else:
            self.dx, self.dy = 1.0, 0.0

    def move(self, dx, dy):
        self.ox += dx; self.oy += dy

    def rotate(self, bx, by, angle_rad):
        self.ox, self.oy = rotate_point(self.ox, self.oy, bx, by, angle_rad)
        ex, ey = rotate_point(self.ox + self.dx, self.oy + self.dy, self.ox, self.oy, angle_rad)
        self.dx, self.dy = ex - self.ox, ey - self.oy
        self._normalize()

    def scale(self, bx, by, factor):
        self.ox, self.oy = scale_point(self.ox, self.oy, bx, by, factor)

    def copy_at_offset(self, dx, dy):
        return RayEntity(self.ox + dx, self.oy + dy, self.dx, self.dy,
                         color=self.color, layer=self.layer)

    def get_snap_points(self):
        return [[self.ox, self.oy]]

    def _viewport_diagonal(self, viewport):
        x1, y1 = viewport.screen_to_world(0, 0)
        x2, y2 = viewport.screen_to_world(viewport.width(), viewport.height())
        return math.hypot(x2 - x1, y2 - y1)

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        diag = self._viewport_diagonal(viewport)
        x2 = self.ox + self.dx * diag
        y2 = self.oy + self.dy * diag
        sx1, sy1 = viewport.world_to_screen(self.ox, self.oy)
        sx2, sy2 = viewport.world_to_screen(x2, y2)
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        painter.setPen(QPen(QColor(self.color), 1.5, Qt.SolidLine))
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))
        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(self.ox, self.oy)])

    def draw_ghost_offset(self, painter, viewport, dx, dy):
        diag = self._viewport_diagonal(viewport)
        ox, oy = self.ox + dx, self.oy + dy
        sx1, sy1 = viewport.world_to_screen(ox, oy)
        sx2, sy2 = viewport.world_to_screen(ox + self.dx * diag, oy + self.dy * diag)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_rotated(self, painter, viewport, bx, by, angle_rad):
        diag = self._viewport_diagonal(viewport)
        ox, oy = rotate_point(self.ox, self.oy, bx, by, angle_rad)
        ex, ey = rotate_point(self.ox + self.dx, self.oy + self.dy, bx, by, angle_rad)
        ndx, ndy = ex - ox, ey - oy
        d = math.hypot(ndx, ndy)
        if d > 1e-12:
            ndx /= d; ndy /= d
        sx1, sy1 = viewport.world_to_screen(ox, oy)
        sx2, sy2 = viewport.world_to_screen(ox + ndx * diag, oy + ndy * diag)
        painter.setPen(_ghost_pen())
        painter.drawLine(QPointF(sx1, sy1), QPointF(sx2, sy2))

    def draw_ghost_scaled(self, painter, viewport, bx, by, factor):
        self.draw_ghost_offset(painter, viewport, 0, 0)


# ══════════════════════════════════════════════════════════════════════════════
#  SplineEntity
# ══════════════════════════════════════════════════════════════════════════════

class SplineEntity(Entity):
    """Smooth curve through fit points using Catmull-Rom interpolation."""

    def __init__(self, points: list[tuple[float, float]], closed: bool = False, **kw):
        super().__init__(**kw)
        self.points = list(points)
        self.closed = closed

    def move(self, dx, dy):
        self.points = [(x + dx, y + dy) for x, y in self.points]

    def rotate(self, bx, by, angle_rad):
        self.points = [rotate_point(x, y, bx, by, angle_rad) for x, y in self.points]

    def scale(self, bx, by, factor):
        self.points = [scale_point(x, y, bx, by, factor) for x, y in self.points]

    def copy_at_offset(self, dx, dy):
        pts = [(x + dx, y + dy) for x, y in self.points]
        return SplineEntity(pts, closed=self.closed, color=self.color, layer=self.layer)

    def get_snap_points(self):
        return [[x, y] for x, y in self.points]

    def _catmull_rom(self, p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                   + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
        y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                   + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
        return x, y

    def _sample_points(self):
        pts = self.points
        n = len(pts)
        if n < 2:
            return list(pts)
        if n == 2:
            return list(pts)

        result = []
        if self.closed:
            for i in range(n):
                p0 = pts[(i - 1) % n]
                p1 = pts[i]
                p2 = pts[(i + 1) % n]
                p3 = pts[(i + 2) % n]
                for j in range(32):
                    t = j / 32.0
                    result.append(self._catmull_rom(p0, p1, p2, p3, t))
        else:
            p0 = pts[0]
            p1 = pts[0]
            p2 = pts[1]
            p3 = pts[2] if n > 2 else pts[1]
            for j in range(32):
                t = j / 32.0
                result.append(self._catmull_rom(p0, p1, p2, p3, t))

            for i in range(1, n - 2):
                p0 = pts[i - 1]
                p1 = pts[i]
                p2 = pts[i + 1]
                p3 = pts[i + 2]
                for j in range(32):
                    t = j / 32.0
                    result.append(self._catmull_rom(p0, p1, p2, p3, t))

            p0 = pts[n - 3] if n > 2 else pts[n - 2]
            p1 = pts[n - 2]
            p2 = pts[n - 1]
            p3 = pts[n - 1]
            for j in range(32):
                t = j / 32.0
                result.append(self._catmull_rom(p0, p1, p2, p3, t))

            result.append(pts[-1])

        return result

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        samples = self._sample_points()
        if not samples:
            return
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in samples]
        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.drawPolyline(screen_pts)
            if self.closed:
                painter.drawLine(screen_pts[-1], screen_pts[0])
        painter.setPen(QPen(QColor(self.color), 2.0, Qt.SolidLine))
        painter.drawPolyline(screen_pts)
        if self.closed:
            painter.drawLine(screen_pts[-1], screen_pts[0])
        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(x, y) for x, y in self.points])

    def draw_ghost_offset(self, painter, viewport, dx, dy):
        if not self.points:
            return
        samples = self._sample_points()
        screen_pts = [QPointF(*viewport.world_to_screen(x + dx, y + dy)) for x, y in samples]
        painter.setPen(_ghost_pen())
        painter.drawPolyline(screen_pts)
        if self.closed:
            painter.drawLine(screen_pts[-1], screen_pts[0])

    def draw_ghost_rotated(self, painter, viewport, bx, by, angle_rad):
        if not self.points:
            return
        rotated = [rotate_point(x, y, bx, by, angle_rad) for x, y in self.points]
        saved = self.points
        self.points = rotated
        samples = self._sample_points()
        self.points = saved
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in samples]
        painter.setPen(_ghost_pen())
        painter.drawPolyline(screen_pts)
        if self.closed:
            painter.drawLine(screen_pts[-1], screen_pts[0])

    def draw_ghost_scaled(self, painter, viewport, bx, by, factor):
        if not self.points:
            return
        scaled = [scale_point(x, y, bx, by, factor) for x, y in self.points]
        saved = self.points
        self.points = scaled
        samples = self._sample_points()
        self.points = saved
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in samples]
        painter.setPen(_ghost_pen())
        painter.drawPolyline(screen_pts)
        if self.closed:
            painter.drawLine(screen_pts[-1], screen_pts[0])


# ══════════════════════════════════════════════════════════════════════════════
#  HatchEntity
# ══════════════════════════════════════════════════════════════════════════════

class HatchEntity(Entity):
    """Solid or pattern fill of a closed boundary."""

    def __init__(self, boundary: list[tuple[float, float]], pattern: str = "SOLID", **kw):
        super().__init__(**kw)
        self.boundary = list(boundary)
        self.pattern = pattern

    def move(self, dx, dy):
        self.boundary = [(x + dx, y + dy) for x, y in self.boundary]

    def rotate(self, bx, by, angle_rad):
        self.boundary = [rotate_point(x, y, bx, by, angle_rad) for x, y in self.boundary]

    def scale(self, bx, by, factor):
        self.boundary = [scale_point(x, y, bx, by, factor) for x, y in self.boundary]

    def copy_at_offset(self, dx, dy):
        bnd = [(x + dx, y + dy) for x, y in self.boundary]
        return HatchEntity(bnd, pattern=self.pattern, color=self.color, layer=self.layer)

    def get_snap_points(self):
        pts = [[x, y] for x, y in self.boundary]
        cx = sum(x for x, y in self.boundary) / len(self.boundary)
        cy = sum(y for x, y in self.boundary) / len(self.boundary)
        pts.append([cx, cy])
        return pts

    def draw(self, painter: QPainter, viewport, show_grips: bool = True):
        if not self.boundary:
            return
        from PySide6.QtGui import QPolygonF
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in self.boundary]
        poly = QPolygonF(screen_pts)

        if self.pattern == "SOLID":
            painter.setBrush(QBrush(QColor(self.color)))
        else:
            painter.setBrush(Qt.NoBrush)
        painter.setPen(Qt.NoPen)
        painter.drawPolygon(poly)

        if self.selected:
            painter.setPen(QPen(QColor(SEL_COLOR), 3, Qt.SolidLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawPolygon(poly)

        painter.setPen(QPen(QColor(self.color), 1.0, Qt.SolidLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(poly)

        if self.selected and show_grips:
            _draw_grips(painter, [viewport.world_to_screen(x, y) for x, y in self.boundary])

    def draw_ghost_offset(self, painter, viewport, dx, dy):
        if not self.boundary:
            return
        from PySide6.QtGui import QPolygonF
        screen_pts = [QPointF(*viewport.world_to_screen(x + dx, y + dy)) for x, y in self.boundary]
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(QPolygonF(screen_pts))

    def draw_ghost_rotated(self, painter, viewport, bx, by, angle_rad):
        if not self.boundary:
            return
        from PySide6.QtGui import QPolygonF
        pts = [rotate_point(x, y, bx, by, angle_rad) for x, y in self.boundary]
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in pts]
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(QPolygonF(screen_pts))

    def draw_ghost_scaled(self, painter, viewport, bx, by, factor):
        if not self.boundary:
            return
        from PySide6.QtGui import QPolygonF
        pts = [scale_point(x, y, bx, by, factor) for x, y in self.boundary]
        screen_pts = [QPointF(*viewport.world_to_screen(x, y)) for x, y in pts]
        painter.setPen(_ghost_pen())
        painter.setBrush(Qt.NoBrush)
        painter.drawPolygon(QPolygonF(screen_pts))


