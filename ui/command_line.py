# -*- coding: utf-8 -*-
"""
ui/command_line.py — Widget de consola inferior estilo AutoCAD.
Muestra historial de mensajes + prefijo de estado + buffer del usuario.
El canvas le actualiza el estado vía update_state().
"""
from PySide6.QtWidgets import QWidget
from PySide6.QtGui     import QPainter, QColor, QPen, QFont
from PySide6.QtCore    import Qt, QTimer


class CommandLineWidget(QWidget):
    """
    Panel inferior de texto: 3 líneas de historial + línea de entrada activa.
    No procesa teclado — solo renderiza lo que el canvas le dice.
    """

    HISTORY_LINES = 3
    HEIGHT        = 90   # px fijos

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)
        self.setAutoFillBackground(False)

        # Estado que el canvas actualiza
        self._history: list[str] = [
            "LaserAlignPro CAD Engine — MVC v3.0",
            "L=Línea  C=Círculo  E=Borrar  M=Mover  CO=Copiar  RO=Rotar  SC=Escalar",
            "Clic der.=Enter en contexto  |  Ctrl+Z=Deshacer  |  ESC=Cancelar",
        ]
        self._prompt: str  = "Comando: "
        self._buffer: str  = ""
        self._cursor_vis   = True

        # Cursor parpadeante
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_timer.start(500)

        # Colores
        self._BG      = QColor(22, 24, 28, 230)
        self._MUTED   = QColor("#8A8A8A")
        self._ACTIVE  = QColor("#E0E0E0")
        self._BORDER  = QColor("#2A2A2A")

    # ── API pública ───────────────────────────────────────────────────────────

    def update_state(self, prompt: str, buffer: str, history: list[str]):
        self._prompt  = prompt
        self._buffer  = buffer
        self._history = list(history)
        self.update()

    def add_history(self, message: str):
        self._history.append(message)
        if len(self._history) > 20:
            self._history.pop(0)
        self.update()

    # ── Render ────────────────────────────────────────────────────────────────

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, False)

        # Fondo oscuro
        painter.fillRect(self.rect(), self._BG)

        # Borde superior
        painter.setPen(QPen(self._BORDER, 1))
        painter.drawLine(0, 0, self.width(), 0)

        font = QFont("Consolas", 10)
        painter.setFont(font)
        fm  = painter.fontMetrics()
        lh  = fm.height() + 3

        # Historial (últimas HISTORY_LINES líneas)
        recent = self._history[-self.HISTORY_LINES:]
        for i, line in enumerate(recent):
            # La última línea del historial es un poco más brillante
            painter.setPen(self._ACTIVE if i == len(recent) - 1 else self._MUTED)
            painter.drawText(12, 8 + i * lh + fm.ascent(), line)

        # Línea de entrada activa
        y_input = 8 + len(recent) * lh
        prefix_w = fm.horizontalAdvance(self._prompt)
        painter.setPen(self._MUTED)
        painter.drawText(12, y_input + fm.ascent(), self._prompt)

        cursor_str = "█" if self._cursor_vis else ""
        painter.setPen(self._ACTIVE)
        painter.drawText(12 + prefix_w, y_input + fm.ascent(),
                         self._buffer + cursor_str)

    # ── Private ───────────────────────────────────────────────────────────────
    def _blink(self):
        self._cursor_vis = not self._cursor_vis
        self.update()
