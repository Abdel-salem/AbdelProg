"""نافذة التطبيق الرئيسية مع التنقل بالتبويبات."""

from PyQt6.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QLabel
from PyQt6.QtCore import Qt, QTimer, QDateTime
import database.db as db

from ui.pos_tab import POSTab
from ui.inventory_tab import InventoryTab
from ui.customers_tab import CustomersTab
from ui.receipts_tab import ReceiptsTab
from ui.reports_tab import ReportsTab
from ui.expenses_tab import ExpensesTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kavero")
        self.setMinimumSize(1100, 720)
        self.resize(1300, 840)
        self._build_ui()
        self._setup_status_bar()
        self._setup_shortcuts()

    def _build_ui(self):
        tabs = QTabWidget()
        tabs.setTabPosition(QTabWidget.TabPosition.West)
        tabs.setDocumentMode(True)

        self._pos_tab = POSTab()
        self._inv_tab = InventoryTab()
        self._cust_tab = CustomersTab()
        self._receipts_tab = ReceiptsTab()
        self._rep_tab = ReportsTab()
        self._exp_tab = ExpensesTab()

        tabs.addTab(self._pos_tab, "🛒 نقطة البيع")
        tabs.addTab(self._inv_tab, "📦 المخزون")
        tabs.addTab(self._cust_tab, "👥 العملاء")
        tabs.addTab(self._receipts_tab, "🧾 سجل الفواتير")
        tabs.addTab(self._rep_tab, "📊 التقارير")
        tabs.addTab(self._exp_tab, "💸 المصروفات")

        self._tabs = tabs
        self.setCentralWidget(tabs)

    def _setup_status_bar(self):
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self._clock_label = QLabel()
        self._clock_label.setStyleSheet("color: #d4e8f7; font-size: 12px; padding: 0 8px;")

        self._sales_today_label = QLabel()
        self._sales_today_label.setStyleSheet("color: #90ee90; font-size: 12px; padding: 0 8px;")

        self._low_stock_label = QLabel()
        self._low_stock_label.setStyleSheet("color: #ffcc80; font-size: 12px; padding: 0 8px;")

        status_bar.addPermanentWidget(self._low_stock_label)
        status_bar.addPermanentWidget(self._sales_today_label)
        status_bar.addPermanentWidget(self._clock_label)

        self._update_status_bar()

        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status_bar)
        self._status_timer.start(60000)  # update every minute

    def _update_status_bar(self):
        now = QDateTime.currentDateTime()
        self._clock_label.setText(now.toString("yyyy-MM-dd  hh:mm"))

        try:
            today_str = now.date().toString("yyyy-MM-dd")
            summary = db.get_pnl_summary(today_str, today_str)
            revenue = summary.get("revenue", 0)
            self._sales_today_label.setText(f"مبيعات اليوم: {revenue:,.2f}")
        except Exception:
            self._sales_today_label.setText("مبيعات اليوم: --")

        try:
            products = db.get_all_products()
            low_count = sum(
                1 for p in products
                if p["stock_qty"] <= p.get("low_stock_alert", 5)
            )
            if low_count > 0:
                self._low_stock_label.setText(f"⚠ مخزون منخفض: {low_count}")
            else:
                self._low_stock_label.setText("مخزون: جيد ✓")
        except Exception:
            self._low_stock_label.setText("")

    def _setup_shortcuts(self):
        from PyQt6.QtGui import QShortcut, QKeySequence
        f5 = QShortcut(QKeySequence("F5"), self)
        f5.activated.connect(self._refresh_current_tab)

    def _refresh_current_tab(self):
        idx = self._tabs.currentIndex()
        tab = self._tabs.widget(idx)
        if hasattr(tab, "refresh"):
            tab.refresh()
        self._update_status_bar()
