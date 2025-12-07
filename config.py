THEMES = {
    "Dark": {
        "bg_main": "#131314",
        "bg_card": "#1E1F20",
        "accent_blue": "#64B5F6",
        "accent_red": "#F28B82",
        "text_main": "#E3E3E3",
        "text_dim": "#9AA0A6",
        "border": "#3C4043",
        "bar_bg": "#303134",
        "grid_line": "#2D2E30",
        "btn_hover": "#303134",
        "menu_bg": "#292A2D",
        "menu_sel": "#3C4043"
    },
    "Light": {
        "bg_main": "#F0F2F5",
        "bg_card": "#FFFFFF",
        "accent_blue": "#1976D2",
        "accent_red": "#D32F2F",
        "text_main": "#1C1E21",
        "text_dim": "#65676B",
        "border": "#CED0D4",
        "bar_bg": "#E4E6EB",
        "grid_line": "#E4E6EB",
        "btn_hover": "#E4E6EB",
        "menu_bg": "#FFFFFF",
        "menu_sel": "#F0F2F5"
    }
}

active_theme = THEMES["Dark"]

def get_stylesheet(theme):
    return f"""
        QWidget {{ background-color: {theme['bg_main']}; color: {theme['text_main']}; font-family: 'Segoe UI', sans-serif; }}
        QLabel {{ background-color: transparent; }}
        QFrame#Card {{ background-color: {theme['bg_card']}; border-radius: 12px; border: 1px solid {theme['border']}; }}
        QLabel#Title {{ font-size: 13px; font-weight: 600; color: {theme['text_dim']}; }}
        QLabel#HeaderCol {{ font-size: 11px; font-weight: 700; color: {theme['text_dim']}; text-transform: uppercase; }}
        QLabel#Value {{ font-size: 26px; font-weight: bold; color: {theme['text_main']}; }}
        QLabel#HeaderTitle {{ font-size: 22px; font-weight: 800; color: {theme['text_main']}; letter-spacing: 1px; }}
        QProgressBar {{ border: none; background-color: {theme['bar_bg']}; border-radius: 4px; height: 6px; text-align: center; }}
        QPushButton {{ background-color: transparent; border: none; border-radius: 6px; color: {theme['text_dim']}; font-size: 16px; padding: 4px; }}
        QPushButton:hover {{ background-color: {theme['btn_hover']}; color: {theme['text_main']}; }}
        QMenu {{ background-color: {theme['menu_bg']}; border: 1px solid {theme['border']}; border-radius: 8px; padding: 6px; }}
        QMenu::item {{ background-color: transparent; padding: 8px 25px 8px 15px; border-radius: 4px; color: {theme['text_main']}; font-size: 13px; }}
        QMenu::item:selected {{ background-color: {theme['menu_sel']}; }}
    """