"""
Kavero — Cashier & Inventory Management with P&L
Entry point
"""

import sys
import matplotlib
matplotlib.rcParams['font.family'] = 'DejaVu Sans'

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from database.db import init_db


APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f8f9fa;
    color: #2c3e50;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar / Tab Bar ─────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #f8f9fa;
}
QTabBar {
    background: #1e3a5f;
}
QTabBar::tab {
    background: #1e3a5f;
    color: #a8c0d6;
    padding: 16px 18px;
    min-width: 140px;
    font-size: 14px;
    font-weight: 500;
    border: none;
    border-left: 3px solid transparent;
}
QTabBar::tab:selected {
    background: #16304f;
    color: #ffffff;
    border-left: 3px solid #f0a500;
}
QTabBar::tab:hover:!selected {
    background: #16304f;
    color: #d4e8f7;
}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton {
    background-color: #f0a500;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #e09400;
}
QPushButton:pressed {
    background-color: #c07d00;
}
QPushButton#dangerBtn {
    background-color: #e53935;
}
QPushButton#dangerBtn:hover {
    background-color: #ef5350;
}
QPushButton#successBtn {
    background-color: #43a047;
}
QPushButton#successBtn:hover {
    background-color: #66bb6a;
}
QPushButton#secondaryBtn {
    background-color: #546e7a;
}
QPushButton#secondaryBtn:hover {
    background-color: #607d8b;
}
QPushButton#primaryBtn {
    background-color: #f0a500;
}
QPushButton#primaryBtn:hover {
    background-color: #e09400;
}

/* ── Line Edits, ComboBox ───────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 4px;
    padding: 6px 8px;
    color: #2c3e50;
    font-size: 13px;
    selection-background-color: #f0a500;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1.5px solid #f0a500;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

/* ── Tables ─────────────────────────────────────────────── */
QTableWidget {
    background: white;
    alternate-background-color: #f0f4ff;
    gridline-color: #e0e4ef;
    border: 1px solid #c5cae9;
    border-radius: 6px;
    selection-background-color: #f0a500;
    selection-color: white;
    font-size: 13px;
}
QHeaderView::section {
    background-color: #1e3a5f;
    color: white;
    padding: 9px 6px;
    border: none;
    font-weight: 700;
    font-size: 13px;
}
QTableWidget::item {
    padding: 6px 6px;
}
QTableWidget::item:hover {
    background-color: #fff3cd;
}

/* ── GroupBox ───────────────────────────────────────────── */
QGroupBox {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 8px;
    margin-top: 10px;
    padding: 10px;
    font-weight: 700;
    font-size: 13px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #1e3a5f;
}

/* ── Labels ─────────────────────────────────────────────── */
QLabel#cardLabel {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 8px;
    padding: 12px 18px;
    color: #1e3a5f;
    font-size: 13px;
}

/* ── Dialogs ────────────────────────────────────────────── */
QDialog {
    background: #f8f9fa;
    border-radius: 8px;
}

/* ── ScrollBar ──────────────────────────────────────────── */
QScrollBar:vertical {
    width: 8px;
    background: #e8eaf6;
}
QScrollBar::handle:vertical {
    background: #f0a500;
    border-radius: 4px;
    min-height: 20px;
}

/* ── Status Bar ─────────────────────────────────────────── */
QStatusBar {
    background: #1e3a5f;
    color: #d4e8f7;
    font-size: 12px;
    padding: 4px 8px;
}
"""


def main():
    init_db()

    if "--check" in sys.argv:
        print("Kavero: DB initialised OK")
        sys.exit(0)

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Kavero")
    app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    app.setStyleSheet(APP_STYLESHEET)
    app.setFont(QFont("Segoe UI", 13))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
