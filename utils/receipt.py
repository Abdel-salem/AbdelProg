"""Receipt text generation and print dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit,
    QPushButton, QLabel
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog


def generate_receipt_text(sale: dict, items: list, customer: dict | None) -> str:
    """Return a formatted receipt string."""
    lines = []
    w = 42  # receipt width

    lines.append("=" * w)
    lines.append("BizManager".center(w))
    lines.append("Sales Receipt".center(w))
    lines.append("=" * w)
    lines.append(f"Date : {sale.get('created_at', '')}")
    lines.append(f"Sale #: {sale.get('id', '')}")
    if customer:
        lines.append(f"Customer: {customer.get('name', 'Walk-in')}")
    lines.append(f"Payment: {sale.get('payment_method', 'cash').upper()}")
    lines.append("-" * w)
    lines.append(f"{'Item':<20} {'Qty':>4} {'Price':>7} {'Total':>8}")
    lines.append("-" * w)

    subtotal = 0.0
    for item in items:
        name = str(item.get("product_name", ""))[:20]
        qty = item.get("quantity", 0)
        price = item.get("unit_price", 0.0)
        total = qty * price
        subtotal += total
        lines.append(f"{name:<20} {qty:>4} {price:>7.2f} {total:>8.2f}")

    lines.append("-" * w)
    discount = sale.get("discount", 0.0)
    discount_amt = subtotal * discount / 100.0
    net_total = sale.get("total_amount", subtotal - discount_amt)

    lines.append(f"{'Subtotal':>32} {subtotal:>8.2f}")
    if discount:
        lines.append(f"{'Discount (' + str(discount) + '%)':>32} {-discount_amt:>8.2f}")
    lines.append(f"{'TOTAL':>32} {net_total:>8.2f}")
    lines.append("=" * w)
    lines.append("Thank you for your purchase!".center(w))
    lines.append("=" * w)

    return "\n".join(lines)


class ReceiptDialog(QDialog):
    def __init__(self, sale: dict, items: list, customer: dict | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Receipt")
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

        title = QLabel("Receipt")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        self._editor = QTextEdit()
        self._editor.setReadOnly(True)
        self._editor.setFont(QFont("Courier New", 10))
        self._editor.setPlainText(self._receipt_text)
        layout.addWidget(self._editor)

        btn_row = QHBoxLayout()
        btn_print = QPushButton("Print")
        btn_close = QPushButton("Close")
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
