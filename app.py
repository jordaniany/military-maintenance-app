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

# --- الشريط الجانبي (Sidebar) ---
styles.render_sidebar_header(
    title=settings.get("sidebar_title", "شعبة الصيانة والتشغيل"),
    subtitle="إدارة مفارز المستشفيات العسكرية"
)

menu_choice = st.sidebar.radio(
    "القائمة الرئيسية:",
    [
        "📊 لوحة المؤشرات العامة",
        "🏥 كشف المفارز والمستشفيات",
        "👥 إدارة المرتبات والفنيين",
        "🔄 سجل حركات النقل",
        "⚙️ الإعدادات وتخصيص المنظومة"
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

            # أزرار الإجراءات (تصدير واستيراد)
            exp_col1, exp_col2 = st.columns([1, 1])
            with exp_col1:
                if not tech_df.empty:
                    # زر تصدير كشف المفرزة بصيغة Excel
                    excel_data = export_to_excel(tech_df, sheet_name=f"كشف {selected_detachment['governorate']}")
                    file_name = f"كشف_مرتبات_{selected_detachment['hospital_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    export_btn_label = settings.get("btn_export_label", "📥 تصدير الكشف إلى Excel")
                    st.download_button(
                        label=export_btn_label,
                        data=excel_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"dl_det_{selected_id}",
                        use_container_width=True
                    )
            with exp_col2:
                template_bytes = db.generate_technicians_template()
                st.download_button(
                    label="📄 تحميل قالب Excel قياسي للاستيراد",
                    data=template_bytes,
                    file_name="قالب_استيراد_فنيي_المفرزة.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"dl_tpl_{selected_id}",
                    use_container_width=True
                )

            # 2.4 قسم استيراد كشف المرتبات من ملف Excel
            with st.expander(f"📤 استيراد كشف فنيين من ملف Excel لمفرزة ({selected_detachment['hospital_name']})", expanded=False):
                st.markdown("""
                <div style="font-size: 13px; color: #94A3B8; margin-bottom: 12px;">
                    💡 يمكنك رفع ملف إكسل يحتوي على كشف مرتبات الفنيين وسيتم إلحاقهم مباشرة بهذه المفرزة.
                    الأعمدة المدعومة: <b>الرقم العسكري *، الرتبة، الاسم الرباعي *، الصنف، المهنة الحالية، مكان السكن، تاريخ الالتحاق بالمفرزة، رقم الهاتف، الملاحظات</b>.
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

    set_tab1, set_tab2, set_tab3, set_tab4, set_tab5 = st.tabs([
        "🏢 هوية البرنامج ومسمياته",
        "🏥 إدارة وتعديل أسماء المستشفيات",
        "🏷️ تخصيص مسميات الأزرار",
        "📊 ترتيب وظهور أعمدة الجداول (يمين / يسار)",
        "💾 النسخ الاحتياطي واستعادة قاعدة البيانات"
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
