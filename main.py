#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — Punto de entrada del CAD.
Solo inicializa la QApplication y lanza la MainWindow.
"""
import sys
import os

os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("LaserAlignPro CAD")
    app.setApplicationVersion("3.0")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
