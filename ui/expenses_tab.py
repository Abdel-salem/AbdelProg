"""تبويب المصروفات — تسجيل وإدارة المصروفات التشغيلية."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QDialog, QFormLayout, QDialogButtonBox,
    QComboBox, QDoubleSpinBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate

import database.db as db


EXPENSE_CATEGORIES = ["إيجار", "مرافق", "رواتب", "مستلزمات", "تسويق", "أخرى"]


class ExpensesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        toolbar = QHBoxLayout()
        add_btn = QPushButton("إضافة مصروف")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add_expense)
        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self._edit_expense)
        del_btn = QPushButton("حذف")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_expense)

        self._search = QLineEdit()
        self._search.setPlaceholderText("تصفية حسب الفئة أو الوصف...")
        self._search.textChanged.connect(self._filter)
        toolbar.addWidget(QLabel("بحث:"))
        toolbar.addWidget(self._search)
        toolbar.addStretch()
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["التاريخ", "الفئة", "الوصف", "المبلغ", "ID"]
        )
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.setColumnHidden(4, True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

        # شريط الملخص
        summary_row = QHBoxLayout()
        self._total_label = QLabel("الإجمالي: 0.00")
        self._total_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #1e3a5f;")
        summary_row.addStretch()
        summary_row.addWidget(self._total_label)
        layout.addLayout(summary_row)

    def refresh(self):
        self._all = db.get_all_expenses()
        self._render(self._all)

    def _render(self, expenses: list):
        self._table.setRowCount(0)
        total = 0.0
        for e in expenses:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(e.get("date", "")))
            self._table.setItem(row, 1, QTableWidgetItem(e.get("category", "")))
            self._table.setItem(row, 2, QTableWidgetItem(e.get("description", "") or ""))
            amt_item = QTableWidgetItem(f"{e.get('amount', 0):.2f}")
            amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 3, amt_item)
            self._table.setItem(row, 4, QTableWidgetItem(str(e["id"])))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, e)
            total += e.get("amount", 0)
        self._total_label.setText(f"الإجمالي: {total:,.2f}")

    def _filter(self, text: str):
        if not text.strip():
            self._render(self._all)
            return
        t = text.lower()
        filtered = [
            e for e in self._all
            if t in e.get("category", "").lower()
            or t in (e.get("description", "") or "").lower()
        ]
        self._render(filtered)

    def _selected_expense(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_expense(self):
        dlg = _ExpenseDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.add_expense(**data)
            self.refresh()

    def _edit_expense(self):
        expense = self._selected_expense()
        if not expense:
            QMessageBox.information(self, "اختر مصروفاً", "الرجاء اختيار مصروف للتعديل.")
            return
        dlg = _ExpenseDialog(expense=expense, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.update_expense(expense["id"], **data)
            self.refresh()

    def _delete_expense(self):
        expense = self._selected_expense()
        if not expense:
            QMessageBox.information(self, "اختر مصروفاً", "الرجاء اختيار مصروف.")
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف المصروف '{expense.get('description','') or expense['category']}' ({expense['amount']:.2f})؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_expense(expense["id"])
            self.refresh()


class _ExpenseDialog(QDialog):
    def __init__(self, expense: dict = None, parent=None):
        super().__init__(parent)
        self._expense = expense
        self.setWindowTitle("تعديل مصروف" if expense else "إضافة مصروف")
        self.setMinimumWidth(360)
        self._build_ui()
        if expense:
            self._populate(expense)

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("yyyy-MM-dd")
        self._date.setDate(QDate.currentDate())

        self._category = QComboBox()
        self._category.addItems(EXPENSE_CATEGORIES)
        self._category.setEditable(True)

        self._description = QLineEdit()
        self._description.setPlaceholderText("وصف اختياري")

        self._amount = QDoubleSpinBox()
        self._amount.setRange(0.01, 9999999)
        self._amount.setDecimals(2)

        layout.addRow("التاريخ *:", self._date)
        layout.addRow("الفئة *:", self._category)
        layout.addRow("الوصف:", self._description)
        layout.addRow("المبلغ *:", self._amount)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("حفظ")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self, e: dict):
        try:
            from PyQt6.QtCore import QDate
            parts = e.get("date", "").split("-")
            if len(parts) == 3:
                self._date.setDate(QDate(int(parts[0]), int(parts[1]), int(parts[2])))
        except Exception:
            pass
        idx = self._category.findText(e.get("category", ""))
        if idx >= 0:
            self._category.setCurrentIndex(idx)
        else:
            self._category.setCurrentText(e.get("category", ""))
        self._description.setText(e.get("description", "") or "")
        self._amount.setValue(e.get("amount", 0))

    def _validate(self):
        if self._amount.value() <= 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "تحقق", "يجب أن يكون المبلغ أكبر من صفر.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "category": self._category.currentText().strip(),
            "description": self._description.text().strip() or None,
            "amount": self._amount.value(),
            "date": self._date.date().toString("yyyy-MM-dd"),
        }
