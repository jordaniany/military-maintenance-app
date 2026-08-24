"""
ملف التنسيقات والسمات البصرية المخصصة ودعم العربية (RTL) لتطبيق إدارة مفارز الصيانة
Custom CSS, RTL configuration, and military-themed UI components.
"""

import streamlit as st
import pandas as pd

def apply_custom_styles():
    """حقن كود CSS المخصص لدعم العربية الكامل (RTL) والمظهر العسكري الاحترافي"""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

    /* تطبيق الخط والاتجاه العام على الصفحة وكافة الحاويات */
    *, *::before, *::after {
        font-family: 'Cairo', sans-serif !important;
    }

    html, body, [class*="css"], .stApp, 
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stElementContainer"],
    [data-testid="stMarkdownContainer"],
    [data-testid="stForm"],
    [data-testid="stExpander"],
    div[data-baseweb] {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    /* قلب اتجاه الأعمدة الأفقية st.columns لتبدأ من اليمين إلى اليسار تماماً */
    [data-testid="stHorizontalBlock"] {
        direction: rtl !important;
        display: flex !important;
        flex-direction: row !important;
        text-align: right !important;
    }

    [data-testid="column"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* الشريط الجانبي */
    [data-testid="stSidebar"] {
        direction: rtl !important;
        text-align: right !important;
        background: linear-gradient(180deg, #0F172A 0%, #1E293B 100%) !important;
        border-left: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
        font-family: 'Cairo', sans-serif !important;
        direction: rtl !important;
        text-align: right !important;
    }

    [data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
        text-align: right !important;
    }

    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.08) !important;
    }

    /* رأس الصفحة والقوائم والعناوين */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        color: #0F172A;
        text-align: right !important;
        direction: rtl !important;
    }

    /* شعار وترويسة الهيدر العسكري */
    .military-header {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        direction: rtl !important;
        text-align: right !important;
        gap: 16px !important;
        padding: 12px 0 !important;
        margin-bottom: 20px !important;
        border-bottom: 2px solid #E2E8F0 !important;
    }
    
    .military-title-box {
        direction: rtl !important;
        text-align: right !important;
    }

    .military-title-box h1 {
        margin: 0 !important;
        font-size: 26px !important;
        color: #0F172A !important;
        font-weight: 900 !important;
        text-align: right !important;
    }
    
    .military-title-box p {
        margin: 2px 0 0 0 !important;
        color: #64748B !important;
        font-size: 14px !important;
        font-weight: 600 !important;
        text-align: right !important;
    }

    /* البطاقات الإحصائية */
    .metric-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.08);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: right !important;
        direction: rtl !important;
        position: relative;
        overflow: hidden;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px -4px rgba(15, 23, 42, 0.12);
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 4px;
        height: 100%;
        background: #15803D;
    }

    .metric-card.alert::before {
        background: #DC2626;
    }

    .metric-card.info::before {
        background: #0284C7;
    }

    .metric-card.warning::before {
        background: #D97706;
    }

    .metric-title {
        font-size: 14px;
        font-weight: 600;
        color: #64748B;
        margin-bottom: 6px;
        text-align: right !important;
    }

    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
        text-align: right !important;
    }

    .metric-subtitle {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 4px;
        text-align: right !important;
    }

    /* تنبيهات النواقص العاجلة */
    .shortage-card {
        background: #FEF2F2;
        border-right: 4px solid #EF4444;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 12px;
        border-top: 1px solid #FEE2E2;
        border-bottom: 1px solid #FEE2E2;
        border-left: 1px solid #FEE2E2;
        direction: rtl !important;
        text-align: right !important;
    }

    .shortage-hospital {
        font-weight: 700;
        font-size: 16px;
        color: #991B1B;
        margin-bottom: 4px;
        text-align: right !important;
    }

    .shortage-text {
        font-size: 14px;
        color: #7F1D1D;
        line-height: 1.6;
        text-align: right !important;
    }

    .shortage-meta {
        font-size: 12px;
        color: #B91C1C;
        margin-top: 6px;
        display: flex;
        gap: 16px;
        direction: rtl !important;
    }

    /* بطاقة تفاصيل المفرزة */
    .detachment-info-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
        direction: rtl !important;
        text-align: right !important;
    }

    .detachment-info-title {
        font-size: 22px;
        font-weight: 800;
        color: #38BDF8;
        margin-bottom: 12px;
        text-align: right !important;
    }

    .detachment-pill {
        display: inline-block;
        background: rgba(255, 255, 255, 0.12);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
        color: #E2E8F0;
        margin-left: 8px;
        margin-bottom: 8px;
    }

    /* عناصر الإدخال، النصوص، الفلاتر، التواريخ */
    .stTextInput, .stTextArea, .stSelectbox, .stMultiSelect, .stDateInput, .stNumberInput {
        direction: rtl !important;
        text-align: right !important;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stSelectbox [data-baseweb="select"], .stMultiSelect div, .stDateInput input {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        border-radius: 8px !important;
    }

    label[data-testid="stWidgetLabel"] {
        direction: rtl !important;
        text-align: right !important;
        display: block !important;
        width: 100% !important;
    }

    label[data-testid="stWidgetLabel"] p {
        text-align: right !important;
        direction: rtl !important;
        font-weight: 700 !important;
    }

    /* الأزرار */
    .stButton button {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    .stButton button[kind="primary"] {
        background-color: #15803D !important;
        border-color: #15803D !important;
        color: white !important;
    }

    .stButton button[kind="primary"]:hover {
        background-color: #166534 !important;
        border-color: #166534 !important;
        box-shadow: 0 4px 12px rgba(21, 128, 61, 0.3) !important;
    }

    .stButton button[kind="secondary"] {
        border-color: #CBD5E1 !important;
    }

    /* علامات التبويب Tabs */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        justify-content: flex-start !important;
        text-align: right !important;
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        font-size: 15px !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 10px 20px !important;
    }

    /* صندوق الإعدادات */
    .settings-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        direction: rtl !important;
        text-align: right !important;
    }

    .settings-box-header {
        font-size: 17px;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 1px solid #F1F5F9;
        padding-bottom: 8px;
        direction: rtl !important;
    }

    /* ========================================================================= */
    /* جداول وكشوفات البيانات الأصيلة من اليمين إلى اليسار (RTL Full Native Table) */
    /* ========================================================================= */
    .rtl-table-wrapper {
        direction: rtl !important;
        text-align: right !important;
        width: 100% !important;
        overflow-x: auto !important;
        overflow-y: auto !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px !important;
        background: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.05) !important;
        margin: 14px 0 20px 0 !important;
    }

    table.rtl-table {
        width: 100% !important;
        border-collapse: collapse !important;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        font-size: 13.5px !important;
    }

    table.rtl-table thead {
        position: sticky !important;
        top: 0 !important;
        z-index: 10 !important;
        background-color: #0F172A !important;
    }

    table.rtl-table th {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        font-weight: 800 !important;
        padding: 13px 14px !important;
        text-align: right !important;
        direction: rtl !important;
        border-bottom: 2px solid #334155 !important;
        white-space: nowrap !important;
        letter-spacing: 0.2px;
    }

    table.rtl-table td {
        padding: 11px 14px !important;
        text-align: right !important;
        direction: rtl !important;
        color: #1E293B !important;
        border-bottom: 1px solid #E2E8F0 !important;
        white-space: nowrap !important;
    }

    table.rtl-table tbody tr:nth-child(even) {
        background-color: #F8FAFC !important;
    }

    table.rtl-table tbody tr:nth-child(odd) {
        background-color: #FFFFFF !important;
    }

    table.rtl-table tbody tr:hover {
        background-color: #F1F5F9 !important;
        transition: background-color 0.15s ease !important;
    }

    .badge-rank {
        display: inline-block;
        background: #F1F5F9;
        color: #0F172A;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 12.5px;
        border: 1px solid #CBD5E1;
    }

    .badge-mil-id {
        font-family: monospace, sans-serif !important;
        font-weight: 700;
        color: #0369A1;
        background: #E0F2FE;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #BAE6FD;
        font-size: 13px;
    }

    .badge-specialty {
        display: inline-block;
        background: #F0FDF4;
        color: #166534;
        font-weight: 600;
        padding: 3px 9px;
        border-radius: 6px;
        border: 1px solid #BBF7D0;
        font-size: 12.5px;
    }

    .badge-commander {
        display: inline-block;
        background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
        color: #92400E;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11.5px;
        border: 1px solid #F59E0B;
        margin-left: 6px;
        box-shadow: 0 1px 3px rgba(245, 158, 11, 0.2);
    }

    .commander-row {
        background-color: #FEFCE8 !important;
        font-weight: 600;
    }

    /* بطاقة الهوية والبيانات العسكرية الشاملة للفني */
    .military-id-card {
        background: #FFFFFF;
        border: 2px solid #0F172A;
        border-radius: 14px;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.12);
        margin: 16px 0 24px 0;
        overflow: hidden;
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    .id-card-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #F8FAFC;
        padding: 14px 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 3px solid #15803D;
    }

    .id-card-title {
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.3px;
    }

    .id-card-badge {
        font-size: 12.5px;
        color: #94A3B8;
        font-weight: 600;
    }

    .id-card-body {
        padding: 18px 20px;
        background: #F8FAFC;
    }

    .id-card-hero {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #FFFFFF;
        padding: 12px 18px;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        margin-bottom: 14px;
    }

    .id-card-name {
        font-size: 19px;
        font-weight: 800;
        color: #0F172A;
    }

    .id-card-mil-badge {
        background: #E0F2FE;
        color: #0369A1;
        font-weight: 800;
        font-size: 14.5px;
        padding: 4px 12px;
        border-radius: 8px;
        border: 1px solid #BAE6FD;
        font-family: monospace, sans-serif !important;
    }

    .id-card-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
        gap: 10px;
        margin-bottom: 12px;
    }

    .id-grid-item {
        background: #FFFFFF;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        font-size: 13.5px;
        color: #334155;
    }

    .id-grid-item b {
        color: #0F172A;
        margin-left: 4px;
    }

    .id-card-notes {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 13.5px;
        color: #92400E;
        margin-top: 10px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_sidebar_header(title="شعبة الصيانة والتشغيل", subtitle="إدارة مفارز المستشفيات العسكرية"):
    """عرض ترويسة الشريط الجانبي بتصميم عسكري موحد قابلة للتخصيص"""
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 15px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px; direction: rtl;">
        <div style="font-size: 36px; margin-bottom: 5px;">🛡️ ⚙️</div>
        <div style="font-size: 18px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px;">{title}</div>
        <div style="font-size: 13px; color: #94A3B8; font-weight: 600;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_page_header(title, subtitle, icon="🎖️"):
    """عرض ترويسة الصفحة مع الأيقونة والوصف محاذاة لليمين"""
    st.markdown(f"""
    <div class="military-header">
        <div style="font-size: 34px; background: #F1F5F9; padding: 10px 14px; border-radius: 12px; border: 1px solid #CBD5E1;">
            {icon}
        </div>
        <div class="military-title-box">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_metric_card(title, value, subtitle="", card_type="default"):
    """توليد بطاقة إحصائية مخصصة"""
    type_class = f" {card_type}" if card_type != "default" else ""
    return f"""
    <div class="metric-card{type_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """

def render_rtl_table(df, max_height="550px", highlight_commander=False):
    """
    توليد جدول HTML عربي من اليمين إلى اليسار (RTL) بالكامل
    يضمن ظهور الأعمدة بالترتيب العربي الطبيعي (العمود الأول في أقصى اليمين)
    مع إمكانية تمييز قائد المفرزة (الأعلى رتبة)
    """
    if df is None or df.empty:
        return '<div style="color: #94A3B8; font-size: 13px; padding: 10px; text-align: right; direction: rtl;">⚠️ لا توجد بيانات لعرضها في الجدول.</div>'
    
    headers_html = "".join([f"<th>{col}</th>" for col in df.columns])
    
    rows_html = []
    for idx, row in df.iterrows():
        cells = []
        is_commander = (idx == 0 and highlight_commander)
        
        for col in df.columns:
            val = str(row[col]) if row[col] is not None and not pd.isna(row[col]) else "-"
            # تنسيق خاص للحقول
            if col == "الرتبة":
                badge_extra = '<span class="badge-commander">👑 قائد المفرزة</span> ' if is_commander else ''
                cells.append(f'<td>{badge_extra}<span class="badge-rank">{val}</span></td>')
            elif col == "الاسم الرباعي":
                name_style = ' style="font-weight: 800; color: #0F172A;"' if is_commander else ''
                cells.append(f'<td{name_style}>{val}</td>')
            elif col == "الرقم العسكري":
                cells.append(f'<td><span class="badge-mil-id">{val}</span></td>')
            elif col in ["الصنف", "التخصص الفني", "الصنف الأساسي"]:
                cells.append(f'<td><span class="badge-specialty">{val}</span></td>')
            elif col == "مدة الخدمة بالمفرزة":
                cells.append(f'<td><b style="color: #15803D;">{val}</b></td>')
            else:
                cells.append(f'<td>{val}</td>')
                
        row_style = ' class="commander-row"' if is_commander else ''
        rows_html.append(f"<tr{row_style}>{''.join(cells)}</tr>")
        
    return f"""
    <div class="rtl-table-wrapper" style="max-height: {max_height};">
        <table class="rtl-table" dir="rtl">
            <thead>
                <tr>{headers_html}</tr>
            </thead>
            <tbody>
                {"".join(rows_html)}
            </tbody>
        </table>
    </div>
    """

def render_technician_card(tech):
    """توليد كود HTML لبطاقة الفني التعريفية العسكرية الشاملة"""
    if tech is None:
        return ""
    
    rank = tech.get("الرتبة") or tech.get("rank") or "-"
    name = tech.get("الاسم الرباعي") or tech.get("full_name") or tech.get("الاسم") or "-"
    mil_id = tech.get("الرقم العسكري") or tech.get("military_id") or "-"
    category = tech.get("الصنف") or tech.get("specialty") or tech.get("الصنف الأساسي") or "-"
    job = tech.get("المهنة الحالية") or tech.get("current_job") or "-"
    hosp = tech.get("المستشفى الحالي") or tech.get("hospital_name") or tech.get("المستشفى") or "-"
    gov = tech.get("المحافظة") or tech.get("governorate") or "-"
    residence = tech.get("مكان السكن") or tech.get("residence") or tech.get("السكن") or "-"
    join_date = tech.get("تاريخ الالتحاق بالمفرزة") or tech.get("join_date") or tech.get("تاريخ الالتحاق") or "-"
    duration = tech.get("مدة الخدمة بالمفرزة") or tech.get("duration") or "-"
    phone = tech.get("رقم الهاتف") or tech.get("phone_number") or tech.get("الهاتف") or "-"
    notes = tech.get("الملاحظات والتقييم الفني") or tech.get("evaluation_and_notes") or tech.get("الملاحظات") or ""

    notes_html = f"""
    <div class="id-card-notes">
        📝 <b>الملاحظات والتقييم الفني:</b> {notes}
    </div>
    """ if notes and str(notes).strip() and str(notes).strip() != "-" else ""

    phone_display = f'<a href="tel:{phone}" style="color: #15803D; font-weight: 700; text-decoration: none;">📞 {phone}</a>' if phone and str(phone).strip() != "-" else "-"

    return f"""
    <div class="military-id-card">
        <div class="id-card-header">
            <div class="id-card-title">🪪 البطاقة التعريفية العسكرية الشاملة</div>
            <div class="id-card-badge">🛡️ القوات المسلحة الأردنية - الجيش العربي</div>
        </div>
        <div class="id-card-body">
            <div class="id-card-hero">
                <div class="id-card-name">🎖️ {rank} / {name}</div>
                <div class="id-card-mil-badge">الرقم العسكري: {mil_id}</div>
            </div>
            <div class="id-card-grid">
                <div class="id-grid-item">🛡️ <b>الصنف:</b> {category}</div>
                <div class="id-grid-item">💼 <b>المهنة الحالية:</b> {job}</div>
                <div class="id-grid-item">🏥 <b>المستشفى / المفرزة:</b> {hosp} ({gov})</div>
                <div class="id-grid-item">📍 <b>مكان السكن:</b> {residence}</div>
                <div class="id-grid-item">📅 <b>تاريخ الالتحاق:</b> {join_date}</div>
                <div class="id-grid-item">⏳ <b>مدة الخدمة بالمفرزة:</b> <span style="color: #15803D; font-weight: 700;">{duration}</span></div>
                <div class="id-grid-item">📱 <b>رقم الهاتف:</b> {phone_display}</div>
            </div>
            {notes_html}
        </div>
    </div>
    """
