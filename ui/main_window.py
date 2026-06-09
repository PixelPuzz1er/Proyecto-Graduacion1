# -*- coding: utf-8 -*-
"""
ui/main_window.py — Ventana principal del CAD con Ribbon UI AutoCAD 2026.
"""
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QGridLayout, QMenu, QToolButton)
from PySide6.QtCore    import Qt

from core.document      import Document
from ui.canvas          import CADCanvas
from ui.command_line    import CommandLineWidget
from ui.ribbon          import (RibbonWidget, RibbonTab, RibbonPanel, 
                                RibbonButtonLarge, RibbonButtonSmall, RibbonSplitButton)

class MainWindow(QMainWindow):
    """
    QMainWindow que ensambla:
      - CADCanvas  (área de trabajo principal)
      - CommandLineWidget (consola inferior estilo AutoCAD)
      - Ribbon UI (Cinta de opciones vectorial estilo AutoCAD 2026 Dark Theme)
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LaserAlignPro CAD  —  AutoCAD 2026 Clone (Phase 1)")
        self.setMinimumSize(1200, 700)
        self.setWindowState(Qt.WindowMaximized)
        
        # Color de fondo de ventana general del AutoCAD Dark Theme
        self.setStyleSheet("background-color: #282828;")

        # ── Modelo compartido ──────────────────────────────────────────────
        self.doc = Document()

        # ── Widgets ───────────────────────────────────────────────────────
        self.canvas  = CADCanvas(self.doc)
        self.cmd_bar = CommandLineWidget()
        self.cmd_bar.setCursor(Qt.ArrowCursor)
        
        # ── Ribbon UI ──────────────────────────────────────────────────────
        self.ribbon_buttons = {}
        self._build_ribbon()

        # ── Layout General ────────────────────────────────────────────────
        central = QWidget()
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.ribbon, stretch=0)
        layout.addWidget(self.canvas,  stretch=1)
        layout.addWidget(self.cmd_bar, stretch=0)
        self.setCentralWidget(central)

        # ── Conexión canvas → CommandLineWidget ───────────────────────────
        self.canvas.state_changed.connect(self._on_state_changed)

        # ── Canvas tiene el foco al arrancar ──────────────────────────────
        self.canvas.setFocus()

    def _build_ribbon(self):
        self.ribbon = RibbonWidget()
        
        # ── Pestaña Home ──
        tab_inicio = RibbonTab()
        
        # Panel: DIBUJO (Draw)
        panel_dibujo = RibbonPanel("Dibujo")
        
        # Left side of Draw Panel (Large Buttons) — Solo los 4 grandes de AutoCAD 2026
        layout_dibujo_left = QHBoxLayout()
        layout_dibujo_left.setContentsMargins(0, 0, 0, 0)
        layout_dibujo_left.setSpacing(2)
        
        btn_line = RibbonButtonLarge("Línea", "line", "L")
        btn_line.clicked.connect(lambda: self.canvas.run_command("L"))
        self.ribbon_buttons["L"] = btn_line
        
        btn_pline = RibbonButtonLarge("Polilínea", "polyline", "PL")
        btn_pline.clicked.connect(lambda: self.canvas.run_command("PL"))
        self.ribbon_buttons["PL"] = btn_pline
        
        btn_circle = RibbonSplitButton("Círculo", "circle", "C")
        btn_circle.btn_main.clicked.connect(lambda: self.canvas.run_command("C"))
        act_c_rad = btn_circle.add_action("Centro, Radio", "circle", "C")
        act_c_rad.triggered.connect(lambda: self.canvas.run_command("C"))
        act_c_dia = btn_circle.add_action("Centro, Diámetro", "circle", "C")
        act_c_dia.triggered.connect(lambda: self.canvas.run_command("C"))
        act_c_2p = btn_circle.add_action("2 Puntos", "circle_2p", "C2P")
        act_c_2p.triggered.connect(lambda: self.canvas.run_command("C2P"))
        act_c_3p = btn_circle.add_action("3 Puntos", "circle_3p", "C3P")
        act_c_3p.triggered.connect(lambda: self.canvas.run_command("C3P"))
        self.ribbon_buttons["C"] = btn_circle.btn_main
        
        btn_arc = RibbonSplitButton("Arco", "arc", "A")
        btn_arc.btn_main.clicked.connect(lambda: self.canvas.run_command("A"))
        act_a_3p = btn_arc.add_action("3 Puntos", "arc", "A")
        act_a_3p.triggered.connect(lambda: self.canvas.run_command("A"))
        act_a_sce = btn_arc.add_action("Inicio, Centro, Fin", "arc_sce", "ASCE")
        act_a_sce.triggered.connect(lambda: self.canvas.run_command("ASCE"))
        act_a_sca = btn_arc.add_action("Inicio, Centro, Ángulo", "arc_sca", "ASCA")
        act_a_sca.triggered.connect(lambda: self.canvas.run_command("ASCA"))
        act_a_scl = btn_arc.add_action("Inicio, Centro, Longitud", "arc_scl", "ASCL")
        act_a_scl.triggered.connect(lambda: self.canvas.run_command("ASCL"))
        act_a_sea = btn_arc.add_action("Inicio, Fin, Ángulo", "arc_sea", "ASEA")
        act_a_sea.triggered.connect(lambda: self.canvas.run_command("ASEA"))
        act_a_ser = btn_arc.add_action("Inicio, Fin, Radio", "arc_ser", "ASER")
        act_a_ser.triggered.connect(lambda: self.canvas.run_command("ASER"))
        act_a_cse = btn_arc.add_action("Centro, Inicio, Fin", "arc_cse", "ACSE")
        act_a_cse.triggered.connect(lambda: self.canvas.run_command("ACSE"))
        act_a_csa = btn_arc.add_action("Centro, Inicio, Ángulo", "arc_csa", "ACSA")
        act_a_csa.triggered.connect(lambda: self.canvas.run_command("ACSA"))
        act_a_csl = btn_arc.add_action("Centro, Inicio, Longitud", "arc_csl", "ACSL")
        act_a_csl.triggered.connect(lambda: self.canvas.run_command("ACSL"))
        act_a_cont = btn_arc.add_action("Continuar", "arc_cont", "ACONT")
        act_a_cont.triggered.connect(lambda: self.canvas.run_command("ACONT"))
        self.ribbon_buttons["A"] = btn_arc.btn_main
        
        layout_dibujo_left.addWidget(btn_line)
        layout_dibujo_left.addWidget(btn_pline)
        layout_dibujo_left.addWidget(btn_circle)
        layout_dibujo_left.addWidget(btn_arc)
        
        # Right side of Draw Panel (grid of small buttons and stacked splits)
        layout_dibujo_right = QGridLayout()
        layout_dibujo_right.setContentsMargins(4, 0, 4, 0)
        layout_dibujo_right.setSpacing(2)
        
        # Menu helper style
        from PySide6.QtWidgets import QMenu, QToolButton
        
        # Column 0: Stacked Split Buttons
        # Row 0: Rectangle / Polygon
        btn_rect = RibbonButtonSmall("Rectángulo", "rectangle", "REC")
        menu_rect = QMenu(self)
        menu_rect.setStyleSheet(btn_circle.menu.styleSheet())
        act_rect = menu_rect.addAction("Rectángulo")
        act_rect.triggered.connect(lambda: self.canvas.run_command("REC"))
        act_pol = menu_rect.addAction("Polígono")
        act_pol.triggered.connect(lambda: self.canvas.run_command("POL"))
        btn_rect.setMenu(menu_rect)
        btn_rect.setPopupMode(QToolButton.MenuButtonPopup)
        btn_rect.clicked.connect(lambda: self.canvas.run_command("REC"))
        self.ribbon_buttons["REC"] = btn_rect
        
        # Row 1: Ellipse
        btn_ellipse = RibbonButtonSmall("Elipse", "ellipse", "EL")
        menu_ellipse = QMenu(self)
        menu_ellipse.setStyleSheet(btn_circle.menu.styleSheet())
        act_el = menu_ellipse.addAction("Elipse")
        act_el.triggered.connect(lambda: self.canvas.run_command("EL"))
        btn_ellipse.setMenu(menu_ellipse)
        btn_ellipse.setPopupMode(QToolButton.MenuButtonPopup)
        btn_ellipse.clicked.connect(lambda: self.canvas.run_command("EL"))
        self.ribbon_buttons["EL"] = btn_ellipse
        
        # Row 2: Hatch / Gradient
        btn_hatch = RibbonButtonSmall("Sombreado", "hatch", "H")
        menu_hatch = QMenu(self)
        menu_hatch.setStyleSheet(btn_circle.menu.styleSheet())
        act_h = menu_hatch.addAction("Sombreado")
        act_h.triggered.connect(lambda: self.canvas.run_command("H"))
        btn_hatch.setMenu(menu_hatch)
        btn_hatch.setPopupMode(QToolButton.MenuButtonPopup)
        btn_hatch.clicked.connect(lambda: self.canvas.run_command("H"))
        self.ribbon_buttons["H"] = btn_hatch
        
        # Column 1: Secondary lines
        # Row 0: Spline
        btn_spline = RibbonButtonSmall("Spline", "spline", "SPL")
        btn_spline.clicked.connect(lambda: self.canvas.run_command("SPL"))
        self.ribbon_buttons["SPL"] = btn_spline
        
        # Row 1: XLine
        btn_xline = RibbonButtonSmall("L. Auxiliar", "xline", "XL")
        btn_xline.clicked.connect(lambda: self.canvas.run_command("XL"))
        self.ribbon_buttons["XL"] = btn_xline
        
        # Row 2: Ray
        btn_ray = RibbonButtonSmall("Rayo", "ray", "RAY")
        btn_ray.clicked.connect(lambda: self.canvas.run_command("RAY"))
        self.ribbon_buttons["RAY"] = btn_ray
        
        # Column 2: Others
        # Row 0: Point
        btn_point = RibbonButtonSmall("Punto", "point", "PO")
        btn_point.clicked.connect(lambda: self.canvas.run_command("PO"))
        self.ribbon_buttons["PO"] = btn_point
        
        # Row 1: Gradient
        btn_gradient = RibbonButtonSmall("Gradiente", "gradient", "H")
        btn_gradient.clicked.connect(lambda: self.canvas.run_command("H"))
        self.ribbon_buttons["GRAD"] = btn_gradient
        
        # Row 2: Break
        btn_break = RibbonButtonSmall("Partir", "break", "BR")
        btn_break.clicked.connect(lambda: self.canvas.run_command("BR"))
        self.ribbon_buttons["BR"] = btn_break
        
        # Column 3: More tools
        # Row 0: Join
        btn_join = RibbonButtonSmall("Juntar", "join", "J")
        btn_join.clicked.connect(lambda: self.canvas.run_command("J"))
        self.ribbon_buttons["J"] = btn_join
        
        layout_dibujo_right.addWidget(btn_rect, 0, 0)
        layout_dibujo_right.addWidget(btn_ellipse, 1, 0)
        layout_dibujo_right.addWidget(btn_hatch, 2, 0)
        
        layout_dibujo_right.addWidget(btn_spline, 0, 1)
        layout_dibujo_right.addWidget(btn_xline, 1, 1)
        layout_dibujo_right.addWidget(btn_ray, 2, 1)
        
        layout_dibujo_right.addWidget(btn_point, 0, 2)
        layout_dibujo_right.addWidget(btn_gradient, 1, 2)
        layout_dibujo_right.addWidget(btn_break, 2, 2)
        
        layout_dibujo_right.addWidget(btn_join, 0, 3)
        
        panel_dibujo.content_layout.addLayout(layout_dibujo_left)
        panel_dibujo.content_layout.addLayout(layout_dibujo_right)
        
        # Panel: MODIFICAR (Modify)
        panel_modificar = RibbonPanel("Modificar")
        
        # Column 1 (Mover, Copiar, Estirar)
        layout_mod_c1 = QVBoxLayout()
        layout_mod_c1.setContentsMargins(0, 0, 0, 0)
        layout_mod_c1.setSpacing(2)
        
        btn_move = RibbonButtonSmall("Mover", "move", "M")
        btn_move.clicked.connect(lambda: self.canvas.run_command("M"))
        self.ribbon_buttons["M"] = btn_move
        layout_mod_c1.addWidget(btn_move)
        
        btn_copy = RibbonButtonSmall("Copiar", "copy", "CO")
        btn_copy.clicked.connect(lambda: self.canvas.run_command("CO"))
        self.ribbon_buttons["CO"] = btn_copy
        layout_mod_c1.addWidget(btn_copy)
        
        btn_stretch = RibbonButtonSmall("Estirar", "stretch", "S")
        btn_stretch.clicked.connect(lambda: self.canvas.run_command("S"))
        self.ribbon_buttons["S"] = btn_stretch
        layout_mod_c1.addWidget(btn_stretch)
        
        # Column 2 (Rotar, Simetría, Escala)
        layout_mod_c2 = QVBoxLayout()
        layout_mod_c2.setContentsMargins(0, 0, 0, 0)
        layout_mod_c2.setSpacing(2)
        
        btn_rotate = RibbonButtonSmall("Rotar", "rotate", "RO")
        btn_rotate.clicked.connect(lambda: self.canvas.run_command("RO"))
        self.ribbon_buttons["RO"] = btn_rotate
        layout_mod_c2.addWidget(btn_rotate)
        
        btn_mirror = RibbonButtonSmall("Simetría", "mirror", "MI")
        btn_mirror.clicked.connect(lambda: self.canvas.run_command("MI"))
        self.ribbon_buttons["MI"] = btn_mirror
        layout_mod_c2.addWidget(btn_mirror)
        
        btn_scale = RibbonButtonSmall("Escala", "scale", "SC")
        btn_scale.clicked.connect(lambda: self.canvas.run_command("SC"))
        self.ribbon_buttons["SC"] = btn_scale
        layout_mod_c2.addWidget(btn_scale)
        
        # Column 3 (Recortar, Empalme, Matriz con submenús estilo AutoCAD)
        layout_mod_c3 = QVBoxLayout()
        layout_mod_c3.setContentsMargins(0, 0, 0, 0)
        layout_mod_c3.setSpacing(2)
        
        # Recortar / Alargar
        btn_trim = RibbonButtonSmall("Recortar ▾", "trim", "TR")
        menu_trim = QMenu(self)
        menu_trim.setStyleSheet(btn_circle.menu.styleSheet())
        act_tr = menu_trim.addAction("Recortar")
        act_tr.triggered.connect(lambda: self.canvas.run_command("TR"))
        act_ex = menu_trim.addAction("Alargar")
        act_ex.triggered.connect(lambda: self.canvas.run_command("EX"))
        btn_trim.setMenu(menu_trim)
        btn_trim.setPopupMode(QToolButton.MenuButtonPopup)
        btn_trim.clicked.connect(lambda: self.canvas.run_command("TR"))
        self.ribbon_buttons["TR"] = btn_trim
        layout_mod_c3.addWidget(btn_trim)
        
        # Empalme / Chaflán
        btn_fillet = RibbonButtonSmall("Empalme ▾", "fillet", "F")
        menu_fillet = QMenu(self)
        menu_fillet.setStyleSheet(btn_circle.menu.styleSheet())
        act_f = menu_fillet.addAction("Empalme")
        act_f.triggered.connect(lambda: self.canvas.run_command("F"))
        act_cha = menu_fillet.addAction("Chaflán")
        act_cha.triggered.connect(lambda: self.canvas.run_command("CHA"))
        btn_fillet.setMenu(menu_fillet)
        btn_fillet.setPopupMode(QToolButton.MenuButtonPopup)
        btn_fillet.clicked.connect(lambda: self.canvas.run_command("F"))
        self.ribbon_buttons["F"] = btn_fillet
        layout_mod_c3.addWidget(btn_fillet)
        
        # Matriz
        btn_array = RibbonButtonSmall("Matriz ▾", "array", "AR")
        menu_array = QMenu(self)
        menu_array.setStyleSheet(btn_circle.menu.styleSheet())
        act_ar = menu_array.addAction("Matriz Rectangular")
        act_ar.triggered.connect(lambda: self.canvas.run_command("AR"))
        btn_array.setMenu(menu_array)
        btn_array.setPopupMode(QToolButton.MenuButtonPopup)
        btn_array.clicked.connect(lambda: self.canvas.run_command("AR"))
        self.ribbon_buttons["AR"] = btn_array
        layout_mod_c3.addWidget(btn_array)
        
        # Column 4 (Borrar, Descomponer, Desfase - Iconos solos para coincidir con AutoCAD)
        layout_mod_c4 = QVBoxLayout()
        layout_mod_c4.setContentsMargins(0, 0, 0, 0)
        layout_mod_c4.setSpacing(2)
        
        btn_erase = RibbonButtonSmall("Borrar", "erase", "E", show_text=False)
        btn_erase.clicked.connect(lambda: self.canvas.run_command("E"))
        self.ribbon_buttons["E"] = btn_erase
        layout_mod_c4.addWidget(btn_erase)
        
        btn_explode = RibbonButtonSmall("Descomponer", "explode", "X", show_text=False)
        btn_explode.clicked.connect(lambda: self.canvas.run_command("X"))
        self.ribbon_buttons["X"] = btn_explode
        layout_mod_c4.addWidget(btn_explode)
        
        btn_offset = RibbonButtonSmall("Desfase", "offset", "O", show_text=False)
        btn_offset.clicked.connect(lambda: self.canvas.run_command("O"))
        self.ribbon_buttons["O"] = btn_offset
        layout_mod_c4.addWidget(btn_offset)
        
        panel_modificar.content_layout.addLayout(layout_mod_c1)
        panel_modificar.content_layout.addLayout(layout_mod_c2)
        panel_modificar.content_layout.addLayout(layout_mod_c3)
        panel_modificar.content_layout.addLayout(layout_mod_c4)
        
        # Assemble Tab
        tab_inicio.add_panel(panel_dibujo)
        tab_inicio.add_panel(panel_modificar)
        tab_inicio.add_stretch()
        
        # Add Tabs to Ribbon
        self.ribbon.add_tab("Inicio", tab_inicio)
        
        tab_insercion = RibbonTab()
        tab_insercion.add_stretch()
        self.ribbon.add_tab("Inserción", tab_insercion)
        
        tab_anotar = RibbonTab()
        tab_anotar.add_stretch()
        self.ribbon.add_tab("Anotar", tab_anotar)
        
        tab_parametrico = RibbonTab()
        tab_parametrico.add_stretch()
        self.ribbon.add_tab("Paramétrico", tab_parametrico)
        
        tab_vista = RibbonTab()
        tab_vista.add_stretch()
        self.ribbon.add_tab("Vista", tab_vista)
        
        # Set active tab
        self.ribbon.set_active_tab("Inicio")

    def _on_state_changed(self, prompt: str, buffer: str, history: list):
        self.cmd_bar.update_state(prompt, buffer, history)
        
        active_alias = None
        if self.canvas._cmd:
            from core.command_registry import COMMAND_CLASS_MAP
            active_alias = COMMAND_CLASS_MAP.get(type(self.canvas._cmd))
            
        for alias, btn in self.ribbon_buttons.items():
            btn.setCheckable(True)
            btn.setChecked(alias == active_alias)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.canvas.setFocus()
