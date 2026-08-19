"""
تطبيق إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية بالمحافظات
نظام تفاعلي متكامل مبني باستخدام Python, Streamlit, Pandas, SQLite مع واجهة عربية كاملة (RTL).
"""

import streamlit as st
import pandas as pd
import io
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

# تهيئة قاعدة البيانات والتأكد من وجود البيانات الأولية
db.init_db()

# قائمة الرتب العسكرية القياسية
MILITARY_RANKS = [
    "جندي مكلف",
    "جندي أول",
    "عريف",
    "رقيب",
    "رقيب أول",
    "وكيل",
    "وكيل أول",
    "ملازم",
    "ملازم أول",
    "نقيب",
    "رئيس رقباء"
]

# قائمة التخصصات الفنية المطلوبة
SPECIALTIES = [
    "تكييف وتبريد",
    "كهرباء قوى ومحولات",
    "شبكات مياه وصحي",
    "إنشائي عام",
    "أجهزة طبية وميكانيك",
    "أخرى"
]

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

# --- الشريط الجانبي (Sidebar) ---
styles.render_sidebar_header()

menu_choice = st.sidebar.radio(
    "القائمة الرئيسية:",
    [
        "📊 لوحة المؤشرات العامة",
        "🏥 كشف المفارز والمستشفيات",
        "👥 إدارة المرتبات والفنيين",
        "🔄 سجل حركات النقل"
    ],
    index=0
)

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
        "لوحة المؤشرات والمتابعة الميدانية",
        "نظرة شاملة ولحظية على القوى البشرية، جاهزية المفارز، وتنبيهات النواقص بالمستشفيات العسكرية",
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
                    <span>👤 <b>مسؤول المفرزة:</b> {shortage['supervisor_rank']} / {shortage['supervisor_name']}</span>
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
            spec_df.columns = ["التخصص", "العدد"]
            fig_spec = px.pie(
                spec_df,
                names="التخصص",
                values="العدد",
                title="توزيع القوة البشرية حسب التخصص الفني",
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
            # اختصار أسماء المستشفيات لجمال الرسم
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
# 2. كشف المفارز والمستشفيات (Detachments View)
# ==============================================================================
elif menu_choice == "🏥 كشف المفارز والمستشفيات":
    styles.render_page_header(
        "كشف وجاهزية المفارز والمستشفيات",
        "عرض تفاصيل المفرزة، تحديث وحفظ النواقص والاحتياجات الفورية، وإدارة كشف مرتبات المستشفى",
        "🏥"
    )

    detachments = db.get_detachments_list()

    if not detachments:
        st.warning("⚠️ لا توجد مفارز مسجلة في قاعدة البيانات حالياً.")
    else:
        # قائمة خيارات المستشفيات
        detachment_options = {
            f"{d['hospital_name']} ({d['governorate']}) - [{d['technicians_count']} فني]": d['id']
            for d in detachments
        }

        selected_label = st.selectbox(
            "🏢 اختر المستشفى العسكري / المفرزة لعرض التفاصيل:",
            options=list(detachment_options.keys())
        )

        selected_id = detachment_options[selected_label]
        selected_detachment = db.get_detachment_by_id(selected_id)

        if selected_detachment:
            # 2.1 بطاقة بيانات المفرزة
            st.markdown(f"""
            <div class="detachment-info-card">
                <div class="detachment-info-title">🏥 {selected_detachment['hospital_name']}</div>
                <div>
                    <span class="detachment-pill">📍 المحافظة: <b>{selected_detachment['governorate']}</b></span>
                    <span class="detachment-pill">👤 مسؤول المفرزة: <b>{selected_detachment['supervisor_rank']} / {selected_detachment['supervisor_name']}</b></span>
                    <span class="detachment-pill">📞 رقم التواصل: <b>{selected_detachment['contact_phone'] or 'غير محدد'}</b></span>
                </div>
                {f'<div style="margin-top: 12px; color: #94A3B8; font-size: 13px;">📝 <b>ملاحظات المفرزة:</b> {selected_detachment["notes"]}</div>' if selected_detachment["notes"] else ''}
            </div>
            """, unsafe_allow_html=True)

            # 2.2 محرر فوري لحفظ وتحديث "النواقص والاحتياجات البشرية"
            st.markdown("#### 📝 النواقص والاحتياجات البشرية للمفرزة")
            with st.container():
                shortages_input = st.text_area(
                    "بيان النواقص والاحتياجات الواردة من مسؤول المفرزة (تحديث فوري):",
                    value=selected_detachment['staffing_shortages'] or '',
                    placeholder="مثال: بحاجة إلى عدد (1) فني تكييف للوردية المسائية، ونقص فني كهرباء قوى...",
                    key=f"shortages_{selected_id}",
                    height=100
                )

                btn_col1, btn_col2 = st.columns([1, 4])
                with btn_col1:
                    if st.button("💾 حفظ وتحديث النواقص", key=f"save_btn_{selected_id}", type="primary", use_container_width=True):
                        db.update_detachment_shortages(selected_id, shortages_input)
                        st.toast("✅ تم تحديث وحفظ النواقص والاحتياجات البشرية بنجاح!", icon="🛡️")
                        st.rerun()

            st.markdown("---")

            # 2.3 جدول تفصيلي بكافة الفنيين التابعين للمفرزة
            st.markdown(f"#### 👥 كشف مرتبات الفنيين التابعين للمفرزة ({selected_detachment['hospital_name']})")
            tech_df = db.get_technicians_by_detachment_df(selected_id)

            if not tech_df.empty:
                st.dataframe(tech_df, use_container_width=True, hide_index=True)

                # زر تصدير كشف المفرزة بصيغة Excel
                excel_data = export_to_excel(tech_df, sheet_name=f"كشف {selected_detachment['governorate']}")
                file_name = f"كشف_مرتبات_{selected_detachment['hospital_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"

                st.download_button(
                    label="📥 تصدير كشف المفرزة إلى Excel (.xlsx)",
                    data=excel_data,
                    file_name=file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_det_{selected_id}"
                )
            else:
                st.warning("⚠️ لا يوجد فنيين مسجلين على مرتب هذه المفرزة حالياً. يمكنك إضافة أو نقل فنيين إليها من شاشة إدارة المرتبات.")

            # 2.4 تعديل البيانات العامة للمستشفى / المفرزة (خيار إضافي موسع)
            with st.expander("⚙️ تعديل البيانات الأساسية للمستشفى / المفرزة"):
                with st.form(key=f"edit_detachment_form_{selected_id}"):
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        new_hosp_name = st.text_input("اسم المستشفى العسكري:", value=selected_detachment['hospital_name'])
                        new_gov = st.selectbox("المحافظة:", options=GOVERNORATES, index=GOVERNORATES.index(selected_detachment['governorate']) if selected_detachment['governorate'] in GOVERNORATES else 0)
                        new_phone = st.text_input("رقم هاتف المفرزة / التواصل:", value=selected_detachment['contact_phone'] or '')
                    with e_col2:
                        new_rank = st.selectbox("رتبة مسؤول المفرزة:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(selected_detachment['supervisor_rank']) if selected_detachment['supervisor_rank'] in MILITARY_RANKS else 0)
                        new_name = st.text_input("اسم مسؤول المفرزة:", value=selected_detachment['supervisor_name'])
                        new_notes = st.text_input("ملاحظات عامة:", value=selected_detachment['notes'] or '')

                    save_edit_btn = st.form_submit_button("حفظ تعديل بيانات المفرزة")
                    if save_edit_btn:
                        db.update_detachment_info(selected_id, new_hosp_name, new_gov, new_rank, new_name, new_phone, new_notes)
                        st.toast("✅ تم تحديث بيانات المفرزة بنجاح!", icon="🏥")
                        st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    # إضافة مفرزة / مستشفى جديد
    with st.expander("➕ إضافة مفرزة أو مستشفى عسكري جديد إلى المنظومة"):
        with st.form(key="add_new_detachment_form", clear_on_submit=True):
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                add_hosp_name = st.text_input("اسم المستشفى العسكري *:")
                add_gov = st.selectbox("المحافظة *:", options=GOVERNORATES)
                add_phone = st.text_input("هاتف التواصل:")
            with a_col2:
                add_rank = st.selectbox("رتبة مسؤول المفرزة *:", options=MILITARY_RANKS)
                add_name = st.text_input("اسم مسؤول المفرزة *:")
                add_shortages = st.text_area("النواقص والاحتياجات الأولية:")
                add_notes = st.text_input("ملاحظات:")

            submit_add_det = st.form_submit_button("إضافة المفرزة لقاعدة البيانات", type="primary")
            if submit_add_det:
                if not add_hosp_name or not add_name:
                    st.error("يرجى ملء جميع الحقول الإجبارية (*)")
                else:
                    db.add_detachment(add_hosp_name, add_gov, add_rank, add_name, add_phone, add_shortages, add_notes)
                    st.toast("✅ تم إضافة المفرزة بنجاح!", icon="🏥")
                    st.rerun()


# ==============================================================================
# 3. إدارة المرتبات والفنيين (Technicians Management)
# ==============================================================================
elif menu_choice == "👥 إدارة المرتبات والفنيين":
    styles.render_page_header(
        "إدارة المرتبات والقوى البشرية",
        "كشف الفنيين الشامل، محرك البحث والفلاتر، إضافة وتعديل الفنيين، وإجراء حركات النقل الفورية",
        "👥"
    )

    detachments = db.get_detachments_list()
    detachment_map = {d['id']: d['hospital_name'] for d in detachments}

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
        st.markdown("#### 🔍 البحث والفلترة السريعة في مرتبات الفنيين")
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        with f_col1:
            search_query = st.text_input("بحث بالاسم الرباعي أو الرقم العسكري:", placeholder="اكتب اسم الفني أو رقمه العسكري...")
        with f_col2:
            specialty_filter = st.selectbox("تصفية حسب التخصص:", options=["الكل"] + SPECIALTIES)
        with f_col3:
            hosp_options = ["الكل"] + [d['hospital_name'] for d in detachments]
            hospital_filter = st.selectbox("تصفية حسب المستشفى:", options=hosp_options)

        # جلب البيانات وتطبيق الفلاتر
        all_tech_df = db.get_all_technicians_df()

        filtered_df = all_tech_df.copy()

        if search_query:
            filtered_df = filtered_df[
                filtered_df["الاسم الرباعي"].str.contains(search_query, case=False, na=False) |
                filtered_df["الرقم العسكري"].astype(str).str.contains(search_query, case=False, na=False)
            ]

        if specialty_filter != "الكل":
            filtered_df = filtered_df[filtered_df["التخصص الفني"] == specialty_filter]

        if hospital_filter != "الكل":
            filtered_df = filtered_df[filtered_df["المستشفى الحالي"] == hospital_filter]

        # إحصائية نتائج البحث
        st.caption(f"📊 عدد الفنيين المطابقين للبحث: **{len(filtered_df)}** من إجمالي **{len(all_tech_df)}**")

        # إخفاء عمود detachment_id التقني في العرض
        display_df = filtered_df.drop(columns=["detachment_id"], errors="ignore")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        # زر تصدير النتائج إلى Excel
        if not display_df.empty:
            excel_all = export_to_excel(display_df, sheet_name="كشف الفنيين")
            st.download_button(
                label="📥 تصدير نتائج البحث الحالية إلى Excel (.xlsx)",
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
                tech_specialty = st.selectbox("التخصص الفني *:", options=SPECIALTIES)

            with col_b:
                det_select_options = {d['hospital_name']: d['id'] for d in detachments}
                tech_detachment_name = st.selectbox("المفرزة / المستشفى التابع لها *:", options=list(det_select_options.keys()))
                tech_join_date = st.date_input("تاريخ الالتحاق بالمفرزة *:", value=date.today())
                tech_phone = st.text_input("رقم الهاتف:", placeholder="مثال: 0791234567")
                tech_eval = st.text_area("الملاحظات والتقييم الفني والأداء:", placeholder="تقييم الأداء والخبرة والجاهزية الفنية...")

            submit_add_tech = st.form_submit_button("💾 حفظ وتسجيل الفني", type="primary", use_container_width=True)

            if submit_add_tech:
                if not tech_mil_id.strip() or not tech_name.strip():
                    st.error("❌ يرجى إدخال الرقم العسكري والاسم الرباعي بشكل صحيح.")
                else:
                    det_id = det_select_options[tech_detachment_name]
                    success, err = db.add_technician(
                        tech_mil_id.strip(),
                        tech_rank,
                        tech_name.strip(),
                        tech_specialty,
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
        st.info("💡 عند تنفيذ حركة النقل، يقوم النظام تلقائياً بتحديث مفرزة الفني وتاريخ التحاقه، وتوثيق القيد في سجل حركات النقل.")

        all_techs = db.get_all_technicians_df()

        if all_techs.empty:
            st.warning("لا يوجد فنيين مسجلين لإجراء حركة نقل.")
        else:
            # قائمة اختيار الفني
            tech_choices = {
                f"{row['الرتبة']} / {row['الاسم الرباعي']} (الرقم العسكري: {row['الرقم العسكري']}) - [حالياً: {row['المستشفى الحالي']}]": row['الرقم العسكري']
                for _, row in all_techs.iterrows()
            }

            selected_tech_label = st.selectbox("👤 اختر الفني المراد نقله:", options=list(tech_choices.keys()))
            selected_mil_id = tech_choices[selected_tech_label]
            tech_info = db.get_technician_by_id(selected_mil_id)

            if tech_info:
                st.markdown(f"""
                <div style="background: #F1F5F9; border-radius: 8px; padding: 14px; margin: 10px 0; border: 1px solid #CBD5E1;">
                    <div><b>الرقم العسكري:</b> {tech_info['military_id']} | <b>الاسم:</b> {tech_info['rank']} / {tech_info['full_name']}</div>
                    <div><b>التخصص:</b> {tech_info['specialty']} | <b>المفرزة الحالية:</b> {tech_info['hospital_name'] or 'غير محدد'} ({tech_info['governorate'] or ''})</div>
                </div>
                """, unsafe_allow_html=True)

                with st.form(key="transfer_form"):
                    t_col1, t_col2 = st.columns(2)
                    with t_col1:
                        # استبعاد المفرزة الحالية من قائمة الوجهات
                        dest_options = {d['hospital_name']: d['id'] for d in detachments if d['id'] != tech_info['current_detachment_id']}
                        if not dest_options:
                            dest_options = {d['hospital_name']: d['id'] for d in detachments}

                        to_hosp_name = st.selectbox("المفرزة / المستشفى المنقول إليه *:", options=list(dest_options.keys()))
                        transfer_date = st.date_input("تاريخ النقل الفعلي *:", value=date.today())

                    with t_col2:
                        transfer_notes = st.text_area("أسباب وملاحظات أمر النقل:", placeholder="مثال: نقل لسد النقص في صيانة التكييف المركزي بأمر شعبة الصيانة...")

                    submit_transfer = st.form_submit_button("🚀 تنفيذ وتوثيق حركة النقل", type="primary", use_container_width=True)

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
                with st.form(key=f"edit_tech_form_{edit_mil_id}"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        st.text_input("الرقم العسكري (للقراءة فقط):", value=target_tech['military_id'], disabled=True)
                        e_rank = st.selectbox("الرتبة العسكرية:", options=MILITARY_RANKS, index=MILITARY_RANKS.index(target_tech['rank']) if target_tech['rank'] in MILITARY_RANKS else 0)
                        e_name = st.text_input("الاسم الرباعي:", value=target_tech['full_name'])
                        e_spec = st.selectbox("التخصص الفني:", options=SPECIALTIES, index=SPECIALTIES.index(target_tech['specialty']) if target_tech['specialty'] in SPECIALTIES else 0)

                    with ec2:
                        all_dets = {d['hospital_name']: d['id'] for d in detachments}
                        cur_idx = 0
                        if target_tech['hospital_name'] in all_dets:
                            cur_idx = list(all_dets.keys()).index(target_tech['hospital_name'])

                        e_det_name = st.selectbox("المفرزة الحالية:", options=list(all_dets.keys()), index=cur_idx)
                        
                        # تحويل تاريخ الالتحاق
                        try:
                            parsed_date = datetime.strptime(target_tech['join_date'], "%Y-%m-%d").date()
                        except Exception:
                            parsed_date = date.today()

                        e_join_date = st.date_input("تاريخ الالتحاق:", value=parsed_date)
                        e_phone = st.text_input("رقم الهاتف:", value=target_tech['phone_number'] or '')
                        e_eval = st.text_area("الملاحظات والتقييم الفني والأداء:", value=target_tech['evaluation_and_notes'] or '')

                    save_tech_edit = st.form_submit_button("💾 حفظ التعديلات", type="primary", use_container_width=True)

                    if save_tech_edit:
                        success, err = db.update_technician(
                            edit_mil_id,
                            e_rank,
                            e_name,
                            e_spec,
                            all_dets[e_det_name],
                            str(e_join_date),
                            e_phone,
                            e_eval
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
                    st.error(f"⚠️ تنبيه: سيؤدي حذف الفني ({target_tech['full_name']}) إلى إزالته نهائياً من مرتبات المفرزة وحذف سجلاته.")
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
        # إحصائيات وبحث سريع
        m_col1, m_col2, m_col3 = st.columns([2, 1, 1])
        with m_col1:
            mov_search = st.text_input("بحث في سجل الحركات (بالاسم أو الرقم العسكري):", placeholder="بحث...")
        with m_col2:
            hosp_list = ["الكل"] + list(set(mov_df["من مستشفى"].tolist() + mov_df["إلى مستشفى"].tolist()))
            hosp_filter = st.selectbox("تصفية حسب المستشفى:", options=hosp_list)
        with m_col3:
            st.metric("إجمالي الحركات المسجلة", f"{len(mov_df)} حركة")

        # تطبيق التصفية
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
        st.dataframe(filtered_mov, use_container_width=True, hide_index=True)

        # زر تصدير السجل إلى Excel
        excel_mov = export_to_excel(filtered_mov, sheet_name="سجل حركات النقل")
        file_mov_name = f"سجل_حركات_النقل_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        st.download_button(
            label="📥 تصدير سجل حركات النقل الكامل إلى Excel (.xlsx)",
            data=excel_mov,
            file_name=file_mov_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_mov_excel"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # عرض أحدث الحركات كبطاقات زمنية سريعة
        st.markdown("#### ⏱️ أحدث حركات النقل المسجلة:")
        recent_moves = mov_df.head(5)
        for _, row in recent_moves.iterrows():
            st.markdown(f"""
            <div style="background: #FFFFFF; border-right: 4px solid #0284C7; border-radius: 8px; padding: 12px 18px; margin-bottom: 8px; border-top: 1px solid #E2E8F0; border-bottom: 1px solid #E2E8F0; border-left: 1px solid #E2E8F0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-weight: 700; color: #0F172A; font-size: 15px;">
                        🎖️ {row['الرتبة']} / {row['اسم الفني']} ({row['الرقم العسكري']}) - {row['التخصص الفني']}
                    </div>
                    <div style="font-size: 12px; color: #64748B; font-weight: 600;">📅 {row['تاريخ النقل']}</div>
                </div>
                <div style="color: #334155; font-size: 13px; margin-top: 4px;">
                    🔄 <b>مسار النقل:</b> من <span style="color: #DC2626; font-weight: 600;">{row['من مستشفى']}</span> إلى <span style="color: #15803D; font-weight: 600;">{row['إلى مستشفى']}</span>
                </div>
                {f'<div style="color: #64748B; font-size: 12px; margin-top: 2px;">📝 <i>{row["ملاحظات أمر النقل"]}</i></div>' if row["ملاحظات أمر النقل"] else ''}
            </div>
            """, unsafe_allow_html=True)
