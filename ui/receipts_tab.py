"""سجل الفواتير — عرض وطباعة وتصدير الفواتير."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QSplitter, QTextEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

import database.db as db
from utils.receipt import PAYMENT_METHOD_AR, generate_receipt_text
from utils.export import export_receipt_pdf


class ReceiptsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._sales: list[dict] = []
        self._current_sale: dict | None = None
        self._current_items: list[dict] = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # ── اللوحة اليسرى: قائمة الفواتير ──────────────────────
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("بحث بالتاريخ أو اسم العميل...")
        self._search.textChanged.connect(self._filter)
        search_row.addWidget(QLabel("بحث:"))
        search_row.addWidget(self._search)
        left_layout.addLayout(search_row)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels([
            "رقم الفاتورة", "التاريخ", "العميل", "الإجمالي", "طريقة الدفع"
        ])
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.selectionModel().selectionChanged.connect(self._on_row_selected)
        left_layout.addWidget(self._table)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.refresh)
        left_layout.addWidget(refresh_btn)

        splitter.addWidget(left_widget)

        # ── اللوحة اليمنى: عارض الفاتورة ───────────────────────
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>عرض الفاتورة</b>"))

        self._receipt_view = QTextEdit()
        self._receipt_view.setReadOnly(True)
        self._receipt_view.setFont(QFont("Courier New", 10))
        self._receipt_view.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._receipt_view.setPlaceholderText("اختر فاتورة من القائمة لعرضها هنا...")
        right_layout.addWidget(self._receipt_view)

        btn_row = QHBoxLayout()
        self._print_btn = QPushButton("طباعة")
        self._print_btn.setObjectName("primaryBtn")
        self._print_btn.setEnabled(False)
        self._print_btn.clicked.connect(self._print_receipt)

        self._pdf_btn = QPushButton("تصدير PDF")
        self._pdf_btn.setObjectName("secondaryBtn")
        self._pdf_btn.setEnabled(False)
        self._pdf_btn.clicked.connect(self._export_pdf)

        btn_row.addWidget(self._print_btn)
        btn_row.addWidget(self._pdf_btn)
        right_layout.addLayout(btn_row)

        splitter.addWidget(right_widget)
        splitter.setSizes([500, 550])

    def refresh(self):
        self._sales = db.get_all_sales_with_details()
        self._render(self._sales)

    def _render(self, sales: list):
        self._table.setRowCount(0)
        for s in sales:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(s.get("created_at", "")[:16]))
            self._table.setItem(row, 2, QTableWidgetItem(s.get("customer_name", "بدون عميل")))
            total_item = QTableWidgetItem(f"{s.get('total_amount', 0):,.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 3, total_item)
            pm = s.get("payment_method", "cash").lower()
            self._table.setItem(row, 4, QTableWidgetItem(PAYMENT_METHOD_AR.get(pm, pm)))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, s)

    def _filter(self, text: str):
        if not text.strip():
            self._render(self._sales)
            return
        t = text.lower()
        filtered = [
            s for s in self._sales
            if t in s.get("customer_name", "").lower()
            or t in s.get("created_at", "").lower()
        ]
        self._render(filtered)

    def _on_row_selected(self):
        row = self._table.currentRow()
        if row < 0:
            self._current_sale = None
            self._current_items = []
            self._receipt_view.clear()
            self._print_btn.setEnabled(False)
            self._pdf_btn.setEnabled(False)
            return

        item = self._table.item(row, 0)
        if not item:
            return
        sale = item.data(Qt.ItemDataRole.UserRole)
        if not sale:
            return

        self._current_sale = sale
        self._current_items = db.get_sale_items(sale["id"])

        # بناء نص الفاتورة
        customer_name = sale.get("customer_name", "بدون عميل")
        # simulate a customer dict for generate_receipt_text
        customer_dict = {"name": customer_name} if customer_name != "بدون عميل" else None

        receipt_text = self._build_receipt_text(sale, self._current_items, customer_name)
        self._receipt_view.setPlainText(receipt_text)
        self._print_btn.setEnabled(True)
        self._pdf_btn.setEnabled(True)

    def _build_receipt_text(self, sale: dict, items: list, customer_name: str) -> str:
        w = 44
        lines = []
        lines.append("=" * w)
        lines.append("فاتورة - Kavero".center(w))
        lines.append("=" * w)
        lines.append(f"رقم الفاتورة: #{sale.get('id', '')}")
        lines.append(f"التاريخ: {sale.get('created_at', '')}")
        lines.append(f"العميل: {customer_name}")
        pm = sale.get("payment_method", "cash").lower()
        lines.append(f"طريقة الدفع: {PAYMENT_METHOD_AR.get(pm, pm)}")
        lines.append("-" * w)
        lines.append(f"{'المنتج':<18} {'الكمية':>6} {'السعر':>8} {'الإجمالي':>9}")
        lines.append("-" * w)

        subtotal = 0.0
        for item in items:
            name = str(item.get("product_name", ""))[:18]
            qty = item.get("quantity", 0)
            price = item.get("unit_price", 0.0)
            lt = item.get("line_total", qty * price)
            subtotal += lt
            lines.append(f"{name:<18} {qty:>6.2f} {price:>8.2f} {lt:>9.2f}")

        lines.append("-" * w)
        discount = sale.get("discount", 0.0)
        discount_amt = subtotal * discount / 100.0
        net_total = sale.get("total_amount", subtotal - discount_amt)

        lines.append(f"الإجمالي قبل الخصم: {subtotal:>10.2f}")
        if discount:
            lines.append(f"الخصم ({discount}%): {-discount_amt:>14.2f}")
        lines.append(f"الإجمالي: {net_total:>20.2f}")
        lines.append("=" * w)
        lines.append("شكراً لتعاملكم معنا".center(w))
        lines.append("=" * w)
        return "\n".join(lines)

    def _print_receipt(self):
        if not self._current_sale:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QPrintDialog.DialogCode.Accepted:
            self._receipt_view.print(printer)

    def _export_pdf(self):
        if not self._current_sale:
            return
        sale_id = self._current_sale["id"]
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير PDF", f"فاتورة_{sale_id}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            customer_name = self._current_sale.get("customer_name", "بدون عميل")
            export_receipt_pdf(
                self._current_sale,
                self._current_items,
                customer_name,
                path
            )
            QMessageBox.information(self, "تم التصدير", f"تم حفظ الفاتورة في:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
