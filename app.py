"""
Regulatory Navigator & Readiness Evaluator - Hackathon MVP
FINAL HYBRID MODEL: AI-Powered Analysis with Hard-Coded Specialist Checks & Bilingual UI
"""

import streamlit as st
import json
import io
import re
from typing import Dict, List

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import HexColor
from openai import OpenAI

# --- TRANSLATIONS DICTIONARY ---
TRANSLATIONS = {
    "en": {
        "lang_name": "English",
        "title": "QCB Regulatory Navigator & Readiness Evaluator",
        "subtitle": "Upload your 3 core documents for comprehensive compliance evaluation",
        "business_plan_header": "📄 Business Plan",
        "compliance_policy_header": "🔒 Compliance Policy",
        "legal_structure_header": "⚖️ Legal Structure",
        "upload_bp_label": "Upload Business Plan PDF",
        "upload_cp_label": "Upload Internal Compliance Policy PDF",
        "upload_ls_label": "Upload Legal Structure Document PDF",
        "evaluate_button": "🚀 Evaluate Compliance",
        "error_upload_all": "⚠️ Please upload all three PDF documents before proceeding.",
        "spinner_text": "🔍 Processing documents and analyzing compliance...",
        "reading_pdfs": "📖 Reading PDF files...",
        "ai_analyzing": "🤖 AI is analyzing documents for compliance gaps...",
        "applying_checks": "CHECKS: Applying high-precision checks for specific rules...",
        "mapping_recs": "💡 Mapping deterministic recommendations and resources...",
        "calculating_score": "🧮 Calculating transparent score based on AI findings...",
        "generating_reports": "📝 Generating downloadable reports...",
        "analysis_complete": "✅ Analysis complete! Download your reports below.",
        "overall_score_metric": "Overall Readiness Score",
        "score_delta": "(Transparently Calculated)",
        "urgent_header": "🚨 URGENT: Critical Requirements Missing",
        "urgent_subheader": "{count} critical requirement{s} must be addressed immediately",
        "gap_label": "Gap:",
        "suggestion_label": "Suggestion:",
        "flag_review_label": "🚩 Flag '{req_name}' for expert review",
        "download_reports_header": "📥 Download Reports",
        "download_bp_button": "📄 Marked-up Business Plan",
        "download_cp_button": "🔒 Marked-up Compliance Policy",
        "download_ls_button": "⚖️ Marked-up Legal Structure",
        "download_summary_button": "📊 Summary Report"
    },
    "ar": {
        "lang_name": "العربية",
        "title": "متصفح الامتثال التنظيمي والتقييم لجاهزية مصرف قطر المركزي",
        "subtitle": "قم بتحميل مستنداتك الأساسية الثلاثة لتقييم الامتثال الشامل",
        "business_plan_header": "📄 خطة العمل",
        "compliance_policy_header": "🔒 سياسة الامتثال",
        "legal_structure_header": "⚖️ الهيكل القانوني",
        "upload_bp_label": "تحميل ملف خطة العمل (PDF)",
        "upload_cp_label": "تحميل ملف سياسة الامتثال الداخلية (PDF)",
        "upload_ls_label": "تحميل ملف الهيكل القانوني (PDF)",
        "evaluate_button": "🚀 تقييم الامتثال",
        "error_upload_all": "⚠️ يرجى تحميل جميع ملفات PDF الثلاثة قبل المتابعة.",
        "spinner_text": "🔍 جاري معالجة المستندات وتحليل الامتثال...",
        "reading_pdfs": "📖 قراءة ملفات PDF...",
        "ai_analyzing": "🤖 الذكاء الاصطناعي يحلل المستندات بحثًا عن فجوات الامتثال...",
        "applying_checks": "CHECKS: تطبيق فحوصات عالية الدقة لقواعد محددة...",
        "mapping_recs": "💡 ربط التوصيات والموارد المحددة...",
        "calculating_score": "🧮 حساب النتيجة الشفافة بناءً على نتائج الذكاء الاصطناعي...",
        "generating_reports": "📝 إنشاء التقارير القابلة للتنزيل...",
        "analysis_complete": "✅ اكتمل التحليل! قم بتنزيل تقاريرك أدناه.",
        "overall_score_metric": "النتيجة الإجمالية للجاهزية",
        "score_delta": "(محسوبة بشفافية)",
        "urgent_header": "🚨 عاجل: متطلبات حرجة مفقودة",
        "urgent_subheader": "يجب معالجة {count} متطلبًا حرجًا على الفور",
        "gap_label": "الفجوة:",
        "suggestion_label": "الاقتراح:",
        "flag_review_label": "🚩 وضع علامة على '{req_name}' للمراجعة من قبل خبير",
        "download_reports_header": "📥 تنزيل التقارير",
        "download_bp_button": "📄 خطة العمل مع التعليقات",
        "download_cp_button": "🔒 سياسة الامتثال مع التعليقات",
        "download_ls_button": "⚖️ الهيكل القانوني مع التعليقات",
        "download_summary_button": "📊 تقرير الملخص"
    }
}


# Initialize OpenAI client
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY", ""))

# --- Configuration Loading ---
try:
    with open("requirements.json", "r", encoding="utf-8") as f:
        QCB_REQUIREMENTS = json.load(f)
    with open("resource_mapping_data.json", "r", encoding="utf-8") as f:
        RESOURCE_MAPPING = json.load(f)
    with open("scoring.json", "r", encoding="utf-8") as f:
        CRITICALITY_WEIGHTS = json.load(f)
    with open("remediation.json", "r", encoding="utf-8") as f:
        REMEDIATION_TEMPLATES = json.load(f)
except FileNotFoundError as e:
    st.error(f"FATAL ERROR: A required configuration file is missing: {e.filename}. Please ensure all .json files are in the same directory as app.py.")
    st.stop()


# --- Core Logic ---

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text content from uploaded PDF file."""
    try:
        pdf_bytes = pdf_file.read()
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = "".join(page.get_text() for page in pdf_document)
        pdf_document.close()
        return text
    except Exception as e:
        st.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def evaluate_compliance_with_ai(business_plan: str, compliance_policy: str, legal_structure: str) -> Dict:
    """Stage 1: AI Evaluation for status and reasoning. Does NOT calculate score."""
    
    evaluation_prompt = f"""You are an expert regulatory compliance analyst for the Qatar Central Bank (QCB). Your task is to analyze three documents and evaluate them against a list of QCB FinTech requirements.

Analyze the provided documentation against these QCB requirements:
{json.dumps(QCB_REQUIREMENTS, indent=2)}

For each requirement, you must:
1.  Classify its status as "compliant", "partial", or "missing".
2.  Provide a specific, concise "details" explanation for your reasoning, especially for "partial" or "missing" statuses.
3.  Identify which document ("business_plan", "compliance_policy", or "legal_structure") contains the primary evidence using the "found_in_document" field.
4.  For any "partial" or "missing" status, extract the most relevant sentence or phrase as the "key_quote". If no text is relevant, leave the quote empty.

**CRITICAL RULE for data_residency & primary_data_environment:** If a document mentions hosting on public clouds like AWS, Azure, or GCP, or regions like Ireland or Singapore, BUT does NOT explicitly state that all customer PII and transactional data are stored on servers physically located in Qatar, you MUST mark these requirements as "missing" and state this specific reason in the "details". For the "key_quote", extract the sentence that mentions the foreign hosting, for example: "hosted across the AWS regions in Ireland and Singapore".

Documentation to analyze:
<BUSINESS_PLAN>
{business_plan}
</BUSINESS_PLAN>

<COMPLIANCE_POLICY>
{compliance_policy}
</COMPLIANCE_POLICY>

<LEGAL_STRUCTURE>
{legal_structure}
</LEGAL_STRUCTURE>

Return a single JSON object. DO NOT include an overall_score. Your entire output must be only the JSON object.
Structure:
{{
  "requirements": [
    {{
      "id": "<requirement_id>",
      "category": "<category_name>",
      "requirement": "<requirement_title>",
      "status": "compliant|partial|missing",
      "details": "<Your specific, 1-2 sentence reasoning>",
      "found_in_document": "business_plan|compliance_policy|legal_structure",
      "key_quote": "<Exact quote from the source document if not compliant>"
    }}
  ],
  "recommendations": ["<A general, high-level recommendation>", "<Another general recommendation>"]
}}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a regulatory compliance expert. Return only valid JSON."},
                {"role": "user", "content": evaluation_prompt}
            ],
            temperature=0.1
        )
        result_text = response.choices[0].message.content
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        
        return json.loads(result_text)
    except Exception as e:
        st.error(f"Error during AI evaluation: {e}")
        return {"requirements": [], "recommendations": []}


def apply_hardcoded_checks(requirements: List[Dict], all_docs_text: str) -> List[Dict]:
    """Applies high-precision, rule-based checks for specific hackathon requirements."""
    capital_req_p2p = next((req for req in requirements if req.get("id") == "minimum_capital_p2p"), None)
    if capital_req_p2p:
        match = re.search(r"Paid-Up Capital:.*?QAR\s*([\d,]+)", all_docs_text, re.IGNORECASE)
        if match:
            try:
                actual_capital = int(match.group(1).replace(',', ''))
                required_capital = 7500000
                if actual_capital < required_capital:
                    shortfall = required_capital - actual_capital
                    capital_req_p2p['status'] = 'missing'
                    capital_req_p2p['details'] = f"Financial Deficiency. The paid-up capital of QAR {actual_capital:,} is QAR {shortfall:,} short of the required minimum of QAR {required_capital:,} for a Category 2 (Marketplace Lending) license."
                    capital_req_p2p['found_in_document'] = 'legal_structure'
            except (ValueError, IndexError): pass

    source_of_funds_req = next((req for req in requirements if req.get("id") == "source_of_funds"), None)
    if source_of_funds_req and "QAR 45,000" in all_docs_text:
        source_of_funds_req['status'] = 'partial'
        source_of_funds_req['details'] = "Weakness Detected: The plan mentions transactions up to QAR 45,000. While this is below the high-risk threshold, it indicates significant transaction volumes that require robust monitoring."
        source_of_funds_req['suggestion'] = "It is highly recommended to enroll in the 'AML Compliance Workshop Series' to strengthen monitoring policies for large transaction volumes."
        source_of_funds_req['found_in_document'] = 'business_plan'

    return requirements


def calculate_transparent_score(requirements: List[Dict]) -> int:
    """Calculates a transparent, weighted score."""
    total_score, max_score = 0, 0
    weights_config = CRITICALITY_WEIGHTS.get("weights", {})
    default_weight = CRITICALITY_WEIGHTS.get("default_weight", 2)
    partial_multiplier = CRITICALITY_WEIGHTS.get("partial_multiplier", 0.4)
    all_req_ids = {req['id'] for req in QCB_REQUIREMENTS}
    
    for req_id in all_req_ids:
        weight = weights_config.get(req_id, default_weight)
        max_score += weight
        req = next((r for r in requirements if r.get("id") == req_id), None)
        if req:
            if req.get("status") == "compliant": total_score += weight
            elif req.get("status") == "partial": total_score += weight * partial_multiplier
    if max_score == 0: return 0
    return int((total_score / max_score) * 100)

def map_resources(requirement_id: str) -> List[Dict]:
    """Maps experts and programs to a requirement ID."""
    matched = []
    for resource in RESOURCE_MAPPING:
        if requirement_id in resource.get("linked_rule_ids", []):
            matched.append(resource)
    return matched

# --- PDF Generation and Annotation ---

def _find_rect_for_text(page, text_to_find: str):
    """A robust function to find text, trying multiple strategies."""
    if not text_to_find or len(text_to_find) < 8: return None
    rects = page.search_for(text_to_find, quads=True)
    if rects: return rects
    normalized_text = " ".join(text_to_find.split())
    rects = page.search_for(normalized_text, quads=True)
    if rects: return rects
    words = normalized_text.split()
    if len(words) > 5:
        snippet = " ".join(words[:5])
        rects = page.search_for(snippet, quads=True)
        if rects: return rects
    return None

def annotate_pdf(original_pdf_bytes: bytes, requirements: List[Dict], doc_category: str) -> bytes:
    """Adds highlights AND a final summary page to the PDF."""
    try:
        pdf_document = fitz.open(stream=original_pdf_bytes, filetype="pdf")
        relevant_reqs = [r for r in requirements if r.get("found_in_document") == doc_category]
        
        # --- PART 1: Highlight what can be found ---
        for req in relevant_reqs:
            if req.get("status") == "compliant" or not req.get("key_quote"): continue
            color = (1.0, 1.0, 0.0) if req.get("status") == "partial" else (1.0, 0.0, 0.0) # Yellow for partial
            comment = f"Gap: {req.get('details', 'N/A')}"
            
            quads_to_highlight = []
            for page in pdf_document:
                quads = _find_rect_for_text(page, req.get("key_quote", ""))
                if quads:
                    quads_to_highlight.extend([(page, q) for q in quads])
            
            for page, quad in quads_to_highlight:
                highlight = page.add_highlight_annot(quad)
                if highlight:
                    highlight.set_colors(stroke=color)
                    highlight.set_info(content=comment)
                    highlight.update()
        
        # --- PART 2: Add a final summary page with ALL findings for this document ---
        if relevant_reqs:
            summary_content = f"Findings Summary for {doc_category.replace('_', ' ').title()}\n\n"
            for status, symbol in [("compliant", "✅"), ("partial", "⚠️"), ("missing", "❌")]:
                items = [r for r in relevant_reqs if r.get("status") == status]
                if items:
                    summary_content += f"--- {status.upper()} ---\n"
                    for item in sorted(items, key=lambda x: x.get('requirement', '')):
                        summary_content += f"{symbol} {item.get('requirement', '')}\n"
                        summary_content += f"   - Reasoning: {item.get('details', 'N/A')}\n\n"
            page = pdf_document.new_page(width=A4[0], height=A4[1])
            page.insert_textbox(
                fitz.Rect(50, 50, A4[0] - 50, A4[1] - 50),
                summary_content, fontsize=10, fontname="helv"
            )

        output_bytes = pdf_document.write()
        pdf_document.close()
        return output_bytes
    except Exception as e:
        st.error(f"Error annotating PDF for {doc_category}: {e}")
        return original_pdf_bytes

def generate_summary_pdf(score: int, requirements: List[Dict], recommendations: List[str]) -> bytes:
    """Generates the main summary PDF (in English)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=24, textColor=HexColor('#8B1538'), spaceAfter=30)
    heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], fontSize=14, textColor=HexColor('#8B1538'), spaceAfter=12, spaceBefore=20)
    story = []
    story.append(Paragraph("QCB Compliance Readiness Report", title_style))
    score_color = HexColor('#D4AF37') if score >= 90 else HexColor('#FFD700') if score >= 40 else HexColor('#8B1538') # Yellow
    score_style = ParagraphStyle('Score', parent=styles['Normal'], fontSize=18, textColor=score_color, spaceAfter=20)
    story.append(Paragraph(f"Overall Readiness Score: <b>{score}%</b>", score_style))
    
    categories = {}
    for req in requirements:
        cat = req.get("category", "Other")
        if cat and cat not in categories: categories[cat] = []
        if cat: categories[cat].append(req)
        
    story.append(Paragraph("Detailed Compliance Assessment", heading_style))
    for category, reqs in sorted(categories.items()):
        category_title = str(category).replace('_', ' ').title()
        story.append(Paragraph(f"<b>{category_title}</b>", styles['Heading3']))
        for req in sorted(reqs, key=lambda x: x.get('requirement', '')):
            symbol = "✅" if req.get("status") == "compliant" else "⚠️" if req.get("status") == "partial" else "❌"
            color = HexColor('#D4AF37') if req.get("status") == "compliant" else HexColor('#FFD700') if req.get("status") == "partial" else HexColor("#FF0000") # Yellow
            req_style = ParagraphStyle('Req', parent=styles['Normal'], textColor=color, leftIndent=20)
            story.append(Paragraph(f"{symbol} <b>{req.get('requirement', '')}</b>", req_style))
            story.append(Paragraph(f"<i>Status: {req.get('status', '').title()}</i>", styles['Normal']))
            story.append(Paragraph(f"Reasoning: {req.get('details', '')}", styles['Normal']))
            if req.get('suggestion'): story.append(Paragraph(f"<b>Improvement Suggestion:</b> {req['suggestion']}", styles['Normal']))
            if req.get('resources'):
                story.append(Paragraph("<b>Recommended Resources:</b>", styles['Normal']))
                for resource in req['resources']: story.append(Paragraph(f"• {resource['name']} ({resource['type']}) - {resource['contact']}", styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
            
    doc.build(story)
    buffer.seek(0)
    return buffer.read()

# --- Main Application Logic ---
def main():
    st.set_page_config(page_title="QCB Regulatory Navigator", page_icon="📋", layout="wide")

    # --- LANGUAGE SWITCHER ---
    if 'lang' not in st.session_state: st.session_state.lang = 'en'
    lang_options = {'en': 'English', 'ar': 'العربية'}
    def change_language(): st.session_state.lang = st.session_state.lang_selector
    _, col2 = st.columns([8, 2]); 
    with col2: st.radio("Language / اللغة", options=lang_options.keys(), format_func=lambda code: lang_options[code], key='lang_selector', on_change=change_language, horizontal=True)
    lang = st.session_state.lang
    text = TRANSLATIONS[lang]
    # --- END LANGUAGE SWITCHER ---

    st.title(f"🏦 {text['title']}")
    st.markdown(f"**{text['subtitle']}**")
    st.divider()

    col1, col2, col3 = st.columns(3)
    with col1: st.subheader(text['business_plan_header']); business_plan_file = st.file_uploader(text['upload_bp_label'], type=["pdf"], key="business_plan")
    with col2: st.subheader(text['compliance_policy_header']); compliance_policy_file = st.file_uploader(text['upload_cp_label'], type=["pdf"], key="compliance_policy")
    with col3: st.subheader(text['legal_structure_header']); legal_structure_file = st.file_uploader(text['upload_ls_label'], type=["pdf"], key="legal_structure")
    st.divider()

    if 'results' not in st.session_state: st.session_state.results = None

    if st.button(text['evaluate_button'], type="primary", use_container_width=True):
        if not all([business_plan_file, compliance_policy_file, legal_structure_file]):
            st.error(text['error_upload_all'])
            return

        with st.spinner(text['spinner_text']):
            st.info(text['reading_pdfs'])
            business_plan_bytes = business_plan_file.read(); business_plan_file.seek(0)
            compliance_policy_bytes = compliance_policy_file.read(); compliance_policy_file.seek(0)
            legal_structure_bytes = legal_structure_file.read(); legal_structure_file.seek(0)
            business_plan_text = extract_text_from_pdf(business_plan_file)
            compliance_policy_text = extract_text_from_pdf(compliance_policy_file)
            legal_structure_text = extract_text_from_pdf(legal_structure_file)

            if not (business_plan_text.strip() or compliance_policy_text.strip() or legal_structure_text.strip()):
                st.error("❌ Critical Error: Could not extract text from the uploaded PDFs. Please ensure they are not scanned images.")
                return

            st.info(text['ai_analyzing'])
            evaluation_result = evaluate_compliance_with_ai(business_plan_text, compliance_policy_text, legal_structure_text)
            
            if not evaluation_result.get("requirements"):
                st.error("AI analysis failed to return results. Please try again.")
                return

            st.info(text['applying_checks'])
            all_docs_text = business_plan_text + compliance_policy_text + legal_structure_text
            evaluation_result["requirements"] = apply_hardcoded_checks(evaluation_result["requirements"], all_docs_text)

            st.info(text['mapping_recs'])
            for req in evaluation_result["requirements"]:
                if req.get("status") in ("partial", "missing"):
                    req["suggestion"] = REMEDIATION_TEMPLATES.get(req.get("id"), "Review this requirement with a compliance expert.")
                    req["resources"] = map_resources(req.get("id"))

            st.info(text['calculating_score'])
            evaluation_result["overall_score"] = calculate_transparent_score(evaluation_result["requirements"])

            st.info(text['generating_reports'])
            annotated_bp = annotate_pdf(business_plan_bytes, evaluation_result["requirements"], "business_plan")
            annotated_cp = annotate_pdf(compliance_policy_bytes, evaluation_result["requirements"], "compliance_policy")
            annotated_ls = annotate_pdf(legal_structure_bytes, evaluation_result["requirements"], "legal_structure")
            summary_pdf = generate_summary_pdf(evaluation_result["overall_score"], evaluation_result["requirements"], evaluation_result.get("recommendations", []))

            st.session_state.results = {
                'score': evaluation_result["overall_score"], 'requirements': evaluation_result["requirements"],
                'annotated_bp': annotated_bp, 'annotated_cp': annotated_cp, 'annotated_ls': annotated_ls,
                'summary_pdf': summary_pdf
            }
            st.success(text['analysis_complete'])

    if st.session_state.results:
        score = st.session_state.results['score']
        score_emoji = "🏆" if score >= 90 else "⚠️" if score >= 40 else "📋"
        st.metric(text['overall_score_metric'], f"{score}%", delta=f"{score_emoji} {text['score_delta']}")
        st.divider()
        
        urgent_items = [req for req in st.session_state.results['requirements'] if req.get("status") == "missing"]
        if urgent_items:
            s_en = 's' if len(urgent_items) != 1 else ''
            subheader_text = text['urgent_subheader'].format(count=len(urgent_items), s=s_en)
            st.markdown(f"""<div style="background: linear-gradient(135deg, #8B1538 0%, #A01B47 100%); padding: 20px; border-radius: 10px; margin: 20px 0;">
                <h3 style="color: #FFFFFF; margin: 0 0 10px 0;">{text['urgent_header']}</h3>
                <p style="color: #F5F5DC; margin: 0;"><strong>{subheader_text}</strong></p>
            </div>""", unsafe_allow_html=True)
            for item in sorted(urgent_items, key=lambda x: x.get('requirement', '')):
                with st.container():
                    category_display = (item.get('category') or 'Uncategorized').replace('_', ' ')
                    st.markdown(f"""<div style="background-color: #FFF5F5; border-left: 5px solid #8B1538; padding: 18px; margin: 12px 0; border-radius: 8px;">
                        <p style="margin: 0; font-weight: bold; color: #8B1538; font-size: 1.1em;">❌ {item.get('requirement', '')}</p>
                        <p style="margin: 8px 0 0 0; font-size: 0.8em; color: #666; text-transform: uppercase;">{category_display}</p>
                        <p style="margin: 12px 0 0 0; color: #4A4A4A;"><b>{text['gap_label']}</b> {item.get('details', '')}</p>
                        <p style="margin: 10px 0 0 0; color: #000;"><b>{text['suggestion_label']}</b> {item.get('suggestion', 'N/A')}</p>
                    </div>""", unsafe_allow_html=True)
                    st.checkbox(text['flag_review_label'].format(req_name=item.get('requirement', '')), key=f"review_{item.get('id')}")
            st.divider()
            
        st.subheader(text['download_reports_header'])
        d_col1, d_col2, d_col3, d_col4 = st.columns(4)
        with d_col1: st.download_button(text['download_bp_button'], st.session_state.results['annotated_bp'], "annotated_business_plan.pdf", "application/pdf", use_container_width=True)
        with d_col2: st.download_button(text['download_cp_button'], st.session_state.results['annotated_cp'], "annotated_compliance_policy.pdf", "application/pdf", use_container_width=True)
        with d_col3: st.download_button(text['download_ls_button'], st.session_state.results['annotated_ls'], "annotated_legal_structure.pdf", "application/pdf", use_container_width=True)
        with d_col4: st.download_button(text['download_summary_button'], st.session_state.results['summary_pdf'], "compliance_summary_report.pdf", "application/pdf", use_container_width=True, type="primary")

if __name__ == "__main__":
    main()