"""
BizManager — Cashier & Inventory Management with P&L
Entry point
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from database.db import init_db


APP_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #f5f6fa;
    color: #2c3e50;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar / Tab Bar ─────────────────────────────────── */
QTabWidget::pane {
    border: none;
    background: #f5f6fa;
}
QTabBar {
    background: #1a237e;
}
QTabBar::tab {
    background: #1a237e;
    color: #9fa8da;
    padding: 14px 20px;
    min-width: 130px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    border-left: 3px solid transparent;
}
QTabBar::tab:selected {
    background: #283593;
    color: #ffffff;
    border-left: 3px solid #7986cb;
}
QTabBar::tab:hover:!selected {
    background: #283593;
    color: #c5cae9;
}

/* ── Buttons ────────────────────────────────────────────── */
QPushButton {
    background-color: #3949ab;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 7px 16px;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #3f51b5;
}
QPushButton:pressed {
    background-color: #283593;
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

/* ── Line Edits, ComboBox ───────────────────────────────── */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTextEdit {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 4px;
    padding: 5px 8px;
    color: #2c3e50;
    selection-background-color: #7986cb;
}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QDateEdit:focus, QTextEdit:focus {
    border: 1.5px solid #3f51b5;
    outline: none;
}
QComboBox::drop-down {
    border: none;
    padding-right: 6px;
}

/* ── Tables ─────────────────────────────────────────────── */
QTableWidget {
    background: white;
    alternate-background-color: #f3f4ff;
    gridline-color: #e8eaf6;
    border: 1px solid #c5cae9;
    border-radius: 6px;
    selection-background-color: #7986cb;
    selection-color: white;
}
QHeaderView::section {
    background-color: #1a237e;
    color: white;
    padding: 8px 6px;
    border: none;
    font-weight: 600;
    font-size: 12px;
}
QTableWidget::item {
    padding: 5px 6px;
}

/* ── GroupBox ───────────────────────────────────────────── */
QGroupBox {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 6px;
    margin-top: 10px;
    padding: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #3949ab;
}

/* ── Labels ─────────────────────────────────────────────── */
QLabel#cardLabel {
    background: white;
    border: 1px solid #c5cae9;
    border-radius: 8px;
    padding: 12px 18px;
    color: #1a237e;
    font-size: 13px;
}

/* ── Dialogs ────────────────────────────────────────────── */
QDialog {
    background: #f5f6fa;
}

/* ── ScrollBar ──────────────────────────────────────────── */
QScrollBar:vertical {
    width: 8px;
    background: #e8eaf6;
}
QScrollBar::handle:vertical {
    background: #9fa8da;
    border-radius: 4px;
    min-height: 20px;
}
"""


def main():
    init_db()

    if "--check" in sys.argv:
        print("BizManager: DB initialised OK")
        sys.exit(0)

    from ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("BizManager")
    app.setStyleSheet(APP_STYLESHEET)
    app.setFont(QFont("Segoe UI", 13))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
