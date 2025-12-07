from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame, QProgressBar
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QLinearGradient, QPainterPath, QFont
import config
from utils import format_speed


class AreaGraph(QWidget):
    def __init__(self, use_secondary=False, max_points=60):
        super().__init__()
        self.max_points = max_points
        self.data = [0.0] * max_points
        self.secondary_data = [0.0] * max_points if use_secondary else None
        self.setFixedHeight(75)
        self.setStyleSheet("background: transparent;")

    def add_value(self, value, value2=None):
        self.data.append(float(value))
        self.data.pop(0)
        if self.secondary_data and value2 is not None:
            self.secondary_data.append(float(value2))
            self.secondary_data.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        theme = config.active_theme

        # Colores
        grid_c = QColor(theme['grid_line'])
        text_c = QColor(theme['text_dim'])
        col_prim = QColor(theme['accent_blue'])
        col_sec = QColor(theme['accent_red'])

        pen_grid = QPen(grid_c)
        pen_grid.setStyle(Qt.DotLine)
        painter.setPen(pen_grid)
        painter.drawLine(0, int(h / 2), w, int(h / 2))
        for i in range(1, 4):
            painter.drawLine(int(i * w / 4), 10, int(i * w / 4), h - 10)

        painter.setPen(text_c)
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.drawText(2, 10, "%")
        painter.drawText(w - 25, 10, "100")

        # Escala dinámica
        max_v = 1.0
        if self.data: max_v = max(max_v, max(self.data))
        if self.secondary_data: max_v = max(max_v, max(self.secondary_data))
        if max_v <= 100.0 and not self.secondary_data: max_v = 100.0

        if self.secondary_data:
            self.draw_single_graph(painter, self.secondary_data, col_sec, max_v)
        self.draw_single_graph(painter, self.data, col_prim, max_v)

    def draw_single_graph(self, painter, data_list, color, max_scale_val):
        w, h = self.width(), self.height()
        margin_top, margin_bottom = 15, 15
        draw_h = h - margin_top - margin_bottom
        path = QPainterPath()
        scale = draw_h / max_scale_val if max_scale_val > 0.001 else 0
        step_w = w / (self.max_points - 1) if self.max_points > 1 else 0

        path.moveTo(0, (margin_top + draw_h) - (data_list[0] * scale))
        for i, val in enumerate(data_list):
            path.lineTo(i * step_w, (margin_top + draw_h) - (val * scale))

        pen = QPen(color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)
        path.lineTo(w, margin_top + draw_h)
        path.lineTo(0, margin_top + draw_h)
        path.closeSubpath()
        grad = QLinearGradient(0, margin_top, 0, margin_top + draw_h)
        c1 = color
        c1.setAlpha(150)
        c2 = color
        c2.setAlpha(20)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)


class HardwareRow(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setObjectName("Card")
        self.setFixedHeight(95)
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setSpacing(15)

        # Columna de texto
        text_cont = QWidget()
        text_cont.setStyleSheet("background: transparent;")
        text_cont.setFixedWidth(85)

        t_layout = QVBoxLayout(text_cont)
        t_layout.setContentsMargins(0, 10, 0, 10)
        t_layout.setSpacing(2)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("Title")

        # Etiqueta Extra (Ghz, GB, etc)
        self.lbl_extra = QLabel("")
        self.lbl_extra.setStyleSheet(f"color: {config.active_theme['text_dim']}; font-size: 10px; font-weight: 500;")
        self.lbl_extra.setAlignment(Qt.AlignLeft)

        self.lbl_val = QLabel("0%")
        self.lbl_val.setObjectName("Value")

        t_layout.addWidget(self.lbl_title)
        t_layout.addWidget(self.lbl_extra)
        t_layout.addWidget(self.lbl_val)
        t_layout.addStretch()

        self.graph = AreaGraph(use_secondary=False)
        layout.addWidget(text_cont)
        layout.addWidget(self.graph, stretch=1)
        self.setLayout(layout)

    def update_val(self, val, extra_text=""):
        self.lbl_val.setText(f"{int(val)}%")
        self.lbl_extra.setText(extra_text)
        self.graph.add_value(val)


class NetworkRow(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Card")
        self.setFixedHeight(110)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 12, 15, 5)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(10)

        # Título principal
        header.addWidget(QLabel("NETWORK", objectName="Title"))

        # Nombre de la interfaz
        self.lbl_iface = QLabel("")
        self.lbl_iface.setStyleSheet(
            f"color: {config.active_theme['accent_blue']}; font-size: 11px; font-weight: bold; padding-top: 2px; margin-left: 22px;")
        header.addWidget(self.lbl_iface)

        header.addStretch()

        self.lbl_info = QLabel()
        self.lbl_info.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header.addWidget(self.lbl_info)

        self.g = AreaGraph(use_secondary=True)
        layout.addLayout(header)
        layout.addStretch()
        layout.addWidget(self.g)
        self.setLayout(layout)
        self.use_bits = False

    def update_style_imm(self):
        self.update_net(0, 0, "", refresh_only=True)

    def set_unit(self, use_bits):
        self.use_bits = use_bits

    def update_net(self, d, u, iface_name="", refresh_only=False):
        theme = config.active_theme
        c_d = theme['accent_blue']
        c_u = theme['accent_red']

        str_d = format_speed(d, self.use_bits)
        str_u = format_speed(u, self.use_bits)

        self.lbl_info.setText(f"""
            <span style='color:{c_d}; font-weight:bold'>▼ {str_d}</span> &nbsp;&nbsp; 
            <span style='color:{c_u}; font-weight:bold'>▲ {str_u}</span>
        """)

        if iface_name:
            self.lbl_iface.setText(iface_name.upper())

        if not refresh_only:
            self.g.add_value(d, u)


class DiskRow(QWidget):
    def __init__(self, letter):
        super().__init__()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)

        self.lbl_name = QLabel(f"{letter}")
        self.lbl_name.setFixedWidth(35)
        f = QFont("Segoe UI", 15)
        f.setBold(True)
        self.lbl_name.setFont(f)

        self.bar = QProgressBar()
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.lbl_pct = QLabel("0%")
        self.lbl_pct.setFixedWidth(40)
        self.lbl_pct.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_read_v = QLabel("▼ 0 KB/s")
        self.lbl_read_v.setFixedWidth(85)
        self.lbl_read_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.lbl_write_v = QLabel("▲ 0 KB/s")
        self.lbl_write_v.setFixedWidth(85)
        self.lbl_write_v.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.bar, stretch=1)
        layout.addWidget(self.lbl_pct)
        layout.addWidget(self.lbl_read_v)
        layout.addWidget(self.lbl_write_v)
        self.setLayout(layout)
        self.use_bits = False
        self.refresh_theme_colors()

    def refresh_theme_colors(self):
        theme = config.active_theme
        self.lbl_name.setStyleSheet(f"color: {theme['text_main']};")
        self.lbl_pct.setStyleSheet(f"color: {theme['text_main']}; font-weight: bold; font-size: 13px;")
        self.lbl_read_v.setStyleSheet(
            f"color: {theme['accent_blue']}; font-size: 12px; font-family: 'Consolas', monospace; font-weight: bold;")
        self.lbl_write_v.setStyleSheet(
            f"color: {theme['accent_red']}; font-size: 12px; font-family: 'Consolas', monospace; font-weight: bold;")

    def set_unit(self, use_bits):
        self.use_bits = use_bits

    def update_state(self, percent, read_mb, write_mb):
        theme = config.active_theme
        self.bar.setValue(int(percent))
        self.lbl_pct.setText(f"{int(percent)}%")

        c_fill = theme['accent_red'] if percent > 90 else theme['accent_blue']
        self.bar.setStyleSheet(f"""
            QProgressBar {{ background-color: {theme['bar_bg']}; border-radius: 4px; }}
            QProgressBar::chunk {{ background-color: {c_fill}; border-radius: 4px; }}
        """)

        self.lbl_read_v.setText(f"▼ {format_speed(read_mb, self.use_bits)}")
        self.lbl_write_v.setText(f"▲ {format_speed(write_mb, self.use_bits)}")