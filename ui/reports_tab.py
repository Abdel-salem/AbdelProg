"""تبويب التقارير — ملخص الأرباح والخسائر، الرسوم البيانية، أفضل المنتجات، التصدير."""

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

SUMMARY_KEYS = {
    "الإيرادات": ("revenue", "#43a047"),
    "تكلفة المبيعات": ("cogs", "#e53935"),
    "الربح الإجمالي": ("gross_profit", "#1e88e5"),
    "المصروفات": ("expenses", "#fb8c00"),
    "صافي الربح": ("net_profit", "#1e3a5f"),
}


class ReportsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        today = date.today()
        self._date_from.setDate(QDate(today.year, today.month, 1))
        self._date_to.setDate(QDate.currentDate())
        self._load_report()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # شريط التاريخ والأدوات
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("من:"))
        self._date_from = QDateEdit()
        self._date_from.setCalendarPopup(True)
        self._date_from.setDisplayFormat("yyyy-MM-dd")
        top_bar.addWidget(self._date_from)
        top_bar.addWidget(QLabel("إلى:"))
        self._date_to = QDateEdit()
        self._date_to.setCalendarPopup(True)
        self._date_to.setDisplayFormat("yyyy-MM-dd")
        top_bar.addWidget(self._date_to)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self._load_report)
        top_bar.addWidget(refresh_btn)
        top_bar.addStretch()

        csv_btn = QPushButton("تصدير CSV")
        csv_btn.setObjectName("secondaryBtn")
        csv_btn.clicked.connect(self._export_csv)
        pdf_btn = QPushButton("تصدير PDF")
        pdf_btn.setObjectName("secondaryBtn")
        pdf_btn.clicked.connect(self._export_pdf)
        top_bar.addWidget(csv_btn)
        top_bar.addWidget(pdf_btn)
        layout.addLayout(top_bar)

        # بطاقات الملخص
        self._cards_layout = QHBoxLayout()
        self._card_labels: dict[str, QLabel] = {}
        for ar_key, (db_key, color) in SUMMARY_KEYS.items():
            frame = QGroupBox(ar_key)
            frame_layout = QVBoxLayout(frame)
            lbl = QLabel("0.00")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
            frame_layout.addWidget(lbl)
            self._cards_layout.addWidget(frame)
            self._card_labels[ar_key] = lbl
        layout.addLayout(self._cards_layout)

        # الرسوم البيانية + الجداول
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)

        # الرسوم البيانية (اليسار)
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)

        # الرسم البياني الشريطي: الإيرادات اليومية مقابل التكلفة
        self._bar_fig = Figure(figsize=(6, 2.8), tight_layout=True)
        self._bar_ax = self._bar_fig.add_subplot(111)
        self._bar_canvas = FigureCanvas(self._bar_fig)
        charts_layout.addWidget(QLabel("<b>الإيرادات اليومية مقابل تكلفة المبيعات</b>"))
        charts_layout.addWidget(self._bar_canvas)

        # الرسم البياني الدائري: حسب طريقة الدفع
        self._pie_fig = Figure(figsize=(4, 2.6), tight_layout=True)
        self._pie_ax = self._pie_fig.add_subplot(111)
        self._pie_canvas = FigureCanvas(self._pie_fig)
        charts_layout.addWidget(QLabel("<b>توزيع طرق الدفع</b>"))
        charts_layout.addWidget(self._pie_canvas)

        # الرسم البياني الخطي: الإيرادات الشهرية
        self._line_fig = Figure(figsize=(6, 2.5), tight_layout=True)
        self._line_ax = self._line_fig.add_subplot(111)
        self._line_canvas = FigureCanvas(self._line_fig)
        charts_layout.addWidget(QLabel("<b>اتجاه الإيرادات الشهرية</b>"))
        charts_layout.addWidget(self._line_canvas)

        bottom_splitter.addWidget(charts_widget)

        # أفضل المنتجات (اليمين)
        top_prod_widget = QWidget()
        top_prod_layout = QVBoxLayout(top_prod_widget)
        top_prod_layout.setContentsMargins(0, 0, 0, 0)
        top_prod_layout.addWidget(QLabel("<b>أفضل 10 منتجات من حيث الإيرادات</b>"))
        self._top_table = QTableWidget()
        self._top_table.setColumnCount(5)
        self._top_table.setHorizontalHeaderLabels(
            ["المنتج", "رمز المنتج", "الكمية المباعة", "الإيرادات", "الربح الإجمالي"]
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

    def refresh(self):
        self._load_report()

    def _load_report(self):
        date_from, date_to = self._date_range()
        summary = db.get_pnl_summary(date_from, date_to)

        net = summary.get("net_profit", 0)
        for ar_key, (db_key, color) in SUMMARY_KEYS.items():
            lbl = self._card_labels[ar_key]
            val = summary.get(db_key, 0)
            actual_color = "#e53935" if db_key == "net_profit" and val < 0 else color
            lbl.setText(f"{val:,.2f}")
            lbl.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {actual_color};")

        self._draw_bar_chart(date_from, date_to)
        self._draw_pie_chart(date_from, date_to)
        self._draw_line_chart()
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
                             label="الإيرادات", color="#1e3a5f", alpha=0.85)
            self._bar_ax.bar([i + width/2 for i in x], cogs, width,
                             label="تكلفة المبيعات", color="#e53935", alpha=0.85)
            self._bar_ax.set_xticks(list(x))
            self._bar_ax.set_xticklabels(days, rotation=45, ha="right", fontsize=8)
            self._bar_ax.legend(fontsize=8)
            self._bar_ax.set_ylabel("المبلغ", fontsize=9)
            self._bar_ax.grid(axis="y", alpha=0.3)
        else:
            self._bar_ax.text(0.5, 0.5, "لا توجد بيانات", transform=self._bar_ax.transAxes,
                              ha="center", va="center", color="grey")
        self._bar_canvas.draw()

    def _draw_pie_chart(self, date_from, date_to):
        data = db.get_sales_by_payment_method(date_from, date_to)
        pm_ar = {"cash": "نقداً", "card": "بطاقة", "mobile": "محفظة إلكترونية"}
        self._pie_ax.clear()
        if data:
            labels = [pm_ar.get(d["payment_method"].lower(), d["payment_method"]) for d in data]
            sizes = [d["total"] for d in data]
            colors = ["#1e3a5f", "#43a047", "#f0a500"]
            self._pie_ax.pie(sizes, labels=labels, autopct="%1.1f%%",
                             colors=colors[:len(sizes)], startangle=140)
        else:
            self._pie_ax.text(0.5, 0.5, "لا توجد بيانات", transform=self._pie_ax.transAxes,
                              ha="center", va="center", color="grey")
        self._pie_canvas.draw()

    def _draw_line_chart(self):
        data = db.get_monthly_revenue(12)
        self._line_ax.clear()
        if data:
            months = [d["month"] for d in data]
            revenues = [d["revenue"] for d in data]
            self._line_ax.plot(months, revenues, marker="o", color="#f0a500",
                               linewidth=2, markersize=5)
            self._line_ax.fill_between(months, revenues, alpha=0.15, color="#f0a500")
            self._line_ax.set_xticks(range(len(months)))
            self._line_ax.set_xticklabels(months, rotation=45, ha="right", fontsize=8)
            self._line_ax.set_ylabel("الإيرادات", fontsize=9)
            self._line_ax.grid(axis="y", alpha=0.3)
        else:
            self._line_ax.text(0.5, 0.5, "لا توجد بيانات", transform=self._line_ax.transAxes,
                               ha="center", va="center", color="grey")
        self._line_canvas.draw()

    def _load_top_products(self, date_from, date_to):
        products = db.get_top_products(date_from, date_to, limit=10)
        self._top_table.setRowCount(0)
        for p in products:
            row = self._top_table.rowCount()
            self._top_table.insertRow(row)
            self._top_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self._top_table.setItem(row, 1, QTableWidgetItem(p.get("sku") or ""))
            self._top_table.setItem(row, 2, QTableWidgetItem(f"{p['qty_sold']:.1f}"))
            self._top_table.setItem(row, 3, QTableWidgetItem(f"{p['revenue']:.2f}"))
            gross = p["revenue"] - p["cogs"]
            gross_item = QTableWidgetItem(f"{gross:.2f}")
            if gross < 0:
                gross_item.setForeground(QColor("#e53935"))
            else:
                gross_item.setForeground(QColor("#2e7d32"))
            self._top_table.setItem(row, 4, gross_item)

    def _export_csv(self):
        date_from, date_to = self._date_range()
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير CSV", f"تقرير_{date_from}_{date_to}.csv",
            "CSV Files (*.csv)"
        )
        if not path:
            return
        try:
            summary = db.get_pnl_summary(date_from, date_to)
            top = db.get_top_products(date_from, date_to)
            expenses = db.get_expenses_for_period(date_from, date_to)

            summary_rows = [{"المؤشر": k, "القيمة": v} for k, v in summary.items()]
            base, ext = os.path.splitext(path)
            export_csv(summary_rows, f"{base}_ملخص{ext}")
            export_csv(top, f"{base}_أفضل_المنتجات{ext}")
            export_csv(expenses, f"{base}_المصروفات{ext}")
            QMessageBox.information(self, "تم التصدير",
                                    f"تم حفظ الملفات في:\n{base}_ملخص{ext}\n"
                                    f"{base}_أفضل_المنتجات{ext}\n{base}_المصروفات{ext}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التصدير", str(e))

    def _export_pdf(self):
        date_from, date_to = self._date_range()
        path, _ = QFileDialog.getSaveFileName(
            self, "تصدير PDF", f"تقرير_{date_from}_{date_to}.pdf",
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
            QMessageBox.information(self, "تم التصدير", f"تم حفظ الـ PDF في:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ في التصدير", str(e))
