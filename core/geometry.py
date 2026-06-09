# -*- coding: utf-8 -*-
"""
core/geometry.py — Funciones matemáticas puras para el motor CAD.
Sin dependencias de UI. Todas las coordenadas en Espacio Mundo (Y-Up).
"""
import math
from PySide6.QtCore import QPointF, QRectF


# ══════════════════════════════════════════════════════════════════════════════
#  Distancias
# ══════════════════════════════════════════════════════════════════════════════

def point_to_segment_distance(p: QPointF, a: QPointF, b: QPointF) -> float:
    """Distancia perpendicular del punto P al segmento AB."""
    dx, dy = b.x() - a.x(), b.y() - a.y()
    l2 = dx * dx + dy * dy
    if l2 == 0.0:
        return math.hypot(p.x() - a.x(), p.y() - a.y())
    t = max(0.0, min(1.0, ((p.x() - a.x()) * dx + (p.y() - a.y()) * dy) / l2))
    return math.hypot(p.x() - (a.x() + t * dx), p.y() - (a.y() + t * dy))


# ══════════════════════════════════════════════════════════════════════════════
#  Intersecciones de segmentos (para Crossing selection)
# ══════════════════════════════════════════════════════════════════════════════

def _ccw(A: QPointF, B: QPointF, C: QPointF) -> bool:
    return (C.y() - A.y()) * (B.x() - A.x()) > (B.y() - A.y()) * (C.x() - A.x())


def segments_intersect(A: QPointF, B: QPointF, C: QPointF, D: QPointF) -> bool:
    """Devuelve True si el segmento AB intersecta el segmento CD."""
    return _ccw(A, C, D) != _ccw(B, C, D) and _ccw(A, B, C) != _ccw(A, B, D)


# ══════════════════════════════════════════════════════════════════════════════
#  Transformaciones de puntos
# ══════════════════════════════════════════════════════════════════════════════

def rotate_point(px: float, py: float,
                 bx: float, by: float,
                 angle_rad: float) -> tuple:
    """Rota el punto (px, py) alrededor de (bx, by) por angle_rad radianes."""
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    dx, dy = px - bx, py - by
    return bx + dx * c - dy * s, by + dx * s + dy * c


def scale_point(px: float, py: float,
                bx: float, by: float,
                factor: float) -> tuple:
    """Escala el punto (px, py) desde (bx, by) por factor."""
    return bx + (px - bx) * factor, by + (py - by) * factor


def mirror_point(px: float, py: float,
                 mx1: float, my1: float,
                 mx2: float, my2: float) -> tuple:
    """Refleja (px, py) respecto a la recta infinita (mx1,my1)-(mx2,my2)."""
    dx = mx2 - mx1
    dy = my2 - my1
    d2 = dx * dx + dy * dy
    if d2 < 1e-9:
        return px, py
    t = ((px - mx1) * dx + (py - my1) * dy) / d2
    proj_x = mx1 + t * dx
    proj_y = my1 + t * dy
    return 2 * proj_x - px, 2 * proj_y - py


# ══════════════════════════════════════════════════════════════════════════════
#  Parseo de coordenadas (Entrada Numérica CAD)
# ══════════════════════════════════════════════════════════════════════════════

import re


def parse_coord_input(text: str, ref: QPointF = None,
                      cursor_dir: tuple = None) -> QPointF | None:
    """
    Parsea texto de entrada y retorna un QPointF en Espacio Mundo.
    Soporta:
      - "@dx,dy"       → relativo desde ref
      - "@dist<angle"  → polar relativo desde ref
      - "x,y"          → coordenada absoluta
      - "dist"         → distancia en dirección cursor_dir desde ref
    Retorna None si no se puede parsear.
    """
    text = text.strip()
    if not text:
        return None

    # #x,y → absoluto (prefix # forces absolute)
    m = re.match(r'^#\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$', text)
    if m:
        return QPointF(float(m.group(1)), float(m.group(2)))

    # @dx,dy → relativo cartesiano
    m = re.match(r'^@\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$', text)
    if m and ref is not None:
        return QPointF(ref.x() + float(m.group(1)),
                       ref.y() + float(m.group(2)))

    # @dist<angle o dist<angle → polar relativo
    m = re.match(r'^@?\s*(\d+(?:\.\d+)?)\s*<\s*(-?\d+(?:\.\d+)?)$', text)
    if m and ref is not None:
        d   = float(m.group(1))
        rad = math.radians(float(m.group(2)))
        return QPointF(ref.x() + d * math.cos(rad),
                       ref.y() + d * math.sin(rad))

    # x,y → RELATIVO si hay ref (AutoCAD DYN mode), ABSOLUTO si no
    m = re.match(r'^(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)$', text)
    if m:
        if ref is not None and cursor_dir is not None:
            # Relative with sign from cursor direction (like AutoCAD DYN)
            dx_val = float(m.group(1))
            dy_val = float(m.group(2))
            sign_x = 1.0
            sign_y = 1.0
            if cursor_dir[0] < 0: sign_x = -1.0
            if cursor_dir[1] < 0: sign_y = -1.0
            return QPointF(ref.x() + dx_val * sign_x,
                           ref.y() + dy_val * sign_y)
        return QPointF(float(m.group(1)), float(m.group(2)))

    # Número suelto → distancia en dirección del cursor
    m = re.match(r'^(\d+(?:\.\d+)?)$', text)
    if m and ref is not None and cursor_dir is not None:
        d = float(m.group(1))
        dx, dy = cursor_dir
        length = math.hypot(dx, dy)
        if length > 1e-9:
            return QPointF(ref.x() + d * dx / length,
                           ref.y() + d * dy / length)

    return None


def parse_angle(text: str) -> float | None:
    """Parsea un texto como ángulo en grados. Retorna radianes o None."""
    text = text.strip()
    m = re.match(r'^(-?\d+(?:\.\d+)?)$', text)
    if m:
        return math.radians(float(m.group(1)))
    return None


def parse_factor(text: str) -> float | None:
    """Parsea un factor de escala positivo. Retorna float o None."""
    text = text.strip()
    m = re.match(r'^(\d+(?:\.\d+)?)$', text)
    if m:
        return float(m.group(1))
    return None


# ══════════════════════════════════════════════════════════════════════════════
#  Cerebro Matemático - Intersecciones de Entidades (Milestone 9)
# ══════════════════════════════════════════════════════════════════════════════

def line_line_intersection(p1: QPointF, p2: QPointF, p3: QPointF, p4: QPointF) -> tuple[QPointF, float] | None:
    """
    Retorna el punto de intersección (QPointF) y el parámetro t sobre la primera recta (p1-p2)
    entre las rectas infinitas que pasan por p1-p2 y p3-p4.
    Retorna None si son paralelas o coincidentes.
    """
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    x3, y3 = p3.x(), p3.y()
    x4, y4 = p4.x(), p4.y()

    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-9:
        return None

    t1 = x1 * y2 - y1 * x2
    t2 = x3 * y4 - y3 * x4
    ix = (t1 * (x3 - x4) - (x1 - x2) * t2) / d
    iy = (t1 * (y3 - y4) - (y1 - y2) * t2) / d
    
    # Calcular parámetro t del punto de intersección sobre la primera recta p1-p2
    vx, vy = x2 - x1, y2 - y1
    length_sq = vx * vx + vy * vy
    if length_sq > 1e-9:
        t = ((ix - x1) * vx + (iy - y1) * vy) / length_sq
    else:
        t = 0.0

    return QPointF(ix, iy), t


def get_line_parameter(p1: QPointF, p2: QPointF, q: QPointF) -> float:
    """Calcula el parámetro paramétrico t del punto q proyectado sobre la recta p1-p2."""
    vx, vy = p2.x() - p1.x(), p2.y() - p1.y()
    length_sq = vx * vx + vy * vy
    if length_sq < 1e-9:
        return 0.0
    return ((q.x() - p1.x()) * vx + (q.y() - p1.y()) * vy) / length_sq


def line_circle_intersection(p1: QPointF, p2: QPointF, center: QPointF, radius: float) -> list[tuple[QPointF, float]]:
    """
    Calcula los puntos donde una línea infinita p1-p2 atraviesa un círculo.
    Retorna una lista de tuplas (QPointF, float) con los puntos y sus parámetros t.
    """
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    cx, cy = center.x(), center.y()

    dx, dy = x2 - x1, y2 - y1
    A = dx * dx + dy * dy
    if abs(A) < 1e-9:
        # Recta degenerada, verificar si está sobre el radio
        dist = math.hypot(x1 - cx, y1 - cy)
        if abs(dist - radius) < 1e-6:
            return [(QPointF(x1, y1), 0.0)]
    return []


# ══════════════════════════════════════════════════════════════════════════════
#  Cálculo de Empalme (Fillet) entre dos líneas (Milestone 10)
# ══════════════════════════════════════════════════════════════════════════════

def compute_fillet(line1, line2, radius: float, pick1: QPointF, pick2: QPointF):
    """
    Calcula el arco de empalme entre dos LineEntity.
    El arco siempre se genera del lado de los picks.
    Usa la bisectriz u1+u2 que apunta naturalmente hacia los picks.

    Retorna (cx, cy, radius, start_angle, span_angle, t1, t2, None, None)
    o None si es imposible.
    """
    from core.entities import LineEntity
    if not isinstance(line1, LineEntity) or not isinstance(line2, LineEntity):
        return None

    p1 = QPointF(line1.x1, line1.y1)
    p2 = QPointF(line1.x2, line1.y2)
    p3 = QPointF(line2.x1, line2.y1)
    p4 = QPointF(line2.x2, line2.y2)

    res = line_line_intersection(p1, p2, p3, p4)
    if res is None:
        return None
    int_pt, _ = res

    dx1, dy1 = p2.x() - p1.x(), p2.y() - p1.y()
    dx2, dy2 = p4.x() - p3.x(), p4.y() - p3.y()
    len1 = math.hypot(dx1, dy1)
    len2 = math.hypot(dx2, dy2)
    if len1 < 1e-9 or len2 < 1e-9:
        return None

    # Dirección desde intersección hacia cada pick
    t_int1 = get_line_parameter(p1, p2, int_pt)
    t_pk1  = get_line_parameter(p1, p2, pick1)
    dir1 = 1.0 if t_pk1 >= t_int1 else -1.0
    u1x, u1y = dir1 * dx1 / len1, dir1 * dy1 / len1

    t_int2 = get_line_parameter(p3, p4, int_pt)
    t_pk2  = get_line_parameter(p3, p4, pick2)
    dir2 = 1.0 if t_pk2 >= t_int2 else -1.0
    u2x, u2y = dir2 * dx2 / len2, dir2 * dy2 / len2

    # Ángulo entre las dos direcciones u1, u2
    dot = u1x * u2x + u1y * u2y
    theta = math.acos(max(-1.0, min(1.0, dot)))

    half = theta / 2.0
    sin_half = math.sin(half)
    if sin_half < 1e-9:
        return None
    tan_half = math.tan(half)

    d_tan = radius / tan_half
    tx1 = int_pt.x() + d_tan * u1x
    ty1 = int_pt.y() + d_tan * u1y
    tx2 = int_pt.x() + d_tan * u2x
    ty2 = int_pt.y() + d_tan * u2y

    # Bisectriz: u1+u2 apunta hacia los picks (entre u1 y u2)
    bx = u1x + u2x
    by = u1y + u2y
    blen = math.hypot(bx, by)
    if blen < 1e-9:
        return None
    bx /= blen
    by /= blen

    d_center = radius / sin_half
    cx = int_pt.x() + d_center * bx
    cy = int_pt.y() + d_center * by

    # Ángulos del arco en espacio mundo (Y-up)
    a_start = math.degrees(math.atan2(ty1 - cy, tx1 - cx)) % 360
    a_end   = math.degrees(math.atan2(ty2 - cy, tx2 - cx)) % 360
    span = (a_end - a_start) % 360
    if span > 180:
        span -= 360

    # Parámetros paramétricos de los puntos tangentes en cada línea
    t1 = get_line_parameter(p1, p2, QPointF(tx1, ty1))
    t2 = get_line_parameter(p3, p4, QPointF(tx2, ty2))

    return (cx, cy, radius, a_start, span, t1, t2, None, None)


def line_circle_intersection(p1: QPointF, p2: QPointF, center: QPointF, radius: float) -> list[tuple[QPointF, float]]:
    """
    Calcula los puntos donde una línea infinita p1-p2 atraviesa un círculo.
    Retorna una lista de tuplas (QPointF, float) con los puntos y sus parámetros t.
    """
    x1, y1 = p1.x(), p1.y()
    x2, y2 = p2.x(), p2.y()
    cx, cy = center.x(), center.y()

    dx, dy = x2 - x1, y2 - y1
    A = dx * dx + dy * dy
    if abs(A) < 1e-9:
        dist = math.hypot(x1 - cx, y1 - cy)
        if abs(dist - radius) < 1e-6:
            return [(QPointF(x1, y1), 0.0)]
        return []

    B = 2 * ((x1 - cx) * dx + (y1 - cy) * dy)
    C = (x1 - cx) * (x1 - cx) + (y1 - cy) * (y1 - cy) - radius * radius

    disc = B * B - 4 * A * C
    if disc < -1e-9:
        return []
    elif abs(disc) < 1e-9:
        t = -B / (2 * A)
        return [(QPointF(x1 + t * dx, y1 + t * dy), t)]
    else:
        sqrt_disc = math.sqrt(disc)
        t_a = (-B - sqrt_disc) / (2 * A)
        t_b = (-B + sqrt_disc) / (2 * A)
        return [(QPointF(x1 + t_a * dx, y1 + t_a * dy), t_a),
                (QPointF(x1 + t_b * dx, y1 + t_b * dy), t_b)]


def circle_circle_intersection(c1: QPointF, r1: float, c2: QPointF, r2: float) -> list[QPointF]:
    """
    Retorna una lista de 0, 1 o 2 puntos de intersección entre dos círculos.
    """
    cx1, cy1 = c1.x(), c1.y()
    cx2, cy2 = c2.x(), c2.y()

    dx = cx2 - cx1
    dy = cy2 - cy1
    d = math.hypot(dx, dy)

    if d > r1 + r2 or d < abs(r1 - r2) or d < 1e-9:
        return []

    a = (r1 * r1 - r2 * r2 + d * d) / (2 * d)
    h_sq = r1 * r1 - a * a
    h = math.sqrt(max(0.0, h_sq))

    x2 = cx1 + a * dx / d
    y2 = cy1 + a * dy / d

    if h < 1e-9:
        return [QPointF(x2, y2)]

    rx = -dy * (h / d)
    ry = dx * (h / d)

    return [
        QPointF(x2 + rx, y2 + ry),
        QPointF(x2 - rx, y2 - ry)
    ]


def get_entities_intersection(e1, e2) -> list[tuple[QPointF, float]]:
    """
    Helper polimórfico para obtener la lista de intersecciones de dos entidades.
    Retorna una lista de tuplas (QPointF, float) indicando el punto y el parámetro t
    con respecto a la línea (si e1 es LineEntity) o con respecto a e2 (si e2 es LineEntity).
    """
    from core.entities import LineEntity, CircleEntity

    if isinstance(e1, LineEntity) and isinstance(e2, LineEntity):
        p1 = QPointF(e1.x1, e1.y1)
        p2 = QPointF(e1.x2, e1.y2)
        p3 = QPointF(e2.x1, e2.y1)
        p4 = QPointF(e2.x2, e2.y2)
        res = line_line_intersection(p1, p2, p3, p4)
        return [res] if res is not None else []

    elif isinstance(e1, LineEntity) and isinstance(e2, CircleEntity):
        p1 = QPointF(e1.x1, e1.y1)
        p2 = QPointF(e1.x2, e1.y2)
        c = QPointF(e2.cx, e2.cy)
        return line_circle_intersection(p1, p2, c, e2.radius)

    elif isinstance(e1, CircleEntity) and isinstance(e2, LineEntity):
        p1 = QPointF(e2.x1, e2.y1)
        p2 = QPointF(e2.x2, e2.y2)
        c = QPointF(e1.cx, e1.cy)
        return line_circle_intersection(p1, p2, c, e1.radius)

    elif isinstance(e1, CircleEntity) and isinstance(e2, CircleEntity):
        c1 = QPointF(e1.cx, e1.cy)
        c2 = QPointF(e2.cx, e2.cy)
        ipts = circle_circle_intersection(c1, e1.radius, c2, e2.radius)
        return [(pt, 0.0) for pt in ipts]

    return []
