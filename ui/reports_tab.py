"""Reports tab — P&L summary, charts, top products, export."""

from __future__ import annotations

from datetime import date, timedelta
import os

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QDateEdit, QFileDialog, QMessageBox, QSplitter, QFrame,
    QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import database.db as db
from utils.export import export_csv, export_pdf


class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        # Load with last 30 days by default
        today = date.today()
        self._date_from.setDate(QDate(today.year, today.month, 1))
        self._date_to.setDate(QDate.currentDate())
        self._load_report()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Date range + controls
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("From:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        top_bar.addWidget(self._date_from)
        top_bar.addWidget(QLabel("To:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        top_bar.addWidget(self._date_to)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._load_report)
        top_bar.addWidget(refresh_btn)
        top_bar.addStretch()

        csv_btn = QPushButton("Export CSV")
        csv_btn.setObjectName("secondaryBtn")
        csv_btn.clicked.connect(self._export_csv)
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.setObjectName("secondaryBtn")
        pdf_btn.clicked.connect(self._export_pdf)
        top_bar.addWidget(csv_btn)
        top_bar.addWidget(pdf_btn)
        layout.addLayout(top_bar)

        # Summary cards
        self._cards_layout = QHBoxLayout()
        self._card_labels: dict[str, QLabel] = {}
        for key in ["Revenue", "COGS", "Gross Profit", "Expenses", "Net Profit"]:
            frame = QGroupBox(key)
            frame_layout = QVBoxLayout(frame)
            lbl = QLabel("$0.00")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a237e;")
            frame_layout.addWidget(lbl)
            self._cards_layout.addWidget(frame)
            self._card_labels[key] = lbl
        layout.addLayout(self._cards_layout)

        # Charts + table splitter
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Charts (left)
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)

        # Bar chart: daily revenue vs cost
        self._bar_fig = Figure(figsize=(6, 3), tight_layout=True)
        self._bar_ax = self._bar_fig.add_subplot(111)
        self._bar_canvas = FigureCanvas(self._bar_fig)
        charts_layout.addWidget(QLabel("<b>Daily Revenue vs COGS</b>"))
        charts_layout.addWidget(self._bar_canvas)

        # Pie chart: by payment method
        self._pie_fig = Figure(figsize=(4, 3), tight_layout=True)
        self._pie_ax = self._pie_fig.add_subplot(111)
        self._pie_canvas = FigureCanvas(self._pie_fig)
        charts_layout.addWidget(QLabel("<b>Sales by Payment Method</b>"))
        charts_layout.addWidget(self._pie_canvas)

        bottom_splitter.addWidget(charts_widget)

        # Top products table (right)
        top_prod_widget = QWidget()
        top_prod_layout = QVBoxLayout(top_prod_widget)
        top_prod_layout.setContentsMargins(0, 0, 0, 0)
        top_prod_layout.addWidget(QLabel("<b>Top 10 Products by Revenue</b>"))
        self._top_table = QTableWidget()
        self._top_table.setColumnCount(5)
        self._top_table.setHorizontalHeaderLabels(
            ["Product", "SKU", "Qty Sold", "Revenue", "Gross"]
        )
        self._top_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._top_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._top_table.setAlternatingRowColors(True)
        top_prod_layout.addWidget(self._top_table)

        bottom_splitter.addWidget(top_prod_widget)
        bottom_splitter.setSizes([600, 450])
        layout.addWidget(bottom_splitter)

    def _date_range(self):
        return (
            self._date_from.date().toString("yyyy-MM-dd"),
            self._date_to.date().toString("yyyy-MM-dd"),
        )

    def _load_report(self):
        date_from, date_to = self._date_range()
        summary = db.get_pnl_summary(date_from, date_to)

        colors_map = {
            "Revenue": "#43a047",
            "COGS": "#e53935",
            "Gross Profit": "#1e88e5",
            "Expenses": "#fb8c00",
            "Net Profit": "#6d4c41" if summary["net_profit"] < 0 else "#1a237e",
        }
        for key, lbl in self._card_labels.items():
            db_key = key.lower().replace(" ", "_")
            val = summary.get(db_key, 0)
            lbl.setText(f"${val:,.2f}")
            lbl.setStyleSheet(
                f"font-size: 20px; font-weight: bold; color: {colors_map.get(key,'#1a237e')};"
            )

        self._draw_bar_chart(date_from, date_to)
        self._draw_pie_chart(date_from, date_to)
        self._load_top_products(date_from, date_to)

    def _draw_bar_chart(self, date_from, date_to):
        data = db.get_daily_revenue_cost(date_from, date_to)
        self._bar_ax.clear()
        if data:
            days = [d["day"] for d in data]
            revenues = [d["revenue"] for d in data]
            cogs = [d["cogs"] for d in data]
            x = range(len(days))
            width = 0.35
            self._bar_ax.bar([i - width/2 for i in x], revenues, width,
                             label="Revenue", color="#3949ab", alpha=0.85)
            self._bar_ax.bar([i + width/2 for i in x], cogs, width,
                             label="COGS", color="#e53935", alpha=0.85)
            self._bar_ax.set_xticks(list(x))
            self._bar_ax.set_xticklabels(days, rotation=45, ha="right", fontsize=8)
            self._bar_ax.legend(fontsize=8)
            self._bar_ax.set_ylabel("Amount ($)", fontsize=9)
            self._bar_ax.grid(axis="y", alpha=0.3)
        else:
            self._bar_ax.text(0.5, 0.5, "No data", transform=self._bar_ax.transAxes,
                              ha="center", va="center", color="grey")
        self._bar_canvas.draw()

    def _draw_pie_chart(self, date_from, date_to):
        data = db.get_sales_by_payment_method(date_from, date_to)
        self._pie_ax.clear()
        if data:
            labels = [d["payment_method"].capitalize() for d in data]
            sizes = [d["total"] for d in data]
            colors = ["#3949ab", "#43a047", "#fb8c00"]
            self._pie_ax.pie(sizes, labels=labels, autopct="%1.1f%%",
                             colors=colors[:len(sizes)], startangle=140)
        else:
            self._pie_ax.text(0.5, 0.5, "No data", transform=self._pie_ax.transAxes,
                              ha="center", va="center", color="grey")
        self._pie_canvas.draw()

    def _load_top_products(self, date_from, date_to):
        products = db.get_top_products(date_from, date_to, limit=10)
        self._top_table.setRowCount(0)
        for p in products:
            row = self._top_table.rowCount()
            self._top_table.insertRow(row)
            self._top_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self._top_table.setItem(row, 1, QTableWidgetItem(p.get("sku") or ""))
            self._top_table.setItem(row, 2, QTableWidgetItem(f"{p['qty_sold']:.1f}"))
            self._top_table.setItem(row, 3, QTableWidgetItem(f"${p['revenue']:.2f}"))
            gross = p["revenue"] - p["cogs"]
            gross_item = QTableWidgetItem(f"${gross:.2f}")
            if gross < 0:
                gross_item.setForeground(QColor("#e53935"))
            else:
                gross_item.setForeground(QColor("#2e7d32"))
            self._top_table.setItem(row, 4, gross_item)

    def _export_csv(self):
        date_from, date_to = self._date_range()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", f"report_{date_from}_{date_to}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            summary = db.get_pnl_summary(date_from, date_to)
            top = db.get_top_products(date_from, date_to)
            expenses = db.get_expenses_for_period(date_from, date_to)

            summary_rows = [
                {"metric": k, "value": v} for k, v in summary.items()
            ]
            base, ext = os.path.splitext(path)
            export_csv(summary_rows, f"{base}_summary{ext}")
            export_csv(top, f"{base}_top_products{ext}")
            export_csv(expenses, f"{base}_expenses{ext}")
            QMessageBox.information(self, "Export Done",
                                    f"Files saved to:\n{base}_summary{ext}\n"
                                    f"{base}_top_products{ext}\n{base}_expenses{ext}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _export_pdf(self):
        date_from, date_to = self._date_range()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"report_{date_from}_{date_to}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        try:
            report_data = {
                "date_from": date_from,
                "date_to": date_to,
                "summary": db.get_pnl_summary(date_from, date_to),
                "top_products": db.get_top_products(date_from, date_to),
                "expenses": db.get_expenses_for_period(date_from, date_to),
            }
            export_pdf(report_data, path)
            QMessageBox.information(self, "Export Done", f"PDF saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
