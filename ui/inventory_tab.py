"""تبويب المخزون — المنتجات + أوامر الشراء."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QDoubleSpinBox, QHeaderView, QMessageBox, QDialog,
    QGridLayout, QGroupBox, QTabWidget, QDialogButtonBox,
    QFormLayout, QSpinBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import database.db as db


CATEGORIES = ["طعام ومشروبات", "إلكترونيات", "ملابس", "صحة وجمال",
              "منزل وحديقة", "مستلزمات مكتبية", "أخرى"]
UNITS = ["قطعة", "كجم", "جرام", "لتر", "مل", "متر", "سم", "صندوق", "علبة", "دستة"]


class InventoryTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        sub_tabs = QTabWidget()
        self._products_widget = _ProductsSubTab()
        self._orders_widget = _PurchaseOrdersSubTab(self._products_widget)
        sub_tabs.addTab(self._products_widget, "المنتجات")
        sub_tabs.addTab(self._orders_widget, "أوامر الشراء")
        layout.addWidget(sub_tabs)

    def refresh(self):
        self._products_widget.refresh()
        self._orders_widget.refresh()


# ──────────────────────────────────────────────────────────────
# تبويب المنتجات الفرعي
# ──────────────────────────────────────────────────────────────

class _ProductsSubTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        # شريط الملخص
        self._summary_bar = QHBoxLayout()
        self._lbl_total_products = QLabel("إجمالي المنتجات: 0")
        self._lbl_total_products.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#1e3a5f; padding:4px 12px;"
            "background:#e8f4fd; border-radius:4px;"
        )
        self._lbl_stock_value = QLabel("قيمة المخزون: 0.00")
        self._lbl_stock_value.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#2e7d32; padding:4px 12px;"
            "background:#e8f5e9; border-radius:4px;"
        )
        self._lbl_low_stock = QLabel("مخزون منخفض: 0")
        self._lbl_low_stock.setStyleSheet(
            "font-size:13px; font-weight:bold; color:#e65100; padding:4px 12px;"
            "background:#fff3e0; border-radius:4px;"
        )
        self._summary_bar.addWidget(self._lbl_total_products)
        self._summary_bar.addWidget(self._lbl_stock_value)
        self._summary_bar.addWidget(self._lbl_low_stock)
        self._summary_bar.addStretch()
        layout.addLayout(self._summary_bar)

        # شريط الأدوات
        toolbar = QHBoxLayout()
        self._search = QLineEdit()
        self._search.setPlaceholderText("بحث بالاسم أو رمز المنتج...")
        self._search.textChanged.connect(self._filter)
        toolbar.addWidget(QLabel("بحث:"))
        toolbar.addWidget(self._search)
        toolbar.addStretch()

        add_btn = QPushButton("إضافة منتج")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add_product)
        edit_btn = QPushButton("تعديل")
        edit_btn.clicked.connect(self._edit_product)
        del_btn = QPushButton("حذف")
        del_btn.setObjectName("dangerBtn")
        del_btn.clicked.connect(self._delete_product)
        toolbar.addWidget(add_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(del_btn)
        layout.addLayout(toolbar)

        # الجدول
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels(
            ["رمز المنتج", "الاسم", "الفئة", "التكلفة", "سعر البيع", "المخزون", "الوحدة", "تنبيه المخزون"]
        )
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def refresh(self):
        self._all = db.get_all_products()
        self._render(self._all)
        self._update_summary(self._all)

    def _update_summary(self, products: list):
        total = len(products)
        stock_value = sum(p.get("stock_qty", 0) * p.get("cost_price", 0) for p in products)
        low_count = sum(1 for p in products if p.get("stock_qty", 0) <= p.get("low_stock_alert", 5))
        self._lbl_total_products.setText(f"إجمالي المنتجات: {total}")
        self._lbl_stock_value.setText(f"قيمة المخزون: {stock_value:,.2f}")
        color = "#e53935" if low_count > 0 else "#2e7d32"
        self._lbl_low_stock.setText(f"مخزون منخفض: {low_count}")
        self._lbl_low_stock.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{color}; padding:4px 12px;"
            "background:#fff3e0; border-radius:4px;"
        )

    def _render(self, products):
        self._table.setRowCount(0)
        for p in products:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(p.get("sku") or ""))
            self._table.setItem(row, 1, QTableWidgetItem(p["name"]))
            self._table.setItem(row, 2, QTableWidgetItem(p.get("category") or ""))
            self._table.setItem(row, 3, QTableWidgetItem(f"{p['cost_price']:.2f}"))
            self._table.setItem(row, 4, QTableWidgetItem(f"{p['sell_price']:.2f}"))
            stock_item = QTableWidgetItem(f"{p['stock_qty']:.2f}")
            if p["stock_qty"] <= 0:
                stock_item.setBackground(QColor("#ffcdd2"))
                stock_item.setForeground(QColor("#c62828"))
            elif p["stock_qty"] <= p.get("low_stock_alert", 5):
                stock_item.setBackground(QColor("#ffe0b2"))
                stock_item.setForeground(QColor("#e65100"))
            self._table.setItem(row, 5, stock_item)
            self._table.setItem(row, 6, QTableWidgetItem(p.get("unit") or "قطعة"))
            self._table.setItem(row, 7, QTableWidgetItem(f"{p.get('low_stock_alert',5):.1f}"))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p)

    def _filter(self, text):
        if text.strip():
            filtered = db.search_products(text.strip())
            self._render(filtered)
        else:
            self._render(self._all)

    def _selected_product(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _add_product(self):
        dlg = _ProductDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.add_product(**data)
            self.refresh()

    def _edit_product(self):
        product = self._selected_product()
        if not product:
            QMessageBox.information(self, "اختر منتجاً", "الرجاء اختيار منتج للتعديل.")
            return
        dlg = _ProductDialog(product=product, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.update_product(product["id"], **data)
            self.refresh()

    def _delete_product(self):
        product = self._selected_product()
        if not product:
            QMessageBox.information(self, "اختر منتجاً", "الرجاء اختيار منتج للحذف.")
            return
        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"هل تريد حذف المنتج '{product['name']}'؟ لا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            db.delete_product(product["id"])
            self.refresh()


class _ProductDialog(QDialog):
    def __init__(self, product: dict = None, parent=None):
        super().__init__(parent)
        self._product = product
        self.setWindowTitle("تعديل منتج" if product else "إضافة منتج")
        self.setMinimumWidth(400)
        self._build_ui()
        if product:
            self._populate(product)

    def _build_ui(self):
        layout = QFormLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self._name = QLineEdit()
        self._sku = QLineEdit()
        self._category = QComboBox()
        self._category.addItems(CATEGORIES)
        self._category.setEditable(True)
        self._cost = QDoubleSpinBox()
        self._cost.setRange(0, 999999)
        self._cost.setDecimals(2)
        self._sell = QDoubleSpinBox()
        self._sell.setRange(0, 999999)
        self._sell.setDecimals(2)
        self._stock = QDoubleSpinBox()
        self._stock.setRange(0, 999999)
        self._stock.setDecimals(2)
        self._low_alert = QDoubleSpinBox()
        self._low_alert.setRange(0, 999999)
        self._low_alert.setDecimals(1)
        self._low_alert.setValue(5)
        self._unit = QComboBox()
        self._unit.addItems(UNITS)
        self._unit.setEditable(True)

        layout.addRow("الاسم *:", self._name)
        layout.addRow("رمز المنتج:", self._sku)
        layout.addRow("الفئة:", self._category)
        layout.addRow("التكلفة:", self._cost)
        layout.addRow("سعر البيع:", self._sell)
        layout.addRow("الكمية:", self._stock)
        layout.addRow("الوحدة:", self._unit)
        layout.addRow("تنبيه المخزون المنخفض:", self._low_alert)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("حفظ")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _populate(self, p: dict):
        self._name.setText(p["name"])
        self._sku.setText(p.get("sku") or "")
        idx = self._category.findText(p.get("category") or "")
        if idx >= 0:
            self._category.setCurrentIndex(idx)
        else:
            self._category.setCurrentText(p.get("category") or "")
        self._cost.setValue(p["cost_price"])
        self._sell.setValue(p["sell_price"])
        self._stock.setValue(p["stock_qty"])
        self._low_alert.setValue(p.get("low_stock_alert", 5))
        idx2 = self._unit.findText(p.get("unit") or "قطعة")
        if idx2 >= 0:
            self._unit.setCurrentIndex(idx2)
        else:
            self._unit.setCurrentText(p.get("unit") or "قطعة")

    def _validate_and_accept(self):
        if not self._name.text().strip():
            QMessageBox.warning(self, "تحقق", "اسم المنتج مطلوب.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "name": self._name.text().strip(),
            "sku": self._sku.text().strip() or None,
            "category": self._category.currentText().strip() or None,
            "cost_price": self._cost.value(),
            "sell_price": self._sell.value(),
            "stock_qty": self._stock.value(),
            "low_stock_alert": self._low_alert.value(),
            "unit": self._unit.currentText().strip() or "قطعة",
        }


# ──────────────────────────────────────────────────────────────
# تبويب أوامر الشراء الفرعي
# ──────────────────────────────────────────────────────────────

class _PurchaseOrdersSubTab(QWidget):
    def __init__(self, products_tab: _ProductsSubTab, parent=None):
        super().__init__(parent)
        self._products_tab = products_tab
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)

        toolbar = QHBoxLayout()
        new_btn = QPushButton("أمر شراء جديد")
        new_btn.setObjectName("successBtn")
        new_btn.clicked.connect(self._new_order)
        toolbar.addWidget(new_btn)
        view_btn = QPushButton("عرض البنود")
        view_btn.clicked.connect(self._view_items)
        toolbar.addWidget(view_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["رقم الأمر", "المورد", "إجمالي التكلفة", "ملاحظات", "التاريخ"]
        )
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        layout.addWidget(self._table)

    def refresh(self):
        orders = db.get_all_purchase_orders()
        self._table.setRowCount(0)
        for o in orders:
            row = self._table.rowCount()
            self._table.insertRow(row)
            self._table.setItem(row, 0, QTableWidgetItem(str(o["id"])))
            self._table.setItem(row, 1, QTableWidgetItem(o.get("supplier") or ""))
            self._table.setItem(row, 2, QTableWidgetItem(f"{o['total_cost']:.2f}"))
            self._table.setItem(row, 3, QTableWidgetItem(o.get("notes") or ""))
            self._table.setItem(row, 4, QTableWidgetItem(o.get("created_at") or ""))
            self._table.item(row, 0).setData(Qt.ItemDataRole.UserRole, o)

    def _selected_order(self):
        row = self._table.currentRow()
        if row < 0:
            return None
        item = self._table.item(row, 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _new_order(self):
        dlg = _PurchaseOrderDialog(parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            data = dlg.get_data()
            db.create_purchase_order(data["supplier"], data["notes"], data["items"])
            self.refresh()
            self._products_tab.refresh()

    def _view_items(self):
        order = self._selected_order()
        if not order:
            QMessageBox.information(self, "اختر أمراً", "الرجاء اختيار أمر شراء.")
            return
        items = db.get_purchase_order_items(order["id"])
        dlg = _OrderItemsDialog(order, items, self)
        dlg.exec()


class _PurchaseOrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("أمر شراء جديد")
        self.setMinimumSize(600, 500)
        self._items: list[dict] = []
        self._build_ui()
        self._load_products()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        self._supplier = QLineEdit()
        self._notes = QLineEdit()
        form.addRow("المورد:", self._supplier)
        form.addRow("ملاحظات:", self._notes)
        layout.addLayout(form)

        add_group = QGroupBox("إضافة بند")
        add_layout = QHBoxLayout(add_group)
        self._product_combo = QComboBox()
        self._product_combo.setMinimumWidth(200)
        self._qty_spin = QDoubleSpinBox()
        self._qty_spin.setRange(0.01, 999999)
        self._qty_spin.setValue(1)
        self._qty_spin.setDecimals(2)
        self._cost_spin = QDoubleSpinBox()
        self._cost_spin.setRange(0, 999999)
        self._cost_spin.setDecimals(2)
        add_item_btn = QPushButton("إضافة بند")
        add_item_btn.setObjectName("successBtn")
        add_item_btn.clicked.connect(self._add_item)

        add_layout.addWidget(QLabel("المنتج:"))
        add_layout.addWidget(self._product_combo)
        add_layout.addWidget(QLabel("الكمية:"))
        add_layout.addWidget(self._qty_spin)
        add_layout.addWidget(QLabel("سعر الوحدة:"))
        add_layout.addWidget(self._cost_spin)
        add_layout.addWidget(add_item_btn)
        layout.addWidget(add_group)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(5)
        self._items_table.setHorizontalHeaderLabels(
            ["المنتج", "الكمية", "سعر الوحدة", "الإجمالي الفرعي", ""]
        )
        self._items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._items_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self._items_table)

        self._total_label = QLabel("الإجمالي: 0.00")
        self._total_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e3a5f;")
        layout.addWidget(self._total_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("حفظ")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("إلغاء")
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load_products(self):
        self._products = db.get_all_products()
        self._product_combo.clear()
        for p in self._products:
            self._product_combo.addItem(f"{p['name']} ({p.get('sku','') or ''})", p["id"])

    def _add_item(self):
        pid = self._product_combo.currentData()
        product = next((p for p in self._products if p["id"] == pid), None)
        if not product:
            return
        qty = self._qty_spin.value()
        cost = self._cost_spin.value()
        self._items.append({
            "product_id": pid,
            "product_name": product["name"],
            "quantity": qty,
            "unit_cost": cost,
        })
        self._refresh_items_table()

    def _refresh_items_table(self):
        self._items_table.setRowCount(0)
        total = 0.0
        for idx, item in enumerate(self._items):
            row = self._items_table.rowCount()
            self._items_table.insertRow(row)
            self._items_table.setItem(row, 0, QTableWidgetItem(item["product_name"]))
            self._items_table.setItem(row, 1, QTableWidgetItem(f"{item['quantity']:.2f}"))
            self._items_table.setItem(row, 2, QTableWidgetItem(f"{item['unit_cost']:.2f}"))
            subtotal = item["quantity"] * item["unit_cost"]
            total += subtotal
            self._items_table.setItem(row, 3, QTableWidgetItem(f"{subtotal:.2f}"))
            rm_btn = QPushButton("✕")
            rm_btn.setObjectName("dangerBtn")
            rm_btn.setFixedWidth(36)
            rm_btn.clicked.connect(lambda _, i=idx: self._remove_item(i))
            self._items_table.setCellWidget(row, 4, rm_btn)
        self._total_label.setText(f"الإجمالي: {total:.2f}")

    def _remove_item(self, index: int):
        if 0 <= index < len(self._items):
            self._items.pop(index)
            self._refresh_items_table()

    def _validate_and_accept(self):
        if not self._items:
            QMessageBox.warning(self, "لا توجد بنود", "أضف بنداً واحداً على الأقل.")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "supplier": self._supplier.text().strip() or None,
            "notes": self._notes.text().strip() or None,
            "items": self._items,
        }


class _OrderItemsDialog(QDialog):
    def __init__(self, order: dict, items: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"أمر رقم #{order['id']} — {order.get('supplier','') or 'بدون مورد'}")
        self.setMinimumSize(500, 350)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"<b>المورد:</b> {order.get('supplier','') or 'غير محدد'}"))
        layout.addWidget(QLabel(f"<b>التاريخ:</b> {order.get('created_at','')}"))
        layout.addWidget(QLabel(f"<b>ملاحظات:</b> {order.get('notes','') or 'لا يوجد'}"))

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["المنتج", "الكمية", "سعر الوحدة", "الإجمالي الفرعي"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for item in items:
            row = table.rowCount()
            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(item.get("product_name", "")))
            table.setItem(row, 1, QTableWidgetItem(f"{item['quantity']:.2f} {item.get('unit','')}"))
            table.setItem(row, 2, QTableWidgetItem(f"{item['unit_cost']:.2f}"))
            table.setItem(row, 3, QTableWidgetItem(f"{item['quantity']*item['unit_cost']:.2f}"))
        layout.addWidget(table)

        layout.addWidget(QLabel(f"<b>الإجمالي: {order['total_cost']:.2f}</b>"))
        close_btn = QPushButton("إغلاق")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
