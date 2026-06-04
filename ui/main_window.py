"""Main application window with tab navigation."""

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar
from PyQt6.QtCore import Qt

from ui.pos_tab import POSTab
from ui.inventory_tab import InventoryTab
from ui.customers_tab import CustomersTab
from ui.reports_tab import ReportsTab
from ui.expenses_tab import ExpensesTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BizManager")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self._build_ui()

    def _build_ui(self):
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.West)
        tabs.setDocumentMode(True)

        self._pos_tab = POSTab()
        self._inv_tab = InventoryTab()
        self._cust_tab = CustomersTab()
        self._rep_tab = ReportsTab()
        self._exp_tab = ExpensesTab()

        tabs.addTab(self._pos_tab, "Point of Sale")
        tabs.addTab(self._inv_tab, "Inventory")
        tabs.addTab(self._cust_tab, "Customers")
        tabs.addTab(self._rep_tab, "Reports")
        tabs.addTab(self._exp_tab, "Expenses")

        self.setCentralWidget(tabs)

        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        status_bar.showMessage("BizManager ready")
