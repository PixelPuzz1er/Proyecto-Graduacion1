import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

app = QApplication(sys.argv)
win = MainWindow()
# win.show() # Don't show to prevent blocking forever, just test instantiating and painting
canvas = win.canvas
# Mock the dynamic tooltip execution
canvas.resize(800, 600)
from PySide6.QtGui import QPainter, QImage
img = QImage(800, 600, QImage.Format_ARGB32)
p = QPainter(img)

# Fake a command with prompt
class DummyCmd:
    def __init__(self):
        self._phase = "WAIT"
        self.prompt = "Indique una opción [Inscrito en el círculo/Circunscrito alrededor del círculo]:"
canvas._cmd = DummyCmd()

try:
    canvas._draw_dynamic_tooltip(p)
    print("Tooltip drawn successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    p.end()
