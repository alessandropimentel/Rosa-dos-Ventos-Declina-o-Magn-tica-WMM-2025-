# -*- coding: utf-8 -*-
import math
import datetime
from qgis.PyQt.QtWidgets import (
    QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QGroupBox,
    QLabel, QDoubleSpinBox, QDateEdit, QPushButton, QCheckBox,
    QMessageBox, QFileDialog, QFrame, QInputDialog, QComboBox
)
from qgis.PyQt.QtCore import Qt, QDate, QSize, QRect
from qgis.PyQt.QtGui import QColor, QPainter

from qgis.core import (
    QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject, QgsPointXY,
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsSymbol, QgsCategorizedSymbolRenderer,
    QgsRendererCategory
)
from qgis.gui import QgsMapToolEmitPoint

# Import custom components
from .geomag import GeoMag
from .compass_rose_widget import CompassRoseWidget

# PyQt5 / PyQt6 compatibility wrapper
try:
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
except AttributeError:
    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT = Qt.AlignLeft


class MapClickTool(QgsMapToolEmitPoint):
    """Custom map tool to capture mouse clicks on the QGIS Map Canvas."""
    def __init__(self, canvas, callback) -> None:
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
        
    def canvasReleaseEvent(self, event) -> None:
        point = self.toMapCoordinates(event.pos())
        self.callback(point)


class MagneticDeclinationDialog(QDialog):
    """Main UI dialog for the Magnetic Declination Compass Rose plugin."""
    
    def __init__(self, iface, parent=None) -> None:
        super().__init__(parent)
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.geomag = GeoMag()
        
        self.prev_tool = None
        self.map_tool = None
        
        self.setWindowTitle("Rosa dos Ventos & Declinação Magnética (WMM-2025)")
        self.resize(700, 480)
        self.setMinimumSize(600, 400)
        
        self.setup_ui()
        self.recalculate()

    def setup_ui(self) -> None:
        """Construct the layout and widget tree."""
        # Main horizontal layout
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ----------------------------------------------------
        # Left Panel (Controls)
        # ----------------------------------------------------
        left_panel = QVBoxLayout()
        left_panel.setSpacing(10)
        
        # Group 1: Coordinates and Date Input
        input_group = QGroupBox("Parâmetros de Entrada", self)
        input_layout = QFormLayout(input_group)
        input_layout.setSpacing(8)
        
        # Latitude Spinbox
        self.spin_lat = QDoubleSpinBox(self)
        self.spin_lat.setRange(-90.0, 90.0)
        self.spin_lat.setDecimals(5)
        self.spin_lat.setSingleStep(0.1)
        self.spin_lat.setValue(0.0)
        input_layout.addRow(QLabel("Latitude (Graus Decimal):"), self.spin_lat)
        
        # Longitude Spinbox
        self.spin_lon = QDoubleSpinBox(self)
        self.spin_lon.setRange(-180.0, 180.0)
        self.spin_lon.setDecimals(5)
        self.spin_lon.setSingleStep(0.1)
        self.spin_lon.setValue(0.0)
        input_layout.addRow(QLabel("Longitude (Graus Decimal):"), self.spin_lon)
        
        # Altitude Spinbox
        self.spin_alt = QDoubleSpinBox(self)
        self.spin_alt.setRange(-1.0, 100.0)
        self.spin_alt.setDecimals(1)
        self.spin_alt.setSingleStep(0.1)
        self.spin_alt.setValue(0.0)
        self.spin_alt.setSuffix(" km")
        input_layout.addRow(QLabel("Altitude (Elipsoidal):"), self.spin_alt)
        
        # Date Input
        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        input_layout.addRow(QLabel("Data do Cálculo:"), self.date_edit)
        
        left_panel.addWidget(input_group)
        
        # Group 2: Map tools
        map_group = QGroupBox("Capturar Coordenadas do Mapa", self)
        map_layout = QVBoxLayout(map_group)
        map_layout.setSpacing(6)
        
        self.btn_map_center = QPushButton("Obter do Centro da Tela", self)
        self.btn_map_center.clicked.connect(self.get_coordinates_from_center)
        map_layout.addWidget(self.btn_map_center)
        
        self.btn_map_click = QPushButton("Clicar no Mapa", self)
        self.btn_map_click.clicked.connect(self.start_map_picking)
        map_layout.addWidget(self.btn_map_click)
        
        left_panel.addWidget(map_group)

        # Group 3: View configurations
        view_group = QGroupBox("Aparência e Exibição", self)
        view_layout = QVBoxLayout(view_group)
        
        view_layout.addWidget(QLabel("Estilo da Rosa dos Ventos:", self))
        self.combo_style = QComboBox(self)
        self.combo_style.addItems([
            "Clássico Cartográfico",
            "Moderno Minimalista",
            "Militar Tático",
            "Tecnológico Digital",
            "Vintage / Antigo",
            "Náutico Premium",
            "Diagrama Técnico"
        ])
        self.combo_style.currentTextChanged.connect(self.change_style)
        view_layout.addWidget(self.combo_style)
        
        self.chk_dark = QCheckBox("Modo Escuro", self)
        self.chk_dark.setChecked(True)
        self.chk_dark.toggled.connect(self.toggle_dark_mode)
        view_layout.addWidget(self.chk_dark)
        
        self.chk_details = QCheckBox("Mostrar Detalhes Numéricos", self)
        self.chk_details.setChecked(True)
        self.chk_details.toggled.connect(self.toggle_details)
        view_layout.addWidget(self.chk_details)
        
        left_panel.addWidget(view_group)
        
        # Group 4: Export Tools
        export_group = QGroupBox("Ações e Exportação", self)
        export_layout = QVBoxLayout(export_group)
        export_layout.setSpacing(6)
        
        self.btn_export_svg = QPushButton("Salvar Rosa dos Ventos como SVG...", self)
        self.btn_export_svg.clicked.connect(self.export_svg)
        export_layout.addWidget(self.btn_export_svg)
        
        self.btn_export_png = QPushButton("Salvar Rosa dos Ventos como PNG...", self)
        self.btn_export_png.clicked.connect(self.export_png)
        export_layout.addWidget(self.btn_export_png)
        
        self.btn_add_layer = QPushButton("Adicionar Camada no Mapa...", self)
        self.btn_add_layer.clicked.connect(self.add_layer_to_map)
        export_layout.addWidget(self.btn_add_layer)
        
        left_panel.addWidget(export_group)
        left_panel.addStretch(1)
        
        # Copyright label
        self.lbl_copyright = QLabel("Plugin Criado por Alessandro Pimentel\nTel: (91)98505-6742", self)
        self.lbl_copyright.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; margin-top: 10px;")
        self.lbl_copyright.setAlignment(ALIGN_CENTER)
        left_panel.addWidget(self.lbl_copyright)
        
        main_layout.addLayout(left_panel, 1)

        # ----------------------------------------------------
        # Right Panel (Interactive Canvas)
        # ----------------------------------------------------
        right_panel = QVBoxLayout()
        right_panel.setSpacing(5)
        
        # Frame containing the custom widget
        canvas_frame = QFrame(self)
        canvas_frame.setFrameShape(QFrame.Shape.StyledPanel)
        canvas_frame.setFrameShadow(QFrame.Shadow.Sunken)
        canvas_frame_layout = QVBoxLayout(canvas_frame)
        canvas_frame_layout.setContentsMargins(2, 2, 2, 2)
        
        self.compass_widget = CompassRoseWidget(self)
        canvas_frame_layout.addWidget(self.compass_widget)
        
        right_panel.addWidget(canvas_frame, 1)
        
        main_layout.addLayout(right_panel, 2)
        
        # Signal Connections for auto-recalculation
        self.spin_lat.valueChanged.connect(self.recalculate)
        self.spin_lon.valueChanged.connect(self.recalculate)
        self.spin_alt.valueChanged.connect(self.recalculate)
        self.date_edit.dateChanged.connect(self.recalculate)

    def date_to_decimal_year(self, qdate: QDate) -> float:
        """Converts QDate to decimal year format."""
        py_date = datetime.date(qdate.year(), qdate.month(), qdate.day())
        year = py_date.year
        current_year = datetime.date(year + 1, 1, 1)
        following_year = datetime.date(year, 1, 1)
        days_in_year = (current_year - following_year).days
        days_passed = (py_date - datetime.date(year, 1, 1)).days
        return year + float(days_passed) / days_in_year

    def recalculate(self) -> None:
        """Performs calculation of magnetic declination and updates the widget."""
        lat = self.spin_lat.value()
        lon = self.spin_lon.value()
        alt = self.spin_alt.value()
        time = self.date_to_decimal_year(self.date_edit.date())
        
        try:
            result = self.geomag.calculate(glat=lat, glon=lon, alt=alt, time=time)
            self.compass_widget.set_magnetic_data(
                declination=result.dec,
                inclination=result.inclination,
                intensity=result.total_intensity
            )
        except Exception as e:
            # Silence error or alert user if date is out of range
            pass

    def get_coordinates_from_center(self) -> None:
        """Fetches coordinates from the center of QGIS map extent and converts to EPSG:4326."""
        center = self.canvas.center()
        self.process_map_point(center)

    def start_map_picking(self) -> None:
        """Sets the active map tool to capture clicks on the map canvas."""
        self.prev_tool = self.canvas.mapTool()
        self.map_tool = MapClickTool(self.canvas, self.on_map_clicked)
        self.canvas.setMapTool(self.map_tool)
        self.iface.messageBar().pushMessage(
            "Capturando Ponto", "Clique em qualquer lugar no mapa para ler as coordenadas.",
            level=0, duration=3
        )

    def on_map_clicked(self, point: QgsPointXY) -> None:
        """Callback when user clicks the map canvas."""
        # Restore previous map tool
        self.canvas.unsetMapTool(self.map_tool)
        if self.prev_tool:
            self.canvas.setMapTool(self.prev_tool)
            
        self.process_map_point(point)

    def process_map_point(self, point: QgsPointXY) -> None:
        """Converts point coordinates to EPSG:4326 and updates spinboxes."""
        canvas_crs = self.canvas.mapSettings().destinationCrs()
        wgs84_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        
        if canvas_crs != wgs84_crs:
            transform = QgsCoordinateTransform(canvas_crs, wgs84_crs, QgsProject.instance())
            wgs84_point = transform.transform(point)
        else:
            wgs84_point = point
            
        # Update inputs (which triggers recalculation automatically via signals)
        self.spin_lat.setValue(wgs84_point.y())
        self.spin_lon.setValue(wgs84_point.x())

    def toggle_dark_mode(self, checked: bool) -> None:
        self.compass_widget.set_dark_mode(checked)

    def toggle_details(self, checked: bool) -> None:
        self.compass_widget.set_show_details(checked)

    def change_style(self, style_name: str) -> None:
        self.compass_widget.set_style(style_name)

    def export_svg(self) -> None:
        """Exports the drawn compass rose to a scalable vector SVG file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Rosa dos Ventos para SVG", "", "Scalable Vector Graphics (*.svg)"
        )
        if not file_path:
            return
            
        try:
            from qgis.PyQt.QtSvg import QSvgGenerator
            
            generator = QSvgGenerator()
            generator.setFileName(file_path)
            generator.setSize(QSize(600, 600))
            generator.setViewBox(QRect(0, 0, 600, 600))
            generator.setTitle("Rosa dos Ventos Geomagnética")
            generator.setDescription(
                f"Calculado para Lat: {self.spin_lat.value():.5f}, "
                f"Lon: {self.spin_lon.value():.5f}, "
                f"Declinação: {self.compass_widget.declination:.2f}°"
            )
            
            painter = QPainter(generator)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            self.compass_widget.render_rose(painter, 600, 600)
            painter.end()
            
            QMessageBox.information(self, "Exportação Concluída", "Arquivo SVG salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Exportação", f"Não foi possível salvar o arquivo: {str(e)}")

    def export_png(self) -> None:
        """Exports the drawn compass rose to a high-resolution PNG image."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Rosa dos Ventos para PNG", "", "Portable Network Graphics (*.png)"
        )
        if not file_path:
            return
            
        try:
            from qgis.PyQt.QtGui import QPixmap
            
            pixmap = QPixmap(800, 800)
            pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
            self.compass_widget.render_rose(painter, 800, 800)
            painter.end()
            
            pixmap.save(file_path, "PNG")
            QMessageBox.information(self, "Exportação Concluída", "Imagem PNG salva com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro de Exportação", f"Não foi possível salvar o arquivo: {str(e)}")

    def add_layer_to_map(self) -> None:
        """Creates a temporary vector layer representing the compass rose at the selected coordinates."""
        center_x = self.spin_lon.value()
        center_y = self.spin_lat.value()
        dec = self.compass_widget.declination
        
        radius_m, ok = QInputDialog.getDouble(
            self, "Tamanho da Rosa dos Ventos", "Raio da Rosa dos Ventos (metros):",
            100.0, 5.0, 100000.0, 1
        )
        if not ok:
            return
            
        # Create memory layer in EPSG:4326
        layer_name = f"Rosa dos Ventos Geomagnética ({dec:.1f}°)"
        vlayer = QgsVectorLayer("LineString?crs=EPSG:4326&field=type:string&field=name:string", layer_name, "memory")
        pr = vlayer.dataProvider()
        
        R_earth = 6378137.0
        
        # Helper to generate offset points
        def get_offset_point(angle_deg, dist_m):
            angle_rad = math.radians(angle_deg)
            dx = dist_m * math.sin(angle_rad)
            dy = dist_m * math.cos(angle_rad)
            dlat = (dy / R_earth) * (180.0 / math.pi)
            dlon = (dx / (R_earth * math.cos(math.radians(center_y)))) * (180.0 / math.pi)
            return QgsPointXY(center_x + dlon, center_y + dlat)
            
        c = QgsPointXY(center_x, center_y)
        
        # 1. Outer circle geometries
        circle_points = []
        for i in range(73):
            circle_points.append(get_offset_point(i * 5, radius_m))
            
        feat_circle = QgsFeature()
        feat_circle.setGeometry(QgsGeometry.fromPolylineXY(circle_points))
        feat_circle.setAttributes(["Ring", "Limite"])
        pr.addFeature(feat_circle)
        
        # 2. True North geometries
        tn_tip = get_offset_point(0, radius_m)
        feat_tn = QgsFeature()
        feat_tn.setGeometry(QgsGeometry.fromPolylineXY([c, tn_tip]))
        feat_tn.setAttributes(["True North", "Norte Verdadeiro"])
        pr.addFeature(feat_tn)
        
        # Arrowhead True North (left/right)
        feat_tn_l = QgsFeature()
        feat_tn_l.setGeometry(QgsGeometry.fromPolylineXY([tn_tip, get_offset_point(-10, radius_m * 0.9)]))
        feat_tn_l.setAttributes(["True North", "Seta NV"])
        pr.addFeature(feat_tn_l)
        
        feat_tn_r = QgsFeature()
        feat_tn_r.setGeometry(QgsGeometry.fromPolylineXY([tn_tip, get_offset_point(10, radius_m * 0.9)]))
        feat_tn_r.setAttributes(["True North", "Seta NV"])
        pr.addFeature(feat_tn_r)
        
        # 3. Magnetic North geometries (offset by declination)
        mn_tip = get_offset_point(dec, radius_m * 1.1)
        feat_mn = QgsFeature()
        feat_mn.setGeometry(QgsGeometry.fromPolylineXY([c, mn_tip]))
        feat_mn.setAttributes(["Magnetic North", "Norte Magnético"])
        pr.addFeature(feat_mn)
        
        # Arrowhead Magnetic North (left/right)
        feat_mn_l = QgsFeature()
        feat_mn_l.setGeometry(QgsGeometry.fromPolylineXY([mn_tip, get_offset_point(dec - 10, radius_m * 1.0)]))
        feat_mn_l.setAttributes(["Magnetic North", "Seta NM"])
        pr.addFeature(feat_mn_l)
        
        feat_mn_r = QgsFeature()
        feat_mn_r.setGeometry(QgsGeometry.fromPolylineXY([mn_tip, get_offset_point(dec + 10, radius_m * 1.0)]))
        feat_mn_r.setAttributes(["Magnetic North", "Seta NM"])
        pr.addFeature(feat_mn_r)
        
        # 4. Cardinal ticks (East, South, West)
        cardinal_angles = [90, 180, 270]
        cardinal_names = ["Leste", "Sul", "Oeste"]
        for angle, name in zip(cardinal_angles, cardinal_names):
            p_in = get_offset_point(angle, radius_m * 0.93)
            p_out = get_offset_point(angle, radius_m)
            feat_card = QgsFeature()
            feat_card.setGeometry(QgsGeometry.fromPolylineXY([p_in, p_out]))
            feat_card.setAttributes(["Ring", name])
            pr.addFeature(feat_card)
            
        vlayer.updateExtents()
        
        # Apply premium styling
        categories = []
        
        # Ring styling (Gray, thin)
        sym_ring = QgsSymbol.defaultSymbol(vlayer.geometryType())
        sym_ring.setColor(QColor("#94A3B8"))
        sym_ring.setWidth(0.6)
        categories.append(QgsRendererCategory("Ring", sym_ring, "Anel do Limite"))
        
        # True North styling (Blue, solid)
        sym_tn = QgsSymbol.defaultSymbol(vlayer.geometryType())
        sym_tn.setColor(QColor("#0284C7"))
        sym_tn.setWidth(1.1)
        categories.append(QgsRendererCategory("True North", sym_tn, "Norte Verdadeiro"))
        
        # Magnetic North styling (Red, thick)
        sym_mn = QgsSymbol.defaultSymbol(vlayer.geometryType())
        sym_mn.setColor(QColor("#EF4444"))
        sym_mn.setWidth(1.4)
        categories.append(QgsRendererCategory("Magnetic North", sym_mn, "Norte Magnético"))
        
        renderer = QgsCategorizedSymbolRenderer("type", categories)
        vlayer.setRenderer(renderer)
        
        # Add to project
        QgsProject.instance().addMapLayer(vlayer)
        self.iface.messageBar().pushMessage(
            "Camada Adicionada", "A camada vetorial com a Rosa dos Ventos foi criada no mapa.",
            level=3, duration=4
        )
