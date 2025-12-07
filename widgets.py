from PySide6.QtWidgets import (QWidget, QLabel, QHBoxLayout, QVBoxLayout, QFrame,
                               QProgressBar, QTreeWidget, QTreeWidgetItem,
                               QHeaderView, QFileIconProvider, QMenu, QMessageBox,
                               QAbstractItemView)
from PySide6.QtCore import Qt, QFileInfo, QSize, QPoint
from PySide6.QtGui import (QPainter, QPen, QColor, QBrush, QLinearGradient,
                           QPainterPath, QFont, QIcon, QAction, QCursor)
import config
from utils import format_speed, format_decimal
import psutil


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
        grid_c = QColor(theme['grid_line'])
        text_c = QColor(theme['text_dim'])
        col_prim = QColor(theme['accent_blue'])
        col_sec = QColor(theme['accent_red'])

        pen_grid = QPen(grid_c)
        pen_grid.setStyle(Qt.DotLine)
        painter.setPen(pen_grid)
        painter.drawLine(0, int(h / 2), w, int(h / 2))
        for i in range(1, 4): painter.drawLine(int(i * w / 4), 10, int(i * w / 4), h - 10)

        painter.setPen(text_c)
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.drawText(2, 10, "%")
        painter.drawText(w - 25, 10, "100")

        max_v = 1.0
        if self.data: max_v = max(max_v, max(self.data))
        if self.secondary_data: max_v = max(max_v, max(self.secondary_data))
        if max_v <= 100.0 and not self.secondary_data: max_v = 100.0

        if self.secondary_data: self.draw_single_graph(painter, self.secondary_data, col_sec, max_v)
        self.draw_single_graph(painter, self.data, col_prim, max_v)

    def draw_single_graph(self, painter, data_list, color, max_scale_val):
        w, h = self.width(), self.height()
        margin_top, margin_bottom = 15, 15
        draw_h = h - margin_top - margin_bottom
        path = QPainterPath()
        scale = draw_h / max_scale_val if max_scale_val > 0.001 else 0
        step_w = w / (self.max_points - 1) if self.max_points > 1 else 0
        path.moveTo(0, (margin_top + draw_h) - (data_list[0] * scale))
        for i, val in enumerate(data_list): path.lineTo(i * step_w, (margin_top + draw_h) - (val * scale))

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
        text_cont = QWidget()
        text_cont.setStyleSheet("background: transparent;")
        text_cont.setFixedWidth(85)
        t_layout = QVBoxLayout(text_cont)
        t_layout.setContentsMargins(0, 10, 0, 10)
        t_layout.setSpacing(2)
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("Title")
        self.lbl_extra = QLabel("")
        self.lbl_extra.setStyleSheet(f"color: {config.active_theme['text_dim']}; font-size: 10px; font-weight: 500;")
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
        header.addWidget(QLabel("NETWORK", objectName="Title"))
        self.lbl_iface = QLabel("")
        self.lbl_iface.setStyleSheet(
            f"color: {config.active_theme['accent_blue']}; font-size: 11px; font-weight: bold; padding-top: 2px; margin-left: 15px;")
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
        self.lbl_info.setText(
            f"<span style='color:{c_d}; font-weight:bold'>▼ {str_d}</span> &nbsp;&nbsp; <span style='color:{c_u}; font-weight:bold'>▲ {str_u}</span>")
        if iface_name: self.lbl_iface.setText(iface_name.upper())
        if not refresh_only: self.g.add_value(d, u)


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
        self.bar.setStyleSheet(
            f"QProgressBar {{ background-color: {theme['bar_bg']}; border-radius: 4px; }} QProgressBar::chunk {{ background-color: {c_fill}; border-radius: 4px; }}")
        self.lbl_read_v.setText(f"▼ {format_speed(read_mb, self.use_bits)}")
        self.lbl_write_v.setText(f"▲ {format_speed(write_mb, self.use_bits)}")


class ProcessTree(QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setColumnCount(5)
        self.setHeaderLabels(["NAME", "PID", "CPU", "RAM", "DISK"])
        self.setIndentation(15)
        self.setIconSize(QSize(20, 20))
        self.setAlternatingRowColors(False)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(False)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_menu)

        self.icon_provider = QFileIconProvider()
        self.icon_cache = {}

        header = self.header()
        header.setSectionsClickable(True)
        header.setSectionsMovable(False)

        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 5): header.setSectionResizeMode(i, QHeaderView.ResizeToContents)

        header.setStretchLastSection(False)

        item = self.headerItem()
        item.setTextAlignment(1, Qt.AlignCenter)
        item.setTextAlignment(2, Qt.AlignCenter)
        item.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
        item.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)

        self.sort_state_name = 0
        self.sort_col = -1
        self.sort_asc = False

        header.sectionClicked.connect(self.on_header_clicked)
        self.refresh_header_visuals()

        self.last_data = []

    def open_menu(self, position):
        item = self.itemAt(position)
        if not item: return
        pids_data = item.data(0, Qt.UserRole)
        menu = QMenu()
        menu.setStyleSheet(config.get_stylesheet(config.active_theme))
        kill_action = QAction(self)
        if isinstance(pids_data, list) and len(pids_data) > 1:
            kill_action.setText(f"Finalizar árbol de procesos ({len(pids_data)})")
        else:
            kill_action.setText("Finalizar tarea")
        if not pids_data:
            kill_action.setEnabled(False)
        else:
            kill_action.triggered.connect(lambda: self.kill_processes(pids_data))
        menu.addAction(kill_action)
        menu.exec(QCursor.pos())

    def kill_processes(self, pids):
        if not isinstance(pids, list): pids = [pids]
        for pid in pids:
            try:
                psutil.Process(pid).terminate()
            except:
                pass

    def on_header_clicked(self, index):
        if index == 0:
            self.sort_state_name = (self.sort_state_name + 1) % 3
            if self.sort_state_name == 0:
                self.sort_col = -1
            else:
                self.sort_col = 0
        else:
            if self.sort_col == index:
                self.sort_asc = not self.sort_asc
            else:
                self.sort_col = index
                self.sort_asc = False
        self.refresh_header_visuals()
        if self.last_data: self.update_data(self.last_data)

    def refresh_header_visuals(self):
        labels = ["NAME", "PID", "CPU", "RAM", "DISK"]
        if self.sort_col != -1:
            arrow = " ▲" if self.sort_asc else " ▼"
            if self.sort_col == 0:
                if self.sort_state_name == 1:
                    labels[0] += " ▲"
                elif self.sort_state_name == 2:
                    labels[0] += " ▼"
            else:
                labels[self.sort_col] += arrow
        self.setHeaderLabels(labels)

    def update_data(self, process_list):
        self.last_data = process_list
        groups = {}
        for p in process_list:
            name = p['name']
            if name not in groups: groups[name] = []
            groups[name].append(p)

        parent_items_data = []
        for name, children in groups.items():
            total_cpu = sum(c['cpu'] for c in children)
            total_ram = sum(c['ram'] for c in children)
            total_disk = sum(c['disk'] for c in children)
            all_pids = [c['pid'] for c in children]
            min_pid = min(all_pids)
            exe_path = children[0]['exe']

            parent_data = {
                'name': name, 'pid': min_pid, 'all_pids': all_pids,
                'cpu': total_cpu, 'ram': total_ram, 'disk': total_disk,
                'exe': exe_path, 'count': len(children), 'children': children
            }
            parent_items_data.append(parent_data)

        col_keys = {0: 'name', 1: 'pid', 2: 'cpu', 3: 'ram', 4: 'disk'}
        key = col_keys.get(self.sort_col, 'ram')

        if self.sort_col == 0:
            if self.sort_state_name == 1:
                parent_items_data.sort(key=lambda x: x['name'].lower())
            elif self.sort_state_name == 2:
                parent_items_data.sort(key=lambda x: x['name'].lower(), reverse=True)
            else:
                parent_items_data.sort(key=lambda x: x['ram'], reverse=True)
        elif self.sort_col == -1:
            parent_items_data.sort(key=lambda x: x['ram'], reverse=True)
        else:
            parent_items_data.sort(key=lambda x: x[key], reverse=not self.sort_asc)

        expanded_names = set()
        root = self.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if item.isExpanded(): expanded_names.add(item.text(0).split(" (")[0])

        self.clear()

        display_limit = len(parent_items_data) if self.sort_col == 0 else 100

        for p_data in parent_items_data[:display_limit]:
            item = QTreeWidgetItem(self)
            item.setData(0, Qt.UserRole, p_data['all_pids'])

            txt_name = f"{p_data['name']} ({p_data['count']})" if p_data['count'] > 1 else p_data['name']
            item.setText(0, txt_name)

            exe_path = p_data['exe']
            if exe_path:
                if exe_path not in self.icon_cache:
                    self.icon_cache[exe_path] = self.icon_provider.icon(QFileInfo(exe_path))
                item.setIcon(0, self.icon_cache[exe_path])

            font = QFont();
            font.setBold(True);
            item.setFont(0, font)
            item.setForeground(0, QBrush(QColor(config.active_theme['text_main'])))

            if p_data['count'] == 1:
                item.setText(1, str(p_data['pid']))
            else:
                item.setText(1, "")
            item.setTextAlignment(1, Qt.AlignCenter)

            item.setText(2, f"{format_decimal(p_data['cpu'])}%")
            item.setTextAlignment(2, Qt.AlignCenter)
            if p_data['cpu'] > 15:
                item.setForeground(2, QBrush(QColor(config.active_theme['accent_red'])))
            elif p_data['cpu'] > 1.0:
                item.setForeground(2, QBrush(QColor(config.active_theme['accent_blue'])))
            else:
                item.setForeground(2, QBrush(QColor(config.active_theme['text_dim'])))

            ram_mb = p_data['ram'] / (1024 * 1024)
            item.setText(3, f"{format_decimal(ram_mb)} MB")
            item.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
            if ram_mb > 1000:
                item.setForeground(3, QBrush(QColor(config.active_theme['accent_red'])))
            elif ram_mb > 300:
                item.setForeground(3, QBrush(QColor(config.active_theme['accent_blue'])))
            else:
                item.setForeground(3, QBrush(QColor(config.active_theme['text_dim'])))

            item.setText(4, f"{format_decimal(p_data['disk'])} MB/s")
            item.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
            if p_data['disk'] > 5.0:
                item.setForeground(4, QBrush(QColor(config.active_theme['accent_red'])))
            elif p_data['disk'] > 0.1:
                item.setForeground(4, QBrush(QColor(config.active_theme['accent_blue'])))
            else:
                item.setForeground(4, QBrush(QColor(config.active_theme['text_dim'])))

            if p_data['count'] > 1:
                if self.sort_col == 0 and self.sort_state_name != 0:
                    p_data['children'].sort(key=lambda x: x['name'].lower(), reverse=(self.sort_state_name == 2))
                else:
                    child_key = col_keys.get(self.sort_col, 'ram')
                    if self.sort_col == -1: child_key = 'ram'
                    reverse = not self.sort_asc if self.sort_col != -1 else True
                    p_data['children'].sort(key=lambda x: x[child_key], reverse=reverse)

                for child in p_data['children']:
                    child_item = QTreeWidgetItem(item)
                    child_item.setData(0, Qt.UserRole, [child['pid']])
                    child_item.setText(0, child['name'])
                    child_item.setForeground(0, QBrush(QColor(config.active_theme['text_dim'])))

                    child_item.setText(1, str(child['pid']))
                    child_item.setTextAlignment(1, Qt.AlignCenter)

                    child_item.setText(2, f"{format_decimal(child['cpu'])}%")
                    child_item.setTextAlignment(2, Qt.AlignCenter)
                    if child['cpu'] > 15:
                        child_item.setForeground(2, QBrush(QColor(config.active_theme['accent_red'])))
                    elif child['cpu'] > 1.0:
                        child_item.setForeground(2, QBrush(QColor(config.active_theme['accent_blue'])))

                    c_ram = child['ram'] / (1024 * 1024)
                    child_item.setText(3, f"{format_decimal(c_ram)} MB")
                    child_item.setTextAlignment(3, Qt.AlignRight | Qt.AlignVCenter)
                    if c_ram > 1000:
                        child_item.setForeground(3, QBrush(QColor(config.active_theme['accent_red'])))
                    elif c_ram > 300:
                        child_item.setForeground(3, QBrush(QColor(config.active_theme['accent_blue'])))

                    child_item.setText(4, f"{format_decimal(child['disk'])} MB/s")
                    child_item.setTextAlignment(4, Qt.AlignRight | Qt.AlignVCenter)
                    if child['disk'] > 5.0:
                        child_item.setForeground(4, QBrush(QColor(config.active_theme['accent_red'])))
                    elif child['disk'] > 0.1:
                        child_item.setForeground(4, QBrush(QColor(config.active_theme['accent_blue'])))

            if p_data['name'] in expanded_names: item.setExpanded(True)