"""أدوات تصدير CSV و PDF."""

import csv
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def export_csv(data: list[dict], filepath: str):
    """كتابة قائمة من القواميس إلى ملف CSV."""
    if not data:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            f.write("")
        return
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def export_pdf(report_data: dict, filepath: str):
    """
    إنشاء تقرير P&L بصيغة PDF باستخدام reportlab.

    report_data keys:
        date_from, date_to,
        summary: dict with revenue/cogs/gross_profit/expenses/net_profit,
        top_products: list of dicts,
        expenses: list of dicts,
    """
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor("#1e3a5f"),
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.grey,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1e3a5f"),
        spaceBefore=16,
        spaceAfter=6,
    )

    elements = []

    # العنوان
    elements.append(Paragraph("Kavero — تقرير الأرباح والخسائر", title_style))
    date_from = report_data.get("date_from", "")
    date_to = report_data.get("date_to", "")
    elements.append(Paragraph(f"الفترة: {date_from}  —  {date_to}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    elements.append(Spacer(1, 0.5 * cm))

    # جدول الملخص المالي
    summary = report_data.get("summary", {})
    elements.append(Paragraph("الملخص المالي", section_style))
    summary_rows = [
        ["المؤشر", "المبلغ"],
        ["الإيرادات", f"{summary.get('revenue', 0):,.2f}"],
        ["تكلفة المبيعات (COGS)", f"{summary.get('cogs', 0):,.2f}"],
        ["الربح الإجمالي", f"{summary.get('gross_profit', 0):,.2f}"],
        ["المصروفات التشغيلية", f"{summary.get('expenses', 0):,.2f}"],
        ["صافي الربح", f"{summary.get('net_profit', 0):,.2f}"],
    ]
    tbl = Table(summary_rows, colWidths=[10 * cm, 5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(tbl)
    elements.append(Spacer(1, 0.4 * cm))

    # أفضل المنتجات
    top_products = report_data.get("top_products", [])
    if top_products:
        elements.append(Paragraph("أفضل المنتجات من حيث الإيرادات", section_style))
        prod_rows = [["المنتج", "رمز المنتج", "الكمية المباعة", "الإيرادات", "التكلفة", "الربح الإجمالي"]]
        for p in top_products:
            gross = p.get("revenue", 0) - p.get("cogs", 0)
            prod_rows.append([
                str(p.get("name", "")),
                str(p.get("sku", "")),
                f"{p.get('qty_sold', 0):,.1f}",
                f"{p.get('revenue', 0):,.2f}",
                f"{p.get('cogs', 0):,.2f}",
                f"{gross:,.2f}",
            ])
        prod_tbl = Table(
            prod_rows,
            colWidths=[5.5 * cm, 2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]
        )
        prod_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(prod_tbl)

    # تفاصيل المصروفات
    expenses = report_data.get("expenses", [])
    if expenses:
        elements.append(Paragraph("تفاصيل المصروفات", section_style))
        exp_rows = [["التاريخ", "الفئة", "الوصف", "المبلغ"]]
        for e in expenses:
            exp_rows.append([
                str(e.get("date", "")),
                str(e.get("category", "")),
                str(e.get("description", "") or ""),
                f"{e.get('amount', 0):,.2f}",
            ])
        exp_tbl = Table(exp_rows, colWidths=[3 * cm, 3 * cm, 8 * cm, 3 * cm])
        exp_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (3, 0), (3, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#e8eaf6")]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.append(exp_tbl)

    # التذييل
    elements.append(Spacer(1, 0.8 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Paragraph(
        f"تم الإنشاء بواسطة Kavero في {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(elements)


def export_receipt_pdf(sale: dict, items: list, customer_name: str, filepath: str):
    """تصدير فاتورة مبيعة واحدة كملف PDF."""
    from utils.receipt import PAYMENT_METHOD_AR

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        rightMargin=3 * cm,
        leftMargin=3 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    center_bold = ParagraphStyle(
        "CenterBold",
        parent=styles["Normal"],
        fontSize=16,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        textColor=colors.HexColor("#1e3a5f"),
        spaceAfter=6,
    )
    normal_center = ParagraphStyle(
        "NormalCenter",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    normal_right = ParagraphStyle(
        "NormalRight",
        parent=styles["Normal"],
        fontSize=11,
        alignment=TA_RIGHT,
        spaceAfter=4,
    )

    elements = []
    elements.append(Paragraph("فاتورة - Kavero", center_bold))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    elements.append(Spacer(1, 0.3 * cm))

    elements.append(Paragraph(f"رقم الفاتورة: #{sale.get('id', '')}", normal_right))
    elements.append(Paragraph(f"التاريخ: {sale.get('created_at', '')}", normal_right))
    elements.append(Paragraph(f"العميل: {customer_name}", normal_right))
    pm = sale.get("payment_method", "cash").lower()
    elements.append(Paragraph(f"طريقة الدفع: {PAYMENT_METHOD_AR.get(pm, pm)}", normal_right))
    elements.append(Spacer(1, 0.3 * cm))

    # جدول البنود
    item_rows = [["المنتج", "الكمية", "السعر", "الإجمالي"]]
    subtotal = 0.0
    for item in items:
        lt = item.get("line_total", item.get("quantity", 0) * item.get("unit_price", 0))
        subtotal += lt
        item_rows.append([
            str(item.get("product_name", "")),
            f"{item.get('quantity', 0):,.2f}",
            f"{item.get('unit_price', 0):,.2f}",
            f"{lt:,.2f}",
        ])

    item_tbl = Table(item_rows, colWidths=[8 * cm, 3 * cm, 3 * cm, 3 * cm])
    item_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(item_tbl)
    elements.append(Spacer(1, 0.3 * cm))

    # الملخص
    discount = sale.get("discount", 0.0)
    discount_amt = subtotal * discount / 100.0
    net_total = sale.get("total_amount", subtotal - discount_amt)

    totals_data = [
        ["الإجمالي قبل الخصم", f"{subtotal:,.2f}"],
    ]
    if discount:
        totals_data.append([f"الخصم ({discount}%)", f"-{discount_amt:,.2f}"])
    totals_data.append(["الإجمالي", f"{net_total:,.2f}"])

    totals_tbl = Table(totals_data, colWidths=[10 * cm, 7 * cm])
    totals_tbl.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#1e3a5f")),
    ]))
    elements.append(totals_tbl)
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1e3a5f")))
    elements.append(Paragraph("شكراً لتعاملكم معنا", normal_center))

    doc.build(elements)
