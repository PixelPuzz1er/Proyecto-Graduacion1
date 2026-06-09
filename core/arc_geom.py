import math
from PySide6.QtCore import QPointF

def angle_from_center(px: float, py: float, cx: float, cy: float) -> float:
    """Ángulo de un punto respecto al centro, en grados (CCW, Y-up)."""
    return math.degrees(math.atan2(py - cy, px - cx)) % 360

def arc_from_sce(start: QPointF, center: QPointF, end: QPointF):
    """Start-Center-End: arco siempre CCW de start a end."""
    r = math.hypot(start.x() - center.x(), start.y() - center.y())
    if r == 0: return None
    sa = angle_from_center(start.x(), start.y(), center.x(), center.y())
    ea = angle_from_center(end.x(), end.y(), center.x(), center.y())
    span = (ea - sa) % 360
    return center.x(), center.y(), r, sa, span

def arc_from_sca(start: QPointF, center: QPointF, included_angle: float):
    """Start-Center-Angle: arco con ángulo incluido (+CCW, -CW)."""
    r = math.hypot(start.x() - center.x(), start.y() - center.y())
    if r == 0: return None
    sa = angle_from_center(start.x(), start.y(), center.x(), center.y())
    return center.x(), center.y(), r, sa, included_angle

def arc_from_scl(start: QPointF, center: QPointF, chord_length: float):
    """Start-Center-Length: cuerda determina el span. Arco CCW siempre."""
    r = math.hypot(start.x() - center.x(), start.y() - center.y())
    if r == 0: return None
    half_chord = chord_length / 2.0
    if half_chord > r: return None
    sa = angle_from_center(start.x(), start.y(), center.x(), center.y())
    span = 2 * math.degrees(math.asin(half_chord / r))
    return center.x(), center.y(), r, sa, span

def arc_from_sea(start: QPointF, end: QPointF, angle: float):
    """Start-End-Angle: centro calculado del chord + ángulo incluido."""
    chord = QPointF(end.x() - start.x(), end.y() - start.y())
    chord_len = math.hypot(chord.x(), chord.y())
    if chord_len == 0: return None
    abs_a = abs(angle)
    if abs_a >= 360: return None
    r = chord_len / (2 * math.sin(math.radians(abs_a / 2)))
    mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
    perp = QPointF(-chord.y(), chord.x())
    perp_len = math.hypot(perp.x(), perp.y())
    if perp_len == 0: return None
    h = math.sqrt(max(0, r*r - (chord_len/2)*(chord_len/2)))
    perp_norm = QPointF(perp.x() / perp_len * h, perp.y() / perp_len * h)
    # Angle > 0 → CCW → center on +perp side
    cx = mid.x() + perp_norm.x()
    cy = mid.y() + perp_norm.y()
    sa = angle_from_center(start.x(), start.y(), cx, cy)
    ea = angle_from_center(end.x(), end.y(), cx, cy)
    span = (ea - sa) % 360
    if span > 180:
        span -= 360
    if angle < 0:
        span = -span if span > 0 else 360 + span
    return cx, cy, r, sa, span

def arc_from_ser(start: QPointF, end: QPointF, radius: float, bulge_up: bool = True):
    """Start-End-Radius: dos posibles arcos (bulge_up=True → arco convexo)."""
    chord = QPointF(end.x() - start.x(), end.y() - start.y())
    chord_len = math.hypot(chord.x(), chord.y())
    if chord_len == 0 or radius < chord_len / 2: return None
    mid = QPointF((start.x() + end.x()) / 2, (start.y() + end.y()) / 2)
    perp = QPointF(-chord.y(), chord.x())
    perp_len = math.hypot(perp.x(), perp.y())
    if perp_len == 0: return None
    h = math.sqrt(radius*radius - (chord_len/2)*(chord_len/2))
    sign = 1 if bulge_up else -1
    perp_norm = QPointF(perp.x() / perp_len * h * sign, perp.y() / perp_len * h * sign)
    cx = mid.x() + perp_norm.x()
    cy = mid.y() + perp_norm.y()
    sa = angle_from_center(start.x(), start.y(), cx, cy)
    ea = angle_from_center(end.x(), end.y(), cx, cy)
    span = (ea - sa) % 360
    if span > 180:
        span -= 360
    return cx, cy, radius, sa, span

def arc_from_sed(start: QPointF, end: QPointF, dir_angle: float):
    """Start-End-Direction: dirección tangente en el punto inicial."""
    # dir_angle es el ángulo de la tangente en start (grados)
    chord = QPointF(end.x() - start.x(), end.y() - start.y())
    chord_len = math.hypot(chord.x(), chord.y())
    if chord_len == 0: return None
    # Ángulo de la cuerda
    chord_angle = math.degrees(math.atan2(chord.y(), chord.x()))
    # Diferencia entre dirección tangente y cuerda
    diff = (dir_angle - chord_angle) % 360
    if diff > 180: diff -= 360
    if abs(diff) < 1 or abs(diff) > 179: return None
    # Ángulo inscrito = 2 * (ángulo entre tangente y cuerda)
    theta = math.radians(diff)
    r = chord_len / (2 * abs(math.sin(abs(theta))))
    # Centro en perpendicular a tangente
    # Tangente unitaria
    tx = math.cos(math.radians(dir_angle))
    ty = math.sin(math.radians(dir_angle))
    # Normal a la tangente (perpendicular CCW)
    nx = -ty
    ny = tx
    # Centro = start + normal * r
    cx = start.x() + nx * r
    cy = start.y() + ny * r
    sa = angle_from_center(start.x(), start.y(), cx, cy)
    ea = angle_from_center(end.x(), end.y(), cx, cy)
    span = (ea - sa) % 360
    if span > 180:
        span -= 360
    if diff < 0:
        span = -(360 - span) if span < 0 else -span
    return cx, cy, r, sa, span

def arc_from_cse(center: QPointF, start: QPointF, end: QPointF):
    """Center-Start-End: igual a SCE (CCW de start a end)."""
    return arc_from_sce(start, center, end)

def arc_from_csa(center: QPointF, start: QPointF, angle: float):
    """Center-Start-Angle: igual a SCA."""
    return arc_from_sca(start, center, angle)

def arc_from_csl(center: QPointF, start: QPointF, chord_length: float):
    """Center-Start-Length: igual a SCL."""
    return arc_from_scl(start, center, chord_length)
