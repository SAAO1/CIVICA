"""Colores y estilo compartidos de la mesa de investigación de CIVICA."""

PETROLEO = "#152d3c"
INDIGO = "#243750"
MARFIL = "#f8edda"
TINTA = "#273746"
CORAL = "#ec9b87"
MENTA = "#8acbbd"

ESTILO_FERIA = """
QWidget#tableroInvestigacion {
    background: #142936; color: #f8edda;
    font-family: 'Atkinson Hyperlegible'; font-size: 16px;
}
QWidget#tableroInvestigacion QWidget { font-family: 'Atkinson Hyperlegible'; font-size: 16px; }
QWidget#tableroInvestigacion QLabel { background: transparent; color: #f8edda; }
QWidget#tableroInvestigacion QLabel#ceja { color: #8acbbd; font-size: 13px; font-weight: 700; }
QWidget#tableroInvestigacion QLabel#tituloCaso { font-size: 27px; font-weight: 700; }
QWidget#tableroInvestigacion QLabel#subtitulo { color: #cbd5d8; }
QWidget#tableroInvestigacion QLabel#aviso { color: #ffc5b4; }
QWidget#tableroInvestigacion QFrame#tarjeta {
    background: #223d4d; border: 1px solid #496371; border-radius: 13px;
}
QWidget#tableroInvestigacion QFrame#papel {
    background: #f8edda; border: 1px solid #d7bfa1; border-radius: 12px;
}
QWidget#tableroInvestigacion QFrame#papel QLabel { color: #273746; }
QWidget#tableroInvestigacion QLabel#tituloPapel { color: #273746; font-size: 22px; font-weight: 700; }
QWidget#tableroInvestigacion QTabWidget::pane { border: 0; background: transparent; }
QWidget#tableroInvestigacion QTabBar::tab {
    background: #22384b; color: #cbd5d8; border: 1px solid #456170;
    padding: 12px 23px; margin: 0 5px 8px 0; border-radius: 8px;
}
QWidget#tableroInvestigacion QTabBar::tab:selected { background: #f8edda; color: #223746; border-color: #f8edda; }
QWidget#tableroInvestigacion QTabBar::tab:focus { border: 2px solid #ec9b87; }
QWidget#tableroInvestigacion QPushButton, QWidget#tableroInvestigacion QToolButton {
    background: #355c65; color: #fff5e5; border: 1px solid #7b9b9e;
    padding: 10px 15px; min-height: 23px; border-radius: 8px; font-weight: 600;
}
QWidget#tableroInvestigacion QPushButton:hover, QWidget#tableroInvestigacion QToolButton:hover { background: #467984; }
QWidget#tableroInvestigacion QPushButton:focus, QWidget#tableroInvestigacion QToolButton:focus { border: 2px solid #ec9b87; }
QWidget#tableroInvestigacion QPushButton:disabled { color: #9aa9b0; background: #263e4b; border-color: #3f5661; }
QWidget#tableroInvestigacion QPushButton#principal { background: #f0b29a; color: #253342; border-color: #f0b29a; }
QWidget#tableroInvestigacion QPushButton#principal:hover { background: #ffd0b9; }
QWidget#tableroInvestigacion QPushButton#principal:disabled { color: #a39991; background: #625a56; border-color: #625a56; }
QWidget#tableroInvestigacion QLineEdit, QWidget#tableroInvestigacion QComboBox,
QWidget#tableroInvestigacion QListWidget, QWidget#tableroInvestigacion QTextBrowser {
    background: #f8edda; color: #273746; border: 1px solid #d0bda4;
    border-radius: 8px; padding: 8px; selection-background-color: #355c65; selection-color: #fff5e5;
}
QWidget#tableroInvestigacion QLineEdit:focus, QWidget#tableroInvestigacion QComboBox:focus,
QWidget#tableroInvestigacion QListWidget:focus { border: 2px solid #ec9b87; }
QWidget#tableroInvestigacion QListWidget::item { padding: 11px 7px; border-bottom: 1px solid #e0d2bc; }
QWidget#tableroInvestigacion QListWidget::item:selected { background: #355c65; color: #fff5e5; }
QWidget#tableroInvestigacion QComboBox QAbstractItemView { color: #273746; background: #f8edda; selection-background-color: #355c65; selection-color: white; }
QWidget#tableroInvestigacion QCheckBox { color: #f8edda; spacing: 9px; padding: 4px; }
QWidget#tableroInvestigacion QCheckBox::indicator { width: 20px; height: 20px; }
QWidget#tableroInvestigacion QSlider::groove:horizontal { height: 7px; border-radius: 3px; background: #54717b; }
QWidget#tableroInvestigacion QSlider::sub-page:horizontal { background: #8acbbd; border-radius: 3px; }
QWidget#tableroInvestigacion QSlider::handle:horizontal { width: 20px; margin: -7px 0; border-radius: 10px; background: #f0b29a; }
QWidget#tableroInvestigacion QScrollArea { border: 0; background: transparent; }
QWidget#tableroInvestigacion QScrollArea > QWidget > QWidget { background: transparent; }
QWidget#tableroInvestigacion QScrollBar:vertical { background: #1a3343; width: 12px; border: 0; }
QWidget#tableroInvestigacion QScrollBar::handle:vertical { background: #64818a; min-height: 35px; border-radius: 5px; }
QWidget#tableroInvestigacion QScrollBar::add-line:vertical, QWidget#tableroInvestigacion QScrollBar::sub-line:vertical { height: 0; }
"""
