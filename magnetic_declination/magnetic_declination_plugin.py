# -*- coding: utf-8 -*-
import os
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtWidgets import QMessageBox

# Layer of compatibility for QAction across Qt5 and Qt6
try:
    from qgis.PyQt.QtGui import QAction, QIcon
except ImportError:
    from qgis.PyQt.QtWidgets import QAction, QIcon

# Import Dialog component
from .magnetic_declination_dialog import MagneticDeclinationDialog


class MagneticDeclinationPlugin:
    """Main QGIS Plugin class that integrates the tool into the QGIS GUI."""

    def __init__(self, iface) -> None:
        self.iface = iface
        self.dialog = None
        self.action = None
        self.menu_name = "Rosa dos Ventos Geomagnética"

    def create_icon_if_missing(self) -> str:
        """Programmatically draws and saves the icon.png if it does not exist.
        Ensures the plugin has a premium icon without requiring pre-existing assets.
        """
        icon_path = os.path.join(os.path.dirname(__file__), "icon.png")
        if os.path.exists(icon_path):
            return icon_path

        from qgis.PyQt.QtGui import QPixmap, QColor, QPen, QBrush, QPolygonF, QPainter
        from qgis.PyQt.QtCore import QPointF
        
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        except AttributeError:
            painter.setRenderHint(QPainter.Antialiasing)
            
        # Draw dark outer circle
        painter.setPen(QPen(QColor("#475569"), 1.5))
        painter.setBrush(QBrush(QColor("#1E293B")))
        painter.drawEllipse(2, 2, 28, 28)
        
        # True North Needle (Blue)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#38BDF8")))
        poly_n_r = QPolygonF([QPointF(16, 16), QPointF(16, 4), QPointF(20, 16)])
        painter.drawPolygon(poly_n_r)
        painter.setBrush(QBrush(QColor("#0284C7")))
        poly_n_l = QPolygonF([QPointF(16, 16), QPointF(16, 4), QPointF(12, 16)])
        painter.drawPolygon(poly_n_l)
        
        # South Needle (Slate)
        painter.setBrush(QBrush(QColor("#E2E8F0")))
        poly_s_r = QPolygonF([QPointF(16, 16), QPointF(16, 28), QPointF(20, 16)])
        painter.drawPolygon(poly_s_r)
        painter.setBrush(QBrush(QColor("#94A3B8")))
        poly_s_l = QPolygonF([QPointF(16, 16), QPointF(16, 28), QPointF(12, 16)])
        painter.drawPolygon(poly_s_l)
        
        # Center pivot
        painter.setBrush(QBrush(QColor("#F59E0B")))
        painter.drawEllipse(14, 14, 4, 4)
        
        painter.end()
        pixmap.save(icon_path, "PNG")
        return icon_path

    def initGui(self) -> None:
        """Called by QGIS when starting the plugin to build the menu and toolbar button."""
        # Generate icon if missing
        icon_path = self.create_icon_if_missing()
        icon = QIcon(icon_path)
        
        # Create action
        self.action = QAction(
            icon,
            "Rosa dos Ventos e Declinação Magnética",
            self.iface.mainWindow()
        )
        self.action.setStatusTip("Calcula declinação magnética e gera a Rosa dos Ventos")
        self.action.triggered.connect(self.run)
        
        # Add plugin to menu and toolbar
        self.iface.addPluginToMenu(self.menu_name, self.action)
        self.iface.addToolBarIcon(self.action)

    def unload(self) -> None:
        """Called by QGIS when deactivating the plugin. Removes GUI items."""
        if self.action:
            self.iface.removePluginMenu(self.menu_name, self.action)
            self.iface.removeToolBarIcon(self.action)

    def run(self) -> None:
        """Launch the plugin dialog window."""
        # Create dialog if it doesn't exist
        if not self.dialog:
            self.dialog = MagneticDeclinationDialog(self.iface)
            
        # Show dialog
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
