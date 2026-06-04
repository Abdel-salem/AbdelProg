"""توليد نص الفاتورة وحوار الطباعة."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

PAYMENT_METHOD_AR = {
    "cash": "نقداً",
    "card": "بطاقة",
    "mobile": "محفظة إلكترونية",
}


def generate_receipt_text(sale: dict, items: list, customer: dict | None) -> str:
    """إرجاع نص الفاتورة منسقاً باللغة العربية."""
    lines = []
    w = 44

    lines.append("=" * w)
    lines.append("فاتورة - Kavero".center(w))
    lines.append("=" * w)
    lines.append(f"رقم الفاتورة: #{sale.get('id', '')}")
    lines.append(f"التاريخ: {sale.get('created_at', '')}")
    if customer:
        lines.append(f"العميل: {customer.get('name', 'بدون عميل')}")
    else:
        lines.append("العميل: بدون عميل")
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
        total = qty * price
        subtotal += total
        lines.append(f"{name:<18} {qty:>6.2f} {price:>8.2f} {total:>9.2f}")

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


class ReceiptDialog(QDialog):
    def __init__(self, sale: dict, items: list, customer: dict | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("الفاتورة")
        self.setMinimumSize(480, 560)
        self._sale = sale
        self._items = items
        self._customer = customer
        self._receipt_text = generate_receipt_text(sale, items, customer)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel("الفاتورة")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self._editor = QTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Courier New", 10))
        self._editor.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        self._editor.setPlainText(self._receipt_text)
        layout.addWidget(self._editor)

        btn_row = QHBoxLayout()
        btn_print = QPushButton("طباعة")
        btn_close = QPushButton("إغلاق")
        btn_print.setObjectName("primaryBtn")
        btn_row.addWidget(btn_print)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

        btn_print.clicked.connect(self._print_receipt)
        btn_close.clicked.connect(self.accept)

    def _print_receipt(self):
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dlg = QPrintDialog(printer, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._editor.print(printer)
