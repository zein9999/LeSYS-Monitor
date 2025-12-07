from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame,
                               QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(450, 450)

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout principal de la ventana transparente
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.container = QFrame()
        self.container.setFixedSize(350, 400)
        self.container.setStyleSheet("""
            QFrame {
                background-color: #2b2d31; /* Un gris oscuro más moderno (Discord Theme) */
                border-radius: 20px;       /* Bordes más redondeados */
                border: 2px solid #1e1f22; /* Borde sutil oscuro */
            }
        """)
        layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setAlignment(Qt.AlignCenter)

        # --- LOGO ---
        self.logo_label = QLabel("LeSYS")
        self.logo_label.setStyleSheet("""
            font-size: 56px; 
            font-weight: 900; 
            color: #5865F2; /* Discord Blurple */
            border: none;
            background-color: transparent;
        """)
        self.logo_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.logo_label)
        container_layout.addSpacing(20)

        # --- TEXTO DE CARGA ---
        # Lista ordenada "LeSYS"
        self.phrases = [
            "Listando módulos del sistema...",
            "estabilizando conexiones de hardware...",
            "Sincronizando sensores disponibles...",
            "Y ajustando precisión de lectura...",
            "Supervisando estabilidad del sistema..."
        ]

        self.loading_label = QLabel(self.phrases[0])
        self.loading_label.setStyleSheet("""
            font-size: 14px; 
            color: #b5bac1; 
            font-weight: bold;
            border: none;
            background-color: transparent;
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.loading_label)

        # --- ANIMACIONES ---

        # Efecto respiración
        self.opacity_effect = QGraphicsOpacityEffect(self.logo_label)
        self.logo_label.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(1200)
        self.anim.setStartValue(0.4)
        self.anim.setEndValue(1)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.setLoopCount(-1)
        self.anim.start()
        self.counter = 1

        self.text_timer = QTimer(self)
        self.text_timer.timeout.connect(self.change_text)
        self.text_timer.start(750)

    def change_text(self):
        text = self.phrases[self.counter]
        self.loading_label.setText(text)

        self.counter = (self.counter + 1) % len(self.phrases)