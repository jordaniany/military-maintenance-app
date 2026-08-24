"""
ملف التنسيقات والسمات البصرية المخصصة ودعم العربية (RTL) لتطبيق إدارة مفارز الصيانة
Custom CSS, RTL configuration, and military-themed UI components.
"""

import streamlit as st

def apply_custom_styles():
    """حقن كود CSS المخصص لدعم العربية الكامل (RTL) والمظهر العسكري الاحترافي"""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;800;900&display=swap');

    /* تطبيق الخط والاتجاه العام */
    html, body, [class*="css"], .stApp {
        font-family: 'Cairo', sans-serif !important;
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
    }

    [data-testid="stSidebar"] .stRadio label {
        color: #E2E8F0 !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }

    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label:hover {
        background: rgba(255, 255, 255, 0.08) !important;
    }

    /* رأس الصفحة والقوائم */
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 700 !important;
        color: #0F172A;
    }

    /* البطاقات الإحصائية والـ Containers */
    .metric-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.08);
        border: 1px solid #E2E8F0;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        text-align: right;
        direction: rtl;
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
    }

    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.2;
    }

    .metric-subtitle {
        font-size: 12px;
        color: #94A3B8;
        margin-top: 4px;
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
    }

    .shortage-hospital {
        font-weight: 700;
        font-size: 16px;
        color: #991B1B;
        margin-bottom: 4px;
    }

    .shortage-text {
        font-size: 14px;
        color: #7F1D1D;
        line-height: 1.6;
    }

    .shortage-meta {
        font-size: 12px;
        color: #B91C1C;
        margin-top: 6px;
        display: flex;
        gap: 16px;
    }

    /* بطاقة تفاصيل المفرزة */
    .detachment-info-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: #F8FAFC;
        border-radius: 14px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.2);
    }

    .detachment-info-title {
        font-size: 22px;
        font-weight: 800;
        color: #38BDF8;
        margin-bottom: 12px;
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

    /* تحسين عناصر الإدخال والأزرار */
    .stTextInput input, .stTextArea textarea, .stSelectbox select, .stSelectbox [data-baseweb="select"], .stMultiSelect {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
        border-radius: 8px !important;
    }

    .stDateInput input {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

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

    /* تحسين الجداول والكشوفات لتكون من اليمين إلى اليسار بالكامل */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrameResizable"],
    [data-testid="stDataFrame"] > div,
    [data-testid="stDataFrame"] iframe,
    .dvn-scroller,
    .dvn-scroll-inner,
    .gdg-style,
    [data-testid="stTable"],
    [data-testid="stTable"] table {
        direction: rtl !important;
        text-align: right !important;
        border-radius: 10px !important;
        border: 1px solid #E2E8F0 !important;
    }

    [data-testid="stDataFrame"] * {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    [data-testid="stDataFrame"] canvas {
        direction: rtl !important;
    }

    /* محاذاة نصوص الجداول وخلايا العناوين والصفوف */
    table, thead, tbody, tr, th, td {
        direction: rtl !important;
        text-align: right !important;
        font-family: 'Cairo', sans-serif !important;
    }

    th {
        background-color: #0F172A !important;
        color: #F8FAFC !important;
        font-weight: 700 !important;
        text-align: right !important;
    }

    td {
        text-align: right !important;
    }

    /* علامات التبويب والقوائم المنسدلة */
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl !important;
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        font-family: 'Cairo', sans-serif !important;
        font-weight: 600 !important;
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
    }

    /* شعار الهيدر العسكري */
    .military-header {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px 0;
        margin-bottom: 20px;
        border-bottom: 2px solid #E2E8F0;
    }
    
    .military-title-box h1 {
        margin: 0;
        font-size: 26px;
        color: #0F172A;
        font-weight: 900;
    }
    
    .military-title-box p {
        margin: 2px 0 0 0;
        color: #64748B;
        font-size: 14px;
        font-weight: 600;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_sidebar_header(title="شعبة الصيانة والتشغيل", subtitle="إدارة مفارز المستشفيات العسكرية"):
    """عرض ترويسة الشريط الجانبي بتصميم عسكري موحد قابلة للتخصيص"""
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 15px 0 20px 0; border-bottom: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">
        <div style="font-size: 36px; margin-bottom: 5px;">🛡️ ⚙️</div>
        <div style="font-size: 18px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px;">{title}</div>
        <div style="font-size: 13px; color: #94A3B8; font-weight: 600;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def render_page_header(title, subtitle, icon="🎖️"):
    """عرض ترويسة الصفحة مع الأيقونة والوصف"""
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
