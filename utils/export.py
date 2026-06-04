"""CSV and PDF export utilities."""

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
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


def export_csv(data: list[dict], filepath: str):
    """Write a list of dicts to a CSV file."""
    if not data:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)


def export_pdf(report_data: dict, filepath: str):
    """
    Generate a P&L report PDF using reportlab.

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
        textColor=colors.HexColor("#1a237e"),
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
        textColor=colors.HexColor("#1a237e"),
        spaceBefore=16,
        spaceAfter=6,
    )

    elements = []

    # Title
    elements.append(Paragraph("BizManager — P&L Report", title_style))
    date_from = report_data.get("date_from", "")
    date_to = report_data.get("date_to", "")
    elements.append(Paragraph(f"Period: {date_from}  →  {date_to}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    elements.append(Spacer(1, 0.5 * cm))

    # Summary table
    summary = report_data.get("summary", {})
    elements.append(Paragraph("Financial Summary", section_style))
    summary_rows = [
        ["Metric", "Amount"],
        ["Revenue", f"${summary.get('revenue', 0):,.2f}"],
        ["Cost of Goods Sold (COGS)", f"${summary.get('cogs', 0):,.2f}"],
        ["Gross Profit", f"${summary.get('gross_profit', 0):,.2f}"],
        ["Operating Expenses", f"${summary.get('expenses', 0):,.2f}"],
        ["Net Profit", f"${summary.get('net_profit', 0):,.2f}"],
    ]
    tbl = Table(summary_rows, colWidths=[10 * cm, 5 * cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a237e")),
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

    # Top Products
    top_products = report_data.get("top_products", [])
    if top_products:
        elements.append(Paragraph("Top Products by Revenue", section_style))
        prod_rows = [["Product", "SKU", "Qty Sold", "Revenue", "COGS", "Gross"]]
        for p in top_products:
            gross = p.get("revenue", 0) - p.get("cogs", 0)
            prod_rows.append([
                str(p.get("name", "")),
                str(p.get("sku", "")),
                f"{p.get('qty_sold', 0):,.1f}",
                f"${p.get('revenue', 0):,.2f}",
                f"${p.get('cogs', 0):,.2f}",
                f"${gross:,.2f}",
            ])
        prod_tbl = Table(
            prod_rows,
            colWidths=[5.5 * cm, 2 * cm, 2 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm]
        )
        prod_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#283593")),
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

    # Expenses
    expenses = report_data.get("expenses", [])
    if expenses:
        elements.append(Paragraph("Expenses Detail", section_style))
        exp_rows = [["Date", "Category", "Description", "Amount"]]
        for e in expenses:
            exp_rows.append([
                str(e.get("date", "")),
                str(e.get("category", "")),
                str(e.get("description", "")),
                f"${e.get('amount', 0):,.2f}",
            ])
        exp_tbl = Table(exp_rows, colWidths=[3 * cm, 3 * cm, 8 * cm, 3 * cm])
        exp_tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#283593")),
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

    # Footer
    elements.append(Spacer(1, 0.8 * cm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.grey))
    elements.append(Paragraph(
        f"Generated by BizManager on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8,
                       textColor=colors.grey, alignment=TA_CENTER)
    ))

    doc.build(elements)
