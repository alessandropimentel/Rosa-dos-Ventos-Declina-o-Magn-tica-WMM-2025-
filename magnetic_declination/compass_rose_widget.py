# -*- coding: utf-8 -*-
import math
from qgis.PyQt.QtCore import Qt, QPointF, QRectF, QSize, QRect
from qgis.PyQt.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPolygonF, QPainterPath
from qgis.PyQt.QtWidgets import QWidget

# PyQt5 / PyQt6 compatibility wrapper
try:
    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    ALIGN_LEFT = Qt.AlignmentFlag.AlignLeft
except AttributeError:
    ALIGN_CENTER = Qt.AlignCenter
    ALIGN_LEFT = Qt.AlignLeft

try:
    ANTIALIASING = QPainter.RenderHint.Antialiasing
    TEXT_ANTIALIASING = QPainter.RenderHint.TextAntialiasing
except AttributeError:
    ANTIALIASING = QPainter.Antialiasing
    TEXT_ANTIALIASING = QPainter.TextAntialiasing


class CompassRoseWidget(QWidget):
    """Custom widget that renders 6 distinct professional styles of Compass Roses.
    Shares the rendering logic between paintEvent and SVG/PNG exports.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.declination = 0.0     # Degrees (East positive, West negative)
        self.inclination = 0.0     # Dip angle in degrees
        self.intensity = 0.0       # Field intensity in nT
        self.dark_mode = True
        self.show_details = True
        self.style = "Clássico Cartográfico"  # Default style
        
        self.setMinimumSize(QSize(280, 280))

    def set_magnetic_data(self, declination: float, inclination: float, intensity: float) -> None:
        self.declination = declination
        self.inclination = inclination
        self.intensity = intensity
        self.update()

    def set_dark_mode(self, enabled: bool) -> None:
        self.dark_mode = enabled
        self.update()

    def set_show_details(self, enabled: bool) -> None:
        self.show_details = enabled
        self.update()

    def set_style(self, style_name: str) -> None:
        self.style = style_name
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(ANTIALIASING)
        painter.setRenderHint(TEXT_ANTIALIASING)
        self.render_rose(painter, self.width(), self.height())
        painter.end()

    def polar_to_cartesian(self, cx: float, cy: float, r: float, angle_deg: float) -> QPointF:
        """Helper to convert polar coordinates to Cartesian relative to center.
        0 degrees points straight UP (North).
        """
        angle_rad = math.radians(angle_deg - 90)
        return QPointF(cx + r * math.cos(angle_rad), cy + r * math.sin(angle_rad))

    def render_rose(self, painter: QPainter, width: int, height: int) -> None:
        cx = width / 2.0
        cy_offset = 15 if self.show_details else 0
        cy = (height / 2.0) - cy_offset
        
        margin = 35
        r_outer = min(cx, cy) - margin
        if r_outer < 50:
            r_outer = 50

        # Styles dispatch
        if self.style == "Clássico Cartográfico":
            self.draw_classic(painter, cx, cy, r_outer, width, height)
        elif self.style == "Moderno Minimalista":
            self.draw_minimalist(painter, cx, cy, r_outer, width, height)
        elif self.style == "Militar Tático":
            self.draw_military(painter, cx, cy, r_outer, width, height)
        elif self.style == "Tecnológico Digital":
            self.draw_technological(painter, cx, cy, r_outer, width, height)
        elif self.style == "Vintage / Antigo":
            self.draw_vintage(painter, cx, cy, r_outer, width, height)
        elif self.style == "Náutico Premium":
            self.draw_nautical(painter, cx, cy, r_outer, width, height)
        elif self.style == "Diagrama Técnico":
            self.draw_diagram(painter, cx, cy, r_outer, width, height)

    # --------------------------------------------------------------------------
    # MODEL 1: CLÁSSICO CARTOGRÁFICO (Traditional map styling)
    # --------------------------------------------------------------------------
    def draw_classic(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        if self.dark_mode:
            bg_color, ring_color, text_color = QColor("#121824"), QColor("#2A3547"), QColor("#E2E8F0")
            n_text_color, true_north_color, mag_arc_color = QColor("#38BDF8"), QColor("#38BDF8"), QColor("#F59E0B")
            star_p_light, star_p_dark = QColor("#E2E8F0"), QColor("#64748B")
            star_s_light, star_s_dark = QColor("#94A3B8"), QColor("#475569")
        else:
            bg_color, ring_color, text_color = QColor("#F4EFE6"), QColor("#A79983"), QColor("#1C1917")
            n_text_color, true_north_color, mag_arc_color = QColor("#0284C7"), QColor("#0284C7"), QColor("#D97706")
            star_p_light, star_p_dark = QColor("#F5F5F4"), QColor("#78716C")
            star_s_light, star_s_dark = QColor("#D6D3D1"), QColor("#44403C")
            
        needle_mag_light, needle_mag_dark = QColor("#EF4444"), QColor("#B91C1C")
        needle_tail_light, needle_tail_dark = QColor("#CBD5E1"), QColor("#64748B")

        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Outer Rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(ring_color, 2))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.setPen(QPen(ring_color, 0.75, Qt.PenStyle.DashLine))
        painter.drawEllipse(QPointF(cx, cy), r * 0.92, r * 0.92)

        # Ticks and Degrees (Classic)
        for deg in range(360):
            if deg % 10 == 0:
                p_out = self.polar_to_cartesian(cx, cy, r, deg)
                p_in = self.polar_to_cartesian(cx, cy, r - r * 0.05, deg)
                painter.setPen(QPen(ring_color, 1.5))
                painter.drawLine(p_out, p_in)
                
                # Degree Labels (Every 30 degrees)
                if deg % 30 == 0:
                    p_text = self.polar_to_cartesian(cx, cy, r + 12, deg)
                    painter.setPen(QPen(text_color))
                    font = QFont("Georgia", int(r * 0.05))
                    painter.setFont(font)
                    
                    painter.save()
                    painter.translate(p_text.x(), p_text.y())
                    painter.rotate(deg)
                    painter.drawText(QRect(-15, -7, 30, 14), ALIGN_CENTER, str(deg))
                    painter.restore()

        # 8-Point Star
        r_p, r_s, r_i = r * 0.75, r * 0.48, r * 0.18
        for angle in [45, 135, 225, 315]: # Secondary
            tip = self.polar_to_cartesian(cx, cy, r_s, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 22.5)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 22.5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(star_s_light))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(star_s_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))
            
        for angle in [0, 90, 180, 270]: # Primary
            tip = self.polar_to_cartesian(cx, cy, r_p, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 22.5)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 22.5)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(star_p_light))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(star_p_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Cardinal Text
        cardinals = [(0, "N"), (90, "L"), (180, "S"), (270, "O")]
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r_p * 0.72, angle)
            font = QFont("Georgia", int(r * 0.085))
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QPen(n_text_color if txt == "N" else text_color))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line
        painter.setPen(QPen(true_north_color, 1.5))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.90, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        painter.setBrush(QBrush(true_north_color))
        painter.drawEllipse(p_tn, 3, 3)
        
        font_nv = QFont("Georgia", int(r * 0.045))
        font_nv.setBold(True)
        painter.setFont(font_nv)
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 20), 50, 16), ALIGN_CENTER, "N.V.")

        # Declination Arc
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(mag_arc_color, 1.5, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.35
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Magnetic Needle
        dec_angle = self.declination
        r_needle = r * 0.85
        r_needle_w = r * 0.07
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle, dec_angle + 180)
        p_side_r = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle + 90)
        p_side_l = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle - 90)

        # Draw North Needle Half
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(needle_mag_light))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_r]))
        painter.setBrush(QBrush(needle_mag_dark))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_l]))
        # Draw South Needle Half
        painter.setBrush(QBrush(needle_tail_light))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_r]))
        painter.setBrush(QBrush(needle_tail_dark))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_l]))

        # Pivot Circle
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(ring_color, 1.5))
        painter.drawEllipse(QPointF(cx, cy), 6, 6)
        painter.setBrush(QBrush(mag_arc_color if abs(self.declination) > 0 else ring_color))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 15, dec_angle)
        font_nm = QFont("Georgia", int(r * 0.05))
        font_nm.setBold(True)
        painter.setFont(font_nm)
        painter.setPen(QPen(needle_mag_light))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, text_color, w, h, r)

    # --------------------------------------------------------------------------
    # MODEL 2: MODERNO MINIMALISTA (Ultra-clean, thin lines, crosshair axes)
    # --------------------------------------------------------------------------
    def draw_minimalist(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        if self.dark_mode:
            bg_color, stroke_color, text_color = QColor("#0F172A"), QColor("#334155"), QColor("#94A3B8")
            n_text_color, true_north_color, mag_arc_color = QColor("#38BDF8"), QColor("#38BDF8"), QColor("#F59E0B")
        else:
            bg_color, stroke_color, text_color = QColor("#FAFAFA"), QColor("#E2E8F0"), QColor("#64748B")
            n_text_color, true_north_color, mag_arc_color = QColor("#0284C7"), QColor("#0284C7"), QColor("#D97706")
            
        needle_n_color, needle_s_color = QColor("#EF4444"), QColor("#64748B")

        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Thin outer circle
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(stroke_color, 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)

        # Crosshairs
        painter.setPen(QPen(stroke_color, 0.75))
        painter.drawLine(QPointF(cx - r * 0.9, cy), QPointF(cx + r * 0.9, cy))
        painter.drawLine(QPointF(cx, cy - r * 0.9), QPointF(cx, cy + r * 0.9))

        # Thin ticks
        for deg in [30, 60, 120, 150, 210, 240, 300, 330]:
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r - r * 0.03, deg)
            painter.drawLine(p_out, p_in)

        # Cardinal Text
        cardinals = [(0, "N"), (90, "L"), (180, "S"), (270, "O")]
        font = QFont("Arial", int(r * 0.075))
        painter.setFont(font)
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r * 0.8, angle)
            painter.setPen(QPen(n_text_color if txt == "N" else text_color))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line (Thin Blue with Dot)
        painter.setPen(QPen(true_north_color, 1.25))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.92, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        painter.setBrush(QBrush(true_north_color))
        painter.drawEllipse(p_tn, 3, 3)
        
        font_nv = QFont("Arial", int(r * 0.045))
        painter.setFont(font_nv)
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 20), 50, 16), ALIGN_CENTER, "N.V.")

        # Arc
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(mag_arc_color, 1, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.45
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Thin Magnetic Needle
        dec_angle = self.declination
        r_needle = r * 0.88
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle, dec_angle + 180)
        
        painter.setPen(QPen(needle_n_color, 2))
        painter.drawLine(QPointF(cx, cy), p_needle_n)
        painter.setBrush(QBrush(needle_n_color))
        painter.drawEllipse(p_needle_n, 3, 3)

        painter.setPen(QPen(needle_s_color, 1.5))
        painter.drawLine(QPointF(cx, cy), p_needle_s)
        painter.setBrush(QBrush(needle_s_color))
        painter.drawEllipse(p_needle_s, 2, 2)

        # Center Pivot Dot
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(stroke_color))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 14, dec_angle)
        font_nm = QFont("Arial", int(r * 0.045))
        font_nm.setBold(True)
        painter.setFont(font_nm)
        painter.setPen(QPen(needle_n_color))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, text_color, w, h, r, font_family="Arial")

    # --------------------------------------------------------------------------
    # MODEL 3: MILITAR TÁTICO (Olive/Dark, heavy protractor scale, green reticle)
    # --------------------------------------------------------------------------
    def draw_military(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        bg_color = QColor("#141A13")  # Stealth dark olive/black
        reticle_color = QColor("#3D523C") # Subdued olive green
        glow_green = QColor("#22C55E")   # Bright tactical green
        dim_green = QColor("#166534")    # Dark tactical green
        needle_color = QColor("#EF4444")  # Red for target
        
        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Reticle concentric circles
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(reticle_color, 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawEllipse(QPointF(cx, cy), r * 0.8, r * 0.8)
        painter.drawEllipse(QPointF(cx, cy), r * 0.3, r * 0.3)

        # Fine protractor lines
        painter.setPen(QPen(reticle_color, 0.5))
        for deg in range(0, 360, 5):
            is_major = (deg % 30 == 0)
            len_tick = r * 0.06 if is_major else r * 0.03
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r - len_tick, deg)
            painter.drawLine(p_out, p_in)

            # Degree digits
            if is_major:
                p_text = self.polar_to_cartesian(cx, cy, r - r * 0.12, deg)
                painter.setPen(QPen(reticle_color))
                painter.setFont(QFont("Consolas", int(r * 0.045)))
                painter.save()
                painter.translate(p_text.x(), p_text.y())
                painter.rotate(deg)
                painter.drawText(QRect(-15, -7, 30, 14), ALIGN_CENTER, str(deg))
                painter.restore()

        # Crosshairs extending out
        painter.setPen(QPen(reticle_color, 1.5))
        painter.drawLine(QPointF(cx - r * 1.05, cy), QPointF(cx - r * 0.8, cy))
        painter.drawLine(QPointF(cx + r * 0.8, cy), QPointF(cx + r * 1.05, cy))
        painter.drawLine(QPointF(cx, cy - r * 1.05), QPointF(cx, cy - r * 0.8))
        painter.drawLine(QPointF(cx, cy + r * 0.8), QPointF(cx, cy + r * 1.05))

        # Heavy military block arrow pointing North
        painter.setPen(QPen(glow_green, 1.5))
        painter.setBrush(QBrush(dim_green))
        poly_n_arrow = QPolygonF([
            QPointF(cx, cy - r * 0.72),
            QPointF(cx + r * 0.12, cy - r * 0.48),
            QPointF(cx + r * 0.05, cy - r * 0.48),
            QPointF(cx + r * 0.05, cy - r * 0.32),
            QPointF(cx - r * 0.05, cy - r * 0.32),
            QPointF(cx - r * 0.05, cy - r * 0.48),
            QPointF(cx - r * 0.12, cy - r * 0.48)
        ])
        painter.drawPolygon(poly_n_arrow)

        # Cardinal Text labels
        cardinals = [(0, "N"), (90, "E"), (180, "S"), (270, "W")]
        painter.setFont(QFont("Consolas", int(r * 0.075), QFont.Weight.Bold))
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r * 0.60 if txt == "N" else r * 0.68, angle)
            painter.setPen(QPen(glow_green if txt == "N" else reticle_color))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line (Subdued dashed line)
        painter.setPen(QPen(glow_green, 1.25, Qt.PenStyle.DashLine))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.95, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        
        painter.setFont(QFont("Consolas", int(r * 0.045), QFont.Weight.Bold))
        painter.setPen(QPen(glow_green))
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 20), 50, 16), ALIGN_CENTER, "N.V.")

        # Declination Arc (Subdued red)
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(needle_color, 1.5, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.40
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Heavy target Needle
        dec_angle = self.declination
        r_needle = r * 0.90
        r_needle_w = r * 0.08
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle * 0.6, dec_angle + 180)
        p_side_r = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle + 90)
        p_side_l = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle - 90)

        # Heavy military needle polygon
        painter.setPen(QPen(needle_color, 1.5))
        painter.setBrush(QBrush(QColor("#7F1D1D"))) # Dark red fill
        poly_needle = QPolygonF([p_needle_n, p_side_r, p_needle_s, p_side_l])
        painter.drawPolygon(poly_needle)
        
        # Draw central targeting circle
        painter.setPen(QPen(needle_color, 1.5))
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        painter.drawEllipse(QPointF(cx, cy), 12, 12)
        painter.drawLine(QPointF(cx - 16, cy), QPointF(cx + 16, cy))
        painter.drawLine(QPointF(cx, cy - 16), QPointF(cx, cy + 16))

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 15, dec_angle)
        painter.setFont(QFont("Consolas", int(r * 0.05), QFont.Weight.Bold))
        painter.setPen(QPen(needle_color))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, glow_green, w, h, r, font_family="Consolas")

    # --------------------------------------------------------------------------
    # MODEL 4: TECNOLÓGICO DIGITAL (Concentric glowing rings, sci-fi vector grid)
    # --------------------------------------------------------------------------
    def draw_technological(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        bg_color = QColor("#080D1A")        # Deep digital navy
        cyber_cyan = QColor("#06B6D4")      # Glowing neon cyan
        cyber_dim_cyan = QColor("#083344")  # Subdued cyan
        cyber_orange = QColor("#F97316")    # Neon orange
        cyber_white = QColor("#F8FAFC")     # Clean white

        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Outer grid rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(cyber_dim_cyan, 1))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawEllipse(QPointF(cx, cy), r * 0.70, r * 0.70)
        painter.drawEllipse(QPointF(cx, cy), r * 0.40, r * 0.40)
        
        painter.setPen(QPen(cyber_cyan, 1.5))
        painter.drawEllipse(QPointF(cx, cy), r * 0.95, r * 0.95)

        # Concentric grid rays
        painter.setPen(QPen(cyber_dim_cyan, 0.5))
        for deg in range(0, 360, 15):
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r * 0.4, deg)
            painter.drawLine(p_out, p_in)

        # Digital tick marks
        painter.setPen(QPen(cyber_cyan, 1.5))
        for deg in range(0, 360, 30):
            p_out = self.polar_to_cartesian(cx, cy, r * 0.98, deg)
            p_in = self.polar_to_cartesian(cx, cy, r * 0.92, deg)
            painter.drawLine(p_out, p_in)
            
            # Numeric degrees
            p_text = self.polar_to_cartesian(cx, cy, r + 15, deg)
            painter.setFont(QFont("Consolas", int(r * 0.045)))
            painter.setPen(QPen(cyber_cyan))
            painter.save()
            painter.translate(p_text.x(), p_text.y())
            painter.rotate(deg)
            painter.drawText(QRect(-15, -7, 30, 14), ALIGN_CENTER, str(deg))
            painter.restore()

        # Geometric futuristic star (hollow line star)
        painter.setPen(QPen(cyber_cyan, 1))
        painter.setBrush(QBrush(QColor(8, 51, 68, 80)))  # Semi-transparent cyber fill
        path_star = QPainterPath()
        path_star.moveTo(self.polar_to_cartesian(cx, cy, r * 0.65, 0))
        for deg in [45, 90, 135, 180, 225, 270, 315]:
            r_val = r * 0.3 if deg % 90 != 0 else r * 0.65
            path_star.lineTo(self.polar_to_cartesian(cx, cy, r_val, deg))
        path_star.closeSubpath()
        painter.drawPath(path_star)

        # Cardinal Text labels
        cardinals = [(0, "N"), (90, "L"), (180, "S"), (270, "O")]
        painter.setFont(QFont("Consolas", int(r * 0.08), QFont.Weight.Bold))
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r * 0.50, angle)
            painter.setPen(QPen(cyber_white if txt == "N" else cyber_cyan))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line (glowing cyan)
        painter.setPen(QPen(cyber_white, 2))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.90, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        painter.setBrush(QBrush(cyber_white))
        painter.drawEllipse(p_tn, 4, 4)
        
        painter.setFont(QFont("Consolas", int(r * 0.045), QFont.Weight.Bold))
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 22), 50, 16), ALIGN_CENTER, "N.V.")

        # Arc
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(cyber_orange, 2, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.35
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Sci-fi neon Needle (Orange)
        dec_angle = self.declination
        r_needle = r * 0.88
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle * 0.5, dec_angle + 180)
        
        # Dual-spine needle lines
        p_side_l = self.polar_to_cartesian(cx, cy, r * 0.06, dec_angle - 90)
        p_side_r = self.polar_to_cartesian(cx, cy, r * 0.06, dec_angle + 90)
        
        painter.setPen(QPen(cyber_orange, 1.5))
        painter.setBrush(QBrush(QColor(249, 115, 22, 60)))
        poly_n = QPolygonF([QPointF(cx, cy), p_side_l, p_needle_n, p_side_r])
        painter.drawPolygon(poly_n)

        painter.setPen(QPen(cyber_dim_cyan, 1))
        painter.setBrush(QBrush(QColor(8, 51, 68, 60)))
        poly_s = QPolygonF([QPointF(cx, cy), p_side_l, p_needle_s, p_side_r])
        painter.drawPolygon(poly_s)

        # Center tech ring
        painter.setPen(QPen(cyber_cyan, 1.5))
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)
        painter.setBrush(QBrush(cyber_orange))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 15, dec_angle)
        painter.setFont(QFont("Consolas", int(r * 0.05), QFont.Weight.Bold))
        painter.setPen(QPen(cyber_orange))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, cyber_cyan, w, h, r, font_family="Consolas")

    # --------------------------------------------------------------------------
    # MODEL 5: VINTAGE / ANTIGO (Aged parchment, gold/bronze 16-point star, Fleur-de-Lis)
    # --------------------------------------------------------------------------
    def draw_vintage(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        # Fixed theme: always vintage parchment tones
        bg_color = QColor("#EADEC9")
        line_color = QColor("#5A3E25")       # Sepia/Dark brown
        gold_color = QColor("#C29B38")
        dark_gold_color = QColor("#916E1D")
        needle_mag = QColor("#A82A2A")       # Madder Red
        needle_mag_dark = QColor("#6E1616")
        
        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Heavy double rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(line_color, 2))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.drawEllipse(QPointF(cx, cy), r * 0.96, r * 0.96)
        painter.setPen(QPen(line_color, 0.75))
        painter.drawEllipse(QPointF(cx, cy), r * 0.88, r * 0.88)

        # Vintage Roman Ticks & Ticks every degree
        painter.setPen(QPen(line_color, 0.5))
        for deg in range(360):
            is_major = (deg % 30 == 0)
            is_medium = (deg % 10 == 0) and not is_major
            
            if is_major:
                len_tick = r * 0.08
                painter.setPen(QPen(line_color, 1.5))
            elif is_medium:
                len_tick = r * 0.05
                painter.setPen(QPen(line_color, 1))
            else:
                len_tick = r * 0.02
                painter.setPen(QPen(line_color, 0.5))
                
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r - len_tick, deg)
            painter.drawLine(p_out, p_in)

            # Degree Labels (Roman numerals or vintage serifs every 30)
            if is_major:
                p_text = self.polar_to_cartesian(cx, cy, r - r * 0.16, deg)
                painter.setPen(QPen(line_color))
                painter.setFont(QFont("Georgia", int(r * 0.045), QFont.Weight.Bold))
                
                # Roman representations
                romans = {0: "N", 30: "I", 60: "II", 90: "III", 120: "IV", 150: "V", 
                          180: "VI", 210: "VII", 240: "VIII", 270: "IX", 300: "X", 330: "XI"}
                txt = romans[deg]
                
                painter.save()
                painter.translate(p_text.x(), p_text.y())
                painter.rotate(deg)
                painter.drawText(QRect(-15, -7, 30, 14), ALIGN_CENTER, txt)
                painter.restore()

        # 16-Point Compass Star (Alternating sepia and gold)
        r_p = r * 0.76
        r_s = r * 0.50
        r_t = r * 0.35 # Tertiary points
        r_i = r * 0.16

        # Draw 8 tertiary points first
        tertiaries = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
        for angle in tertiaries:
            tip = self.polar_to_cartesian(cx, cy, r_t, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#C5A880"))) # Vintage light parchment shadow
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(QColor("#8C765C"))) # Dark parchment shadow
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Draw 4 secondary points
        for angle in [45, 135, 225, 315]:
            tip = self.polar_to_cartesian(cx, cy, r_s, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(gold_color))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(dark_gold_color))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Draw 4 primary points
        for angle in [0, 90, 180, 270]:
            if angle == 0:
                continue # Skip North to draw Fleur-de-lis on top
            tip = self.polar_to_cartesian(cx, cy, r_p, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(line_color))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(QColor("#A88C74")))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Draw Fleur-de-Lis at North (0°)
        painter.save()
        painter.translate(cx, cy)
        # Scale according to radius
        scale_f = r_p / 120.0
        painter.scale(scale_f, scale_f)
        
        # Left petal path
        path_l = QPainterPath()
        path_l.moveTo(0, 0)
        path_l.cubicTo(-10, -20, -25, -45, -25, -60)
        path_l.cubicTo(-25, -75, -12, -75, -8, -60)
        path_l.cubicTo(-5, -45, -2, -20, 0, 0)
        path_l.closeSubpath()
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(dark_gold_color))
        painter.drawPath(path_l)
        
        # Right petal path
        path_r = QPainterPath()
        path_r.moveTo(0, 0)
        path_r.cubicTo(10, -20, 25, -45, 25, -60)
        path_r.cubicTo(25, -75, 12, -75, 8, -60)
        path_r.cubicTo(5, -45, 2, -20, 0, 0)
        path_r.closeSubpath()
        painter.setBrush(QBrush(gold_color))
        painter.drawPath(path_r)
        
        # Center petal
        path_c_l = QPainterPath()
        path_c_l.moveTo(0, -96)
        path_c_l.cubicTo(-5, -75, -10, -45, 0, 0)
        path_c_l.closeSubpath()
        painter.setBrush(QBrush(line_color))
        painter.drawPath(path_c_l)
        
        path_c_r = QPainterPath()
        path_c_r.moveTo(0, -96)
        path_c_r.cubicTo(5, -75, 10, -45, 0, 0)
        path_c_r.closeSubpath()
        painter.setBrush(QBrush(gold_color))
        painter.drawPath(path_c_r)

        # Crossbar ring
        painter.setBrush(QBrush(line_color))
        painter.drawRect(-18, -15, 36, 6)
        
        painter.restore()

        # Cardinal text N, L, S, O in serif italics
        cardinals = [(90, "L"), (180, "S"), (270, "O")]
        painter.setFont(QFont("Times New Roman", int(r * 0.085), QFont.Weight.Bold, italic=True))
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r_p * 0.72, angle)
            painter.setPen(QPen(line_color))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line (thin vintage solid)
        painter.setPen(QPen(line_color, 1.25))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.90, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        painter.setFont(QFont("Times New Roman", int(r * 0.05), QFont.Weight.Bold, italic=True))
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 20), 50, 16), ALIGN_CENTER, "N.V.")

        # Arc (Subdued vintage color)
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(needle_mag, 1.5, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.38
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Vintage scroll Needle (Bronze/Gold + Madder Red)
        dec_angle = self.declination
        r_needle = r * 0.85
        r_needle_w = r * 0.065
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle, dec_angle + 180)
        p_side_r = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle + 90)
        p_side_l = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle - 90)

        painter.setPen(Qt.PenStyle.NoPen)
        # Red magnetized half
        painter.setBrush(QBrush(needle_mag))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_r]))
        painter.setBrush(QBrush(needle_mag_dark))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_l]))
        # Bronze tail half
        painter.setBrush(QBrush(gold_color))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_r]))
        painter.setBrush(QBrush(dark_gold_color))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_l]))

        # Center Pivot ornament
        painter.setPen(QPen(line_color, 1))
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(QPointF(cx, cy), 8, 8)
        painter.setBrush(QBrush(line_color))
        painter.drawEllipse(QPointF(cx, cy), 4, 4)

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 15, dec_angle)
        painter.setFont(QFont("Times New Roman", int(r * 0.05), QFont.Weight.Bold, italic=True))
        painter.setPen(QPen(needle_mag))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, line_color, w, h, r, font_family="Times New Roman", italic=True)

    # --------------------------------------------------------------------------
    # MODEL 6: NÁUTICO PREMIUM (Deep Navy/Gold marine dial, 16-point nautical star)
    # --------------------------------------------------------------------------
    def draw_nautical(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        bg_color = QColor("#0B132B")        # Maritime deep navy
        gold_color = QColor("#E0A96D")      # Metallic bronze gold
        navy_dark = QColor("#1C2541")       # Shading navy
        marine_white = QColor("#F8FAFC")    # White sail
        mag_red = QColor("#E11D48")         # Warning/Magnetic Red

        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)

        # Heavy double golden rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(gold_color, 2.5))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        painter.setPen(QPen(gold_color, 1))
        painter.drawEllipse(QPointF(cx, cy), r * 0.94, r * 0.94)
        
        # Alternating black/white wedges along the outer ring (marine compass card)
        painter.setPen(QPen(gold_color, 0.5))
        for i in range(72):
            deg = i * 5
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r * 0.94, deg)
            painter.drawLine(p_out, p_in)

        # Ticks and Degrees (Gold)
        for deg in range(0, 360, 30):
            p_text = self.polar_to_cartesian(cx, cy, r + 13, deg)
            painter.setPen(QPen(gold_color))
            painter.setFont(QFont("Georgia", int(r * 0.045)))
            painter.save()
            painter.translate(p_text.x(), p_text.y())
            painter.rotate(deg)
            painter.drawText(QRect(-15, -7, 30, 14), ALIGN_CENTER, str(deg))
            painter.restore()

        # 16-Point Nautical Star (Navy & White shaded wedges)
        r_p = r * 0.76
        r_s = r * 0.50
        r_t = r * 0.35
        r_i = r * 0.16

        # Draw 8 tertiary points
        tertiaries = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
        for angle in tertiaries:
            tip = self.polar_to_cartesian(cx, cy, r_t, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(QPen(gold_color, 0.3))
            painter.setBrush(QBrush(navy_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(bg_color))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Draw 4 secondary points
        for angle in [45, 135, 225, 315]:
            tip = self.polar_to_cartesian(cx, cy, r_s, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(QPen(gold_color, 0.4))
            painter.setBrush(QBrush(marine_white))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(navy_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Draw 4 primary points
        for angle in [0, 90, 180, 270]:
            tip = self.polar_to_cartesian(cx, cy, r_p, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(QPen(gold_color, 0.5))
            painter.setBrush(QBrush(marine_white))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(navy_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))

        # Cardinal Text labels
        cardinals = [(0, "N"), (90, "L"), (180, "S"), (270, "O")]
        painter.setFont(QFont("Georgia", int(r * 0.085), QFont.Weight.Bold))
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r_p * 0.72, angle)
            painter.setPen(QPen(gold_color if txt != "N" else marine_white))
            painter.drawText(QRect(int(p_card.x() - 15), int(p_card.y() - 15), 30, 30), ALIGN_CENTER, txt)

        # True North Line (Heavy gold line with star anchor)
        painter.setPen(QPen(gold_color, 2))
        p_tn = self.polar_to_cartesian(cx, cy, r * 0.90, 0)
        painter.drawLine(QPointF(cx, cy), p_tn)
        
        # Gold Star symbol at True North tip
        painter.setBrush(QBrush(gold_color))
        painter.drawEllipse(p_tn, 4, 4)
        
        painter.setFont(QFont("Georgia", int(r * 0.045), QFont.Weight.Bold))
        painter.setPen(QPen(gold_color))
        painter.drawText(QRect(int(p_tn.x() - 25), int(p_tn.y() - 22), 50, 16), ALIGN_CENTER, "N.V.")

        # Arc (Subdued gold dotted)
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(gold_color, 1.5, Qt.PenStyle.DotLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 0.38
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))

        # Marine Needle (Gold + Red)
        dec_angle = self.declination
        r_needle = r * 0.86
        r_needle_w = r * 0.075
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle, dec_angle + 180)
        p_side_r = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle + 90)
        p_side_l = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle - 90)

        # Draw red magnetized end
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(mag_red))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_r]))
        painter.setBrush(QBrush(QColor("#9F1239"))) # Dark Red
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_n, p_side_l]))
        # Draw gold tail end
        painter.setBrush(QBrush(gold_color))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_r]))
        painter.setBrush(QBrush(navy_dark))
        painter.drawPolygon(QPolygonF([QPointF(cx, cy), p_needle_s, p_side_l]))

        # Center Pivot circle
        painter.setPen(QPen(gold_color, 1.5))
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(QPointF(cx, cy), 7, 7)
        painter.setBrush(QBrush(gold_color))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)

        # N.M. Label
        p_nm = self.polar_to_cartesian(cx, cy, r_needle + 15, dec_angle)
        painter.setFont(QFont("Georgia", int(r * 0.05), QPointF(0,0), QFont.Weight.Bold))
        painter.setPen(QPen(mag_red))
        painter.save()
        painter.translate(p_nm.x(), p_nm.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-25, -12, 50, 24), ALIGN_CENTER, "N.M.")
        painter.restore()

        if self.show_details:
            self.draw_details_text(painter, gold_color, w, h, r, font_family="Georgia")

    # --------------------------------------------------------------------------
    # COMMON DRAWING UTILITIES
    # --------------------------------------------------------------------------
    def draw_details_text(self, painter: QPainter, color: QColor, w: int, h: int, r: float, 
                          font_family: str = "Consolas", italic: bool = False) -> None:
        """Helper to draw numerical data below the compass rose."""
        font = QFont(font_family, int(r * 0.045))
        font.setItalic(italic)
        if font.pointSize() < 7:
            font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QPen(color))
        
        sign = "+" if self.declination >= 0 else ""
        dir_letter = "E" if self.declination >= 0 else "W"
        decl_str = f"Declinação (D): {sign}{self.declination:.2f}° ({dir_letter})"
        inc_str = f"Inclinação (I): {self.inclination:.2f}°"
        int_str = f"Intensidade (F): {self.intensity:.0f} nT"
        
        y_text = h - 42
        painter.drawText(QRect(0, int(y_text), w, 14), ALIGN_CENTER, decl_str)
        painter.drawText(QRect(0, int(y_text + 14), w, 14), ALIGN_CENTER, inc_str)
        painter.drawText(QRect(0, int(y_text + 28), w, 14), ALIGN_CENTER, int_str)

    # --------------------------------------------------------------------------
    # MODEL 7: DIAGRAMA TÉCNICO (Textbook style, dashed refs, +D arc, dual-color needle)
    # --------------------------------------------------------------------------
    def draw_diagram(self, painter: QPainter, cx: float, cy: float, r: float, w: int, h: int) -> None:
        bg_color = QColor("#F8F9FA")
        line_color = QColor("#1E293B")
        text_color = QColor("#0F172A")
        
        # Star colors
        star_p_light, star_p_dark = QColor("#FFFFFF"), QColor("#1E293B")
        star_s_light, star_s_dark = QColor("#F1F5F9"), QColor("#475569")
        star_t_light, star_t_dark = QColor("#E2E8F0"), QColor("#64748B")
        
        # Needle colors (Shaded dark gray and white)
        needle_light, needle_dark = QColor("#FFFFFF"), QColor("#334155")
        
        # Background
        painter.fillRect(QRect(0, 0, w, h), bg_color)
        
        # Rings
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(line_color, 1.5))
        painter.drawEllipse(QPointF(cx, cy), r, r)
        
        # Inner fine ring
        painter.setPen(QPen(line_color, 0.75))
        painter.drawEllipse(QPointF(cx, cy), r * 0.95, r * 0.95)
        
        # Ticks around the ring
        for deg in range(360):
            is_major = (deg % 10 == 0)
            is_medium = (deg % 5 == 0) and not is_major
            len_tick = r * 0.04 if is_major else (r * 0.025 if is_medium else r * 0.012)
            painter.setPen(QPen(line_color, 1.0 if is_major else 0.5))
            
            p_out = self.polar_to_cartesian(cx, cy, r, deg)
            p_in = self.polar_to_cartesian(cx, cy, r - len_tick, deg)
            painter.drawLine(p_out, p_in)
            
        # Draw 16-point star
        r_p = r * 0.72
        r_s = r * 0.48
        r_t = r * 0.30
        r_i = r * 0.16
        
        # Tertiaries
        tertiaries = [22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5]
        for angle in tertiaries:
            tip = self.polar_to_cartesian(cx, cy, r_t, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(star_t_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(star_t_light))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))
            
        # Secondaries
        for angle in [45, 135, 225, 315]:
            tip = self.polar_to_cartesian(cx, cy, r_s, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(star_s_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(star_s_light))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))
            
        # Primaries
        for angle in [0, 90, 180, 270]:
            tip = self.polar_to_cartesian(cx, cy, r_p, angle)
            inner_cw = self.polar_to_cartesian(cx, cy, r_i, angle + 11.25)
            inner_ccw = self.polar_to_cartesian(cx, cy, r_i, angle - 11.25)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(star_p_dark))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_cw]))
            painter.setBrush(QBrush(star_p_light))
            painter.drawPolygon(QPolygonF([QPointF(cx, cy), tip, inner_ccw]))
            
        # Draw Cardinal Labels: N, NE, E, SE, S, SW, W, NW
        cardinals = [
            (0, "N"), (45, "NE"), (90, "E"), (135, "SE"),
            (180, "S"), (225, "SW"), (270, "W"), (315, "NW")
        ]
        font = QFont("Arial", int(r * 0.065))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(text_color))
        
        for angle, txt in cardinals:
            p_card = self.polar_to_cartesian(cx, cy, r * 0.84, angle)
            
            painter.save()
            painter.translate(p_card.x(), p_card.y())
            if angle % 90 != 0:
                painter.rotate(angle)
            rect = QRect(-20, -12, 40, 24)
            painter.drawText(rect, ALIGN_CENTER, txt)
            painter.restore()

        # Dashed line for True North (NORTE VERDADEIRO) going high up
        painter.setPen(QPen(line_color, 1.25, Qt.PenStyle.DashLine))
        y_top_limit = 50
        painter.drawLine(QPointF(cx, cy), QPointF(cx, y_top_limit))
        
        # Label "NORTE VERDADEIRO" above the line
        font_label = QFont("Arial", int(r * 0.045))
        font_label.setBold(True)
        painter.setFont(font_label)
        painter.setPen(QPen(text_color))
        painter.drawText(QRect(int(cx - 60), int(y_top_limit - 32), 120, 28), ALIGN_CENTER, "NORTE\nVERDADEIRO")

        # Dashed line for Magnetic North (NORTE MAGNÉTICO)
        dec_angle = self.declination
        p_nm_line = self.polar_to_cartesian(cx, cy, r * 1.35, dec_angle)
        painter.setPen(QPen(line_color, 1.25, Qt.PenStyle.DashLine))
        painter.drawLine(QPointF(cx, cy), p_nm_line)
        
        # Label "NORTE MAGNÉTICO" above the magnetic line
        painter.setPen(QPen(text_color))
        painter.save()
        painter.translate(p_nm_line.x(), p_nm_line.y())
        painter.rotate(dec_angle)
        painter.drawText(QRect(-60, -32, 120, 28), ALIGN_CENTER, "NORTE\nMAGNÉTICO")
        painter.restore()

        # Arc between True North (0°) and Magnetic North (dec_angle)
        if abs(self.declination) >= 0.1:
            painter.setPen(QPen(line_color, 1.0, Qt.PenStyle.SolidLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r_arc = r * 1.12
            painter.drawArc(QRectF(cx - r_arc, cy - r_arc, r_arc * 2, r_arc * 2), 90 * 16, int(self.declination * 16))
            
            # Label "+D" or "-D" at the midpoint of the arc
            mid_angle = dec_angle / 2.0
            p_mid = self.polar_to_cartesian(cx, cy, r * 1.20, mid_angle)
            
            # Format sign
            sign = "+" if self.declination >= 0 else ""
            label_d = f"{sign}D"
            
            painter.setFont(QFont("Arial", int(r * 0.05), QFont.Weight.Bold))
            painter.drawText(QRect(int(p_mid.x() - 25), int(p_mid.y() - 12), 50, 24), ALIGN_CENTER, label_d)

        # Draw the main technical pointer (needle) rotated by dec_angle
        # Shaded double wedge
        r_needle = r * 0.88
        r_needle_w = r * 0.075
        p_needle_n = self.polar_to_cartesian(cx, cy, r_needle, dec_angle)
        p_needle_s = self.polar_to_cartesian(cx, cy, r_needle * 0.9, dec_angle + 180)
        p_side_r = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle + 90)
        p_side_l = self.polar_to_cartesian(cx, cy, r_needle_w, dec_angle - 90)
        
        # Drawing the needle
        painter.setPen(QPen(line_color, 1.0))
        # Left half (CCW) -> White
        painter.setBrush(QBrush(needle_light))
        poly_l = QPolygonF([p_needle_n, p_side_l, p_needle_s])
        painter.drawPolygon(poly_l)
        
        # Right half (CW) -> Dark gray
        painter.setBrush(QBrush(needle_dark))
        poly_r = QPolygonF([p_needle_n, p_side_r, p_needle_s])
        painter.drawPolygon(poly_r)
        
        # Center pivot
        painter.setPen(QPen(line_color, 1.5))
        painter.setBrush(QBrush(bg_color))
        painter.drawEllipse(QPointF(cx, cy), 6, 6)
        painter.setBrush(QBrush(line_color))
        painter.drawEllipse(QPointF(cx, cy), 3, 3)

        if self.show_details:
            self.draw_details_text(painter, text_color, w, h, r, font_family="Arial")
