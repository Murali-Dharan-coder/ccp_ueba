from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from io import BytesIO
import datetime


# ── Colour Palette ──────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#0f172a")
DARK_CARD  = colors.HexColor("#1e293b")
BLUE       = colors.HexColor("#3b82f6")
RED        = colors.HexColor("#ef4444")
AMBER      = colors.HexColor("#f59e0b")
GREEN      = colors.HexColor("#10b981")
SLATE      = colors.HexColor("#64748b")
WHITE      = colors.white
LIGHT_GREY = colors.HexColor("#e2e8f0")


def _severity_color(severity: str):
    s = (severity or "").upper()
    if s == "CRITICAL": return RED
    if s == "HIGH":     return AMBER
    return BLUE


def generate_user_pdf_report(user_data: dict, anomalies: list) -> BytesIO:
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()
    W = letter[0] - 40 * mm   # usable width

    # ── Custom Paragraph Styles ──────────────────────────────────────────
    def make_style(name, parent="Normal", **kw):
        s = ParagraphStyle(name, parent=styles[parent])
        for k, v in kw.items():
            setattr(s, k, v)
        return s

    sTitle      = make_style("sTitle",      fontSize=22, textColor=WHITE,      fontName="Helvetica-Bold", spaceAfter=2)
    sSubtitle   = make_style("sSubtitle",   fontSize=10, textColor=SLATE,      fontName="Helvetica", spaceAfter=10)
    sSection    = make_style("sSection",    fontSize=12, textColor=BLUE,       fontName="Helvetica-Bold", spaceBefore=10, spaceAfter=4)
    sLabel      = make_style("sLabel",      fontSize=9,  textColor=SLATE,      fontName="Helvetica-Bold")
    sValue      = make_style("sValue",      fontSize=10, textColor=LIGHT_GREY, fontName="Helvetica")
    sDesc       = make_style("sDesc",       fontSize=8,  textColor=LIGHT_GREY, fontName="Helvetica", leading=12)
    sFooter     = make_style("sFooter",     fontSize=8,  textColor=SLATE,      fontName="Helvetica", alignment=1)

    story = []

    # ── Header Banner ────────────────────────────────────────────────────
    header_data = [[
        Paragraph("<b>UEBA SHIELD</b>", make_style("h1b", fontSize=16, textColor=BLUE, fontName="Helvetica-Bold")),
        Paragraph(
            f"<b>Behavioral Analytics Report</b><br/>"
            f"<font color='#64748b' size='8'>Generated: {datetime.datetime.now().strftime('%d %b %Y, %H:%M:%S')}</font>",
            make_style("h1r", fontSize=11, textColor=WHITE, fontName="Helvetica-Bold", alignment=2)
        )
    ]]
    header_table = Table(header_data, colWidths=[W * 0.5, W * 0.5])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("ROWBACKGROUNDS",(0,0), (-1,-1), [NAVY]),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [6]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))

    # ── User Details + Risk Score cards (side-by-side) ───────────────────
    score       = user_data.get("anomaly_score", 0)
    level       = user_data.get("critical_level", "Low")
    status      = user_data.get("status", "Active")
    score_col   = RED if score > 80 else (AMBER if score > 60 else (BLUE if score > 40 else GREEN))
    status_col  = RED if status == "Locked" else GREEN

    details_inner = Table(
        [
            [Paragraph("NAME", sLabel),        Paragraph(user_data.get("name", "—"), sValue)],
            [Paragraph("EMPLOYEE ID", sLabel), Paragraph(user_data.get("employee_id", "—"), sValue)],
            [Paragraph("DEPARTMENT", sLabel),  Paragraph(user_data.get("department", "—"), sValue)],
            [Paragraph("STATUS", sLabel),
             Paragraph(f'<font color="{status_col.hexval()}"><b>{status.upper()}</b></font>', sValue)],
        ],
        colWidths=[30 * mm, None]
    )
    details_inner.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.3, colors.HexColor("#1e293b")),
    ]))

    risk_inner = Table(
        [
            [Paragraph("RISK SCORE", sLabel),
             Paragraph(f'<font color="{score_col.hexval()}" size="20"><b>{round(score)}</b></font> <font color="#64748b" size="9">/ 100</font>', sValue)],
            [Paragraph("SEVERITY LEVEL", sLabel),
             Paragraph(f'<font color="{score_col.hexval()}"><b>{level.upper()}</b></font>', sValue)],
            [Paragraph("ANOMALY COUNT", sLabel),
             Paragraph(f"<b>{len(anomalies)}</b> events recorded", sValue)],
        ],
        colWidths=[35 * mm, None]
    )
    risk_inner.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LINEBELOW",    (0, 0), (-1, -2), 0.3, colors.HexColor("#1e293b")),
    ]))

    cards = Table(
        [[
            Table([[Paragraph("SUBJECT PROFILE", sSection)], [details_inner]], colWidths=[None]),
            Table([[Paragraph("RISK ASSESSMENT", sSection)],  [risk_inner]],   colWidths=[None]),
        ]],
        colWidths=[W * 0.52, W * 0.48]
    )
    cards.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, 0), DARK_CARD),
        ("BACKGROUND",   (1, 0), (1, 0), DARK_CARD),
        ("TOPPADDING",   (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 12),
        ("LEFTPADDING",  (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("ROUNDEDCORNERS", [6]),
        ("INNERGRID",    (0, 0), (-1, -1), 0.3, NAVY),
    ]))
    story.append(cards)
    story.append(Spacer(1, 8 * mm))

    # ── Anomaly Table ────────────────────────────────────────────────────
    story.append(Paragraph("DETECTED BEHAVIORAL ANOMALIES", sSection))
    story.append(HRFlowable(width=W, thickness=0.5, color=BLUE, spaceAfter=4))

    if not anomalies:
        story.append(Paragraph("No anomalies detected for this entity.", sDesc))
    else:
        # Header row
        anom_rows = [[
            Paragraph("<b>#</b>",          make_style("th", fontSize=8, textColor=SLATE, fontName="Helvetica-Bold")),
            Paragraph("<b>ALERT TYPE</b>", make_style("th", fontSize=8, textColor=SLATE, fontName="Helvetica-Bold")),
            Paragraph("<b>SEVERITY</b>",   make_style("th", fontSize=8, textColor=SLATE, fontName="Helvetica-Bold")),
            Paragraph("<b>TIMESTAMP</b>",  make_style("th", fontSize=8, textColor=SLATE, fontName="Helvetica-Bold")),
            Paragraph("<b>DESCRIPTION</b>",make_style("th", fontSize=8, textColor=SLATE, fontName="Helvetica-Bold")),
        ]]

        row_bg_a = DARK_CARD
        row_bg_b = colors.HexColor("#162032")

        for idx, anomaly in enumerate(anomalies):
            sev = (anomaly.get("severity") or "MEDIUM").upper()
            sev_col = _severity_color(sev)

            # Truncate description if very long
            desc_raw = anomaly.get("description", "—")
            if len(desc_raw) > 200:
                desc_raw = desc_raw[:197] + "..."

            ts_raw = anomaly.get("timestamp", "—")
            try:
                ts_fmt = datetime.datetime.fromisoformat(ts_raw).strftime("%d %b %Y\n%H:%M:%S")
            except Exception:
                ts_fmt = ts_raw

            anom_rows.append([
                Paragraph(str(idx + 1), make_style(f"n{idx}", fontSize=8, textColor=SLATE, fontName="Helvetica")),
                Paragraph(anomaly.get("type", "—"), make_style(f"t{idx}", fontSize=8, textColor=LIGHT_GREY, fontName="Helvetica-Bold")),
                Paragraph(
                    f'<font color="{sev_col.hexval()}"><b>{sev}</b></font>',
                    make_style(f"s{idx}", fontSize=8, fontName="Helvetica-Bold")
                ),
                Paragraph(ts_fmt, make_style(f"ts{idx}", fontSize=7, textColor=SLATE, fontName="Helvetica", leading=10)),
                Paragraph(desc_raw, make_style(f"d{idx}", fontSize=7.5, textColor=LIGHT_GREY, fontName="Helvetica", leading=11)),
            ])

        col_widths = [8 * mm, 38 * mm, 22 * mm, 28 * mm, W - 8*mm - 38*mm - 22*mm - 28*mm]
        anom_table = Table(anom_rows, colWidths=col_widths, repeatRows=1)

        ts = TableStyle([
            # Header
            ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR",    (0, 0), (-1, 0), SLATE),
            ("TOPPADDING",   (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING",(0, 0), (-1, 0), 6),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING",   (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING",(0, 1), (-1, -1), 5),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [row_bg_a, row_bg_b]),
            ("LINEBELOW",    (0, 0), (-1, -1), 0.3, colors.HexColor("#1e293b")),
            ("ROUNDEDCORNERS", [4]),
        ])
        anom_table.setStyle(ts)
        story.append(anom_table)

    story.append(Spacer(1, 10 * mm))

    # ── Footer ───────────────────────────────────────────────────────────
    story.append(HRFlowable(width=W, thickness=0.3, color=SLATE, spaceAfter=4))
    story.append(Paragraph(
        "CONFIDENTIAL — UEBA Shield Intelligence Report · For authorized security personnel only",
        sFooter
    ))

    # ── Build ─────────────────────────────────────────────────────────────
    # Dark page background
    def on_page(canvas_obj, doc_obj):
        canvas_obj.saveState()
        canvas_obj.setFillColor(NAVY)
        canvas_obj.rect(0, 0, letter[0], letter[1], fill=1, stroke=0)
        canvas_obj.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    buffer.seek(0)
    return buffer
