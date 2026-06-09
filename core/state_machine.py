# -*- coding: utf-8 -*-
"""
core/state_machine.py — Enumerados de fase para los comandos CAD.
Referencia centralizada de strings de fase. Úsalos en los comandos
para evitar strings mágicos sueltos.
"""
from enum import Enum


class Phase(str, Enum):
    """Fases internas que cada comando usa en su atributo `_phase`."""
    IDLE        = "IDLE"
    SELECT      = "SELECT"
    BASE        = "BASE"
    DESTINATION = "DESTINATION"
    DRAG        = "DRAG"
    NEXT_POINT  = "NEXT_POINT"
    CENTER      = "CENTER"
    RADIUS      = "RADIUS"


class CommandAlias(str, Enum):
    """Alias canónicos de cada comando CAD (para evitar strings mágicos)."""
    LINE    = "L"
    CIRCLE  = "C"
    ERASE   = "E"
    MOVE    = "M"
    COPY    = "CO"
    ROTATE  = "RO"
    SCALE   = "SC"
