"""
PDF Generator — generates blueprint, pitch deck, and canvas PDFs
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not installed — PDF export will produce JSON fallback")

EXPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports"
)
os.makedirs(EXPORTS_DIR, exist_ok=True)


class PDFGenerator:

    def generate_blueprint_pdf(self, blueprint: dict, filename: Optional[str] = None) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"blueprint_{ts}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)

        if not REPORTLAB_AVAILABLE:
            return self._save_json_fallback(blueprint, filename.replace(".pdf", ".json"))

        try:
            doc = SimpleDocTemplate(filepath, pagesize=A4,
                                    rightMargin=2*cm, leftMargin=2*cm,
                                    topMargin=2*cm, bottomMargin=2*cm)
            story = []
            styles = getSampleStyleSheet()
            # Custom styles
            title_style   = ParagraphStyle("Title", parent=styles["Title"], fontSize=24, spaceAfter=12, textColor=colors.HexColor("#1a1a2e"))
            h1_style      = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, textColor=colors.HexColor("#3b82d4"), spaceBefore=16, spaceAfter=8)
            h2_style      = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13, textColor=colors.HexColor("#7c5cd8"), spaceBefore=12, spaceAfter=6)
            body_style    = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=16)
            caption_style = ParagraphStyle("Caption", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#57606a"), italic=True)

            es = blueprint.get("executive_summary", {})
            sc = blueprint.get("scores", {})

            # Cover
            story.append(Spacer(1, 1*inch))
            story.append(Paragraph("🚀 STARTUP BLUEPRINT", title_style))
            story.append(Paragraph(es.get("tagline", "AI-Generated Startup Blueprint"), ParagraphStyle("Sub", parent=styles["Normal"], fontSize=14, textColor=colors.HexColor("#57606a"), alignment=TA_CENTER)))
            story.append(Spacer(1, 0.3*inch))
            story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#3b82d4")))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%B %d, %Y')} | Powered by IBM Granite AI + RAG", caption_style))
            story.append(PageBreak())

            # Scores
            story.append(Paragraph("Startup Readiness Scores", h1_style))
            score_data = [["Dimension", "Score", "Status"]]
            score_map = {
                "Overall": sc.get("overall", 0), "Innovation": sc.get("innovation", 0),
                "Market Demand": sc.get("market_demand", 0), "Investment Potential": sc.get("investment_potential", 0),
                "Feasibility": sc.get("feasibility", 0), "Scalability": sc.get("scalability", 0)
            }
            for dim, val in score_map.items():
                status = "🟢 Strong" if val >= 75 else ("🟡 Moderate" if val >= 50 else "🔴 Needs Work")
                score_data.append([dim, f"{val}/100", status])
            story.append(Table(score_data, colWidths=[7*cm, 3*cm, 5*cm],
                style=TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1a1a2e")),
                    ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                    ("FONTSIZE", (0,0), (-1,-1), 10),
                    ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f7f8fa")]),
                    ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
                    ("PADDING", (0,0), (-1,-1), 8),
                ])))
            story.append(Spacer(1, 0.2*inch))

            # Executive Summary
            story.append(Paragraph("Executive Summary", h1_style))
            for key, label in [("problem","Problem"), ("solution","Solution"), ("target_customers","Target Customers"), ("estimated_budget","Estimated Budget")]:
                if es.get(key):
                    story.append(Paragraph(f"<b>{label}:</b> {es.get(key)}", body_style))
                    story.append(Spacer(1, 4))

            # SWOT
            swot = blueprint.get("swot", {})
            if swot:
                story.append(PageBreak())
                story.append(Paragraph("SWOT Analysis", h1_style))
                for label, key, color in [("Strengths ✅","strengths","#22c55e"),("Weaknesses ⚠️","weaknesses","#f59e0b"),("Opportunities 🚀","opportunities","#3b82d4"),("Threats 🛡️","threats","#ef4444")]:
                    items = swot.get(key, [])
                    story.append(Paragraph(label, ParagraphStyle("SW", parent=h2_style, textColor=colors.HexColor(color))))
                    for item in items:
                        story.append(Paragraph(f"• {item}", body_style))
                    story.append(Spacer(1, 8))

            # Budget
            budget = blueprint.get("budget", {})
            if budget:
                story.append(PageBreak())
                story.append(Paragraph("Budget Estimation", h1_style))
                bud_data = [["Category", "Amount (₹)", "% of Total"]]
                total = budget.get("total", 1) or 1
                for key in ["development","infrastructure","marketing","operations","hiring","legal","miscellaneous"]:
                    val = budget.get(key, 0)
                    bud_data.append([key.title(), f"₹{val:,.0f}", f"{val/total*100:.1f}%"])
                bud_data.append(["TOTAL", f"₹{total:,.0f}", "100%"])
                story.append(Table(bud_data, colWidths=[6*cm, 5*cm, 4*cm],
                    style=TableStyle([
                        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#3b82d4")),
                        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                        ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#1a1a2e")),
                        ("TEXTCOLOR", (0,-1), (-1,-1), colors.white),
                        ("FONTSIZE", (0,0), (-1,-1), 10),
                        ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, colors.HexColor("#f7f8fa")]),
                        ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#e5e7eb")),
                        ("PADDING", (0,0), (-1,-1), 8),
                    ])))

            # Roadmap
            roadmap = blueprint.get("roadmap", [])
            if roadmap:
                story.append(PageBreak())
                story.append(Paragraph("Startup Roadmap", h1_style))
                for step in roadmap:
                    story.append(Paragraph(f"<b>{step.get('phase', '')} — {step.get('duration', '')}</b>", h2_style))
                    story.append(Paragraph(f"🏆 Milestone: {step.get('milestone', '')}", body_style))
                    for task in step.get("tasks", []):
                        story.append(Paragraph(f"• {task}", body_style))
                    story.append(Spacer(1, 8))

            # Footer
            story.append(PageBreak())
            story.append(Spacer(1, 2*inch))
            story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e5e7eb")))
            story.append(Paragraph("Generated by AI Startup Blueprint Generator | Powered by IBM Granite AI + IBM Cloud + RAG", caption_style))
            story.append(Paragraph("⚠️ Disclaimer: This blueprint is AI-generated and should be validated by domain experts before making investment decisions.", caption_style))

            doc.build(story)
            logger.info(f"PDF generated: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"PDF generation error: {e}")
            return self._save_json_fallback(blueprint, filename.replace(".pdf", ".json"))

    def generate_pitch_deck_pdf(self, blueprint: dict, filename: Optional[str] = None) -> str:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = filename or f"pitch_deck_{ts}.pdf"
        filepath = os.path.join(EXPORTS_DIR, filename)

        if not REPORTLAB_AVAILABLE:
            return self._save_json_fallback(blueprint, filename.replace(".pdf", ".json"))

        try:
            from reportlab.lib.pagesizes import LETTER
            doc = SimpleDocTemplate(filepath, pagesize=LETTER,
                                    rightMargin=1.5*cm, leftMargin=1.5*cm,
                                    topMargin=1.5*cm, bottomMargin=1.5*cm)
            styles = getSampleStyleSheet()
            slide_title = ParagraphStyle("SlideTitle", parent=styles["Title"], fontSize=28, textColor=colors.HexColor("#1a1a2e"), spaceAfter=12)
            slide_sub   = ParagraphStyle("SlideSub", parent=styles["Normal"], fontSize=14, leading=20, textColor=colors.HexColor("#374151"))
            story = []
            es = blueprint.get("executive_summary", {})

            slides = [
                ("Slide 1: Cover", es.get("startup_names", ["Your Startup"])[0], es.get("tagline",""), es.get("industry","")),
                ("Slide 2: Problem", "The Problem", es.get("problem",""), ""),
                ("Slide 3: Solution", "Our Solution", es.get("solution",""), ""),
                ("Slide 4: Market Opportunity", "Market Opportunity", f"TAM: {blueprint.get('market_analysis',{}).get('tam','')}\nSAM: {blueprint.get('market_analysis',{}).get('sam','')}\nSOM: {blueprint.get('market_analysis',{}).get('som','')}", ""),
                ("Slide 5: Product", "What We Built", es.get("solution",""), ""),
                ("Slide 6: Business Model", "Revenue Model", f"Recommended: {blueprint.get('revenue_model',{}).get('recommended','')}", ""),
                ("Slide 7: Traction", "Traction & Roadmap", "\n".join([f"• {r.get('phase')} — {r.get('milestone')}" for r in blueprint.get("roadmap",[])[:4]]), ""),
                ("Slide 8: Team", "The Team", f"Team size: {es.get('target_customers','')}", ""),
                ("Slide 9: Financials", "Financial Projections", f"Total Budget: {es.get('estimated_budget','')}\nBurn Rate: ₹{blueprint.get('simulation',{}).get('burn_rate',0):,.0f}/month\nBreak-even: Month {blueprint.get('simulation',{}).get('break_even_month',12)}", ""),
                ("Slide 10: Ask", "The Ask & Use of Funds", f"Seeking: {es.get('estimated_budget','')}\nTimeline: {blueprint.get('investor_readiness',{}).get('funding_timeline','')}", ""),
            ]

            for label, title, body, sub in slides:
                story.append(Paragraph(label, ParagraphStyle("SlideLabel", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#57606a"))))
                story.append(HRFlowable(width="100%", thickness=3, color=colors.HexColor("#3b82d4")))
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph(title, slide_title))
                if body:
                    for line in body.split("\n"):
                        story.append(Paragraph(line, slide_sub))
                story.append(PageBreak())

            doc.build(story)
            return filepath
        except Exception as e:
            logger.error(f"Pitch deck PDF error: {e}")
            return self._save_json_fallback(blueprint, filename.replace(".pdf", ".json"))

    def _save_json_fallback(self, data: dict, filename: str) -> str:
        filepath = os.path.join(EXPORTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return filepath


# Singleton
pdf_generator = PDFGenerator()
