"""Point of Sale tab."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QDoubleSpinBox, QHeaderView, QMessageBox, QDialog,
    QGridLayout, QGroupBox, QSplitter, QSpinBox, QScrollArea,
    QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont

import database.db as db
from utils.receipt import ReceiptDialog


class CartItem:
    def __init__(self, product: dict, quantity: float = 1.0):
        self.product_id = product["id"]
        self.product_name = product["name"]
        self.unit_price = product["sell_price"]
        self.cost_price = product["cost_price"]
        self.quantity = quantity
        self.unit = product.get("unit", "pcs")
        self.stock_qty = product["stock_qty"]

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class POSTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cart: list[CartItem] = []
        self._all_products: list[dict] = []
        self._build_ui()
        self._load_products()
        self._load_customers()

    # ──────────────────────────────────────────────────────────
    # UI Construction
    # ──────────────────────────────────────────────────────────

    def _build_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left: product search + grid
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        search_row = QHBoxLayout()
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText("Search product by name or SKU...")
        self._search_box.textChanged.connect(self._filter_products)
        search_row.addWidget(QLabel("Search:"))
        search_row.addWidget(self._search_box)
        left_layout.addLayout(search_row)

        self._product_table = QTableWidget()
        self._product_table.setColumnCount(4)
        self._product_table.setHorizontalHeaderLabels(["Name", "SKU", "Price", "Stock"])
        self._product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._product_table.setAlternatingRowColors(True)
        self._product_table.doubleClicked.connect(self._add_selected_to_cart)
        left_layout.addWidget(self._product_table)

        add_btn = QPushButton("Add to Cart")
        add_btn.setObjectName("successBtn")
        add_btn.clicked.connect(self._add_selected_to_cart)
        left_layout.addWidget(add_btn)

        splitter.addWidget(left_widget)

        # Right: cart + payment
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # Customer selector
        cust_row = QHBoxLayout()
        cust_row.addWidget(QLabel("Customer:"))
        self._customer_combo = QComboBox()
        self._customer_combo.setMinimumWidth(200)
        self._customer_combo.setEditable(True)
        self._customer_combo.lineEdit().setPlaceholderText("Walk-in (optional)")
        cust_row.addWidget(self._customer_combo)
        cust_row.addStretch()
        right_layout.addLayout(cust_row)

        # Cart table
        cart_group = QGroupBox("Cart")
        cart_group_layout = QVBoxLayout(cart_group)
        self._cart_table = QTableWidget()
        self._cart_table.setColumnCount(5)
        self._cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Unit Price", "Total", ""])
        self._cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._cart_table.setColumnWidth(1, 70)
        self._cart_table.setColumnWidth(2, 90)
        self._cart_table.setColumnWidth(3, 90)
        self._cart_table.setColumnWidth(4, 60)
        self._cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._cart_table.setAlternatingRowColors(True)
        cart_group_layout.addWidget(self._cart_table)
        right_layout.addWidget(cart_group)

        # Totals + controls
        controls_group = QGroupBox("Payment")
        controls_layout = QGridLayout(controls_group)

        controls_layout.addWidget(QLabel("Discount (%):"), 0, 0)
        self._discount_spin = QDoubleSpinBox()
        self._discount_spin.setRange(0, 100)
        self._discount_spin.setDecimals(1)
        self._discount_spin.valueChanged.connect(self._update_totals)
        controls_layout.addWidget(self._discount_spin, 0, 1)

        controls_layout.addWidget(QLabel("Payment Method:"), 1, 0)
        self._payment_combo = QComboBox()
        self._payment_combo.addItems(["Cash", "Card", "Mobile"])
        controls_layout.addWidget(self._payment_combo, 1, 1)

        controls_layout.addWidget(QLabel("Cash Tendered:"), 2, 0)
        self._cash_tendered = QDoubleSpinBox()
        self._cash_tendered.setRange(0, 999999)
        self._cash_tendered.setDecimals(2)
        self._cash_tendered.valueChanged.connect(self._update_change)
        controls_layout.addWidget(self._cash_tendered, 2, 1)

        controls_layout.addWidget(QLabel("Subtotal:"), 3, 0)
        self._subtotal_label = QLabel("$0.00")
        self._subtotal_label.setStyleSheet("font-size:14px; font-weight:bold;")
        controls_layout.addWidget(self._subtotal_label, 3, 1)

        controls_layout.addWidget(QLabel("Discount:"), 4, 0)
        self._discount_label = QLabel("$0.00")
        controls_layout.addWidget(self._discount_label, 4, 1)

        controls_layout.addWidget(QLabel("TOTAL:"), 5, 0)
        self._total_label = QLabel("$0.00")
        self._total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a237e;")
        controls_layout.addWidget(self._total_label, 5, 1)

        controls_layout.addWidget(QLabel("Change:"), 6, 0)
        self._change_label = QLabel("$0.00")
        self._change_label.setStyleSheet("font-size:14px; font-weight:bold; color: #43a047;")
        controls_layout.addWidget(self._change_label, 6, 1)

        right_layout.addWidget(controls_group)

        btn_row = QHBoxLayout()
        clear_btn = QPushButton("Clear Cart")
        clear_btn.setObjectName("dangerBtn")
        clear_btn.clicked.connect(self._clear_cart)

        process_btn = QPushButton("Process Sale")
        process_btn.setObjectName("successBtn")
        process_btn.clicked.connect(self._process_sale)

        btn_row.addWidget(clear_btn)
        btn_row.addWidget(process_btn)
        right_layout.addLayout(btn_row)

        splitter.addWidget(right_widget)
        splitter.setSizes([550, 550])

    # ──────────────────────────────────────────────────────────
    # Data Loading
    # ──────────────────────────────────────────────────────────

    def _load_products(self):
        self._all_products = db.get_all_products()
        self._render_products(self._all_products)

    def _render_products(self, products: list):
        self._product_table.setRowCount(0)
        for p in products:
            row = self._product_table.rowCount()
            self._product_table.insertRow(row)
            self._product_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self._product_table.setItem(row, 1, QTableWidgetItem(p.get("sku") or ""))
            self._product_table.setItem(row, 2, QTableWidgetItem(f"${p['sell_price']:.2f}"))
            stock_item = QTableWidgetItem(f"{p['stock_qty']:.1f} {p.get('unit','pcs')}")
            if p["stock_qty"] <= 0:
                stock_item.setForeground(QColor("#e53935"))
            elif p["stock_qty"] <= p.get("low_stock_alert", 5):
                stock_item.setForeground(QColor("#f57c00"))
            self._product_table.setItem(row, 3, stock_item)
            self._product_table.item(row, 0).setData(Qt.ItemDataRole.UserRole, p)

    def _load_customers(self):
        self._customer_combo.clear()
        self._customer_combo.addItem("-- Walk-in --", None)
        for c in db.get_all_customers():
            self._customer_combo.addItem(f"{c['name']} ({c.get('phone','') or c.get('email','')})", c["id"])

    # ──────────────────────────────────────────────────────────
    # Interactions
    # ──────────────────────────────────────────────────────────

    def _filter_products(self, text: str):
        if text.strip():
            products = db.search_products(text.strip())
        else:
            products = self._all_products
        self._render_products(products)

    def _add_selected_to_cart(self):
        rows = self._product_table.selectedItems()
        if not rows:
            return
        row = self._product_table.currentRow()
        product = self._product_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not product:
            return

        if product["stock_qty"] <= 0:
            QMessageBox.warning(self, "Out of Stock", f"'{product['name']}' is out of stock.")
            return

        # Ask quantity
        qty_dialog = _QuantityDialog(product, self)
        if qty_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        qty = qty_dialog.quantity()

        # Check if already in cart
        for item in self._cart:
            if item.product_id == product["id"]:
                new_qty = item.quantity + qty
                if new_qty > product["stock_qty"]:
                    QMessageBox.warning(self, "Insufficient Stock",
                                        f"Only {product['stock_qty']:.1f} {product.get('unit','pcs')} available.")
                    return
                item.quantity = new_qty
                self._refresh_cart_table()
                self._update_totals()
                return

        if qty > product["stock_qty"]:
            QMessageBox.warning(self, "Insufficient Stock",
                                f"Only {product['stock_qty']:.1f} {product.get('unit','pcs')} available.")
            return

        self._cart.append(CartItem(product, qty))
        self._refresh_cart_table()
        self._update_totals()

    def _refresh_cart_table(self):
        self._cart_table.setRowCount(0)
        for idx, item in enumerate(self._cart):
            row = self._cart_table.rowCount()
            self._cart_table.insertRow(row)
            self._cart_table.setItem(row, 0, QTableWidgetItem(item.product_name))

            qty_item = QTableWidgetItem(f"{item.quantity:.2f}")
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._cart_table.setItem(row, 1, qty_item)

            price_item = QTableWidgetItem(f"${item.unit_price:.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._cart_table.setItem(row, 2, price_item)

            total_item = QTableWidgetItem(f"${item.line_total:.2f}")
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._cart_table.setItem(row, 3, total_item)

            remove_btn = QPushButton("✕")
            remove_btn.setObjectName("dangerBtn")
            remove_btn.setFixedWidth(36)
            remove_btn.clicked.connect(lambda checked, i=idx: self._remove_from_cart(i))
            self._cart_table.setCellWidget(row, 4, remove_btn)

    def _remove_from_cart(self, index: int):
        if 0 <= index < len(self._cart):
            self._cart.pop(index)
            self._refresh_cart_table()
            self._update_totals()

    def _update_totals(self):
        subtotal = sum(item.line_total for item in self._cart)
        discount_pct = self._discount_spin.value()
        discount_amt = subtotal * discount_pct / 100
        total = subtotal - discount_amt

        self._subtotal_label.setText(f"${subtotal:.2f}")
        self._discount_label.setText(f"-${discount_amt:.2f}")
        self._total_label.setText(f"${total:.2f}")
        self._update_change()

    def _update_change(self):
        try:
            total_text = self._total_label.text().replace("$", "")
            total = float(total_text)
        except ValueError:
            total = 0.0
        tendered = self._cash_tendered.value()
        change = tendered - total if tendered >= total else 0
        self._change_label.setText(f"${change:.2f}")

    def _clear_cart(self):
        self._cart.clear()
        self._refresh_cart_table()
        self._update_totals()
        self._discount_spin.setValue(0)
        self._cash_tendered.setValue(0)

    def _process_sale(self):
        if not self._cart:
            QMessageBox.warning(self, "Empty Cart", "Add items to the cart before processing.")
            return

        # Validate stock again
        for item in self._cart:
            fresh = db.get_product_by_id(item.product_id)
            if fresh["stock_qty"] < item.quantity:
                QMessageBox.critical(
                    self, "Insufficient Stock",
                    f"Only {fresh['stock_qty']:.1f} {fresh.get('unit','pcs')} of "
                    f"'{item.product_name}' available."
                )
                return

        subtotal = sum(i.line_total for i in self._cart)
        discount_pct = self._discount_spin.value()
        discount_amt = subtotal * discount_pct / 100
        total = subtotal - discount_amt
        payment_method = self._payment_combo.currentText().lower()
        customer_id = self._customer_combo.currentData()

        items_data = [
            {
                "product_id": ci.product_id,
                "quantity": ci.quantity,
                "unit_price": ci.unit_price,
                "cost_price": ci.cost_price,
            }
            for ci in self._cart
        ]

        sale_id = db.create_sale(
            customer_id=customer_id,
            total_amount=total,
            discount=discount_pct,
            payment_method=payment_method,
            items=items_data,
        )

        if customer_id:
            # 1 point per dollar
            db.add_loyalty_points(customer_id, int(total))

        sale, sale_items = db.get_sale_with_items(sale_id)
        customer = db.get_customer_by_id(customer_id) if customer_id else None

        receipt_dlg = ReceiptDialog(sale, sale_items, customer, self)
        receipt_dlg.exec()

        self._clear_cart()
        self._load_products()  # refresh stock display


# ──────────────────────────────────────────────────────────────
# Helper Dialog: enter quantity
# ──────────────────────────────────────────────────────────────

class _QuantityDialog(QDialog):
    def __init__(self, product: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enter Quantity")
        self.setFixedSize(300, 160)
        layout = QVBoxLayout(self)

        layout.addWidget(QLabel(f"<b>{product['name']}</b>"))
        layout.addWidget(QLabel(f"Available: {product['stock_qty']:.1f} {product.get('unit','pcs')}"))
        layout.addWidget(QLabel(f"Price: ${product['sell_price']:.2f}"))

        self._spin = QDoubleSpinBox()
        self._spin.setRange(0.01, product["stock_qty"])
        self._spin.setValue(1)
        self._spin.setDecimals(2)
        layout.addWidget(self._spin)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("Add to Cart")
        ok_btn.setObjectName("successBtn")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def quantity(self) -> float:
        return self._spin.value()
