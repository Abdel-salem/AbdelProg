"""تبويب العملاء — إدارة العملاء وعرض سجل المشتريات."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import database.db as db

PAYMENT_METHOD_AR = {
    "cash": "نقداً",
    "card": "بطاقة",
    "mobile": "محفظة إلكترونية",
}


class CustomersTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # الجزء العلوي: جدول العملاء
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        toolbar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("بحث بالاسم أو الهاتف أو البريد الإلكتروني...")
        self._search.textChanged.connect(self._filter)
        toolbar.addWidget(QLabel("بحث:"))
        toolbar.addWidget(self._search)
        toolbar.addStretch()

        add_btn = QPushButton("إضافة عميل")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add_customer)
        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self._edit_customer)
        del_btn = QPushButton("حذف")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_customer)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        top_layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["الاسم", "الهاتف", "البريد الإلكتروني", "نقاط الولاء", "تاريخ الانضمام"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.selectionModel().selectionChanged.connect(self._on_selection)
        top_layout.addWidget(self._table)

        splitter.addWidget(top_widget)

        # الجزء السفلي: سجل المشتريات
        bottom_widget = QGroupBox("سجل المشتريات")
        bottom_layout = QVBoxLayout(bottom_widget)

        self._history_table = QTableWidget()
        self._history_table.setColumnCount(5)
        self._history_table.setHorizontalHeaderLabels(
            ["رقم الفاتورة", "الإجمالي", "الخصم %", "طريقة الدفع", "التاريخ"]
        )
        self._history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._history_table.setAlternatingRowColors(True)
        bottom_layout.addWidget(self._history_table)

        splitter.addWidget(bottom_widget)
        splitter.setSizes([400, 200])
        layout.addWidget(splitter)

    def refresh(self):
        self._all = db.get_all_customers()
        self._render(self._all)

    def _render(self, customers: list):
        self._table.setRowCount(0)
        for c in customers:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(c["name"]))
            self._table.setItem(row, 1, QTableWidgetItem(c.get("phone") or ""))
            self._table.setItem(row, 2, QTableWidgetItem(c.get("email") or ""))
            pts_item = QTableWidgetItem(str(c.get("loyalty_points", 0)))
            pts_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, pts_item)
            self._table.setItem(row, 4, QTableWidgetItem(c.get("created_at", "")[:10]))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, c)

    def _filter(self, text: str):
        if not text.strip():
            self._render(self._all)
            return
        t = text.lower()
        filtered = [
            c for c in self._all
            if t in c["name"].lower()
            or t in (c.get("phone") or "").lower()
            or t in (c.get("email") or "").lower()
        ]
        self._render(filtered)

    def _selected_customer(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _on_selection(self):
        customer = self._selected_customer()
        self._history_table.setRowCount(0)
        if not customer:
            return
        sales = db.get_customer_sales(customer["id"])
        for s in sales:
            row = self._history_table.rowCount()
            self._history_table.insertRow(row)
            self._history_table.setItem(row, 0, QTableWidgetItem(str(s["id"])))
            amt_item = QTableWidgetItem(f"{s['total_amount']:.2f}")
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._history_table.setItem(row, 1, amt_item)
            self._history_table.setItem(row, 2, QTableWidgetItem(f"{s.get('discount',0):.1f}%"))
            pm = s.get("payment_method", "").lower()
            self._history_table.setItem(row, 3, QTableWidgetItem(PAYMENT_METHOD_AR.get(pm, pm)))
            self._history_table.setItem(row, 4, QTableWidgetItem(s.get("created_at", "")))

    def _add_customer(self):
        dlg = _CustomerDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.add_customer(**data)
            self.refresh()

    def _edit_customer(self):
        customer = self._selected_customer()
        if not customer:
            QMessageBox.information(self, "اختر عميلاً", "الرجاء اختيار عميل للتعديل.")
            return
        dlg = _CustomerDialog(customer=customer, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.update_customer(customer["id"], **data)
            self.refresh()

    def _delete_customer(self):
        customer = self._selected_customer()
        if not customer:
            QMessageBox.information(self, "اختر عميلاً", "الرجاء اختيار عميل.")
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف العميل '{customer['name']}'؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_customer(customer["id"])
            self.refresh()


class _CustomerDialog(QDialog):
    def __init__(self, customer: dict = None, parent=None):
        super().__init__(parent)
        self._customer = customer
        self.setWindowTitle("تعديل عميل" if customer else "إضافة عميل")
        self.setMinimumWidth(350)
        self._build_ui()
        if customer:
            self._populate(customer)

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self._name = QLineEdit()
        self._phone = QLineEdit()
        self._email = QLineEdit()

        layout.addRow("الاسم *:", self._name)
        layout.addRow("الهاتف:", self._phone)
        layout.addRow("البريد الإلكتروني:", self._email)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("حفظ")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self, c: dict):
        self._name.setText(c["name"])
        self._phone.setText(c.get("phone") or "")
        self._email.setText(c.get("email") or "")

    def _validate(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "تحقق", "اسم العميل مطلوب.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip(),
            "phone": self._phone.text().strip() or None,
            "email": self._email.text().strip() or None,
        }
