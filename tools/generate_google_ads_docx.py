from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH


def set_normal_style(doc: Document) -> None:
    style = doc.styles["Normal"]
    font = style.font
    font.name = "Calibri"
    font.size = Pt(11)


def add_title(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(18)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_subtitle(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.italic = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_h(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(14)


def add_label_value(doc: Document, label: str, value: str) -> None:
    p = doc.add_paragraph()
    r1 = p.add_run(f"{label}: ")
    r1.bold = True
    p.add_run(value)


def add_bullets(doc: Document, items: list[str]) -> None:
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def add_placeholder_box(doc: Document, title: str, hint: str) -> None:
    p = doc.add_paragraph()
    r = p.add_run(title)
    r.bold = True
    tbl = doc.add_table(rows=1, cols=1)
    tbl.style = "Table Grid"
    cell = tbl.rows[0].cells[0]
    cell.text = hint
    for para in cell.paragraphs:
        if para.runs:
            para.runs[0].italic = True
    doc.add_paragraph()


def add_table(doc: Document, headers: list[str], rows: list[tuple[str, ...]]) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        run = hdr_cells[i].paragraphs[0].add_run(h)
        run.bold = True
    for row in rows:
        cells = table.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = v
    doc.add_paragraph()


def build_docx(out_path: str) -> None:
    doc = Document()
    set_normal_style(doc)

    add_title(doc, "Google Ads Search Campaign Design — Submission")
    add_subtitle(doc, "Stop at Review stage • Do NOT publish • Do NOT add payment details")
    doc.add_paragraph()

    add_h(doc, "Student Info")
    add_label_value(doc, "Student Name", "[Your Name]")
    add_label_value(doc, "Course/Section", "[Course/Section]")
    add_label_value(doc, "Date", "[Date]")
    add_label_value(doc, "Google Ads Account Email", "[Optional — do not share password]")
    doc.add_paragraph()

    add_h(doc, "Important Instructions (Acknowledgement)")
    add_bullets(
        doc,
        [
            "I will NOT publish or run the campaign.",
            "I will NOT add payment details.",
            "I will stop at the Review stage.",
            "I will provide screenshots as proof of work.",
        ],
    )

    add_h(doc, "1) Business Overview")
    add_label_value(doc, "Business name", "Glow Dental Clinic (example — replace if needed)")
    add_label_value(doc, "Industry", "Dental / Healthcare")
    add_label_value(
        doc,
        "Target audience",
        "Adults 18–55 in [City], including urgent and routine dental care seekers",
    )
    add_label_value(
        doc,
        "Product/service description",
        "Emergency dental care, cleanings/checkups, whitening, consultations",
    )
    add_placeholder_box(
        doc,
        "Screenshot 1 (Required):",
        "Paste screenshot of your chosen business/website OR a brief business profile page (if you created one).",
    )

    add_h(doc, "2) Campaign Objective & Type")
    add_label_value(doc, "Goal", "Lead generation (calls + appointment form submissions)")
    add_label_value(doc, "Campaign type", "Search")
    add_label_value(
        doc,
        "Why this objective fits",
        "Search captures high-intent users actively looking for a dentist; leads align with clinic bookings.",
    )
    add_placeholder_box(
        doc,
        "Screenshot 2 (Recommended):",
        "Paste screenshot showing campaign objective/type selection in Google Ads.",
    )

    add_h(doc, "3) Keyword Strategy")
    add_label_value(doc, "Seed keyword (Keyword Planner)", "dentist near me")
    add_label_value(
        doc,
        "Justification using Planner analytics",
        "Use Avg. monthly searches + competition + top-of-page bid range to justify demand and intent.",
    )

    doc.add_paragraph("Fill these from Keyword Planner:")
    add_bullets(
        doc,
        [
            "Avg. monthly searches: [____]",
            "Competition: [Low/Medium/High]",
            "Top of page bid (low range): [____]",
            "Top of page bid (high range): [____]",
        ],
    )
    add_placeholder_box(
        doc,
        "Screenshot 3 (Required):",
        "Paste Keyword Planner screenshot showing seed keyword + metrics + keyword ideas.",
    )

    add_label_value(doc, "Generated keyword list (10–15)", "")
    add_bullets(
        doc,
        [
            "dentist near me",
            "dental clinic near me",
            "emergency dentist near me",
            "teeth cleaning near me",
            "dental checkup appointment",
            "tooth pain dentist",
            "same day dentist appointment",
            "teeth whitening near me",
            "affordable dentist near me",
            "dentist open today",
            "best dentist in [City]",
            "book dentist appointment online",
            "braces consultation near me (if offered)",
            "root canal specialist near me (if offered)",
            "pediatric dentist near me (if offered)",
        ],
    )

    intent_rows = [
        (
            "Informational",
            "tooth pain dentist; dental checkup appointment (mixed)",
            "Users seeking guidance; may still convert with strong offer",
        ),
        ("Navigational", "best dentist in [City]", "Users comparing options in a location"),
        (
            "Commercial",
            "affordable dentist near me; teeth whitening near me; braces consultation near me",
            "Users evaluating services/prices",
        ),
        (
            "Transactional",
            "emergency dentist near me; same day dentist appointment; book dentist appointment online; dentist open today",
            "High intent to book/call now",
        ),
    ]
    add_table(doc, ["Intent Type", "Example Keywords", "Why"], intent_rows)

    add_h(doc, "Match Types (Broad / Phrase / Exact)")
    add_bullets(
        doc,
        [
            "Broad: dentist near me",
            'Phrase: “emergency dentist near me”, “teeth cleaning near me”',
            "Exact: [emergency dentist near me], [same day dentist appointment]",
        ],
    )

    add_h(doc, "Reasoning for at least 5 keywords (match type aligns with intent)")
    reason_rows = [
        (
            "[emergency dentist near me]",
            "Exact",
            "Highest urgency; keep relevance tight and reduce irrelevant queries",
        ),
        ("“emergency dentist near me”", "Phrase", "Captures close variants while preserving urgent intent"),
        (
            "[same day dentist appointment]",
            "Exact",
            "Direct booking intent; exact aligns with conversion-focused traffic",
        ),
        (
            "“teeth cleaning near me”",
            "Phrase",
            "Targets service seekers; phrase catches common variants (best/affordable/etc.)",
        ),
        ("dentist near me", "Broad", "Volume/discovery; acceptable with negatives and search-term monitoring"),
    ]
    add_table(doc, ["Keyword", "Match Type", "Reason"], reason_rows)

    add_h(doc, "4) Campaign Structure")
    add_label_value(doc, "Campaign", "Search | Leads | Glow Dental")
    add_label_value(doc, "Ad group 1", "Emergency Dentist")
    add_bullets(
        doc,
        [
            "[emergency dentist near me]",
            "“emergency dentist near me”",
            "[dentist open today]",
            "“dentist open today”",
            "[tooth pain dentist]",
            "“same day dentist appointment”",
        ],
    )
    add_label_value(doc, "Ad group 2", "Cleaning & Checkup")
    add_bullets(
        doc,
        [
            "“teeth cleaning near me”",
            "[teeth cleaning near me]",
            "“dental clinic near me”",
            "[dental checkup appointment]",
            "“book dentist appointment online”",
            "[affordable dentist near me]",
        ],
    )
    add_placeholder_box(
        doc,
        "Screenshot 4 (Required):",
        "Paste screenshot of Campaign → Ad groups screen showing at least 2 ad groups.",
    )
    add_placeholder_box(
        doc,
        "Screenshot 5 (Required):",
        "Paste screenshot of each Ad group → Keywords list (5–7 each).",
    )

    add_h(doc, "5) Google Ads Setup")
    add_bullets(
        doc,
        [
            "Campaign objective/type: Leads → Search",
            "Bidding strategy: Maximize conversions (or Maximize clicks if conversions are not set yet; explain plan to switch later)",
            "Location targeting: [City] + 10–20 km radius (adjust to business service area)",
            "Language targeting: English (+ add additional languages if relevant)",
            "Ad schedule: Business hours (e.g., Mon–Sat 10am–8pm) or 24/7 for emergency if supported",
        ],
    )
    add_placeholder_box(
        doc,
        "Screenshot 6 (Required):",
        "Paste screenshot of Campaign settings (bidding, locations, languages, schedule).",
    )

    add_h(doc, "6) Ad Copy & Extensions")
    add_label_value(doc, "Ad Group 1 — Responsive Search Ad (Emergency)", "")
    add_bullets(
        doc,
        [
            "Headlines (examples): Emergency Dentist Near You; Same‑Day Appointments Available; Tooth Pain? Get Fast Relief; Call Now For Immediate Help; Trusted Dental Clinic in [City]",
            "Descriptions (examples): Get urgent dental care today. Book online or call now.; Same-day slots available. Clear pricing and convenient location.",
            "Pinning: Pin ‘Emergency Dentist Near You’ to Headline 1 to maintain urgent relevance.",
            "Call-to-action: Call Now / Book Appointment",
        ],
    )

    add_label_value(doc, "Ad Group 2 — Responsive Search Ad (Cleaning & Checkup)", "")
    add_bullets(
        doc,
        [
            "Headlines (examples): Teeth Cleaning & Dental Checkup; Book A Dentist Appointment Online; Affordable Dental Care in [City]; Gentle Cleaning, Professional Care; New Patient Slots Available",
            "Descriptions (examples): Routine checkups/cleanings with a friendly team. Choose a time that fits.; Transparent pricing and quality care. Book online in minutes.",
            "Call-to-action: Book Online",
        ],
    )

    add_h(doc, "Extensions")
    add_bullets(
        doc,
        [
            "Sitelinks: Book Appointment; Emergency Dental Care; Teeth Cleaning; Contact & Location",
            "Callouts: Same‑Day Visits; Experienced Dentists; Hygiene & Safety First; Transparent Pricing; Convenient Location",
            "Other (if applicable): Call extension; Location extension; Structured snippets (Services)",
        ],
    )
    add_placeholder_box(doc, "Screenshot 7 (Required):", "Paste screenshot of ads (RSA) created for each ad group.")
    add_placeholder_box(doc, "Screenshot 8 (Required):", "Paste screenshot of extensions (sitelinks/callouts/etc.).")

    add_h(doc, "7) Landing Page Strategy")
    add_bullets(
        doc,
        [
            "Destination: Dedicated landing pages (e.g., /emergency-dentist and /teeth-cleaning) OR the most relevant service pages on the website.",
            "Intent match: Emergency page emphasizes call-now, same-day availability, pain relief; Cleaning page emphasizes routine care, what’s included, booking form.",
            "Consistency: Page headline matches keyword theme; clear CTA above the fold; trust elements (reviews, credentials, location).",
        ],
    )
    add_placeholder_box(doc, "Screenshot 9 (Recommended):", "Paste screenshot of landing page(s) you selected or a wireframe description.")

    add_h(doc, "Final Proof")
    add_bullets(
        doc,
        [
            "I confirm the campaign was NOT published and NO payment method was added.",
            "Work stopped at the Review stage as instructed.",
        ],
    )
    add_placeholder_box(
        doc,
        "Screenshot 10 (Required):",
        "Paste screenshot of the Review screen showing the campaign is ready but not published.",
    )

    doc.save(out_path)


if __name__ == "__main__":
    build_docx("Google_Ads_Campaign_Design_Submission.docx")

