"""
تطبيق إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية بالمحافظات
نظام تفاعلي متكامل مبني باستخدام Python, Streamlit, Pandas, SQLite مع واجهة عربية كاملة (RTL).
"""

import streamlit as st
import pandas as pd
import io
import json
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

import database as db
import styles

# --- إعداد الصفحة العامة ---
st.set_page_config(
    page_title="نظام إدارة مفارز الصيانة العسكرية",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# تطبيق التنسيقات العربية المخصصة (RTL)
styles.apply_custom_styles()

# تهيئة قاعدة البيانات والتأكد من وجود الجداول والحقول والإعدادات
db.init_db()

# جلب إعدادات المنظومة المخصصة
settings = db.get_app_settings()

# قائمة الرتب العسكرية القياسية (مرتبة من الأعلى إلى الأدنى)
MILITARY_RANKS = [
    "مقدم",
    "رائد",
    "نقيب",
    "ملازم/1",
    "ملازم",
    "وكيل أول",
    "وكيل",
    "رقيب أول",
    "رقيب",
    "عريف",
    "جندي أول",
    "جندي مكلف",
    "مدني"
]

# قائمة أصناف الفنيين المعتمدة (المهن والتخصصات الفنية)
MILITARY_CATEGORIES = [
    "تكييف وتبريد",
    "كهرباء قوى ومحولات",
    "شبكات مياه وصحي",
    "إنشائي عام",
    "أجهزة طبية وميكانيك",
    "صنف آخر"
]
SPECIALTIES = MILITARY_CATEGORIES

# قائمة المحافظات
GOVERNORATES = [
    "إربد",
    "الزرقاء",
    "الكرك",
    "العقبة",
    "مأدبا",
    "المفرق",
    "جرش",
    "عجلون",
    "عمان",
    "البلقاء",
    "معان",
    "الطفيلة"
]

# دالة مساعدة لتصدير البيانات إلى ملف Excel منسق في الذاكرة
def export_to_excel(df: pd.DataFrame, sheet_name="البيانات") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()

# --- التحقق من تسجيل الدخول (Authentication Gateway) ---
if not st.session_state.get("authenticated", False):
    styles.apply_custom_styles()
    
    _, login_col, _ = st.columns([1, 2, 1])
    with login_col:
        st.markdown("""<div style="background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%); color: #F8FAFC; padding: 24px 20px; border-radius: 14px 14px 0 0; text-align: center; border-bottom: 4px solid #15803D; box-shadow: 0 10px 25px rgba(15, 23, 42, 0.2); direction: rtl;"><div style="font-size: 42px; margin-bottom: 6px;">🛡️ ⚙️ 🏥</div><div style="font-size: 22px; font-weight: 900; color: #F8FAFC; letter-spacing: 0.5px;">شعبة صيانة المستشفيات العسكرية</div><div style="font-size: 13.5px; color: #94A3B8; font-weight: 600; margin-top: 4px;">فرع صيانة المستشفيات العسكرية</div></div>""", unsafe_allow_html=True)
        
        with st.form(key="login_gateway_form"):
            st.markdown("##### 🔐 تسجيل الدخول إلى المنظومة بواسطة الرقم العسكري:")
            login_u = st.text_input("👤 الرقم العسكري / رقم التعريف:", placeholder="أدخل الرقم العسكري (مثال: 10001 أو 20002)...", key="input_login_u")
            login_p = st.text_input("🔑 كلمة المرور:", type="password", placeholder="أدخل كلمة المرور...", key="input_login_p")
            
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            login_btn = st.form_submit_button("🚀 تسجيل الدخول", type="primary", use_container_width=True)
            
            if login_btn:
                ok, user_dict, auth_msg = db.authenticate_user(login_u, login_p)
                if ok:
                    st.session_state["authenticated"] = True
                    st.session_state["current_user"] = user_dict
                    st.toast(f"مرحباً بك {user_dict['rank']} / {user_dict['full_name']}", icon="🛡️")
                    st.rerun()
                else:
                    st.error(auth_msg)
        
        # دليل إرشادي سريع للحسابات الافتراضية
        with st.expander("ℹ️ دليل الحسابات المصرحة بالرقم العسكري لتجربة المنظومة:", expanded=True):
            st.markdown("""<div style="font-size: 13px; line-height: 1.8; color: #334155; direction: rtl; text-align: right;">👑 <b>حساب رئيس الفرع (المقدم المهندس رامي سبع العيش - الصلاحية الشاملة):</b><br>• الرقم العسكري: <code style="color: #0369A1; font-weight: 700;">10001</code> أو <code style="color: #0369A1; font-weight: 700;">admin</code> | كلمة المرور: <code>123456</code><br><br>🏥 <b>حساب قائد مفرزة مستشفى الأمير علي - الكرك (المقدم المهندسة منار):</b><br>• الرقم العسكري: <code style="color: #15803D; font-weight: 700;">20002</code> أو <code style="color: #15803D; font-weight: 700;">cmd_karak</code> | كلمة المرور: <code>123456</code><br><br>🏥 <b>حسابات قادة المفارز بالمستشفيات العسكرية بالمحافظات:</b><br>• مفرزة مستشفى الأمير راشد (إربد): الرقم العسكري <code style="color: #15803D; font-weight: 700;">20001</code> | كلمة المرور: <code>123456</code><br>• مفرزة مستشفى الأمير هاشم (الزرقاء): الرقم العسكري <code style="color: #15803D; font-weight: 700;">20003</code> | كلمة المرور: <code>123456</code><br>• مفرزة مستشفى الأميرة هيا (جرش/عجلون): الرقم العسكري <code style="color: #15803D; font-weight: 700;">20004</code> | كلمة المرور: <code>123456</code><br>• مفرزة مستشفى الملكة علياء (عمان): الرقم العسكري <code style="color: #15803D; font-weight: 700;">20005</code> | كلمة المرور: <code>123456</code></div>""", unsafe_allow_html=True)
            
    st.stop()

# ==============================================================================
# المستخدم المسجل والجلسة النشطة (Authenticated Session)
# ==============================================================================
current_user = st.session_state.get("current_user", {})
user_role = current_user.get("role", "قائد مفرزة")
is_branch_chief = (user_role == "رئيس الفرع")
active_detachment_id = current_user.get("detachment_id")

# --- الشريط الجانبي (Sidebar) ---
styles.render_sidebar_header(
    title=settings.get("sidebar_title", "شعبة الصيانة والتشغيل"),
    subtitle="إدارة مفارز المستشفيات العسكرية"
)

# بطاقة المستخدم النشط في الشريط الجانبي
hosp_badge_str = f"🏥 <b>المفرزة:</b> {current_user['hospital_name']}" if current_user.get('hospital_name') else "🛡️ <b>النطاق:</b> إشراف وتعديل شامل لكافة المفارز"
st.sidebar.markdown(f"""
<div class="user-profile-badge">
    <div style="font-size: 14.5px; font-weight: 800; color: #38BDF8; margin-bottom: 4px;">
        👤 {current_user.get('rank', 'مقدم')} / {current_user.get('full_name', 'المهندس رامي سبع العيش')}
    </div>
    <div style="font-size: 12.5px; color: #CBD5E1;">
        🎖️ <b>الصفة:</b> <span style="color: #FDE68A; font-weight: 700;">{user_role}</span><br>
        {hosp_badge_str}
    </div>
</div>
""", unsafe_allow_html=True)

# زر تسجيل الخروج
if st.sidebar.button("🚪 تسجيل الخروج", key="btn_logout_top", use_container_width=True, type="secondary"):
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.toast("تم تسجيل الخروج بنجاح.", icon="👋")
    st.rerun()

st.sidebar.markdown("---")

# بناء خيارات القائمة حسب الصلاحيات والدور
if is_branch_chief:
    menu_options = [
        "📊 لوحة المؤشرات العامة",
        "📋 الموجود الصباحي اليومي",
        "🏥 كشف المفارز والمستشفيات",
        "👥 إدارة المرتبات والفنيين",
        "🔄 سجل حركات النقل",
        "⚙️ الإعدادات وتخصيص المنظومة"
    ]
else:
    menu_options = [
        "📋 الموجود الصباحي لمفرزتي",
        "🏥 كشف مفرزتي وبيانات المرتب"
    ]

menu_choice = st.sidebar.radio("القائمة الرئيسية:", menu_options, index=0)

st.sidebar.markdown("---")

# إحصائيات سريعة في الشريط الجانبي
stats = db.get_dashboard_stats()
st.sidebar.markdown(f"""
<div style="background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 8px; font-size: 13px; color: #CBD5E1;">
    <div style="font-weight: 700; color: #F8FAFC; margin-bottom: 8px;">📌 ملخص المنظومة الفورية:</div>
    <div>• إجمالي المفارز: <b style="color: #38BDF8;">{stats['total_detachments']}</b></div>
    <div>• إجمالي الفنيين: <b style="color: #4ADE80;">{stats['total_technicians']}</b></div>
    <div>• مفارز بها نواقص: <b style="color: {'#F87171' if stats['detachments_with_shortages'] > 0 else '#4ADE80'};">{stats['detachments_with_shortages']}</b></div>
    <div>• حركات النقل الموثقة: <b style="color: #FBBF24;">{stats['total_movements']}</b></div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 1. لوحة المؤشرات العامة (Dashboard)
# ==============================================================================
if menu_choice == "📊 لوحة المؤشرات العامة":
    styles.render_page_header(
        settings.get("app_title", "نظام إدارة مفارز الصيانة العسكرية"),
        settings.get("app_subtitle", "نظرة شاملة ولحظية على القوى البشرية، جاهزية المفارز، وتنبيهات النواقص بالمستشفيات العسكرية"),
        "📊"
    )

    # 1.1 بطاقات المؤشرات الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(styles.render_metric_card("إجمالي الفنيين المسجلين", f"{stats['total_technicians']} فني", "جاهزية القوى البشرية", "info"), unsafe_allow_html=True)
    with col2:
        st.markdown(styles.render_metric_card("إجمالي المفارز العسكرية", f"{stats['total_detachments']} مفرزة", "موزعة بالمحافظات", "default"), unsafe_allow_html=True)
    with col3:
        shortage_type = "alert" if stats['detachments_with_shortages'] > 0 else "default"
        st.markdown(styles.render_metric_card("مفارز بها نواقص مسجلة", f"{stats['detachments_with_shortages']} مستشفى", "تتطلب متابعة عاجلة", shortage_type), unsafe_allow_html=True)
    with col4:
        st.markdown(styles.render_metric_card("حركات النقل الموثقة", f"{stats['total_movements']} حركة", "سجل التبديل والتعزيز", "warning"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 1.2 قسم تنبيهات النواقص والاحتياجات البشرية (Alert Section)
    st.markdown("### ⚠️ سجل وتنبيهات النواقص والاحتياجات البشرية العاجلة")
    st.caption("يعرض الاحتياجات والنواقص المسجلة مباشرة من قادة المفارز بالمستشفيات لمتابعة إجراءات التزويد والتعزيز")

    if stats["shortages_list"]:
        for shortage in stats["shortages_list"]:
            st.markdown(f"""
            <div class="shortage-card">
                <div class="shortage-hospital">🏥 {shortage['hospital_name']} ({shortage['governorate']})</div>
                <div class="shortage-text">📋 <b>الاحتياجات والنواقص:</b> {shortage['staffing_shortages']}</div>
                <div class="shortage-meta">
                    <span>👤 <b>قائد المفرزة:</b> {shortage['supervisor_rank']} / {shortage['supervisor_name']}</span>
                    <span>📞 <b>هاتف التواصل:</b> {shortage['contact_phone'] or 'غير مسجل'}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("✅ لا توجد نواقص مسجلة حالياً في أي من المفارز. كافة المستشفيات مكتملة النصاب الفني.")

    st.markdown("<br>", unsafe_allow_html=True)

    # 1.3 المخططات البيانية
    st.markdown("### 📈 التحليلات الإحصائية وتوزيع القوة البشرية")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # رسم بياني: توزيع الفنيين حسب التخصص
        if stats["specialty_distribution"]:
            spec_df = pd.DataFrame(stats["specialty_distribution"])
            spec_df.columns = ["الصنف", "العدد"]
            fig_spec = px.pie(
                spec_df,
                names="الصنف",
                values="العدد",
                title="توزيع القوة البشرية حسب الصنف",
                hole=0.45,
                color_discrete_sequence=["#0F172A", "#15803D", "#0284C7", "#D97706", "#7E22CE", "#64748B"]
            )
            fig_spec.update_layout(
                font=dict(family="Cairo", size=13),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_spec, use_container_width=True)
        else:
            st.info("لا توجد بيانات فنيين كافية للرسم البياني.")

    with chart_col2:
        # رسم بياني: توزيع الفنيين على المستشفيات
        if stats["hospital_distribution"]:
            hosp_df = pd.DataFrame(stats["hospital_distribution"])
            hosp_df.columns = ["المستشفى", "المحافظة", "عدد الفنيين"]
            hosp_df["المستشفى_المختصر"] = hosp_df["المستشفى"].str.replace("بن الحسن العسكري", "").str.replace("بنت الحسين العسكري", "").str.replace("بن الحسين", "")

            fig_hosp = px.bar(
                hosp_df,
                x="المستشفى_المختصر",
                y="عدد الفنيين",
                color="المحافظة",
                text="عدد الفنيين",
                title="توزيع القوة البشرية على المستشفيات والمحافظات",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_hosp.update_traces(textposition='outside')
            fig_hosp.update_layout(
                font=dict(family="Cairo", size=13),
                xaxis_title="المستشفى العسكري",
                yaxis_title="عدد الفنيين المرتبين",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig_hosp, use_container_width=True)
        else:
            st.info("لا توجد بيانات مستشفيات كافية للرسم البياني.")


# ==============================================================================
# 2. الموجود الصباحي اليومي (Daily Morning Roll Call)
# ==============================================================================
elif menu_choice in ["📋 الموجود الصباحي اليومي", "📋 الموجود الصباحي لمفرزتي"]:
    is_branch_chief = (user_role == "رئيس الفرع")
    active_commander_detachment = db.get_detachment_by_id(active_detachment_id) if active_detachment_id else None

    if is_branch_chief:
        styles.render_page_header(
            "الموجود الصباحي اليومي للمفارز",
            "إشراف قيادي على كشوفات الموجود اليومي لكافة المفارز بالمملكة، متابعة الجاهزية، وصلاحية التعديل الشاملة للأيام السابقة",
            "📋"
        )
    else:
        hosp_title = active_commander_detachment['hospital_name'] if active_commander_detachment else 'المفرزة'
        styles.render_page_header(
            f"الموجود الصباحي - كشف مرتبات {hosp_title}",
            "تسجيل واعتماد الحضور والموجود اليومي لفنيي المفرزة (موجود / مجاز / مراجعة مرضية)، وأرشيف الأيام السابقة",
            "📋"
        )

    # --------------------------------------------------------------------------
    # أ. واجهة قائد المفرزة (Detachment Commander View)
    # --------------------------------------------------------------------------
    if not is_branch_chief:
        if not active_commander_detachment:
            st.error("⚠️ لم يتم تحديد المفرزة المسندة لحسابك. يرجى مراجعة رئيس الفرع لربط حسابك بالمفرزة.")
        else:
            det_id = active_commander_detachment["id"]
            det_name = active_commander_detachment["hospital_name"]
            det_gov = active_commander_detachment["governorate"]
            supervisor_name = active_commander_detachment["supervisor_name"]
            supervisor_rank = active_commander_detachment["supervisor_rank"]

            cmd_tab1, cmd_tab2 = st.tabs([
                "📝 تسجيل / كشف موجود اليوم",
                "🗓️ كشف وسجل الأيام السابقة للمفرزة"
            ])

            # --- تبويب موجود اليوم للمفرزة ---
            with cmd_tab1:
                col_d1, col_d2 = st.columns([1, 2])
                with col_d1:
                    selected_roll_date = st.date_input(
                        "📅 تاريخ الموجود الصباحي:",
                        value=date.today(),
                        key="cmd_roll_date"
                    )
                with col_d2:
                    st.markdown(f"""
                    <div style="background: rgba(15, 23, 42, 0.04); border: 1px solid #CBD5E1; border-radius: 8px; padding: 10px 14px; margin-top: 24px; font-size: 13.5px;">
                        🏥 <b>المفرزة:</b> {det_name} ({det_gov}) | 👤 <b>قائد المفرزة:</b> {supervisor_rank} / {supervisor_name}
                    </div>
                    """, unsafe_allow_html=True)

                roll_date_str = str(selected_roll_date)
                existing_rc, existing_entries = db.get_daily_roll_call(det_id, roll_date_str)

                # حالة 1: تم حفظ واعتماد الموجود مسبقاً (مغلق ومحمي من التعديل)
                if existing_rc is not None:
                    st.markdown(f"""
                    <div class="rollcall-banner">
                        <div>
                            <div style="font-size: 17px; font-weight: 800; color: #38BDF8; margin-bottom: 4px;">
                                🔒 تم حفظ واعتماد الموجود الصباحي لهذا اليوم بنجاح
                            </div>
                            <div style="font-size: 13px; color: #94A3B8;">
                                👤 <b>القائم بالاعتماد:</b> {existing_rc['saved_by_rank']} / {existing_rc['saved_by_name']} &nbsp;|&nbsp; 
                                ⏰ <b>وقت الحفظ:</b> {existing_rc['saved_at']}
                            </div>
                        </div>
                        <div>
                            <span class="badge-locked">🔒 معتمد ومقفل</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.warning("⚠️ **قاعدة القفل:** ما دام أتم قائد المفرزة الحفظ للموجود الصباحي فلا يمكن إجراء أي تعديل عليه. (صلاحية التعديل للأيام السابقة أو فك القفل مقتصرة حصرياً على **رئيس الفرع**).")

                    # بطاقات إحصائيات الموجود المعتمد
                    mcol1, mcol2, mcol3, mcol4, mcol5 = st.columns(5)
                    with mcol1:
                        st.markdown(styles.render_metric_card("القوة الإجمالية", f"{existing_rc['total_strength']} فني", "كشف المرتب الكامل", "default"), unsafe_allow_html=True)
                    with mcol2:
                        st.markdown(styles.render_metric_card("الموجود الفعلي", f"{existing_rc['present_count']} فني", "حاضر بالمفرزة", "info"), unsafe_allow_html=True)
                    with mcol3:
                        st.markdown(styles.render_metric_card("المجازين", f"{existing_rc['leave_count']} فني", "إجازات رسمية", "warning"), unsafe_allow_html=True)
                    with mcol4:
                        st.markdown(styles.render_metric_card("مراجعة مرضية", f"{existing_rc['sick_count']} فني", "مراجعات وتقارير", "alert"), unsafe_allow_html=True)
                    with mcol5:
                        readiness = round((existing_rc['present_count'] / existing_rc['total_strength'] * 100), 1) if existing_rc['total_strength'] > 0 else 0
                        st.markdown(styles.render_metric_card("نسبة الجاهزية", f"{readiness}%", "نسبة القوة الحاضرة", "info"), unsafe_allow_html=True)

                    if existing_rc.get("notes"):
                        st.info(f"📝 **ملاحظات قائد المفرزة:** {existing_rc['notes']}")

                    # عرض جدول المرتب المعتمد بالشارات اللونية
                    st.markdown(f"#### 👥 كشف مرتبات المفرزة المعتمد لتاريخ ({roll_date_str})")
                    
                    roster_rows = []
                    for idx, e in enumerate(existing_entries, 1):
                        st_val = e.get("status", "موجود")
                        if st_val == "موجود":
                            st_html = '<span class="badge-present">✅ موجود</span>'
                        elif st_val == "مجاز":
                            st_html = '<span class="badge-leave">🏖️ مجاز</span>'
                        else:
                            st_html = '<span class="badge-sick">🏥 مراجعة مرضية</span>'

                        note_val = e.get("notes") or "-"
                        roster_rows.append(f'<tr><td style="text-align: center; font-weight: 700;">{idx}</td><td><span class="badge-mil-id">{e["military_id"]}</span></td><td><span class="badge-rank">{e["rank"]}</span></td><td style="font-weight: 800; color: #0F172A;">{e["full_name"]}</td><td><span class="badge-specialty">{e["specialty"]}</span></td><td style="text-align: center;">{st_html}</td><td style="color: #475569;">{note_val}</td></tr>')

                    table_html = f'<div class="rtl-table-wrapper"><table class="rtl-table" dir="rtl"><thead><tr><th style="text-align: center; width: 40px;">م</th><th>الرقم العسكري</th><th>الرتبة</th><th>الاسم الرباعي</th><th>الصنف</th><th style="text-align: center;">الحالة</th><th>الملاحظات / سبب الغياب</th></tr></thead><tbody>{"".join(roster_rows)}</tbody></table></div>'
                    st.markdown(table_html, unsafe_allow_html=True)

                    # زر تصدير كشف الموجود إلى Excel
                    excel_bytes = db.export_roll_call_to_excel(existing_rc, existing_entries)
                    st.download_button(
                        label=f"📥 تصدير كشف موجود ({roll_date_str}) إلى Excel",
                        data=excel_bytes,
                        file_name=f"موجود_{det_name.replace(' ', '_')}_{roll_date_str}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_locked_rc_{det_id}_{roll_date_str}",
                        use_container_width=True
                    )

                # حالة 2: لم يتم الحفظ بعد -> نموذج إدخال الموجود الصباحي
                else:
                    tech_df = db.get_technicians_by_detachment_df(det_id, apply_custom_columns=False)
                    if tech_df.empty:
                        st.warning("⚠️ لا يوجد فنيين مسجلين على مرتب هذه المفرزة لإدخال الموجود. يرجى إضافة مرتبات للمفرزة أولاً.")
                    else:
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%); border: 1px solid #86EFAC; border-radius: 12px; padding: 16px 20px; margin-bottom: 18px;">
                            <div style="font-weight: 800; color: #166534; font-size: 16px; margin-bottom: 4px;">
                                📋 كشف الموجود الصباحي وتحديد تمام المرتب ليوم: <b>{roll_date_str}</b>
                            </div>
                            <div style="font-size: 13.5px; color: #15803D;">
                                ضع إشارة أمام حالة كل فرد من مرتب المفرزة (<b>موجود ✅</b> أو <b>مجاز 🏖️</b> أو <b>مراجعة مرضية 🏥</b>)، ثم اضغط على حفظ الموجود للاعتماد النهائي.
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # أزرار الإجراء السريع
                        act_col1, act_col2 = st.columns([2, 2])
                        with act_col1:
                            preset_all_present = st.button("⚡ تحديد كافة المرتب (موجود ✅)", key="btn_all_present_cmd", type="secondary", use_container_width=True)
                            if preset_all_present:
                                for _, r in tech_df.iterrows():
                                    st.session_state[f"status_cmd_{r['الرقم العسكري']}"] = "موجود"
                                st.toast("تم ضبط كافة المرتب على حالة 'موجود'", icon="✅")

                        # ترويسة الجدول التفاعلي
                        st.markdown("""
                        <div style="background: #0F172A; color: #F8FAFC; border-radius: 8px 8px 0 0; padding: 10px 16px; font-weight: 800; font-size: 13.5px; display: flex; justify-content: space-between; direction: rtl;">
                            <div style="width: 38%;">👥 بيانات الفني والرتبة والصنف</div>
                            <div style="width: 38%; text-align: center;">🎯 حالة التواجد (موجود / مجاز / مراجعة مرضية)</div>
                            <div style="width: 24%; text-align: right;">📝 الملاحظات والسبب</div>
                        </div>
                        """, unsafe_allow_html=True)

                        with st.form(key=f"cmd_roll_call_form_{det_id}_{roll_date_str}"):
                            entries_to_save = []
                            for idx, (_, r) in enumerate(tech_df.iterrows(), 1):
                                m_id = str(r["الرقم العسكري"])
                                rank = str(r["الرتبة"])
                                name = str(r["الاسم الرباعي"])
                                spec = str(r["الصنف"])
                                is_cmd = (idx == 1)

                                row_col1, row_col2, row_col3 = st.columns([4, 4, 3])
                                with row_col1:
                                    cmd_badge = "👑 " if is_cmd else ""
                                    st.markdown(f"""
                                    <div style="padding-top: 4px; line-height: 1.4;">
                                        <b style="color: #0F172A; font-size: 14px;">{idx}. {cmd_badge}{rank} / {name}</b><br>
                                        <span class="badge-mil-id">{m_id}</span> <span class="badge-specialty">{spec}</span>
                                    </div>
                                    """, unsafe_allow_html=True)

                                with row_col2:
                                    def_status = st.session_state.get(f"status_cmd_{m_id}", "موجود")
                                    status_options = ["موجود", "مجاز", "مراجعة مرضية"]
                                    status_idx = status_options.index(def_status) if def_status in status_options else 0
                                    
                                    sel_status = st.radio(
                                        f"الحالة ({m_id}):",
                                        options=status_options,
                                        index=status_idx,
                                        key=f"status_cmd_{m_id}",
                                        horizontal=True,
                                        label_visibility="collapsed"
                                    )

                                with row_col3:
                                    item_note = st.text_input(
                                        f"ملاحظة / سبب ({m_id}):",
                                        value="",
                                        key=f"note_cmd_{m_id}",
                                        placeholder="ملاحظات / سبب الغياب...",
                                        label_visibility="collapsed"
                                    )

                                entries_to_save.append({
                                    "military_id": m_id,
                                    "rank": rank,
                                    "full_name": name,
                                    "specialty": spec,
                                    "status": sel_status,
                                    "notes": item_note
                                })
                                st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px solid #E2E8F0;'>", unsafe_allow_html=True)

                            # ملاحظات عامة
                            general_notes = st.text_area(
                                "📝 ملاحظات قائد المفرزة على الموجود الصباحي (اختياري):",
                                placeholder="اكتب أي ملاحظات تتعلق بالجاهزية الفنية أو المناوبات أو النواقص...",
                                key="cmd_general_notes",
                                height=70
                            )

                            st.markdown("""
                            <div style="background: #FEF2F2; border: 1px solid #FCA5A5; border-radius: 8px; padding: 10px 14px; font-size: 13px; color: #991B1B; margin: 12px 0;">
                                ⚠️ <b>قاعدة القفل العسكرية:</b> بمجرد الضغط على حفظ واعتماد الموجود الصباحي، يتم قفل السجل نهائياً ولا يمكن لقائد المفرزة تعديله بعد ذلك.
                            </div>
                            """, unsafe_allow_html=True)

                            save_submitted = st.form_submit_button("💾 حفظ واعتماد الموجود الصباحي للمفرزة", type="primary", use_container_width=True)

                            if save_submitted:
                                with st.spinner("جاري حفظ واعتماد الموجود الصباحي..."):
                                    ok, msg = db.save_daily_roll_call(
                                        detachment_id=det_id,
                                        roll_call_date=roll_date_str,
                                        entries=entries_to_save,
                                        saved_by_rank=supervisor_rank,
                                        saved_by_name=supervisor_name,
                                        notes=general_notes,
                                        is_branch_chief=False
                                    )
                                    if ok:
                                        st.success(msg)
                                        st.toast("✅ تم حفظ الموجود الصباحي واعتماده بنجاح!", icon="🛡️")
                                        st.rerun()
                                    else:
                                        st.error(msg)

            # --- تبويب سجل الأيام السابقة للمفرزة ---
            with cmd_tab2:
                st.markdown(f"#### 🗓️ أرشيف وسجل الموجود الصباحي للأيام السابقة ({det_name})")
                st.caption("يعرض سجلات الموجود الصباحي المعتمدة للمفرزة. التعديل على الأيام السابقة مقتصر على رئيس الفرع فقط.")

                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    h_start = st.date_input("من تاريخ:", value=date.today().replace(day=1), key="cmd_h_start")
                with h_col2:
                    h_end = st.date_input("إلى تاريخ:", value=date.today(), key="cmd_h_end")

                history_df = db.get_roll_call_history_df(detachment_id=det_id, start_date=h_start, end_date=h_end)

                if not history_df.empty:
                    display_cols = ["رقم السجل", "التاريخ", "القوة الإجمالية", "الموجود", "المجاز", "مراجعة مرضية", "نسبة الجاهزية %", "القائم بالحفظ", "تاريخ ووقت الحفظ", "ملاحظات الموجود"]
                    st.markdown(styles.render_rtl_table(history_df[display_cols]), unsafe_allow_html=True)

                    # تفاصيل سجل محدد وتنزيل إكسل
                    st.markdown("##### 🔍 استعراض تفاصيل يوم محدد من الأرشيف:")
                    available_records = history_df["التاريخ"].tolist()
                    selected_hist_date = st.selectbox("اختر التاريخ لعرض كشف المرتب المفصل:", options=available_records, key="cmd_sel_hist_date")

                    if selected_hist_date:
                        hist_rc, hist_entries = db.get_daily_roll_call(det_id, selected_hist_date)
                        if hist_rc:
                            st.markdown(f"""
                            <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 12px; margin-bottom: 12px; font-size: 13px;">
                                📅 <b>تاريخ الكشف:</b> {hist_rc['roll_call_date']} &nbsp;|&nbsp; 
                                👥 <b>القوة:</b> {hist_rc['total_strength']} | 
                                🟢 <b>الموجود:</b> {hist_rc['present_count']} | 
                                🟡 <b>المجاز:</b> {hist_rc['leave_count']} | 
                                🔴 <b>مراجعة مرضية:</b> {hist_rc['sick_count']} &nbsp;|&nbsp; 
                                👤 <b>المعتمد:</b> {hist_rc['saved_by_rank']} / {hist_rc['saved_by_name']}
                            </div>
                            """, unsafe_allow_html=True)

                            h_excel = db.export_roll_call_to_excel(hist_rc, hist_entries)
                            st.download_button(
                                label=f"📥 تنزيل كشف ({selected_hist_date}) بصيغة Excel",
                                data=h_excel,
                                file_name=f"موجود_{det_name}_{selected_hist_date}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"dl_hist_{det_id}_{selected_hist_date}",
                                use_container_width=True
                            )
                else:
                    st.info(f"ℹ️ لا توجد سجلات موجود صباحي محفوظة لمفرزة ({det_name}) في الفترة المحددة.")

    # --------------------------------------------------------------------------
    # ب. واجهة رئيس الفرع (Branch Chief View - Full Authority)
    # --------------------------------------------------------------------------
    else:
        all_detachments_list = db.get_detachments_list()
        bc_tab1, bc_tab2, bc_tab3 = st.tabs([
            "📊 الموقف العام اليومي لكافة المفارز",
            "📝 استعراض / تعديل كشف مفرزة محددة",
            "🗓️ الأرشيف الشامل والبحث المتقدم"
        ])

        # --- تبويب 1: الموقف العام لكافة المفارز ---
        with bc_tab1:
            col_b1, col_b2 = st.columns([1, 2])
            with col_b1:
                bc_selected_date = st.date_input(
                    "📅 اختيار تاريخ الموقف العام:",
                    value=date.today(),
                    key="bc_global_date"
                )
            with col_b2:
                st.markdown("""<div style="background: rgba(2, 132, 199, 0.08); border: 1px solid #BAE6FD; border-radius: 8px; padding: 10px 16px; margin-top: 24px; font-size: 13.5px; color: #0369A1;">👑 <b>لوحة تحكم رئيس الفرع:</b> متابعة لحظية لحالة تسليم الموجود الصباحي وجاهزية كافة المفارز بالمستشفيات العسكرية.</div>""", unsafe_allow_html=True)

            bc_date_str = str(bc_selected_date)
            consol_data = db.get_consolidated_roll_call_summary(bc_date_str)

            # بطاقات الموقف العام
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(styles.render_metric_card("إجمالي المفارز", f"{consol_data['total_detachments']} مفرزة", "المفارز الميدانية", "default"), unsafe_allow_html=True)
            with c2:
                sub_class = "default" if consol_data['submitted_detachments'] == consol_data['total_detachments'] else "info"
                st.markdown(styles.render_metric_card("مفارز سلّمت الموجود", f"{consol_data['submitted_detachments']} مفرزة", f"معلقة: {consol_data['pending_detachments']}", sub_class), unsafe_allow_html=True)
            with c3:
                st.markdown(styles.render_metric_card("القوة البشرية الإجمالية", f"{consol_data['total_strength']} فني", f"الموجود: {consol_data['total_present']} فني", "info"), unsafe_allow_html=True)
            with c4:
                read_class = "info" if consol_data['overall_readiness'] >= 75 else ("warning" if consol_data['overall_readiness'] >= 50 else "alert")
                st.markdown(styles.render_metric_card("نسبة الجاهزية الكلية", f"{consol_data['overall_readiness']}%", f"مجاز: {consol_data['total_leave']} | مرضي: {consol_data['total_sick']}", read_class), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # جدول الموقف العام لكافة المفارز
            st.markdown(f"#### 📋 كشف جاهزية وتسليم المفارز لتاريخ ({bc_date_str}):")
            
            table_rows = []
            for idx, item in enumerate(consol_data["summary_list"], 1):
                if item["is_submitted"]:
                    badge_html = '<span class="badge-present">✅ تم التسليم والاعتماد</span>'
                else:
                    badge_html = '<span class="badge-sick">⏳ قيد الانتظار (معلق)</span>'

                table_rows.append(f'<tr><td style="text-align: center; font-weight: 700;">{idx}</td><td style="font-weight: 800; color: #0F172A;">{item["hospital_name"]}</td><td><span class="badge-rank">{item["governorate"]}</span></td><td>{item["supervisor"]}</td><td style="text-align: center;">{badge_html}</td><td style="text-align: center; font-weight: 700;">{item["total_strength"]}</td><td style="text-align: center; color: #166534; font-weight: 800;">{item["present_count"]}</td><td style="text-align: center; color: #92400E; font-weight: 700;">{item["leave_count"]}</td><td style="text-align: center; color: #991B1B; font-weight: 700;">{item["sick_count"]}</td><td style="text-align: center; font-weight: 800; color: #0284C7;">{item["readiness_pct"]}%</td><td style="font-size: 12px; color: #64748B;">{item["saved_by"]}</td></tr>')

            consol_table_html = f'<div class="rtl-table-wrapper"><table class="rtl-table" dir="rtl"><thead><tr><th style="text-align: center; width: 40px;">م</th><th>المستشفى العسكري / المفرزة</th><th>المحافظة</th><th>قائد المفرزة</th><th style="text-align: center;">حالة التسليم</th><th style="text-align: center;">القوة</th><th style="text-align: center;">الموجود</th><th style="text-align: center;">المجاز</th><th style="text-align: center;">مرضية</th><th style="text-align: center;">الجاهزية %</th><th>المعتمد</th></tr></thead><tbody>{"".join(table_rows)}</tbody></table></div>'
            st.markdown(consol_table_html, unsafe_allow_html=True)

            # تصدير تقرير الموقف العام لليوم بالكامل
            summary_df = pd.DataFrame(consol_data["summary_list"])
            if not summary_df.empty:
                rename_map = {
                    "hospital_name": "المستشفى / المفرزة",
                    "governorate": "المحافظة",
                    "supervisor": "قائد المفرزة",
                    "contact_phone": "هاتف التواصل",
                    "status_badge": "حالة التسليم",
                    "total_strength": "القوة الإجمالية",
                    "present_count": "الموجود الفعلي",
                    "leave_count": "المجاز",
                    "sick_count": "مراجعة مرضية",
                    "readiness_pct": "نسبة الجاهزية %",
                    "saved_by": "القائم بالاعتماد",
                    "saved_at": "تاريخ ووقت الحفظ",
                    "notes": "الملاحظات"
                }
                export_cols = [c for c in rename_map.keys() if c in summary_df.columns]
                out_df = summary_df[export_cols].rename(columns=rename_map)

                all_day_excel = export_to_excel(out_df, sheet_name=f"موقف_{bc_date_str}")
                st.download_button(
                    label=f"📥 تصدير تقرير الموقف العام الشامل ليوم ({bc_date_str}) إلى Excel",
                    data=all_day_excel,
                    file_name=f"الموقف_العام_للمفارز_{bc_date_str}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_bc_consol_{bc_date_str}",
                    use_container_width=True
                )

        # --- تبويب 2: استعراض وتعديل كشف مفرزة محددة (صلاحية رئيس الفرع الحصرية) ---
        with bc_tab2:
            st.markdown("#### ✏️ فحص وتعديل كشف الموجود الصباحي لمفرزة (صلاحية رئيس الفرع)")
            st.info("💡 **تنويه الصلاحية:** كرئيس فرع، يمكنك استعراض أو تعديل أو تصحيح كشف الموجود الصباحي لأي مفرزة وفي أي تاريخ سابق وحفظ التعديلات رسمياً.")

            col_bc_det, col_bc_dt = st.columns([2, 1])
            with col_bc_det:
                if all_detachments_list:
                    bc_det_options = {f"{d['hospital_name']} ({d['governorate']})": d['id'] for d in all_detachments_list}
                    bc_selected_det_label = st.selectbox("🏢 اختر المفرزة / المستشفى المراد مراجعته أو تعديله:", options=list(bc_det_options.keys()), key="bc_edit_det_sel")
                    target_det_id = bc_det_options[bc_selected_det_label]
                    target_det = db.get_detachment_by_id(target_det_id)
                else:
                    st.warning("لا توجد مفارز مسجلة.")
                    target_det_id = None
                    target_det = None

            with col_bc_dt:
                target_date = st.date_input("📅 تاريخ الكشف المراد مراجعته:", value=date.today(), key="bc_edit_date_sel")

            if target_det and target_date:
                t_date_str = str(target_date)
                t_rc, t_entries = db.get_daily_roll_call(target_det_id, t_date_str)

                # إذا كان السجل محفوظاً:
                if t_rc:
                    st.markdown(f"""
                    <div class="rollcall-banner">
                        <div>
                            <div style="font-size: 16px; font-weight: 800; color: #38BDF8;">
                                🛡️ كشف مفرزة {target_det['hospital_name']} لتاريخ {t_date_str}
                            </div>
                            <div style="font-size: 13px; color: #CBD5E1; margin-top: 4px;">
                                👤 <b>المعتمد الأصلي:</b> {t_rc['saved_by_rank']} / {t_rc['saved_by_name']} | 
                                ⏰ <b>وقت الحفظ:</b> {t_rc['saved_at']} | 
                                🟢 <b>موجود:</b> {t_rc['present_count']} | 
                                🟡 <b>مجاز:</b> {t_rc['leave_count']} | 
                                🔴 <b>مرضي:</b> {t_rc['sick_count']}
                            </div>
                        </div>
                        <div>
                            <span class="badge-locked">🔒 محفوظ في السجلات</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("""
                    <div style="background: #0F172A; color: #F8FAFC; border-radius: 8px 8px 0 0; padding: 10px 16px; font-weight: 800; font-size: 13.5px; display: flex; justify-content: space-between; direction: rtl;">
                        <div style="width: 38%;">👥 بيانات الفني والرتبة والصنف</div>
                        <div style="width: 38%; text-align: center;">🎯 حالة التواجد (موجود / مجاز / مراجعة مرضية)</div>
                        <div style="width: 24%; text-align: right;">📝 الملاحظات والسبب</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.form(key=f"bc_edit_form_{target_det_id}_{t_date_str}"):
                        edited_entries = []
                        for idx, e in enumerate(t_entries, 1):
                            m_id = e["military_id"]
                            rank = e["rank"]
                            name = e["full_name"]
                            spec = e.get("specialty", "")
                            cur_status = e.get("status", "موجود")
                            cur_note = e.get("notes", "")

                            ecol1, ecol2, ecol3 = st.columns([4, 4, 3])
                            with ecol1:
                                st.markdown(f"""
                                <div style="padding-top: 4px; line-height: 1.4;">
                                    <b style="color: #0F172A; font-size: 14px;">{idx}. {rank} / {name}</b><br>
                                    <span class="badge-mil-id">{m_id}</span> <span class="badge-specialty">{spec}</span>
                                </div>
                                """, unsafe_allow_html=True)

                            with ecol2:
                                s_opts = ["موجود", "مجاز", "مراجعة مرضية"]
                                s_idx = s_opts.index(cur_status) if cur_status in s_opts else 0
                                new_st = st.radio(
                                    f"حالة {m_id}:",
                                    options=s_opts,
                                    index=s_idx,
                                    key=f"bc_st_{m_id}_{t_date_str}",
                                    horizontal=True,
                                    label_visibility="collapsed"
                                )

                            with ecol3:
                                new_nt = st.text_input(
                                    f"ملاحظة {m_id}:",
                                    value=cur_note or "",
                                    key=f"bc_nt_{m_id}_{t_date_str}",
                                    placeholder="ملاحظات / سبب...",
                                    label_visibility="collapsed"
                                )

                            edited_entries.append({
                                "military_id": m_id,
                                "rank": rank,
                                "full_name": name,
                                "specialty": spec,
                                "status": new_st,
                                "notes": new_nt
                            })
                            st.markdown("<hr style='margin: 4px 0; border: none; border-top: 1px dashed #E2E8F0;'>", unsafe_allow_html=True)

                        bc_notes_val = st.text_area(
                            "📝 ملاحظات رئيس الفرع على هذا الكشف / سبب التعديل:",
                            value=t_rc.get("notes") or "",
                            key=f"bc_notes_area_{target_det_id}_{t_date_str}"
                        )

                        b_save_col, b_del_col = st.columns([2, 1])
                        with b_save_col:
                            save_mod_btn = st.form_submit_button("💾 حفظ وتأكيد التعديلات الاستثنائية (رئيس الفرع)", type="primary", use_container_width=True)
                            if save_mod_btn:
                                with st.spinner("جاري حفظ التعديل..."):
                                    ok, msg = db.update_or_unlock_roll_call(
                                        roll_call_id=t_rc["id"],
                                        entries=edited_entries,
                                        notes=bc_notes_val,
                                        modified_by_rank="رئيس الفرع",
                                        modified_by_name="تعديل قيادي معتمد"
                                    )
                                    if ok:
                                        st.success(msg)
                                        st.toast("✅ تم تحديث كشف الموجود الصباحي بنجاح!", icon="👑")
                                        st.rerun()
                                    else:
                                        st.error(msg)

                    # خيار حذف السجل لإعادة فتحه
                    with st.expander("⚠️ خيارات إدارية متقدمة (إلغاء قفل السجل بالكامل)"):
                        st.warning("سيؤدي حذف هذا السجل إلى إتاحته مجدداً لقائد المفرزة لإدخاله من جديد كأنه لم يُسجَّل.")
                        if st.button("🗑️ حذف السجل وإعادة فتحه للإدخال من قبل قائد المفرزة", key=f"del_rc_btn_{t_rc['id']}", type="secondary"):
                            ok, msg = db.delete_daily_roll_call(t_rc["id"])
                            if ok:
                                st.success(msg)
                                st.toast("تم حذف السجل وإعادة فتحه.", icon="🔄")
                                st.rerun()
                            else:
                                st.error(msg)

                # إذا لم يكن مسجلاً بعد في هذا التاريخ:
                else:
                    st.warning(f"⚠️ لم يتم إدخال الموجود الصباحي لمفرزة ({target_det['hospital_name']}) في تاريخ ({t_date_str}) بعد.")
                    st.info("💡 يمكنك كرئيس فرع إدخال واعتماد الموجود الصباحي نيابة عن المفرزة إذا لزم الأمر:")

                    tech_df = db.get_technicians_by_detachment_df(target_det_id, apply_custom_columns=False)
                    if not tech_df.empty:
                        with st.form(key=f"bc_new_form_{target_det_id}_{t_date_str}"):
                            new_entries_bc = []
                            for idx, (_, r) in enumerate(tech_df.iterrows(), 1):
                                m_id = str(r["الرقم العسكري"])
                                rank = str(r["الرتبة"])
                                name = str(r["الاسم الرباعي"])
                                spec = str(r["الصنف"])

                                ecol1, ecol2, ecol3 = st.columns([3, 3, 2])
                                with ecol1:
                                    st.markdown(f"<b>{idx}. {rank} / {name}</b><br><span class='badge-mil-id'>{m_id}</span> | <span class='badge-specialty'>{spec}</span>", unsafe_allow_html=True)
                                with ecol2:
                                    nst = st.radio(f"حالة {m_id}:", options=["موجود", "مجاز", "مراجعة مرضية"], index=0, key=f"bc_new_st_{m_id}", horizontal=True, label_visibility="collapsed")
                                with ecol3:
                                    nnt = st.text_input(f"ملاحظة {m_id}:", value="", key=f"bc_new_nt_{m_id}", placeholder="ملاحظات...", label_visibility="collapsed")

                                new_entries_bc.append({
                                    "military_id": m_id,
                                    "rank": rank,
                                    "full_name": name,
                                    "specialty": spec,
                                    "status": nst,
                                    "notes": nnt
                                })

                            bc_notes_new = st.text_area("ملاحظات رئيس الفرع:", key=f"bc_notes_new_{target_det_id}")
                            if st.form_submit_button("💾 حفظ واعتماد كشف الموجود (بواسطة رئيس الفرع)", type="primary", use_container_width=True):
                                ok, msg = db.save_daily_roll_call(
                                    detachment_id=target_det_id,
                                    roll_call_date=t_date_str,
                                    entries=new_entries_bc,
                                    saved_by_rank="رئيس الفرع",
                                    saved_by_name="إدخال معتمد من الإدارة",
                                    notes=bc_notes_new,
                                    is_branch_chief=True
                                )
                                if ok:
                                    st.success(msg)
                                    st.toast("✅ تم حفظ الموجود بنجاح!", icon="👑")
                                    st.rerun()
                                else:
                                    st.error(msg)
                    else:
                        st.warning("لا يوجد فنيين مسجلين على مرتب هذه المفرزة.")

        # --- تبويب 3: الأرشيف الشامل والبحث المتقدم ---
        with bc_tab3:
            st.markdown("#### 🗓️ الأرشيف التاريخي الشامل للموجود الصباحي")
            st.caption("بحث وفلترة في كافة سجلات الموجود الصباحي السابقة لكافة المفارز بالمملكة وتصديرها:")

            fcol1, fcol2, fcol3 = st.columns(3)
            with fcol1:
                all_hosp_filter = ["(كافة المفارز)"] + [f"{d['hospital_name']} ({d['governorate']})" for d in all_detachments_list]
                sel_hosp_filter = st.selectbox("تصفية حسب المفرزة:", options=all_hosp_filter, key="bc_arch_hosp")
                filter_det_id = None
                if sel_hosp_filter != "(كافة المفارز)":
                    filter_det_id = next(d['id'] for d in all_detachments_list if f"{d['hospital_name']} ({d['governorate']})" == sel_hosp_filter)

            with fcol2:
                arch_start = st.date_input("من تاريخ:", value=date.today().replace(day=1), key="bc_arch_start")
            with fcol3:
                arch_end = st.date_input("إلى تاريخ:", value=date.today(), key="bc_arch_end")

            all_history_df = db.get_roll_call_history_df(detachment_id=filter_det_id, start_date=arch_start, end_date=arch_end)

            if not all_history_df.empty:
                disp_cols = ["رقم السجل", "التاريخ", "المستشفى / المفرزة", "المحافظة", "القوة الإجمالية", "الموجود", "المجاز", "مراجعة مرضية", "نسبة الجاهزية %", "القائم بالحفظ", "تاريخ ووقت الحفظ", "ملاحظات الموجود"]
                st.markdown(styles.render_rtl_table(all_history_df[disp_cols]), unsafe_allow_html=True)

                # تصدير الأرشيف المفلتر
                arch_excel = export_to_excel(all_history_df[disp_cols], sheet_name="أرشيف_الموجود_الصباحي")
                st.download_button(
                    label="📥 تصدير السجلات المفلترة إلى Excel",
                    data=arch_excel,
                    file_name=f"أرشيف_الموجود_الصباحي_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_bc_arch_all",
                    use_container_width=True
                )
            else:
                st.info("ℹ️ لا توجد سجلات موجود صباحي تطابق معايير البحث المحددة.")


# ==============================================================================
# 3. كشف المفارز والمستشفيات (Detachments View)
# ==============================================================================
elif menu_choice in ["🏥 كشف المفارز والمستشفيات", "🏥 كشف مفرزتي وبيانات المرتب"]:
    if is_branch_chief:
        styles.render_page_header(
            "كشف وجاهزية المفارز والمستشفيات",
            "عرض تفاصيل المفرزة، تحديث وحفظ النواقص والاحتياجات الفورية، وإدارة كشف مرتبات المستشفى",
            "🏥"
        )
    else:
        styles.render_page_header(
            f"كشف وبيانات مرتبات {current_user.get('hospital_name', 'مفرزتي')}",
            "عرض تفاصيل المفرزة، تحديث وحفظ النواقص والاحتياجات الفورية، وكشف مرتبات الفنيين التابعين للمفرزة",
            "🏥"
        )

    detachments = db.get_detachments_list()

    if not detachments:
        st.warning("⚠️ لا توجد مفارز مسجلة في قاعدة البيانات حالياً.")
    else:
        if is_branch_chief:
            # قائمة خيارات المستشفيات لرئيس الفرع
            detachment_options = {
                f"{d['hospital_name']} ({d['governorate']}) - [{d['technicians_count']} فني]": d['id']
                for d in detachments
            }

            selected_label = st.selectbox(
                "🏢 اختر المستشفى العسكري / المفرزة لعرض التفاصيل:",
                options=list(detachment_options.keys())
            )

            selected_id = detachment_options[selected_label]
        else:
            # لقائد المفرزة: مفرزته المسندة حصراً
            selected_id = active_detachment_id
            if not selected_id:
                st.error("⚠️ لم يتم تحديد المفرزة المسندة لحسابك. يرجى مراجعة رئيس الفرع.")
                st.stop()

        selected_detachment = db.get_detachment_by_id(selected_id)

        if selected_detachment:
            # 2.1 بطاقة بيانات المفرزة
            st.markdown(f"""
            <div class="detachment-info-card">
                <div class="detachment-info-title">🏥 {selected_detachment['hospital_name']}</div>
                <div>
                    <span class="detachment-pill">📍 المحافظة: <b>{selected_detachment['governorate']}</b></span>
                    <span class="detachment-pill" style="background: rgba(245, 158, 11, 0.2); border: 1px solid #F59E0B; color: #FEF3C7;">👑 قائد المفرزة: <b style="color: #FDE68A;">{selected_detachment['supervisor_rank']} / {selected_detachment['supervisor_name']}</b></span>
                    <span class="detachment-pill">📞 رقم التواصل: <b>{selected_detachment['contact_phone'] or 'غير محدد'}</b></span>
                </div>
                {f'<div style="margin-top: 12px; color: #94A3B8; font-size: 13px;">📝 <b>ملاحظات المفرزة:</b> {selected_detachment["notes"]}</div>' if selected_detachment["notes"] else ''}
            </div>
            """, unsafe_allow_html=True)

            # 2.2 محرر فوري لحفظ وتحديث "النواقص والاحتياجات البشرية"
            st.markdown("#### 📝 النواقص والاحتياجات البشرية للمفرزة")
            with st.container():
                shortages_input = st.text_area(
                    "بيان النواقص والاحتياجات الواردة من قائد المفرزة (تحديث فوري):",
                    value=selected_detachment['staffing_shortages'] or '',
                    placeholder="مثال: بحاجة إلى عدد (1) فني تكييف للوردية المسائية، ونقص فني كهرباء قوى...",
                    key=f"shortages_{selected_id}",
                    height=100
                )

                btn_col1, btn_col2 = st.columns([1, 3])
                with btn_col1:
                    save_shortage_btn_text = settings.get("btn_save_shortages_label", "💾 حفظ وتحديث النواقص")
                    if st.button(save_shortage_btn_text, key=f"save_btn_{selected_id}", type="primary", use_container_width=True):
                        db.update_detachment_shortages(selected_id, shortages_input)
                        st.toast("✅ تم حفظ وتحديث النواقص بنجاح!", icon="🛡️")
                        st.rerun()

            st.markdown("---")

            # 2.3 جدول تفصيلي بكافة الفنيين التابعين للمفرزة
            st.markdown(f"#### 👥 كشف مرتبات الفنيين التابعين للمفرزة ({selected_detachment['hospital_name']})")
            tech_df = db.get_technicians_by_detachment_df(selected_id, apply_custom_columns=True)

            if not tech_df.empty:
                st.markdown(styles.render_rtl_table(tech_df, highlight_commander=True), unsafe_allow_html=True)
            else:
                st.warning("⚠️ لا يوجد فنيين مسجلين على مرتب هذه المفرزة حالياً. يمكنك استيراد كشف الفنيين من ملف Excel أدناه أو إضافة فنيين من شاشة إدارة المرتبات.")

            st.markdown("---")

            # شريط الأزرار الملونة للعمليات السريعة بجانب بعضها
            st.markdown("##### ⚡ العمليات والإجراءات السريعة للمفرزة:")

            act_col1, act_col2, act_col3, act_col4, act_col5 = st.columns(5)

            curr_action_key = f"active_det_action_{selected_id}"
            curr_action = st.session_state.get(curr_action_key, None)

            with act_col1:
                if not tech_df.empty:
                    excel_data = export_to_excel(tech_df, sheet_name=f"كشف {selected_detachment['governorate']}")
                    file_name = f"كشف_مرتبات_{selected_detachment['hospital_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    export_btn_label = settings.get("btn_export_label", "📊 تصدير الكشف Excel")
                    st.download_button(
                        label=export_btn_label,
                        data=excel_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_det_{selected_id}",
                        use_container_width=True
                    )
                else:
                    st.button("📊 تصدير الكشف Excel", disabled=True, key=f"dl_det_dis_{selected_id}", use_container_width=True)

            with act_col2:
                template_bytes = db.generate_technicians_template()
                st.download_button(
                    label="📄 تحميل قالب Excel",
                    data=template_bytes,
                    file_name="قالب_استيراد_فنيي_المفرزة.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_tpl_{selected_id}",
                    use_container_width=True
                )

            with act_col3:
                btn_add_text = "➕ إضافة فني جديد" if curr_action != "add" else "✖️ إغلاق الإضافة"
                if st.button(btn_add_text, key=f"btn_act_add_{selected_id}", use_container_width=True):
                    st.session_state[curr_action_key] = "add" if curr_action != "add" else None
                    st.rerun()

            with act_col4:
                btn_edit_text = "✏️ تعديل بيانات فني" if curr_action != "edit" else "✖️ إغلاق التعديل"
                if st.button(btn_edit_text, key=f"btn_act_edit_{selected_id}", use_container_width=True):
                    st.session_state[curr_action_key] = "edit" if curr_action != "edit" else None
                    st.rerun()

            with act_col5:
                btn_import_text = "📥 استيراد كشف Excel" if curr_action != "import" else "✖️ إغلاق الاستيراد"
                if st.button(btn_import_text, key=f"btn_act_import_{selected_id}", use_container_width=True):
                    st.session_state[curr_action_key] = "import" if curr_action != "import" else None
                    st.rerun()

            # لوحة العمليات التفاعلية النشطة
            if curr_action == "add":
                st.markdown(f"""
                <div class="action-panel-container add">
                    <div class="action-panel-header">
                        <div class="action-panel-title">➕ نموذج تسجيل وإلحاق فني جديد بمفرزة ({selected_detachment['hospital_name']})</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                with st.form(key=f"form_add_tech_det_{selected_id}", clear_on_submit=True):
                    af_c1, af_c2 = st.columns(2)
                    with af_c1:
                        new_m_id = st.text_input("الرقم العسكري *:", placeholder="أدخل الرقم العسكري...")
                        new_m_name = st.text_input("الاسم الرباعي الكامل *:", placeholder="أدخل الاسم الرباعي...")
                        new_m_rank = st.selectbox("الرتبة العسكرية *:", options=MILITARY_RANKS, index=len(MILITARY_RANKS)-3, key=f"add_rnk_{selected_id}")
                        new_m_spec = st.selectbox("الصنف الفني *:", options=MILITARY_CATEGORIES, key=f"add_spc_{selected_id}")
                    with af_c2:
                        new_m_job = st.text_input("المهنة الحالية بالمفرزة:", placeholder="مثال: فني تكييف / صيانة عامة...", key=f"add_job_{selected_id}")
                        new_m_res = st.selectbox("مكان السكن:", options=GOVERNORATES, key=f"add_res_{selected_id}")
                        new_m_ph = st.text_input("رقم الهاتف:", placeholder="07XXXXXXXX", key=f"add_ph_{selected_id}")
                        new_m_jd = st.date_input("تاريخ الالتحاق بالمفرزة:", value=date.today(), key=f"add_jd_{selected_id}")
                        
                    new_m_notes = st.text_area("الملاحظات والتقييم الأولي:", placeholder="أدخل أي ملاحظات أو تقييم فني...", key=f"add_nt_{selected_id}")
                    
                    sub_c1, sub_c2 = st.columns([2, 1])
                    with sub_c1:
                        add_tech_btn = st.form_submit_button("💾 حفظ وتسجيل الفني بالمفرزة", type="primary", use_container_width=True)
                    with sub_c2:
                        pass

                    if add_tech_btn:
                        if not new_m_id.strip() or not new_m_name.strip():
                            st.error("يرجى إدخال الرقم العسكري والاسم الرباعي (*).")
                        else:
                            ok_a, err_a = db.add_technician(
                                new_m_id.strip(),
                                new_m_rank,
                                new_m_name.strip(),
                                new_m_spec,
                                new_m_job.strip(),
                                new_m_res,
                                selected_id,
                                str(new_m_jd),
                                new_m_ph.strip(),
                                new_m_notes.strip()
                            )
                            if ok_a:
                                st.toast("✅ تم تسجيل الفني بنجاح!", icon="🎉")
                                st.success("✅ تم تسجيل وإلحاق الفني بالمفرزة بنجاح!")
                                st.session_state[curr_action_key] = None
                                st.rerun()
                            else:
                                st.error(f"❌ {err_a}")

            elif curr_action == "edit":
                st.markdown(f"""
                <div class="action-panel-container edit">
                    <div class="action-panel-header">
                        <div class="action-panel-title">✏️ تعديل بيانات فني وإضافة الملاحظات والتقييم لمفرزة ({selected_detachment['hospital_name']})</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                if not tech_df.empty:
                    tech_list = db.get_all_technicians_df(apply_custom_columns=False)
                    det_techs = tech_list[tech_list["detachment_id"] == selected_id]
                    
                    if not det_techs.empty:
                        tech_select_map = {
                            f"{t['الرتبة']} / {t['الاسم الرباعي']} (الرقم: {t['الرقم العسكري']})": t['الرقم العسكري']
                            for _, t in det_techs.iterrows()
                        }
                        selected_t_label = st.selectbox("اختر الفني للتعديل أو إضافة الملاحظات والتقييم:", options=list(tech_select_map.keys()), key=f"sel_edit_tech_{selected_id}")
                        target_mil_id = tech_select_map[selected_t_label]
                        target_tech = db.get_technician_by_id(target_mil_id)
                        
                        if target_tech:
                            with st.form(key=f"form_edit_tech_{selected_id}_{target_mil_id}"):
                                ef_c1, ef_c2 = st.columns(2)
                                with ef_c1:
                                    st.text_input("الرقم العسكري (ثابت):", value=target_tech['military_id'], disabled=True)
                                    t_name = st.text_input("الاسم الرباعي الكامل *:", value=target_tech['full_name'])
                                    t_rank = st.selectbox("الرتبة العسكرية *:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(target_tech['rank']) if target_tech['rank'] in MILITARY_RANKS else 0)
                                    t_spec = st.selectbox("الصنف / التخصص الفني *:", options=MILITARY_CATEGORIES, index=MILITARY_CATEGORIES.index(target_tech['specialty']) if target_tech['specialty'] in MILITARY_CATEGORIES else 0)
                                with ef_c2:
                                    t_job = st.text_input("المهنة / الواجب الحالي بالمفرزة:", value=target_tech['current_job'] or '')
                                    t_res = st.selectbox("مكان السكن:", options=GOVERNORATES, index=GOVERNORATES.index(target_tech['residence']) if target_tech['residence'] in GOVERNORATES else 0)
                                    t_phone = st.text_input("رقم هاتف الفني للتواصل:", value=target_tech['phone_number'] or '')
                                    try:
                                        parsed_jdate = datetime.strptime(target_tech['join_date'], "%Y-%m-%d").date() if target_tech['join_date'] else date.today()
                                    except Exception:
                                        parsed_jdate = date.today()
                                    t_jdate = st.date_input("تاريخ الالتحاق بالمفرزة:", value=parsed_jdate)
                                    
                                t_notes = st.text_area("📋 الملاحظات والتقييم الفني وسلوك الفني:", value=target_tech['evaluation_and_notes'] or '', placeholder="أدخل تقييم قائد المفرزة، مستوى الانضباط، الكفاءة الفنية، أو أي ملاحظات هامة...")
                                
                                save_tech_btn = st.form_submit_button("💾 حفظ تعديلات الفني والملاحظات والتقييم", type="primary", use_container_width=True)
                                if save_tech_btn:
                                    ok_u, err_u = db.update_technician(
                                        target_mil_id,
                                        t_rank,
                                        t_name.strip(),
                                        t_spec,
                                        t_job.strip(),
                                        t_res,
                                        selected_id,
                                        str(t_jdate),
                                        t_phone.strip(),
                                        t_notes.strip()
                                    )
                                    if ok_u:
                                        st.toast("✅ تم حفظ وتحديث بيانات الفني وملاحظاته بنجاح!", icon="💾")
                                        st.success("✅ تم تحديث بيانات الفني بنجاح!")
                                        st.session_state[curr_action_key] = None
                                        st.rerun()
                                    else:
                                        st.error(f"❌ تعذر التحديث: {err_u}")
                else:
                    st.warning("⚠️ لا يوجد فنيين مسجلين بهذه المفرزة لتعديلهم.")

            elif curr_action == "import":
                st.markdown(f"""
                <div class="action-panel-container import">
                    <div class="action-panel-header">
                        <div class="action-panel-title">📥 استيراد كشف فنيين من ملف Excel لمفرزة ({selected_detachment['hospital_name']})</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                <div style="font-size: 13.5px; color: #475569; margin-bottom: 12px; direction: rtl; text-align: right;">
                    💡 ارفع ملف Excel يحتوي على كشف المرتبات، وسيتم إلحاقهم بالمفرزة مباشرة.<br>
                    الأعمدة المدعومة: <b>الرقم العسكري *، الرتبة، الاسم الرباعي *، الصنف، المهنة الحالية، مكان السكن، تاريخ الالتحاق، رقم الهاتف، الملاحظات</b>.
                </div>
                """, unsafe_allow_html=True)

                up_file = st.file_uploader(
                    "اختر ملف Excel (.xlsx أو .xls):",
                    type=["xlsx", "xls"],
                    key=f"uploader_det_{selected_id}"
                )

                update_existing_techs = st.checkbox(
                    "تحديث بيانات الفني ونقله لهذه المفرزة إذا كان رقمه العسكري مسجلاً مسبقاً",
                    value=True,
                    key=f"chk_upd_{selected_id}"
                )

                if up_file is not None:
                    try:
                        preview_df = pd.read_excel(up_file)
                        excel_cols = list(preview_df.columns)
                        detected_map = db.detect_column_mapping(excel_cols)

                        st.markdown("##### 🎯 مطابقة وتأكيد أعمدة ملف الإكسل:")
                        st.caption("تأكد من اختيار عمود الصنف والمهنة والرتبة المطابق لملفك:")

                        mcol1, mcol2, mcol3 = st.columns(3)
                        with mcol1:
                            mil_idx = excel_cols.index(detected_map["military_id"]) if "military_id" in detected_map and detected_map["military_id"] in excel_cols else 0
                            sel_mil = st.selectbox("📌 عمود الرقم العسكري *:", options=excel_cols, index=mil_idx, key=f"map_mil_{selected_id}")

                            name_idx = excel_cols.index(detected_map["full_name"]) if "full_name" in detected_map and detected_map["full_name"] in excel_cols else min(1, len(excel_cols)-1)
                            sel_name = st.selectbox("👤 عمود الاسم الرباعي *:", options=excel_cols, index=name_idx, key=f"map_name_{selected_id}")

                            rank_opts = ["(غير موجود)"] + excel_cols
                            rank_idx = rank_opts.index(detected_map["rank"]) if "rank" in detected_map and detected_map["rank"] in rank_opts else 0
                            sel_rank = st.selectbox("🎖️ عمود الرتبة:", options=rank_opts, index=rank_idx, key=f"map_rank_{selected_id}")

                        with mcol2:
                            spec_opts = ["(غير موجود)"] + excel_cols
                            spec_idx = spec_opts.index(detected_map["specialty"]) if "specialty" in detected_map and detected_map["specialty"] in spec_opts else (spec_opts.index(detected_map["current_job"]) if "current_job" in detected_map and detected_map["current_job"] in spec_opts else 0)
                            sel_spec = st.selectbox("🛡️ عمود الصنف *:", options=spec_opts, index=spec_idx, key=f"map_spec_{selected_id}")

                            job_opts = ["(غير موجود)"] + excel_cols
                            job_idx = job_opts.index(detected_map["current_job"]) if "current_job" in detected_map and detected_map["current_job"] in job_opts else 0
                            sel_job = st.selectbox("💼 عمود المهنة الحالية:", options=job_opts, index=job_idx, key=f"map_job_{selected_id}")

                        with mcol3:
                            res_opts = ["(غير موجود)"] + excel_cols
                            res_idx = res_opts.index(detected_map["residence"]) if "residence" in detected_map and detected_map["residence"] in res_opts else 0
                            sel_res = st.selectbox("🏠 عمود مكان السكن:", options=res_opts, index=res_idx, key=f"map_res_{selected_id}")

                            join_opts = ["(غير موجود)"] + excel_cols
                            join_idx = join_opts.index(detected_map["join_date"]) if "join_date" in detected_map and detected_map["join_date"] in join_opts else 0
                            sel_join = st.selectbox("📅 عمود تاريخ الالتحاق:", options=join_opts, index=join_idx, key=f"map_join_{selected_id}")

                            ph_opts = ["(غير موجود)"] + excel_cols
                            ph_idx = ph_opts.index(detected_map["phone_number"]) if "phone_number" in detected_map and detected_map["phone_number"] in ph_opts else 0
                            sel_ph = st.selectbox("📞 عمود رقم الهاتف:", options=ph_opts, index=ph_idx, key=f"map_ph_{selected_id}")

                        custom_mapping = {
                            "military_id": sel_mil,
                            "full_name": sel_name,
                            "rank": sel_rank if sel_rank != "(غير موجود)" else None,
                            "specialty": sel_spec if sel_spec != "(غير موجود)" else None,
                            "current_job": sel_job if sel_job != "(غير موجود)" else None,
                            "primary_category": None,
                            "residence": sel_res if sel_res != "(غير موجود)" else None,
                            "join_date": sel_join if sel_join != "(غير موجود)" else None,
                            "phone_number": sel_ph if sel_ph != "(غير موجود)" else None,
                            "evaluation_and_notes": None
                        }

                        st.markdown(f"##### 👁️ معاينة أول 10 سجلات من الملف المرفوع ({len(preview_df)} سجل):")
                        st.markdown(styles.render_rtl_table(preview_df.head(10)), unsafe_allow_html=True)

                        if st.button(f"🚀 تأكيد استيراد ({len(preview_df)}) فني إلى المفرزة", type="primary", key=f"btn_do_import_{selected_id}"):
                            with st.spinner("جاري استيراد وحفظ البيانات في قاعدة البيانات..."):
                                res = db.import_technicians_from_df(preview_df, selected_id, update_existing=update_existing_techs, custom_col_map=custom_mapping)
                                
                                if res.get("success"):
                                    st.success(f"""
                                    🎉 **تمت عملية الاستيراد بنجاح!**
                                    - إجمالي السجلات بالملف: **{res['total']}**
                                    - سجلات جديدة أُضيفت: **{res['inserted']}**
                                    - سجلات حُدثت: **{res['updated']}**
                                    - سجلات تم تخطيها: **{res['skipped']}**
                                    """)
                                    if res.get("errors"):
                                        with st.expander("⚠️ تفاصيل الملاحظات والتنبيهات أثناء الاستيراد"):
                                            for err in res["errors"]:
                                                st.write(f"• {err}")
                                    st.toast("✅ تم استيراد كشف المفرزة بنجاح!", icon="🛡️")
                                    st.session_state[curr_action_key] = None
                                    st.rerun()
                                else:
                                    st.error("❌ فشلت عملية الاستيراد:")
                                    for err in res.get("errors", []):
                                        st.write(f"• {err}")
                    except Exception as ex:
                        st.error(f"⚠️ تعذر قراءة ملف الإكسل: {str(ex)}")


# ==============================================================================
# 3. إدارة المرتبات والفنيين (Technicians Management)
# ==============================================================================
elif menu_choice == "👥 إدارة المرتبات والفنيين":
    styles.render_page_header(
        "إدارة المرتبات والقوى البشرية",
        "كشف الفنيين الشامل، البحث والفلاتر، إضافة وتعديل الفنيين، وإجراء حركات النقل الميدانية",
        "👥"
    )

    detachments = db.get_detachments_list()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 كشف الفنيين العام والبحث",
        "➕ إضافة فني جديد",
        "🔄 إجراء حركة نقل",
        "✏️ تعديل / حذف بيانات فني"
    ])

    # --------------------------------------------------------------------------
    # تبويب 1: كشف الفنيين العام والبحث المتقدم
    # --------------------------------------------------------------------------
    with tab1:
        st.markdown("#### 🔍 البحث والفلترة المتقدمة في مرتبات الفنيين")

        # جلب البيانات الشاملة مع كافة الحقول
        all_tech_df = db.get_all_technicians_df(apply_custom_columns=False)

        # استخراج قائمة المهن الحالية المسجلة في النظام
        existing_jobs = []
        if not all_tech_df.empty and "المهنة الحالية" in all_tech_df.columns:
            existing_jobs = sorted(list(set([str(j).strip() for j in all_tech_df["المهنة الحالية"].dropna() if str(j).strip() and str(j).strip() != "-"])))

        # استخراج قائمة الأصناف والمهن الحالية المسجلة في النظام فعلياً
        existing_categories = []
        if not all_tech_df.empty and "الصنف" in all_tech_df.columns:
            existing_categories = sorted(list(set([str(c).strip() for c in all_tech_df["الصنف"].dropna() if str(c).strip() and str(c).strip() != "-"])))

        existing_jobs = []
        if not all_tech_df.empty and "المهنة الحالية" in all_tech_df.columns:
            existing_jobs = sorted(list(set([str(j).strip() for j in all_tech_df["المهنة الحالية"].dropna() if str(j).strip() and str(j).strip() != "-"])))

        # نموذج الفلترة والبحث بحسب الترتيب المطلوب
        with st.form(key="technicians_filter_form"):
            # السطر الأول: الاسم / البحث العام + زر تطبيق الفلترة
            r1_col1, r1_col2 = st.columns([3, 1])
            with r1_col1:
                search_query = st.text_input("🔎 الاسم / الرقم العسكري / مكان السكن:", placeholder="اكتب الاسم أو الرقم العسكري أو السكن للبحث...")
            with r1_col2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                apply_filters = st.form_submit_button("🔍 تطبيق الفلترة والبحث", type="primary", use_container_width=True)

            # السطر الثاني: تصفية حسب المستشفى / المفرزة .. حسب الصنف .. حسب المهنة الحالية
            r2_col1, r2_col2, r2_col3 = st.columns(3)
            with r2_col1:
                hosp_options = ["الكل"] + [d['hospital_name'] for d in detachments]
                hospital_filter = st.selectbox("🏥 تصفية حسب المستشفى / المفرزة:", options=hosp_options)
            with r2_col2:
                category_filter = st.selectbox("🛡️ تصفية حسب الصنف:", options=["الكل"] + existing_categories)
            with r2_col3:
                job_options = ["الكل"] + existing_jobs
                job_filter = st.selectbox("💼 تصفية حسب المهنة الحالية:", options=job_options)

        # تطبيق الفلاتر على البيانات
        filtered_df = all_tech_df.copy()

        if search_query:
            filtered_df = filtered_df[
                filtered_df["الاسم الرباعي"].astype(str).str.contains(search_query, case=False, na=False) |
                filtered_df["الرقم العسكري"].astype(str).str.contains(search_query, case=False, na=False) |
                filtered_df["مكان السكن"].astype(str).str.contains(search_query, case=False, na=False)
            ]

        if hospital_filter != "الكل" and "المستشفى الحالي" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["المستشفى الحالي"] == hospital_filter]

        if category_filter != "الكل" and "الصنف" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["الصنف"] == category_filter]

        if job_filter != "الكل" and "المهنة الحالية" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["المهنة الحالية"] == job_filter]

        # إحصائية نتائج البحث
        st.caption(f"📊 عدد الفنيين المطابقين للبحث: **{len(filtered_df)}** من إجمالي **{len(all_tech_df)}**")

        # عرض جدول النتائج بالمعلومات المحددة
        TARGET_RESULT_COLUMNS = ["الرتبة", "الاسم الرباعي", "الصنف", "المهنة الحالية", "المستشفى الحالي", "مدة الخدمة بالمفرزة"]
        display_columns = [col for col in TARGET_RESULT_COLUMNS if col in filtered_df.columns]
        display_df = filtered_df[display_columns]
        st.markdown(styles.render_rtl_table(display_df), unsafe_allow_html=True)

        # إدارة وعرض البطاقة التعريفية الشاملة وتعديل بيانات الفني
        st.markdown("---")
        st.markdown("#### 🪪 البطاقة التعريفية وتعديل بيانات الفني")
        st.caption("اختر أي فني من الجدول أعلاه لعرض بطاقته العسكرية وتعديل بياناته:")

        if not filtered_df.empty:
            tech_options = {"(اختر اسماً لعرض بطاقته وتعديل بياناته...)": None}
            for _, row_item in filtered_df.iterrows():
                mil = str(row_item.get("الرقم العسكري", ""))
                rnk = str(row_item.get("الرتبة", ""))
                nam = str(row_item.get("الاسم الرباعي", ""))
                hsp = str(row_item.get("المستشفى الحالي", ""))
                opt_label = f"🎖️ {rnk} / {nam} (رقم عسكري: {mil}) - {hsp}"
                tech_options[opt_label] = row_item.to_dict()

            # أزرار سريعة للضغط على الأسماء مباشرة
            st.write("**🔹 أزرار سريعة للاختيار المباشر من الجدول أعلاه:**")
            num_cols = min(len(filtered_df), 4) if len(filtered_df) > 0 else 1
            btn_cols = st.columns(num_cols)
            for i, (_, row_item) in enumerate(filtered_df.head(12).iterrows()):
                c_idx = i % num_cols
                with btn_cols[c_idx]:
                    b_label = f"👤 {row_item['الرتبة']} / {row_item['الاسم الرباعي']}"
                    if st.button(b_label, key=f"quick_tech_card_{row_item['الرقم العسكري']}", use_container_width=True):
                        st.session_state["selected_card_mil_id"] = str(row_item["الرقم العسكري"])

            opt_keys = list(tech_options.keys())
            default_index = 0
            if "selected_card_mil_id" in st.session_state and st.session_state["selected_card_mil_id"]:
                for k, v in tech_options.items():
                    if v and str(v.get("الرقم العسكري")) == str(st.session_state["selected_card_mil_id"]):
                        default_index = opt_keys.index(k)
                        break

            selected_key = st.selectbox(
                "اختيار الفني:",
                options=opt_keys,
                index=default_index,
                key="tech_card_selector",
                label_visibility="collapsed"
            )

            selected_tech = tech_options.get(selected_key)
            if selected_tech:
                # عرض البطاقة العسكرية الشاملة
                st.markdown(styles.render_technician_card(selected_tech), unsafe_allow_html=True)

                # نموذج تعديل بيانات الفني المباشر
                with st.expander(f"✏️ تعديل بيانات الفني ({selected_tech['الرتبة']} / {selected_tech['الاسم الرباعي']})", expanded=True):
                    with st.form(key=f"card_modal_edit_tech_form_{selected_tech['الرقم العسكري']}"):
                        c_e1, c_e2 = st.columns(2)
                        with c_e1:
                            edit_rank = st.selectbox("الرتبة العسكرية *:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(selected_tech['الرتبة']) if selected_tech['الرتبة'] in MILITARY_RANKS else 0)
                            edit_name = st.text_input("الاسم الرباعي *:", value=selected_tech['الاسم الرباعي'])
                            st.text_input("الرقم العسكري (ثابت):", value=selected_tech['الرقم العسكري'], disabled=True)
                            cur_cat_val = selected_tech.get('الصنف') or selected_tech.get('specialty') or ''
                            edit_cat = st.text_input("الصنف (كما في الإكسل) *:", value=str(cur_cat_val))
                        with c_e2:
                            edit_job = st.text_input("المهنة الحالية بالمفرزة:", value=selected_tech.get('المهنة الحالية', '') or '')
                            det_dict = {d['hospital_name']: d['id'] for d in detachments}
                            cur_h = selected_tech.get('المستشفى الحالي', '')
                            cur_h_idx = list(det_dict.keys()).index(cur_h) if cur_h in det_dict else 0
                            edit_hosp = st.selectbox("المستشفى / المفرزة الحالية:", options=list(det_dict.keys()), index=cur_h_idx)
                            edit_res = st.text_input("مكان السكن:", value=selected_tech.get('مكان السكن', '') or '')
                            try:
                                cur_j_d = datetime.strptime(str(selected_tech.get('تاريخ الالتحاق بالمفرزة', '')), "%Y-%m-%d").date()
                            except Exception:
                                cur_j_d = date.today()
                            edit_join = st.date_input("تاريخ الالتحاق بالمفرزة:", value=cur_j_d)
                            edit_phone = st.text_input("رقم الهاتف:", value=selected_tech.get('رقم الهاتف', '') or '')

                        edit_notes = st.text_area("الملاحظات والتقييم الفني:", value=selected_tech.get('الملاحظات والتقييم الفني', '') or '')

                        btn_s, _ = st.columns([1, 2])
                        with btn_s:
                            save_btn = st.form_submit_button("💾 حفظ تعديلات الفني", type="primary", use_container_width=True)
                            if save_btn:
                                t_det_id = det_dict[edit_hosp]
                                suc, err_msg = db.update_technician(
                                    selected_tech['الرقم العسكري'],
                                    edit_rank,
                                    edit_name.strip(),
                                    edit_cat.strip(),
                                    edit_job.strip(),
                                    edit_res.strip(),
                                    t_det_id,
                                    edit_join.isoformat(),
                                    edit_phone.strip(),
                                    edit_notes.strip()
                                )
                                if suc:
                                    st.toast("✅ تم حفظ وتحديث بيانات الفني بنجاح!", icon="💾")
                                    st.rerun()
                                else:
                                    st.error(f"❌ تعذر الحفظ: {err_msg}")

        # زر تصدير النتائج إلى Excel
        if not display_df.empty:
            excel_all = export_to_excel(display_df, sheet_name="كشف الفنيين")
            export_btn_label = settings.get("btn_export_label", "📥 تصدير الكشف إلى Excel")
            st.download_button(
                label=f"{export_btn_label} (النتائج الحالية)",
                data=excel_all,
                file_name=f"كشف_الفنيين_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_filtered_techs"
            )

    # --------------------------------------------------------------------------
    # تبويب 2: إضافة فني جديد
    # --------------------------------------------------------------------------
    with tab2:
        st.markdown("#### ➕ نموذج تسجيل فني جديد على مرتبات المفارز")
        with st.form(key="add_tech_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                tech_mil_id = st.text_input("الرقم العسكري (مفتاح فريد) *:", placeholder="مثال: 987654")
                tech_rank = st.selectbox("الرتبة العسكرية *:", options=MILITARY_RANKS, index=2)
                tech_name = st.text_input("الاسم الرباعي *:", placeholder="مثال: أحمد محمد علي حسن")
                tech_category = st.text_input("الصنف *:", placeholder="اكتب الصنف كما في الإكسل (مثال: مهندس مدني / تكييف وتبريد / نجار...)")
                tech_job = st.text_input("المهنة الحالية / الوظيفة الفعلية بالمفرزة:", placeholder="مثال: قائد مفرزة / فني شيلرات...")

            with col_b:
                det_select_options = {d['hospital_name']: d['id'] for d in detachments}
                tech_detachment_name = st.selectbox("المفرزة / المستشفى التابع لها *:", options=list(det_select_options.keys()))
                tech_residence = st.text_input("مكان السكن الفعلي *:", placeholder="مثال: إربد - لواء بني عبيد (الحصن)")
                tech_join_date = st.date_input("تاريخ الالتحاق بالمفرزة *:", value=date.today())
                tech_phone = st.text_input("رقم الهاتف:", placeholder="مثال: 0791234567")
                tech_eval = st.text_area("الملاحظات والتقييم الفني والأداء:", placeholder="تقييم الأداء والجاهزية الفنية...")

            add_btn_label = settings.get("btn_add_tech_label", "💾 حفظ وتسجيل الفني")
            submit_add_tech = st.form_submit_button(add_btn_label, type="primary", use_container_width=True)

            if submit_add_tech:
                if not tech_mil_id.strip() or not tech_name.strip() or not tech_category.strip():
                    st.error("❌ يرجى إدخال الرقم العسكري والاسم الرباعي والصنف بشكل صحيح.")
                else:
                    det_id = det_select_options[tech_detachment_name]
                    success, err = db.add_technician(
                        tech_mil_id.strip(),
                        tech_rank,
                        tech_name.strip(),
                        tech_category.strip(),
                        tech_job.strip(),
                        tech_residence.strip(),
                        det_id,
                        str(tech_join_date),
                        tech_phone.strip(),
                        tech_eval.strip()
                    )
                    if success:
                        st.toast(f"✅ تم إضافة الفني {tech_name} بنجاح!", icon="🎖️")
                        st.success(f"تم تسجيل الفني (الرقم العسكري: {tech_mil_id}) بنجاح على مرتب {tech_detachment_name}.")
                        st.rerun()
                    else:
                        st.error(f"❌ خطأ أثناء الإضافة: {err}")

    # --------------------------------------------------------------------------
    # تبويب 3: إجراء حركة نقل
    # --------------------------------------------------------------------------
    with tab3:
        st.markdown("#### 🔄 إجراء وتوثيق حركة نقل فني بين المفارز")
        st.info("💡 عند تنفيذ حركة النقل، يقوم النظام تلقائياً بتحديث مفرزة الفني وتاريخ التحاقه وتوثيق القيد في سجل حركات النقل.")

        all_techs = db.get_all_technicians_df(apply_custom_columns=False)

        if all_techs.empty:
            st.warning("لا يوجد فنيين مسجلين لإجراء حركة نقل.")
        else:
            tech_choices = {
                f"{row['الرتبة']} / {row['الاسم الرباعي']} (الرقم العسكري: {row['الرقم العسكري']}) - [سكن: {row.get('مكان السكن', 'غير محدد')}] - [حالياً: {row['المستشفى الحالي']}]": row['الرقم العسكري']
                for _, row in all_techs.iterrows()
            }

            selected_tech_label = st.selectbox("👤 اختر الفني المراد نقله:", options=list(tech_choices.keys()))
            selected_mil_id = tech_choices[selected_tech_label]
            tech_info = db.get_technician_by_id(selected_mil_id)

            if tech_info:
                duration_arabic = db.calculate_duration_arabic(tech_info.get("join_date", ""))
                st.markdown(f"""
                <div style="background: #F1F5F9; border-radius: 8px; padding: 14px; margin: 10px 0; border: 1px solid #CBD5E1;">
                    <div><b>الرقم العسكري:</b> {tech_info['military_id']} | <b>الاسم:</b> {tech_info['rank']} / {tech_info['full_name']} | <b>الصنف:</b> {tech_info.get('specialty', '')}</div>
                    <div><b>المهنة الحالية:</b> {tech_info.get('current_job', 'غير محدد')} | <b>مكان السكن:</b> {tech_info.get('residence', 'غير محدد')}</div>
                    <div><b>المفرزة الحالية:</b> {tech_info['hospital_name'] or 'غير محدد'} ({tech_info['governorate'] or ''}) | <b>تاريخ الالتحاق:</b> {tech_info['join_date']} (خدمة بالمفرزة: <b style="color: #15803D;">{duration_arabic}</b>)</div>
                </div>
                """, unsafe_allow_html=True)

                with st.form(key="transfer_form"):
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        dest_options = {d['hospital_name']: d['id'] for d in detachments if d['id'] != tech_info['current_detachment_id']}
                        if not dest_options:
                            dest_options = {d['hospital_name']: d['id'] for d in detachments}

                        to_hosp_name = st.selectbox("المفرزة / المستشفى المنقول إليه *:", options=list(dest_options.keys()))
                        transfer_date = st.date_input("تاريخ النقل الفعلي *:", value=date.today())

                    with t_col2:
                        transfer_notes = st.text_area("أسباب وملاحظات أمر النقل:", placeholder="مثال: نقل بناءً على مقتضيات المصلحة وسد النقص وتقريب مكان السكن...")

                    transfer_btn_label = settings.get("btn_transfer_label", "🔄 تنفيذ وتوثيق حركة النقل")
                    submit_transfer = st.form_submit_button(transfer_btn_label, type="primary", use_container_width=True)

                    if submit_transfer:
                        to_det_id = dest_options[to_hosp_name]
                        success, msg = db.transfer_technician(
                            selected_mil_id,
                            to_det_id,
                            str(transfer_date),
                            transfer_notes.strip()
                        )
                        if success:
                            st.toast("✅ تم تنفيذ وتوثيق حركة النقل بنجاح!", icon="🔄")
                            st.success(f"تم نقل الفني {tech_info['full_name']} إلى {to_hosp_name} وتوثيق الحركة بالسجل.")
                            st.rerun()
                        else:
                            st.error(f"❌ تعذر تنفيذ النقل: {msg}")

    # --------------------------------------------------------------------------
    # تبويب 4: تعديل / حذف بيانات فني
    # --------------------------------------------------------------------------
    with tab4:
        st.markdown("#### ✏️ تعديل بيانات فني أو حذفه من المنظومة")
        if all_techs.empty:
            st.warning("لا يوجد فنيين مسجلين.")
        else:
            edit_choices = {
                f"{row['الرتبة']} / {row['الاسم الرباعي']} ({row['الرقم العسكري']})": row['الرقم العسكري']
                for _, row in all_techs.iterrows()
            }
            edit_label = st.selectbox("اختر الفني لتعديل بياناته:", options=list(edit_choices.keys()), key="edit_tech_select")
            edit_mil_id = edit_choices[edit_label]
            target_tech = db.get_technician_by_id(edit_mil_id)

            if target_tech:
                with st.form(key=f"tab4_standalone_edit_tech_form_{edit_mil_id}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.text_input("الرقم العسكري (للقراءة فقط):", value=target_tech['military_id'], disabled=True)
                        e_rank = st.selectbox("الرتبة العسكرية:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(target_tech['rank']) if target_tech['rank'] in MILITARY_RANKS else 0)
                        e_name = st.text_input("الاسم الرباعي:", value=target_tech['full_name'])
                        
                        cur_cat_val = target_tech.get('specialty') or ''
                        e_cat = st.text_input("الصنف (كما في الإكسل):", value=str(cur_cat_val))
                        e_job = st.text_input("المهنة الحالية / الوظيفة الفعلية:", value=target_tech.get('current_job', '') or '')

                    with ec2:
                        all_dets = {d['hospital_name']: d['id'] for d in detachments}
                        cur_idx = 0
                        if target_tech['hospital_name'] in all_dets:
                            cur_idx = list(all_dets.keys()).index(target_tech['hospital_name'])

                        e_det_name = st.selectbox("المفرزة الحالية:", options=list(all_dets.keys()), index=cur_idx)
                        e_residence = st.text_input("مكان السكن الفعلي:", value=target_tech.get('residence', '') or '')
                        
                        try:
                            parsed_date = datetime.strptime(str(target_tech['join_date']).strip(), "%Y-%m-%d").date()
                        except Exception:
                            parsed_date = date.today()

                        e_join_date = st.date_input("تاريخ الالتحاق بالمفرزة:", value=parsed_date)
                        e_phone = st.text_input("رقم الهاتف:", value=target_tech['phone_number'] or '')
                        e_eval = st.text_area("الملاحظات والتقييم الفني والأداء:", value=target_tech['evaluation_and_notes'] or '')

                    save_tech_edit = st.form_submit_button("💾 حفظ تعديلات الفني", type="primary", use_container_width=True)

                    if save_tech_edit:
                        success, err = db.update_technician(
                            edit_mil_id,
                            e_rank,
                            e_name.strip(),
                            e_cat.strip(),
                            e_job.strip(),
                            e_residence.strip(),
                            all_dets[e_det_name],
                            str(e_join_date),
                            e_phone.strip(),
                            e_eval.strip()
                        )
                        if success:
                            st.toast("✅ تم تحديث بيانات الفني بنجاح!", icon="✏️")
                            st.success("تم حفظ التعديلات بنجاح.")
                            st.rerun()
                        else:
                            st.error(f"❌ خطأ أثناء التعديل: {err}")

                # خيار الحذف النهائي
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("🗑️ حذف الفني نهائياً من المنظومة"):
                    st.error(f"⚠️ تنبيه: سيؤدي حذف الفني ({target_tech['full_name']}) إلى إزالته نهائياً من مرتبات المفرزة.")
                    del_confirm = st.checkbox(f"أؤكد الرغبة في حذف الفني صاحب الرقم العسكري ({edit_mil_id}) نهائياً.", key="del_check")
                    if del_confirm:
                        if st.button("تأكيد الحذف النهائي", type="primary", key="del_btn"):
                            db.delete_technician(edit_mil_id)
                            st.toast("تم حذف الفني بنجاح.", icon="🗑️")
                            st.rerun()


# ==============================================================================
# 4. سجل حركات النقل (Movement History)
# ==============================================================================
elif menu_choice == "🔄 سجل حركات النقل":
    styles.render_page_header(
        "سجل وأرشيف حركات النقل",
        "التوثيق الزمني لحركات تنقلات الفنيين بين المفارز والمستشفيات العسكرية بالمحافظات",
        "🔄"
    )

    mov_df = db.get_movement_logs_df()

    if mov_df.empty:
        st.info("ℹ️ لا توجد حركات نقل مسجلة في الأرشيف حتى الآن.")
    else:
        m_col1, m_col2, m_col3 = st.columns([2, 1, 1])
        with m_col1:
            mov_search = st.text_input("بحث في سجل الحركات (بالاسم أو الرقم العسكري):", placeholder="بحث...")
        with m_col2:
            hosp_list = ["الكل"] + list(set(mov_df["من مستشفى"].tolist() + mov_df["إلى مستشفى"].tolist()))
            hosp_filter = st.selectbox("تصفية حسب المستشفى:", options=hosp_list)
        with m_col3:
            st.metric("إجمالي الحركات المسجلة", f"{len(mov_df)} حركة")

        filtered_mov = mov_df.copy()
        if mov_search:
            filtered_mov = filtered_mov[
                filtered_mov["اسم الفني"].str.contains(mov_search, case=False, na=False) |
                filtered_mov["الرقم العسكري"].astype(str).str.contains(mov_search, case=False, na=False)
            ]
        if hosp_filter != "الكل":
            filtered_mov = filtered_mov[
                (filtered_mov["من مستشفى"] == hosp_filter) | (filtered_mov["إلى مستشفى"] == hosp_filter)
            ]

        st.markdown("#### 📜 جدول حركات النقل الموثقة")
        st.markdown(styles.render_rtl_table(filtered_mov), unsafe_allow_html=True)

        excel_mov = export_to_excel(filtered_mov, sheet_name="سجل حركات النقل")
        file_mov_name = f"سجل_حركات_النقل_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        export_btn_label = settings.get("btn_export_label", "📥 تصدير الكشف إلى Excel")
        st.download_button(
            label=f"{export_btn_label} (سجل النقل الكامل)",
            data=excel_mov,
            file_name=file_mov_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_mov_excel"
        )


# ==============================================================================
# 5. الإعدادات وتخصيص المنظومة (Settings Screen)
# ==============================================================================
elif menu_choice == "⚙️ الإعدادات وتخصيص المنظومة":
    styles.render_page_header(
        "لوحة الإعدادات وتخصيص المنظومة",
        "تعديل مسميات وهوية البرنامج، إدارة وتعديل المستشفيات، تخصيص مسميات الأزرار، والتحكم في ترتيب أعمدة الجداول",
        "⚙️"
    )

    set_tab1, set_tab2, set_tab3, set_tab4, set_tab5, set_tab6 = st.tabs([
        "🏢 هوية البرنامج ومسمياته",
        "🏥 إدارة وتعديل أسماء المستشفيات",
        "🏷️ تخصيص مسميات الأزرار",
        "📊 ترتيب وظهور أعمدة الجداول (يمين / يسار)",
        "💾 النسخ الاحتياطي واستعادة قاعدة البيانات",
        "👥 إدارة المستخدمين والصلاحيات"
    ])

    # --------------------------------------------------------------------------
    # تبويب 1: هوية ومسميات المنظومة
    # --------------------------------------------------------------------------
    with set_tab1:
        st.markdown("#### 🏢 تخصيص اسم البرنامج والشعارات")
        with st.form(key="app_identity_form"):
            new_title = st.text_input("اسم البرنامج الرئيسي (عنوان الصفحة):", value=settings.get("app_title", ""))
            new_sub = st.text_input("العنوان الفرعي للبرنامج:", value=settings.get("app_subtitle", ""))
            new_sidebar = st.text_input("عنوان الشريط الجانبي (اسم الشعبة / القيادة):", value=settings.get("sidebar_title", ""))

            save_identity = st.form_submit_button("💾 حفظ مسميات وهوية البرنامج", type="primary")
            if save_identity:
                db.update_app_settings(
                    new_title,
                    new_sub,
                    new_sidebar,
                    settings.get("btn_export_label", "📥 تصدير الكشف إلى Excel"),
                    settings.get("btn_transfer_label", "🔄 تنفيذ وتوثيق حركة النقل"),
                    settings.get("btn_save_shortages_label", "💾 حفظ وتحديث النواقص"),
                    settings.get("btn_add_tech_label", "💾 حفظ وتسجيل الفني")
                )
                st.toast("✅ تم تحديث اسم وهوية البرنامج بنجاح!", icon="🏢")
                st.rerun()

    # --------------------------------------------------------------------------
    # تبويب 2: إدارة وتعديل أسماء وبيانات المستشفيات والمفارز
    # --------------------------------------------------------------------------
    with set_tab2:
        st.markdown("#### 🏥 تعديل أسماء المستشفيات والمفارز الحالية")
        all_dets = db.get_detachments_list()

        if all_dets:
            det_edit_map = {f"{d['hospital_name']} ({d['governorate']})": d['id'] for d in all_dets}
            selected_det_name = st.selectbox("اختر المستشفى المراد تعديل اسمه أو بياناته:", options=list(det_edit_map.keys()))
            target_det_id = det_edit_map[selected_det_name]
            target_det = db.get_detachment_by_id(target_det_id)

            if target_det:
                with st.form(key=f"edit_det_full_{target_det_id}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        h_name = st.text_input("اسم المستشفى العسكري *:", value=target_det['hospital_name'])
                        h_gov = st.selectbox("المحافظة *:", options=GOVERNORATES, index=GOVERNORATES.index(target_det['governorate']) if target_det['governorate'] in GOVERNORATES else 0)
                        h_phone = st.text_input("هاتف التواصل / المفرزة:", value=target_det['contact_phone'] or '')
                    with c2:
                        h_rank = st.selectbox("رتبة قائد المفرزة *:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(target_det['supervisor_rank']) if target_det['supervisor_rank'] in MILITARY_RANKS else 0)
                        h_supervisor = st.text_input("اسم قائد المفرزة *:", value=target_det['supervisor_name'])
                        h_notes = st.text_input("ملاحظات المفرزة العامة:", value=target_det['notes'] or '')

                    save_hosp_btn = st.form_submit_button("💾 حفظ تعديلات المستشفى", type="primary", use_container_width=True)
                    if save_hosp_btn:
                        db.update_detachment_info(target_det_id, h_name, h_gov, h_rank, h_supervisor, h_phone, h_notes)
                        st.toast("✅ تم تحديث بيانات واسم المستشفى بنجاح!", icon="🏥")
                        st.rerun()

                # حذف مستشفى
                with st.expander(f"🗑️ حذف مستشفى ({target_det['hospital_name']}) من المنظومة"):
                    st.warning("⚠️ تنبيه: سيؤدي الحذف إلى إزالة المستشفى من قائمة المفارز وفصل ارتباط فنييه.")
                    if st.checkbox(f"تأكيد الرغبة في حذف المستشفى (معرف: {target_det_id})", key=f"del_hosp_{target_det_id}"):
                        if st.button("حذف المستشفى نهائياً", type="primary", key=f"btn_del_hosp_{target_det_id}"):
                            db.delete_detachment(target_det_id)
                            st.toast("تم حذف المستشفى بنجاح.", icon="🗑️")
                            st.rerun()

        st.markdown("---")
        st.markdown("#### ➕ إضافة مستشفى / مفرزة جديدة")
        with st.form(key="add_hosp_settings_form", clear_on_submit=True):
            a1, a2 = st.columns(2)
            with a1:
                new_h_name = st.text_input("اسم المستشفى العسكري الجديد *:")
                new_h_gov = st.selectbox("المحافظة *:", options=GOVERNORATES, key="new_gov_set")
                new_h_phone = st.text_input("هاتف التواصل:", key="new_ph_set")
            with a2:
                new_h_rank = st.selectbox("رتبة قائد المفرزة *:", options=MILITARY_RANKS, key="new_rank_set")
                new_h_sup = st.text_input("اسم قائد المفرزة *:", key="new_sup_set")
                new_h_short = st.text_area("النواقص والاحتياجات الأولية:", key="new_sh_set")
                new_h_note = st.text_input("ملاحظات:", key="new_nt_set")

            add_hosp_sub = st.form_submit_button("إضافة المستشفى للمنظومة", type="primary")
            if add_hosp_sub:
                if not new_h_name.strip() or not new_h_sup.strip():
                    st.error("يرجى ملء الحقول الإجبارية (*)")
                else:
                    db.add_detachment(new_h_name.strip(), new_h_gov, new_h_rank, new_h_sup.strip(), new_h_phone.strip(), new_h_short.strip(), new_h_note.strip())
                    st.toast("✅ تم إضافة المستشفى بنجاح!", icon="🏥")
                    st.rerun()

    # --------------------------------------------------------------------------
    # تبويب 3: تخصيص مسميات الأزرار
    # --------------------------------------------------------------------------
    with set_tab3:
        st.markdown("#### 🏷️ تخصيص نصوص ومسميات الأزرار في الواجهة")
        with st.form(key="buttons_label_form"):
            b1, b2 = st.columns(2)
            with b1:
                new_btn_export = st.text_input("مسمى زر تصدير ملفات Excel:", value=settings.get("btn_export_label", ""))
                new_btn_transfer = st.text_input("مسمى زر تنفيذ حركة النقل:", value=settings.get("btn_transfer_label", ""))
            with b2:
                new_btn_short = st.text_input("مسمى زر حفظ النواقص والاحتياجات:", value=settings.get("btn_save_shortages_label", ""))
                new_btn_add = st.text_input("مسمى زر حفظ وتسجيل الفني الجديد:", value=settings.get("btn_add_tech_label", ""))

            save_btn_labels = st.form_submit_button("💾 حفظ مسميات الأزرار المخصصة", type="primary")
            if save_btn_labels:
                db.update_app_settings(
                    settings.get("app_title", "نظام إدارة مفارز الصيانة العسكرية"),
                    settings.get("app_subtitle", "إدارة القوى البشرية ومرتبات مفارز المستشفيات العسكرية بالمحافظات"),
                    settings.get("sidebar_title", "شعبة الصيانة والتشغيل"),
                    new_btn_export,
                    new_btn_transfer,
                    new_btn_short,
                    new_btn_add
                )
                st.toast("✅ تم تحديث مسميات الأزرار بنجاح!", icon="🏷️")
                st.rerun()

    # --------------------------------------------------------------------------
    # تبويب 4: التحكم في ترتيب وظهور أعمدة الجداول (يمين / يسار)
    # --------------------------------------------------------------------------
    with set_tab4:
        st.markdown("#### 📊 التحكم في ترتيب وظهور أعمدة جدول الفنيين")
        st.caption("يمكنك تقديم أو تأخير أي عمود (يمين / يسار في الجدول) أو تفعيل وإلغاء ظهور أي حقل بحسب رغبتك.")

        current_cols = settings.get("columns_order", db.DEFAULT_TECH_COLUMNS)

        st.markdown("##### 📌 الترتيب الحالي لأعمدة الجدول (من اليمين إلى اليسار):")
        cols_display_str = " ⬅️ ".join([f"**[{i+1}] {col}**" for i, col in enumerate(current_cols)])
        st.info(cols_display_str)

        st.markdown("---")
        st.markdown("##### 🔀 إعادة ترتيب عمود (تقديم / تأخير):")
        r_col1, r_col2, r_col3 = st.columns([2, 1, 1])

        with r_col1:
            selected_col_to_move = st.selectbox("اختر العمود المراد تحريكه:", options=current_cols)
        
        idx = current_cols.index(selected_col_to_move)

        with r_col2:
            move_up = st.button("➡️ تحريك لليمين (تقديم)", disabled=(idx == 0), use_container_width=True)
            if move_up and idx > 0:
                current_cols[idx], current_cols[idx - 1] = current_cols[idx - 1], current_cols[idx]
                db.update_columns_order(current_cols)
                st.toast(f"تم تحريك عمود '{selected_col_to_move}' لليمين", icon="➡️")
                st.rerun()

        with r_col3:
            move_down = st.button("⬅️ تحريك لليسار (تأخير)", disabled=(idx == len(current_cols) - 1), use_container_width=True)
            if move_down and idx < len(current_cols) - 1:
                current_cols[idx], current_cols[idx + 1] = current_cols[idx + 1], current_cols[idx]
                db.update_columns_order(current_cols)
                st.toast(f"تم تحريك عمود '{selected_col_to_move}' لليسار", icon="⬅️")
                st.rerun()

        st.markdown("---")
        st.markdown("##### 👁️ تحديد الأعمدة الظاهرة في الجدول:")
        with st.form(key="columns_selection_form"):
            selected_visible_cols = []
            c_cols = st.columns(3)
            for i, col in enumerate(db.DEFAULT_TECH_COLUMNS):
                with c_cols[i % 3]:
                    is_checked = col in current_cols
                    checked = st.checkbox(col, value=is_checked, key=f"chk_col_{i}")
                    if checked:
                        selected_visible_cols.append(col)

            # الحفاظ على الترتيب الحالي للأعمدة المختارة
            final_ordered = [c for c in current_cols if c in selected_visible_cols]
            # إضافة أي أعمدة جديدة تم اختيارها
            for c in selected_visible_cols:
                if c not in final_ordered:
                    final_ordered.append(c)

            b_save_cols, b_reset_cols = st.columns(2)
            with b_save_cols:
                save_cols_btn = st.form_submit_button("💾 حفظ اختيار وترتيب الأعمدة", type="primary", use_container_width=True)
                if save_cols_btn:
                    if not final_ordered:
                        st.error("يجب اختيار عمود واحد على الأقل.")
                    else:
                        db.update_columns_order(final_ordered)
                        st.toast("✅ تم حفظ ترتيب وظهور الأعمدة بنجاح!", icon="📊")
                        st.rerun()

        # زر إعادة الضبط الافتراضي
        if st.button("🔄 استعادة الترتيب الافتراضي للأعمدة", type="secondary"):
            db.reset_columns_order()
            st.toast("تمت استعادة الترتيب الافتراضي للأعمدة.", icon="🔄")
            st.rerun()

    # --------------------------------------------------------------------------
    # تبويب 5: النسخ الاحتياطي واستعادة قاعدة البيانات
    # --------------------------------------------------------------------------
    with set_tab5:
        st.markdown("#### 💾 إدارة النسخ الاحتياطي واستعادة قاعدة البيانات")
        st.info("💡 يمكنك من هنا حفظ وتنزيل نسخة احتياطية كاملة من قاعدة البيانات، أو استعادة نسخة سابقة تم حفظها بضغطة زر واحدة.")

        bk_col1, bk_col2 = st.columns(2)

        with bk_col1:
            st.markdown("##### 📥 تنزيل نسخة احتياطية كاملة:")
            st.caption("احفظ نسخة من كافة البيانات (المفارز، الفنيين، حركات النقل، الإعدادات):")

            # 1. تنزيل ملف SQLite الأصلي
            db_bytes = db.get_db_bytes()
            if db_bytes:
                st.download_button(
                    label="💾 تنزيل ملف قاعدة البيانات الكامل (SQLite .db)",
                    data=db_bytes,
                    file_name=f"military_maintenance_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.db",
                    mime="application/x-sqlite3",
                    type="primary",
                    use_container_width=True
                )

            # 2. تنزيل ملف Excel شامل لكافة الجداول
            excel_all_bytes = db.export_full_database_excel()
            st.download_button(
                label="📊 تصدير قاعدة البيانات كملف Excel شامل",
                data=excel_all_bytes,
                file_name=f"military_maintenance_full_excel_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

        with bk_col2:
            st.markdown("##### 📤 استعادة قاعدة البيانات من ملف احتياطي:")
            st.caption("ارفع ملف قاعدة البيانات (.db) لاستعادة كافة البيانات فورياً:")

            uploaded_db = st.file_uploader("اختر ملف قاعدة البيانات (.db) للاستعادة:", type=["db", "sqlite", "sqlite3"], key="restore_db_uploader")
            if uploaded_db is not None:
                if st.button("⚠️ تأكيد استعادة قاعدة البيانات واستبدال البيانات الحالية", type="primary", use_container_width=True):
                    with st.spinner("جاري استعادة وتحديث قاعدة البيانات..."):
                        content = uploaded_db.read()
                        ok, msg = db.restore_db_bytes(content)
                        if ok:
                            st.success(msg)
                            st.toast("✅ تمت الاستعادة بنجاح!", icon="💾")
                            st.rerun()
                        else:
                            st.error(msg)

    # --------------------------------------------------------------------------
    # تبويب 6: إدارة حسابات المستخدمين وصلاحيات المفارز
    # --------------------------------------------------------------------------
    with set_tab6:
        st.markdown("#### 👥 إدارة حسابات المستخدمين ومستويات الصلاحية")
        st.caption("التحكم في حسابات الدخول، تعيين قادة المفارز بالمستشفيات العسكرية، وتحديد نطاق الصلاحيات لكل مستخدم.")

        # بطاقة توضيحية لنظام الصلاحيات
        st.markdown("""
        <div style="background: rgba(15, 23, 42, 0.04); border-right: 4px solid #0284C7; padding: 12px 16px; border-radius: 6px; margin-bottom: 20px; font-size: 13.5px; color: #334155; line-height: 1.8;">
            👑 <b>رئيس الفرع (المقدم المهندس رامي سبع العيش):</b> صلاحية قيادية وإدارية شاملة وكاملة (لوحة المؤشرات، كشف وتعديل كافة المفارز والمستشفيات، إدارة القوى البشرية وحركات النقل، فك قفل وتعديل الموجود للأيام السابقة، وإدارة الحسابات والإعدادات).<br>
            🏥 <b>قادة المفارز بالمستشفيات (مثل المقدم المهندسة منار - مفرزة مستشفى الأمير علي بالكرك):</b> صلاحية مقيدة حصرياً بالمستشفى المسند، تسجيل واعتماد الموجود الصباحي لمفرزته فقط (مع قفل التعديل فور الحفظ)، واستعراض وتحديث بيانات مفرزته ونواقصها.
        </div>
        """, unsafe_allow_html=True)

        users_df = db.get_all_users_df()
        all_dets = db.get_detachments_list()
        det_choice_map = {f"{d['hospital_name']} ({d['governorate']})": d['id'] for d in all_dets}

        # 1. كشف المستخدمين الحاليين في المنظومة
        st.markdown(f"##### 📋 قائمة المستخدمين المسجلين في المنظومة ({len(users_df)} مستخدم):")

        if not users_df.empty:
            users_table_rows = []
            for idx, u in enumerate(users_df.to_dict(orient="records"), 1):
                role_val = u.get("role", "قائد مفرزة")
                if role_val == "رئيس الفرع":
                    role_badge = '<span style="background: #0284C7; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 11.5px; font-weight: 700;">👑 رئيس الفرع</span>'
                else:
                    role_badge = '<span style="background: #15803D; color: #FFFFFF; padding: 3px 10px; border-radius: 12px; font-size: 11.5px; font-weight: 700;">🏥 قائد مفرزة</span>'

                status_badge = '<span style="color: #16A34A; font-weight: 700;">✅ نشط</span>' if u.get("is_active") == 1 else '<span style="color: #DC2626; font-weight: 700;">⛔ معطل</span>'
                raw_hosp = u.get("hospital_name")
                if pd.isna(raw_hosp) or not raw_hosp or str(raw_hosp).lower() == 'nan':
                    hosp_name_val = "🛡️ إشراف شامل لكافة المفارز" if role_val == "رئيس الفرع" else "غير مسند"
                else:
                    hosp_name_val = str(raw_hosp)

                last_l = u.get('last_login')
                last_login_str = str(last_l) if last_l and not pd.isna(last_l) and str(last_l).lower() != 'nan' else 'لم يسجل بعد'

                users_table_rows.append(f'<tr><td style="text-align: center; font-weight: 700;">{idx}</td><td><span class="badge-mil-id">{u["username"]}</span></td><td><span class="badge-rank">{u["rank"]}</span></td><td style="font-weight: 800; color: #0F172A;">{u["full_name"]}</td><td style="text-align: center;">{role_badge}</td><td><b style="color: #0369A1;">{hosp_name_val}</b></td><td style="text-align: center;">{status_badge}</td><td style="font-size: 12px; color: #64748B;">{last_login_str}</td></tr>')

            users_html = f'<div class="rtl-table-wrapper"><table class="rtl-table" dir="rtl"><thead><tr><th style="text-align: center; width: 40px;">م</th><th>رقم التعريف / اسم الدخول</th><th>الرتبة</th><th>الاسم الرباعي الكامل</th><th style="text-align: center;">نوع الصلاحية</th><th>المستشفى / المفرزة المسندة</th><th style="text-align: center;">الحالة</th><th>آخر تسجيل دخول</th></tr></thead><tbody>{"".join(users_table_rows)}</tbody></table></div>'
            st.markdown(users_html, unsafe_allow_html=True)

        st.markdown("---")

        # أقسام العمليات على المستخدمين (إضافة، تعديل، تغيير كلمة المرور، حذف)
        u_tab1, u_tab2, u_tab3, u_tab4 = st.tabs([
            "➕ إضافة مستخدم / قائد جديد",
            "✏️ تعديل بيانات وصلاحيات مستخدم",
            "🔑 تغيير كلمة المرور لمستخدم",
            "🗑️ حذف أو إلغاء تفعيل حساب"
        ])

        # --- أ. إضافة مستخدم جديد ---
        with u_tab1:
            st.markdown("##### ➕ إنشاء حساب مستخدم أو قائد مفرزة جديد")
            with st.form(key="create_user_form", clear_on_submit=True):
                cu1, cu2 = st.columns(2)
                with cu1:
                    new_u_username = st.text_input("👤 رقم التعريف / الرقم العسكري / اسم المستخدم *:", placeholder="مثال: 10008 أو cmd_aqaba")
                    new_u_name = st.text_input("📝 الاسم الكامل رباعياً *:", placeholder="مثال: أحمد محمد علي العبادي")
                    new_u_rank = st.selectbox("🎖️ الرتبة العسكرية *:", options=MILITARY_RANKS, index=0)
                with cu2:
                    new_u_role = st.selectbox("🛡️ نوع الصلاحية / الدور *:", options=["قائد مفرزة", "رئيس الفرع"], index=0)
                    new_u_det_id = None
                    if new_u_role == "قائد مفرزة":
                        selected_det_label = st.selectbox("🏥 المستشفى العسكري المسند إليه:", options=list(det_choice_map.keys()))
                        new_u_det_id = det_choice_map.get(selected_det_label)
                    else:
                        st.info("ℹ️ رئيس الفرع يمتلك صلاحية الإشراف والتعديل على كافة المفارز تلقائياً.")

                    new_u_pwd = st.text_input("🔑 كلمة المرور *:", type="password", placeholder="أدخل كلمة المرور...")
                    new_u_pwd_confirm = st.text_input("🔑 تأكيد كلمة المرور *:", type="password", placeholder="أعد إدخال كلمة المرور...")

                create_user_btn = st.form_submit_button("🚀 إنشاء وتفعيل الحساب", type="primary", use_container_width=True)
                if create_user_btn:
                    if not new_u_username.strip() or not new_u_name.strip() or not new_u_pwd:
                        st.error("يرجى ملء جميع الحقول المطلوبة (*).")
                    elif new_u_pwd != new_u_pwd_confirm:
                        st.error("كلمتا المرور غير متطابقتين.")
                    else:
                        ok_create, msg_create = db.create_user(
                            username=new_u_username.strip(),
                            password=new_u_pwd,
                            full_name=new_u_name.strip(),
                            rank=new_u_rank,
                            role=new_u_role,
                            detachment_id=new_u_det_id
                        )
                        if ok_create:
                            st.toast(msg_create, icon="✅")
                            st.success(msg_create)
                            st.rerun()
                        else:
                            st.error(msg_create)

        # --- ب. تعديل بيانات مستخدم ---
        with u_tab2:
            st.markdown("##### ✏️ تعديل بيانات المستخدم والصلاحية والمستشفى المسند")
            if not users_df.empty:
                user_select_dict = {f"{u['rank']} / {u['full_name']} ({u['username']}) - [{u['role']}]": u['id'] for u in users_df.to_dict(orient="records")}
                selected_user_label = st.selectbox("اختر المستخدم المراد تعديل بياناته:", options=list(user_select_dict.keys()), key="sel_user_edit")
                target_user_id = user_select_dict[selected_user_label]
                target_user_obj = db.get_user_by_id(target_user_id)

                if target_user_obj:
                    with st.form(key=f"edit_user_form_{target_user_id}"):
                        eu1, eu2 = st.columns(2)
                        with eu1:
                            st.text_input("رقم التعريف / اسم المستخدم (ثابت):", value=target_user_obj['username'], disabled=True)
                            ed_name = st.text_input("الاسم الكامل:", value=target_user_obj['full_name'])
                            ed_rank = st.selectbox(
                                "الرتبة:",
                                options=MILITARY_RANKS,
                                index=MILITARY_RANKS.index(target_user_obj['rank']) if target_user_obj['rank'] in MILITARY_RANKS else 0
                            )
                        with eu2:
                            ed_role = st.selectbox(
                                "نوع الصلاحية:",
                                options=["قائد مفرزة", "رئيس الفرع"],
                                index=0 if target_user_obj['role'] == "قائد مفرزة" else 1
                            )
                            ed_det_id = None
                            if ed_role == "قائد مفرزة":
                                current_det_idx = 0
                                det_keys = list(det_choice_map.keys())
                                if target_user_obj.get("detachment_id"):
                                    for i, k in enumerate(det_keys):
                                        if det_choice_map[k] == target_user_obj["detachment_id"]:
                                            current_det_idx = i
                                            break
                                ed_det_label = st.selectbox("المستشفى المسند:", options=det_keys, index=current_det_idx)
                                ed_det_id = det_choice_map[ed_det_label]

                            ed_active = st.checkbox("الحساب نشط ومفعل", value=(target_user_obj.get('is_active', 1) == 1))

                        save_user_edits_btn = st.form_submit_button("💾 حفظ تعديلات المستخدم والصلاحيات", type="primary", use_container_width=True)
                        if save_user_edits_btn:
                            ok_upd, msg_upd = db.update_user(
                                user_id=target_user_id,
                                full_name=ed_name.strip(),
                                rank=ed_rank,
                                role=ed_role,
                                detachment_id=ed_det_id,
                                is_active=1 if ed_active else 0
                            )
                            if ok_upd:
                                st.toast(msg_upd, icon="✅")
                                st.success(msg_upd)
                                st.rerun()
                            else:
                                st.error(msg_upd)

        # --- ج. تغيير كلمة المرور ---
        with u_tab3:
            st.markdown("##### 🔑 إعادة ضبط / تغيير كلمة المرور")
            if not users_df.empty:
                pwd_user_dict = {f"{u['rank']} / {u['full_name']} ({u['username']})": u['id'] for u in users_df.to_dict(orient="records")}
                selected_pwd_user = st.selectbox("اختر المستخدم لإعادة ضبط كلمة المرور:", options=list(pwd_user_dict.keys()), key="sel_user_pwd")
                target_pwd_uid = pwd_user_dict[selected_pwd_user]

                with st.form(key=f"reset_pwd_form_{target_pwd_uid}"):
                    cp1, cp2 = st.columns(2)
                    with cp1:
                        new_pass_val = st.text_input("كلمة المرور الجديدة *:", type="password", placeholder="أدخل كلمة المرور الجديدة...")
                    with cp2:
                        new_pass_confirm = st.text_input("تأكيد كلمة المرور الجديدة *:", type="password", placeholder="أعد إدخال كلمة المرور...")

                    reset_pass_btn = st.form_submit_button("🔑 تحديث كلمة المرور فورياً", type="primary", use_container_width=True)
                    if reset_pass_btn:
                        if not new_pass_val or len(new_pass_val.strip()) < 3:
                            st.error("يجب إدخال كلمة مرور مكونة من 3 خانات على الأقل.")
                        elif new_pass_val != new_pass_confirm:
                            st.error("كلمتا المرور غير متطابقتين.")
                        else:
                            ok_pwd, msg_pwd = db.change_user_password(target_pwd_uid, new_pass_val)
                            if ok_pwd:
                                st.toast(msg_pwd, icon="🔑")
                                st.success(msg_pwd)
                                st.rerun()
                            else:
                                st.error(msg_pwd)

        # --- د. حذف مستخدم ---
        with u_tab4:
            st.markdown("##### 🗑️ حذف حساب مستخدم من المنظومة")
            if not users_df.empty:
                # تصفية الحسابات لحماية الحساب الرئيسي
                del_user_dict = {f"{u['rank']} / {u['full_name']} ({u['username']})": u['id'] for u in users_df.to_dict(orient="records") if u['username'] not in ['admin', '10001']}
                
                if not del_user_dict:
                    st.info("لا توجد حسابات فرعية إضافية قابلة للحذف (الحساب الرئيسي لرئيس الفرع محمي).")
                else:
                    selected_del_user = st.selectbox("اختر المستخدم المراد حذفه نهائياً:", options=list(del_user_dict.keys()), key="sel_user_del")
                    target_del_uid = del_user_dict[selected_del_user]

                    st.warning("⚠️ تنبيه: سيؤدي حذف المستخدم إلى إلغاء صلاحية دخوله نهائياً إلى المنظومة.")
                    if st.checkbox("تأكيد الرغبة في حذف هذا الحساب نهائياً", key=f"chk_del_u_{target_del_uid}"):
                        if st.button("🗑️ تأكيد الحذف النهائي", type="primary", key=f"btn_confirm_del_u_{target_del_uid}"):
                            ok_del, msg_del = db.delete_user(target_del_uid)
                            if ok_del:
                                st.toast(msg_del, icon="🗑️")
                                st.success(msg_del)
                                st.rerun()
                            else:
                                st.error(msg_del)

