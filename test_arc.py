import sys
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtGui import QPainter, QImage, QPen
from PySide6.QtCore import Qt, QRectF

app = QApplication(sys.argv)
img = QImage(200, 200, QImage.Format_ARGB32)
img.fill(Qt.white)

p = QPainter(img)
p.setPen(QPen(Qt.black, 2))
# Draw arc from 0 (3 o'clock) for 90 degrees (positive)
p.drawArc(QRectF(50, 50, 100, 100), 0 * 16, 90 * 16)
p.end()

img.save("arc_test.png")
print("Saved arc_test.png")
