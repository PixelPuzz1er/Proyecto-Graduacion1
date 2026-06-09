# -*- coding: utf-8 -*-
"""
ui/ribbon.py — Motor Arquitectónico del Ribbon estilo AutoCAD 2026 Dark Theme.
Implementa pestañas, paneles colapsables, y distintos tipos de botones (grandes, pequeños, split).
"""
import os
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QToolButton, 
                               QLabel, QFrame, QMenu, QGridLayout)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer

def _svg_icon(path: str, size: int = 32) -> QIcon:
    """Carga un SVG como QIcon con tamaño fijo renderizado a pixmap."""
    if not os.path.exists(path):
        return QIcon()
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

# Esquema de Colores AutoCAD 2026 Dark Theme Exacto
C_RIBBON_BG = "#3B4453"    # Fondo detrás de pestañas / paneles
C_TAB_ACTIVE = "#3B4453"   # Fondo de la pestaña activa y paneles
C_PANEL_BOTTOM = "#333D4B" # Fondo de la barrita del título del panel
C_TEXT_ACTIVE = "#FFFFFF"  # Blanco puro para texto activo
C_TEXT_DIM = "#8F9BA6"     # Gris-azul tenue para títulos e inactivos
C_HOVER = "#272F3A"        # Resaltado al pasar el mouse
C_PRESSED = "#2D3A4C"      # Resaltado al hacer clic o estar seleccionado
C_BORDER = "#4A5568"       # Línea de borde sutil de 1px
C_ACCENT = "#0078D4"       # Azul de acento para grips y selecciones


class RibbonButtonLarge(QToolButton):
    """Botón grande con icono arriba y texto abajo. Típico de Línea, Mover, etc."""
    def __init__(self, text: str, icon_name: str, command: str = None, parent=None):
        super().__init__(parent)
        self.command = command
        self.setText(text)
        
        icon_path = os.path.join("assets", "icons", f"{icon_name}.svg")
        self.setIcon(_svg_icon(icon_path, 32))
        self.setIconSize(QSize(32, 32))
        
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedSize(62, 70)
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                color: {C_TEXT_ACTIVE};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 8pt;
                padding: 2px;
            }}
            QToolButton:hover {{
                background-color: {C_HOVER};
                border: 1px solid {C_BORDER};
            }}
            QToolButton:pressed {{
                background-color: {C_PRESSED};
            }}
            QToolButton:checked {{
                background-color: {C_HOVER};
                border: 1px solid {C_BORDER};
            }}
        """)

class RibbonButtonSmall(QToolButton):
    """Botón pequeño con icono a la izquierda y texto a la derecha (opcional)."""
    def __init__(self, text: str, icon_name: str, command: str = None, show_text: bool = True, parent=None):
        super().__init__(parent)
        self.command = command
        if show_text:
            self.setText(f" {text}")
            self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        else:
            self.setToolTip(text)
            self.setToolButtonStyle(Qt.ToolButtonIconOnly)
            
        icon_path = os.path.join("assets", "icons", f"{icon_name}.svg")
        self.setIcon(_svg_icon(icon_path, 20))
        self.setIconSize(QSize(20, 20))
        
        self.setFocusPolicy(Qt.NoFocus)
        self.setFixedHeight(24)
        if not show_text:
            self.setFixedWidth(30)
            
        self.setStyleSheet(f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                color: {C_TEXT_ACTIVE};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 8pt;
                text-align: left;
                padding-left: 2px;
                padding-right: 4px;
            }}
            QToolButton:hover {{
                background-color: {C_HOVER};
                border: 1px solid {C_BORDER};
            }}
            QToolButton:pressed {{
                background-color: {C_PRESSED};
            }}
        """)

class RibbonSplitButton(QWidget):
    """Botón con parte superior clickeable y parte inferior para abrir un menú desplegable."""
    def __init__(self, text: str, icon_name: str, main_command: str = None, parent=None):
        super().__init__(parent)
        self.main_command = main_command
        self.setFixedSize(62, 70)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Botón principal (Icono)
        self.btn_main = QToolButton()
        icon_path = os.path.join("assets", "icons", f"{icon_name}.svg")
        self.btn_main.setIcon(_svg_icon(icon_path, 32))
        self.btn_main.setIconSize(QSize(32, 32))
        self.btn_main.setFixedSize(62, 46)
        self.btn_main.setFocusPolicy(Qt.NoFocus)
        
        # Botón desplegable (Texto + Flecha)
        self.btn_drop = QToolButton()
        self.btn_drop.setText(f"{text} ▾")
        self.btn_drop.setPopupMode(QToolButton.InstantPopup)
        self.btn_drop.setFixedSize(62, 24)
        self.btn_drop.setFocusPolicy(Qt.NoFocus)
        self.btn_drop.setToolButtonStyle(Qt.ToolButtonTextOnly)
        
        # Menú
        self.menu = QMenu(self)
        self.menu.setStyleSheet(f"""
            QMenu {{
                background-color: {C_TAB_ACTIVE};
                border: 1px solid {C_BORDER};
                color: {C_TEXT_ACTIVE};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }}
            QMenu::item {{
                padding: 6px 40px 6px 6px;
                icon-size: 32px 32px;
            }}
            QMenu::item:selected {{
                background-color: {C_HOVER};
            }}
            QMenu::icon {{
                padding-left: 4px;
                padding-right: 8px;
                width: 32px;
                height: 32px;
            }}
        """)
        self.btn_drop.setMenu(self.menu)
        
        btn_style = f"""
            QToolButton {{
                background-color: transparent;
                border: 1px solid transparent;
                color: {C_TEXT_ACTIVE};
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 8pt;
            }}
            QToolButton:hover {{
                background-color: {C_HOVER};
                border: 1px solid {C_BORDER};
            }}
            QToolButton:pressed {{
                background-color: {C_PRESSED};
            }}
        """
        self.btn_main.setStyleSheet(btn_style + "QToolButton { border-bottom-left-radius: 0px; border-bottom-right-radius: 0px; }")
        self.btn_drop.setStyleSheet(btn_style + "QToolButton::menu-indicator { image: none; } QToolButton { border-top-left-radius: 0px; border-top-right-radius: 0px; text-align: center; padding: 0px; }")
        
        layout.addWidget(self.btn_main)
        layout.addWidget(self.btn_drop)

    def add_action(self, text: str, icon_name: str, command: str) -> QAction:
        icon_path = os.path.join("assets", "icons", f"{icon_name}.svg")
        action = QAction(text, self)
        action.setIcon(_svg_icon(icon_path, 32))
        action.setData(command)
        self.menu.addAction(action)
        return action


class RibbonPanel(QWidget):
    """Panel individual dentro de una pestaña (ej. Panel 'Dibujo')."""
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(105)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Contenedor del contenido (Botones)
        self.content_widget = QWidget()
        self.content_widget.setStyleSheet(f"background-color: {C_TAB_ACTIVE};")
        self.content_layout = QHBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(4, 4, 4, 2)
        self.content_layout.setSpacing(2)
        
        # Título inferior
        self.title_widget = QWidget()
        self.title_widget.setFixedHeight(20)
        self.title_widget.setStyleSheet(f"background-color: {C_PANEL_BOTTOM}; border-top: 1px solid {C_BORDER};")
        title_layout = QHBoxLayout(self.title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_title = QLabel(f"{title} ▾")
        self.lbl_title.setAlignment(Qt.AlignCenter)
        self.lbl_title.setStyleSheet(f"""
            color: {C_TEXT_DIM}; 
            font-family: 'Segoe UI', Arial, sans-serif; 
            font-size: 7.5pt; 
            font-weight: 500;
            border: none;
        """)
        
        title_layout.addWidget(self.lbl_title)
        
        layout.addWidget(self.content_widget)
        layout.addWidget(self.title_widget)


class RibbonTab(QWidget):
    """Pestaña completa que contiene múltiples paneles (ej. 'Inicio')."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(105)
        self.setStyleSheet(f"background-color: {C_TAB_ACTIVE};")
        
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
    def add_panel(self, panel: RibbonPanel):
        self.layout.addWidget(panel)
        # Separator (1px)
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Plain)
        sep.setStyleSheet(f"color: {C_BORDER}; background-color: {C_BORDER}; max-width: 1px; min-width: 1px;")
        self.layout.addWidget(sep)
        
    def add_stretch(self):
        self.layout.addStretch(1)


class RibbonWidget(QWidget):
    """El contenedor principal del Ribbon (Pestañas superiores + Contenido)."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(135)
        self.setStyleSheet(f"background-color: {C_RIBBON_BG};")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header (Tabs)
        header_widget = QWidget()
        header_widget.setFixedHeight(30)
        self.header_layout = QHBoxLayout(header_widget)
        self.header_layout.setContentsMargins(8, 0, 0, 0)
        self.header_layout.setSpacing(2)
        
        # Contenedor dinámico de la pestaña activa
        self.content_area = QWidget()
        self.content_area.setStyleSheet(f"background-color: {C_TAB_ACTIVE}; border-bottom: 1px solid {C_BORDER};")
        self.content_layout = QVBoxLayout(self.content_area)
        


        layout.addWidget(header_widget)
        layout.addWidget(self.content_area)
        
        # Línea de separación inferior
        bottom_sep = QFrame()
        bottom_sep.setFrameShape(QFrame.HLine)
        bottom_sep.setFrameShadow(QFrame.Plain)
        bottom_sep.setStyleSheet(f"color: {C_BORDER}; background-color: {C_BORDER}; max-height: 1px; min-height: 1px;")
        layout.addWidget(bottom_sep)

        self.tabs = {}
        self.active_tab_name = None

    def _create_tool_button(self, icon, text, tooltip):
        btn = QToolButton()
        btn.setIcon(_svg_icon(f"assets/icons/{icon}", 20))
        btn.setText(text)
        btn.setToolTip(tooltip)
        return btn

    def add_tab(self, name: str, tab_widget: RibbonTab):
        btn = QLabel(name)
        btn.setAlignment(Qt.AlignCenter)
        btn.setCursor(Qt.PointingHandCursor)
        
        self.tabs[name] = {"btn": btn, "widget": tab_widget}
        
        self.header_layout.addWidget(btn)
        
        if len(self.tabs) == 1:
            self.set_active_tab(name)
            self.header_layout.addStretch(1)
        else:
            self._update_tab_styles()


            
    def set_active_tab(self, name: str):
        if name not in self.tabs:
            return
            
        self.active_tab_name = name
        
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
                
        self.content_layout.addWidget(self.tabs[name]["widget"])
        self._update_tab_styles()
        
    def _update_tab_styles(self):
        for name, data in self.tabs.items():
            btn = data["btn"]
            if name == self.active_tab_name:
                btn.setStyleSheet(f"""
                    QLabel {{
                        background-color: {C_TAB_ACTIVE};
                        color: {C_TEXT_ACTIVE};
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 8.5pt;
                        padding-left: 14px;
                        padding-right: 14px;
                        border: none;
                        border-bottom: 1px solid {C_TAB_ACTIVE};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QLabel {{
                        background-color: transparent;
                        color: {C_TEXT_DIM};
                        font-family: 'Segoe UI', Arial, sans-serif;
                        font-size: 8.5pt;
                        padding-left: 14px;
                        padding-right: 14px;
                        border: none;
                    }}
                    QLabel:hover {{
                        background-color: {C_HOVER};
                        color: {C_TEXT_ACTIVE};
                    }}
                """)
