import sys
import psutil
import gc
import os

from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout,
                               QHBoxLayout, QFrame, QPushButton, QMenu)
from PySide6.QtCore import Qt, QSize, QPoint, QTimer
from PySide6.QtGui import QAction, QIcon, QPainter, QColor

import config
from workers import WorkerThread
from widgets import HardwareRow, NetworkRow, DiskRow
from splash import SplashScreen


class MonitorFinal(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LeSYS")
        self.resize(520, 650)
        self.use_bits = False
        self.is_dark = True

        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(self.main_layout)

        h_box = QHBoxLayout()
        h_box.addWidget(QLabel("PERFORMANCE", objectName="HeaderTitle"))
        h_box.addStretch()

        self.btn_opts = QPushButton()
        self.btn_opts.setCursor(Qt.PointingHandCursor)
        self.btn_opts.setFixedSize(30, 30)
        self.btn_opts.setIconSize(QSize(20, 20))

        self.menu = QMenu(self)
        self.act_unit = QAction("Switch to Kbps/Mbps", self, checkable=True)
        self.act_unit.triggered.connect(self.toggle_unit)
        self.act_theme = QAction("Light Mode", self, checkable=True)
        self.act_theme.triggered.connect(self.toggle_theme)
        self.menu.addAction(self.act_unit)
        self.menu.addAction(self.act_theme)

        self.btn_opts.clicked.connect(lambda: self.menu.exec(self.btn_opts.mapToGlobal(QPoint(0, 30))))

        h_box.addWidget(self.btn_opts)
        self.main_layout.addLayout(h_box)

        self.row_cpu = HardwareRow("CPU")
        self.main_layout.addWidget(self.row_cpu)
        self.row_ram = HardwareRow("RAM")
        self.main_layout.addWidget(self.row_ram)
        self.row_gpu = HardwareRow("GPU")
        self.main_layout.addWidget(self.row_gpu)
        self.row_net = NetworkRow()
        self.main_layout.addWidget(self.row_net)

        self.disk_frame = QFrame()
        self.disk_frame.setObjectName("Card")
        self.d_layout = QVBoxLayout()
        self.d_layout.setContentsMargins(15, 10, 15, 10)
        self.d_layout.addWidget(QLabel("STORAGE", objectName="Title"))

        header_disk = QHBoxLayout()
        header_disk.setContentsMargins(0, 5, 0, 0)
        header_disk.setSpacing(10)

        lbl_h_dev = QLabel("DRIVE")
        lbl_h_dev.setObjectName("HeaderCol")
        lbl_h_dev.setFixedWidth(35)
        lbl_h_use = QLabel("USAGE")
        lbl_h_use.setObjectName("HeaderCol")
        lbl_h_pct = QLabel("%")
        lbl_h_pct.setObjectName("HeaderCol")
        lbl_h_pct.setFixedWidth(40)
        lbl_h_pct.setAlignment(Qt.AlignRight)
        lbl_h_read = QLabel("READ")
        lbl_h_read.setObjectName("HeaderCol")
        lbl_h_read.setFixedWidth(85)
        lbl_h_read.setAlignment(Qt.AlignRight)
        lbl_h_write = QLabel("WRITE")
        lbl_h_write.setObjectName("HeaderCol")
        lbl_h_write.setFixedWidth(85)
        lbl_h_write.setAlignment(Qt.AlignRight)

        header_disk.addWidget(lbl_h_dev)
        header_disk.addWidget(lbl_h_use, stretch=1)
        header_disk.addWidget(lbl_h_pct)
        header_disk.addWidget(lbl_h_read)
        header_disk.addWidget(lbl_h_write)

        self.d_layout.addLayout(header_disk)
        self.d_layout.addWidget(QLabel("", styleSheet="border-top: 1px solid #3C4043; margin-bottom: 5px;"))

        self.disks = {}
        for p in psutil.disk_partitions():
            if 'cdrom' in p.opts or p.fstype == '': continue
            try:
                psutil.disk_usage(p.mountpoint)
                l = p.device.rstrip("\\")
                r = DiskRow(l)
                self.d_layout.addWidget(r)
                self.disks[l] = r
            except:
                pass
        self.d_layout.addStretch()
        self.disk_frame.setLayout(self.d_layout)
        self.main_layout.addWidget(self.disk_frame, stretch=1)

        self.apply_stylesheet()
        self.refresh_settings_icon()

        gc.collect()

        self.worker = WorkerThread()
        self.worker.data_signal.connect(self.update_ui)
        self.worker.start()

    def get_icon_path(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, "assets", "icon-ajustes.png")

    def refresh_settings_icon(self):
        try:
            path = self.get_icon_path()
            pixmap = QIcon(path).pixmap(QSize(20, 20))
            if pixmap.isNull(): return
            color = QColor(config.active_theme["text_dim"])
            painter = QPainter(pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
            painter.fillRect(pixmap.rect(), color)
            painter.end()
            self.btn_opts.setIcon(QIcon(pixmap))
        except:
            pass

    def toggle_unit(self, checked):
        self.use_bits = checked
        self.row_net.set_unit(checked)
        for d in self.disks.values(): d.set_unit(checked)

    def toggle_theme(self, checked):
        self.is_dark = not checked
        config.active_theme = config.THEMES["Dark"] if self.is_dark else config.THEMES["Light"]
        self.act_theme.setText("Dark Mode" if checked else "Light Mode")
        self.apply_stylesheet()
        for d in self.disks.values(): d.refresh_theme_colors()
        self.row_net.update_style_imm()
        self.refresh_settings_icon()
        self.repaint()

    def apply_stylesheet(self):
        self.setStyleSheet(config.get_stylesheet(config.active_theme))

    def update_ui(self, data):
        self.row_cpu.update_val(data['cpu'], data.get('cpu_extra', ''))
        self.row_ram.update_val(data['ram'], data.get('ram_extra', ''))
        self.row_gpu.update_val(data['gpu'], data.get('gpu_extra', ''))
        self.row_net.update_net(data['net_down'], data['net_up'], data.get('net_iface', ''))

        for name, row in self.disks.items():
            if name in data['disk_usage']:
                usage = data['disk_usage'][name]
                r_mb, w_mb = data['disk_io'].get(name, (0, 0))
                row.update_state(usage, r_mb, w_mb)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    splash = SplashScreen()
    splash.show()
    main_window = None


    def start_main_app():
        global main_window
        main_window = MonitorFinal()
        splash_geo = splash.geometry()
        win_geo = main_window.geometry()
        x = splash_geo.x() + (splash_geo.width() - win_geo.width()) // 2
        y = splash_geo.y() + (splash_geo.height() - win_geo.height()) // 2
        main_window.move(x, y)
        main_window.show()
        splash.close()


    QTimer.singleShot(4500, start_main_app)
    sys.exit(app.exec())