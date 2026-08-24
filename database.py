"""
قاعدة بيانات نظام إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية
Database models, SQLite operations, Settings management, and Schema Migration.
"""

import sqlite3
import os
import json
import pandas as pd
from datetime import datetime, date

DB_NAME = "military_maintenance.db"

# الأعمدة الافتراضية لجدول الفنيين بالترتيب القياسي
DEFAULT_TECH_COLUMNS = [
    "الرقم العسكري",
    "الرتبة",
    "الاسم الرباعي",
    "الصنف",
    "المهنة الحالية",
    "المستشفى الحالي",
    "المحافظة",
    "مكان السكن",
    "تاريخ الالتحاق بالمفرزة",
    "مدة الخدمة بالمفرزة",
    "رقم الهاتف",
    "الملاحظات والتقييم الفني"
]

def get_db_connection(db_path=DB_NAME):
    """إرجاع اتصال بقاعدة بيانات SQLite مع دعم الصفوف كقواميس"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def calculate_duration_arabic(join_date_str):
    """احتساب مدة الخدمة في المفرزة باللغة العربية بدقة"""
    if not join_date_str:
        return "غير محدد"
    try:
        join_d = datetime.strptime(str(join_date_str).strip(), "%Y-%m-%d").date()
        today = date.today()
        if join_d > today:
            return "تاريخ مستقبلي"
        
        # حساب الفارق بالأعوام والشهور
        years = today.year - join_d.year
        months = today.month - join_d.month
        days = today.day - join_d.day

        if days < 0:
            months -= 1
        if months < 0:
            years -= 1
            months += 12

        parts = []
        if years > 0:
            if years == 1:
                parts.append("سنة واحدة")
            elif years == 2:
                parts.append("سنتان")
            elif 3 <= years <= 10:
                parts.append(f"{years} سنوات")
            else:
                parts.append(f"{years} سنة")

        if months > 0:
            if months == 1:
                parts.append("شهر واحد")
            elif months == 2:
                parts.append("شهران")
            elif 3 <= months <= 10:
                parts.append(f"{months} أشهر")
            else:
                parts.append(f"{months} شهر")

        if not parts:
            return "أقل من شهر"
        return " و ".join(parts)
    except Exception:
        return str(join_date_str)

def init_db(db_path=DB_NAME):
    """إنشاء وتحديث جداول قاعدة البيانات (Migration آمن بدون فقدان بيانات)"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. جدول المفارز والمستشفيات (Detachments)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hospital_name TEXT NOT NULL,
        governorate TEXT NOT NULL,
        supervisor_rank TEXT NOT NULL,
        supervisor_name TEXT NOT NULL,
        contact_phone TEXT,
        staffing_shortages TEXT DEFAULT '',
        notes TEXT DEFAULT ''
    );
    """)

    # 2. جدول الفنيين والقوى البشرية (Technicians)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS technicians (
        military_id TEXT PRIMARY KEY,
        rank TEXT NOT NULL,
        full_name TEXT NOT NULL,
        specialty TEXT NOT NULL,
        primary_category TEXT DEFAULT 'سلاح الصيانة الملكي',
        current_job TEXT DEFAULT '',
        residence TEXT DEFAULT '',
        current_detachment_id INTEGER,
        join_date TEXT NOT NULL,
        phone_number TEXT,
        evaluation_and_notes TEXT DEFAULT '',
        FOREIGN KEY (current_detachment_id) REFERENCES detachments (id) ON DELETE SET NULL
    );
    """)

    # 3. جدول سجل حركات النقل (Movement_Log)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movement_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_military_id TEXT NOT NULL,
        from_detachment_id INTEGER,
        to_detachment_id INTEGER NOT NULL,
        effective_date TEXT NOT NULL,
        notes TEXT DEFAULT '',
        FOREIGN KEY (technician_military_id) REFERENCES technicians (military_id) ON DELETE CASCADE,
        FOREIGN KEY (from_detachment_id) REFERENCES detachments (id) ON DELETE SET NULL,
        FOREIGN KEY (to_detachment_id) REFERENCES detachments (id) ON DELETE CASCADE
    );
    """)

    # 4. جدول إعدادات وتخصيصات المنظومة (App Settings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        app_title TEXT NOT NULL,
        app_subtitle TEXT NOT NULL,
        sidebar_title TEXT NOT NULL,
        btn_export_label TEXT NOT NULL,
        btn_transfer_label TEXT NOT NULL,
        btn_save_shortages_label TEXT NOT NULL,
        btn_add_tech_label TEXT NOT NULL,
        columns_order_json TEXT NOT NULL
    );
    """)

    # التحقق من وجود الحقول الجديدة في جدول technicians وعمل Alter Table إن لزم (Migration)
    cursor.execute("PRAGMA table_info(technicians);")
    existing_cols = [col["name"] for col in cursor.fetchall()]

    if "primary_category" not in existing_cols:
        cursor.execute("ALTER TABLE technicians ADD COLUMN primary_category TEXT DEFAULT 'سلاح الصيانة الملكي';")
    if "current_job" not in existing_cols:
        cursor.execute("ALTER TABLE technicians ADD COLUMN current_job TEXT DEFAULT '';")
    if "residence" not in existing_cols:
        cursor.execute("ALTER TABLE technicians ADD COLUMN residence TEXT DEFAULT '';")

    # تهيئة صف الإعدادات الافتراضية إذا لم يكن موجوداً
    cursor.execute("SELECT COUNT(*) FROM app_settings WHERE id = 1;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO app_settings (id, app_title, app_subtitle, sidebar_title, btn_export_label, btn_transfer_label, btn_save_shortages_label, btn_add_tech_label, columns_order_json)
        VALUES (
            1,
            'نظام إدارة مفارز الصيانة العسكرية',
            'إدارة القوى البشرية ومرتبات مفارز المستشفيات العسكرية بالمحافظات',
            'شعبة الصيانة والتشغيل',
            '📥 تصدير الكشف إلى Excel',
            '🔄 تنفيذ وتوثيق حركة النقل',
            '💾 حفظ وتحديث النواقص',
            '💾 حفظ وتسجيل الفني',
            ?
        );
        """, (json.dumps(DEFAULT_TECH_COLUMNS, ensure_ascii=False),))

    conn.commit()
    conn.close()

    # التحقق من وجود بيانات أولية
    seed_if_empty(db_path)

def seed_if_empty(db_path=DB_NAME):
    """حقن بيانات تجريبية موسعة تشمل الصنف والسكن والمهنة"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM detachments;")
    count = cursor.fetchone()[0]

    if count == 0:
        # 1. إضافة المستشفيات والمفارز
        hospitals_data = [
            (
                "مستشفى الأمير راشد بن الحسن العسكري",
                "إربد",
                "رئيس رقباء",
                "محمد خليل عبيدات",
                "0772123456",
                "بحاجة ماسة إلى عدد (2) فني تكييف وتبريد متخصص في غرف العمليات، ونقص فني مولدات ضغط عالي.",
                "مفرزة إقليم الشمال - تغطية شاملة لجميع أقسام الجراحة والباطني."
            ),
            (
                "مستشفى الأمير علي بن الحسين العسكري",
                "الكرك",
                "وكيل أول",
                "أحمد سالم الطراونة",
                "0773987654",
                "نقص فني تمديدات صحية وشبكات مياه مركزية لفرع الطوارئ الجديد.",
                "مفرزة إقليم الجنوب - جاهزية فنية مستقرة وجدول مناوبات منتظم."
            ),
            (
                "مستشفى الأمير هاشم بن الحسين العسكري",
                "الزرقاء",
                "وكيل",
                "خالد محمود الزيود",
                "0775551234",
                "المفرزة مكتملة العدد حالياً ولا توجد نواقص حرجة لهذا الشهر.",
                "مفرزة الوسط - تم إنهاء صيانة وحدات التبريد المركزية بنجاح."
            ),
            (
                "مستشفى الأميرة هيا بنت الحسين العسكري",
                "جرش / عجلون",
                "رقيب أول",
                "طارق إبراهيم القضاة",
                "0778889900",
                "بحاجة إلى عدد (1) فني كهرباء قوى ومحولات للوردية الليلية.",
                "مفرزة مشتركة تغطي محافظة جرش ومحافظة عجلون بكفاءة عالية."
            ),
            (
                "مستشفى الملكة علياء العسكري",
                "عمان",
                "وكيل أول",
                "عمر يوسف العدوان",
                "0771122334",
                "بحاجة إلى دعم إضافي بفني إنشائي عام لأعمال ترميم الأجنحة القديمة.",
                "المستشفى الميداني والإسناد الهندسي المركزي."
            )
        ]

        cursor.executemany("""
        INSERT INTO detachments (hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, hospitals_data)
        conn.commit()

        # جلب المعرفات للمفارز
        cursor.execute("SELECT id, hospital_name FROM detachments;")
        hospitals = {row["hospital_name"]: row["id"] for row in cursor.fetchall()}

        # 2. إضافة الفنيين الأوليين مع الصنف الأساسي ومكان السكن والمهنة الحالية
        technicians_data = [
            # مستشفى الأمير راشد (إربد)
            ("984512", "رقيب أول", "عبدالله محمود الخصاونة", "تكييف وتبريد", "سلاح الصيانة الملكي", "فني تكييف مركزي وشيلرات", "إربد - لواء بني عبيد (إيدون)", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-01-15", "0795111222", "فني ممتاز، متميز في صيانة الشيلرات المركزية ومحطات الأكسجين."),
            ("874120", "رقيب", "عمر سامي بني هاني", "كهرباء قوى ومحولات", "سلاح الصيانة الملكي", "كهربائي لوحات توزيع ومحولات", "إربد - كفر يوبا", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-06-01", "0788222333", "ملتزم جداً وخبرة ممتازة في لوحات التوزيع الرئيسية."),
            ("652198", "عريف", "سامر فؤاد بطاينة", "شبكات مياه وصحي", "الخدمات الطبية الملكية", "فني تمديدات ومضخات تحلية", "إربد - حكما", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2024-02-10", "0777333444", "أداء جيد، يتابع مضخات المياه العذبة ومحطة التحلية."),

            # مستشفى الأمير علي (الكرك)
            ("741852", "رقيب أول", "حمزة نايف المجالي", "كهرباء قوى ومحولات", "سلاح الصيانة الملكي", "مسؤول صيانة مولدات الطوارئ", "الكرك - لواء القصر", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2022-11-01", "0776444555", "كفاءة فنية عالية، يدير لوحات الطوارئ والمولدات الاحتياطية بنجاح."),
            ("963258", "عريف", "ليث خالد الصرايرة", "تكييف وتبريد", "سلاح الهندسة الملكي", "فني سبليت وغرف عناية حثيثة", "الكرك - مؤتة", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2023-09-15", "0799555666", "متخصص في وحدات السبليت وغرف العناية الحثيثة."),

            # مستشفى الأمير هاشم (الزرقاء)
            ("852963", "وكيل", "حسام جمال الغويري", "تكييف وتبريد", "سلاح الصيانة الملكي", "رئيس ورشة التكييف والميكانيك", "الزرقاء - حي معصوم", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2021-08-20", "0785666777", "أقدم فني بالمفرزة، خبرة واسعة في جميع أنظمة التبريد والميكانيك."),
            ("369258", "رقيب", "يزن مخلد العموش", "كهرباء قوى ومحولات", "سلاح الصيانة الملكي", "فني كهرباء عامة وطوارئ", "المفرق - بلعما", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-03-01", "0774777888", "سرعة استجابة عالية للأعطال الكهربائية الطارئة."),
            ("147852", "جندي أول", "معاذ علي الحنيطي", "شبكات مياه وصحي", "الخدمات الطبية الملكية", "سباك صحي ومتابعة خزانات", "عمان - سحاب", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2024-01-10", "0798888999", "فني واعد، منضبط ويؤدي المهام بدقة."),
            ("258147", "عريف", "براء فيصل الخلايلة", "إنشائي عام", "سلاح الصيانة الملكي", "فني أعمال قواطع ودهان", "الزرقاء - الهاشمية", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-11-20", "0771999000", "أعمال دهان وصيانة عامة للأبواب والقواطع."),

            # مستشفى الأميرة هيا (جرش / عجلون)
            ("357159", "رقيب", "أنس بسام العتوم", "تكييف وتبريد", "سلاح الصيانة الملكي", "فني صيانة غسيل كلى وتبريد", "جرش - سوف", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2023-05-12", "0789111333", "مسؤول صيانة قسم غسيل الكلى والعناية الحثيثة."),
            ("951357", "عريف", "مؤمن أحمد الزغول", "إنشائي عام", "سلاح الهندسة الملكي", "فني جبس بورد وألمنيوم", "عجلون - عنجرة", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2024-04-01", "0772222444", "ملم بأعمال الصيانة الإنشائية والجبس بورد والألمنيوم."),

            # مستشفى الملكة علياء (عمان)
            ("159357", "رقيب أول", "رامي ناصر الحديد", "كهرباء قوى ومحولات", "سلاح الصيانة الملكي", "خبير صيانة أنظمة UPS وتحكم", "عمان - القويسمة", hospitals["مستشفى الملكة علياء العسكري"], "2022-04-10", "0793333555", "خبير صيانة أنظمة UPS والمحولات الرئيسية."),
            ("753951", "رقيب", "جهاد توفيق المناصير", "شبكات مياه وصحي", "الخدمات الطبية الملكية", "مشرف غلايات بخار وشبكات صرف", "عمان - مرج الحمام", hospitals["مستشفى الملكة علياء العسكري"], "2023-07-22", "0784444666", "يشرف على شبكات الصرف وغلايات البخار المركزية.")
        ]

        cursor.executemany("""
        INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, technicians_data)
        conn.commit()

        # 3. إضافة سجلات حركات نقل تجريبية سابقة
        movements_data = [
            ("984512", hospitals["مستشفى الملكة علياء العسكري"], hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-01-15", "نقل لسد النقص في صيانة التكييف المركزي بإربد وتقريب مكان السكن"),
            ("852963", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2021-08-20", "نقل بناءً على مقتضيات المصلحة العامة والخبرة الميدانية"),
            ("357159", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2023-05-12", "نقل لتعزيز كادر المفرزة في مستشفى الأميرة هيا")
        ]

        cursor.executemany("""
        INSERT INTO movement_log (technician_military_id, from_detachment_id, to_detachment_id, effective_date, notes)
        VALUES (?, ?, ?, ?, ?);
        """, movements_data)
        conn.commit()

    conn.close()

# --- إدارة الإعدادات (Settings API) ---

def get_app_settings():
    """جلب إعدادات المنظومة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM app_settings WHERE id = 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        try:
            d["columns_order"] = json.loads(d["columns_order_json"])
        except Exception:
            d["columns_order"] = DEFAULT_TECH_COLUMNS
        return d
    return {
        "app_title": "نظام إدارة مفارز الصيانة العسكرية",
        "app_subtitle": "إدارة القوى البشرية ومرتبات مفارز المستشفيات العسكرية بالمحافظات",
        "sidebar_title": "شعبة الصيانة والتشغيل",
        "btn_export_label": "📥 تصدير الكشف إلى Excel",
        "btn_transfer_label": "🔄 تنفيذ وتوثيق حركة النقل",
        "btn_save_shortages_label": "💾 حفظ وتحديث النواقص",
        "btn_add_tech_label": "💾 حفظ وتسجيل الفني",
        "columns_order": DEFAULT_TECH_COLUMNS
    }

def update_app_settings(app_title, app_subtitle, sidebar_title, btn_export_label, btn_transfer_label, btn_save_shortages_label, btn_add_tech_label):
    """تحديث نصوص وهوية المنظومة ومسميات الأزرار"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE app_settings
    SET app_title = ?, app_subtitle = ?, sidebar_title = ?, btn_export_label = ?, btn_transfer_label = ?, btn_save_shortages_label = ?, btn_add_tech_label = ?
    WHERE id = 1;
    """, (app_title, app_subtitle, sidebar_title, btn_export_label, btn_transfer_label, btn_save_shortages_label, btn_add_tech_label))
    conn.commit()
    conn.close()
    return True

def update_columns_order(order_list):
    """تحديث الترتيب المخصص لأعمدة جدول الفنيين"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE app_settings
    SET columns_order_json = ?
    WHERE id = 1;
    """, (json.dumps(order_list, ensure_ascii=False),))
    conn.commit()
    conn.close()
    return True

def reset_columns_order():
    """إعادة ضبط ترتيب الأعمدة للترتيب الافتراضي"""
    return update_columns_order(DEFAULT_TECH_COLUMNS)

# --- دوال الاستعلام والبيانات (Queries) ---

def get_detachments_list():
    """إرجاع قائمة بجميع المفارز مع قائد المفرزة (الأعلى رتبة دائماً)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT d.*, COUNT(t.military_id) as technicians_count
    FROM detachments d
    LEFT JOIN technicians t ON d.id = t.current_detachment_id
    GROUP BY d.id
    ORDER BY d.hospital_name ASC;
    """)
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # تحديث قائد المفرزة ليكون الأعلى رتبة دائماً بين مرتباتها
    for r in rows:
        cmd = get_detachment_commander(r["id"])
        if cmd:
            r["supervisor_rank"] = cmd["rank"]
            r["supervisor_name"] = cmd["name"]
            if cmd.get("phone"):
                r["contact_phone"] = cmd["phone"]
                
    return rows

def get_detachments_df():
    """إرجاع جدول المفارز كـ DataFrame مع إحصائية عدد الفنيين"""
    conn = get_db_connection()
    query = """
    SELECT 
        d.id as "المعرف",
        d.hospital_name as "اسم المستشفى العسكري",
        d.governorate as "المحافظة",
        d.supervisor_rank as "رتبة قائد المفرزة",
        d.supervisor_name as "اسم قائد المفرزة",
        d.contact_phone as "هاتف التواصل",
        COUNT(t.military_id) as "عدد الفنيين",
        d.staffing_shortages as "النواقص والاحتياجات البشرية",
        d.notes as "ملاحظات عامة"
    FROM detachments d
    LEFT JOIN technicians t ON d.id = t.current_detachment_id
    GROUP BY d.id
    ORDER BY d.hospital_name ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_detachment_by_id(detachment_id):
    """إرجاع بيانات مفرزة محددة مع تحديد قائد المفرزة تلقائياً كأعلى رتبة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detachments WHERE id = ?;", (detachment_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    d_dict = dict(row)
    
    # قائد المفرزة هو الأعلى رتبة دائماً بين مرتبات المفرزة
    cmd = get_detachment_commander(detachment_id)
    if cmd:
        d_dict["supervisor_rank"] = cmd["rank"]
        d_dict["supervisor_name"] = cmd["name"]
        d_dict["commander_mil_id"] = cmd["military_id"]
        if cmd.get("phone"):
            d_dict["contact_phone"] = cmd["phone"]
            
    return d_dict

def update_detachment_shortages(detachment_id, shortages_text):
    """تحديث حقل النواقص والاحتياجات البشرية للمفرزة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE detachments SET staffing_shortages = ? WHERE id = ?;", (shortages_text, detachment_id))
    conn.commit()
    conn.close()
    return True

def update_detachment_info(detachment_id, hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, notes):
    """تحديث البيانات الأساسية للمفرزة / المستشفى"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE detachments 
    SET hospital_name = ?, governorate = ?, supervisor_rank = ?, supervisor_name = ?, contact_phone = ?, notes = ?
    WHERE id = ?;
    """, (hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, notes, detachment_id))
    conn.commit()
    conn.close()
    return True

def add_detachment(hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages="", notes=""):
    """إضافة مفرزة / مستشفى عسكري جديد"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO detachments (hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages, notes))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def delete_detachment(detachment_id):
    """حذف مفرزة / مستشفى من المنظومة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # نقل أي فنيين مرتبطين بها إلى غير محدد
        cursor.execute("UPDATE technicians SET current_detachment_id = NULL WHERE current_detachment_id = ?;", (detachment_id,))
        cursor.execute("DELETE FROM detachments WHERE id = ?;", (detachment_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

# جدول أوزان الأقدمية للرتب العسكرية من الأعلى إلى الأدنى
MILITARY_RANK_SENIORITY = {
    "مقدم": 90,
    "رائد": 80,
    "نقيب": 70,
    "ملازم/1": 60,
    "ملازم أول": 60,
    "ملازم 1": 60,
    "ملازم": 50,
    "وكيل أول": 40,
    "وكيل 1": 40,
    "وكيل": 30,
    "رقيب أول": 20,
    "رقيب 1": 20,
    "رقيب": 15,
    "عريف": 10,
    "جندي أول": 5,
    "جندي 1": 5,
    "جندي مكلف": 3,
    "جندي": 3,
    "مكلف": 3,
    "مدني": 1,
    "مستخدم مدني": 1
}

def get_rank_weight(rank_str):
    """إرجاع وزن الأقدمية العسكرية للرتبة للترتيب الدقيق"""
    if not rank_str:
        return -1
    clean_r = str(rank_str).strip()
    return MILITARY_RANK_SENIORITY.get(clean_r, 0)

def get_mil_id_sort_key(mil_id_val):
    """إرجاع الرقم العسكري كرقم صحيح للترتيب العددي الأقدم (الرقم الأقل أولاً)"""
    if mil_id_val is None or pd.isna(mil_id_val):
        return 999999999
    try:
        digits = ''.join(filter(str.isdigit, str(mil_id_val)))
        return int(digits) if digits else 999999999
    except Exception:
        return 999999999

def get_detachment_commander(detachment_id):
    """
    تحديد قائد المفرزة تلقائياً وهو دائماً صاحب الرتبة الأعلى والأقدم رقماً عسكرياً بين مرتبات المفرزة
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.military_id, t.rank, t.full_name, t.phone_number
    FROM technicians t
    WHERE t.current_detachment_id = ?;
    """, (detachment_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if rows:
        for r in rows:
            r["_rank_weight"] = get_rank_weight(r["rank"])
            r["_mil_sort"] = get_mil_id_sort_key(r["military_id"])
            
        rows.sort(key=lambda x: (x["_rank_weight"], -x["_mil_sort"]), reverse=True)
        top = rows[0]
        return {
            "rank": top["rank"],
            "name": top["full_name"],
            "military_id": top["military_id"],
            "phone": top.get("phone_number") or "",
            "is_auto": True
        }
        
    return None

def get_all_technicians_df(apply_custom_columns=True):
    """إرجاع جدول جميع الفنيين مرتباً حسب الرتبة العسكرية (من الأعلى للأدنى) ثم الرقم العسكري الأقل"""
    conn = get_db_connection()
    query = """
    SELECT 
        t.military_id as "الرقم العسكري",
        t.rank as "الرتبة",
        t.full_name as "الاسم الرباعي",
        COALESCE(t.specialty, '') as "الصنف",
        COALESCE(t.current_job, '') as "المهنة الحالية",
        COALESCE(d.hospital_name, 'غير محدد') as "المستشفى الحالي",
        COALESCE(d.governorate, 'غير محدد') as "المحافظة",
        COALESCE(t.residence, '') as "مكان السكن",
        t.join_date as "تاريخ الالتحاق بالمفرزة",
        t.phone_number as "رقم الهاتف",
        t.evaluation_and_notes as "الملاحظات والتقييم الفني",
        t.current_detachment_id as detachment_id
    FROM technicians t
    LEFT JOIN detachments d ON t.current_detachment_id = d.id;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if not df.empty:
        # احتساب مدة الخدمة بالمفرزة
        df["مدة الخدمة بالمفرزة"] = df["تاريخ الالتحاق بالمفرزة"].apply(calculate_duration_arabic)

        # الترتيب الافتراضي: الرتبة العسكرية (من الأعلى للأدنى)، ثم الرقم العسكري الأقل
        df["_rank_weight"] = df["الرتبة"].apply(get_rank_weight)
        df["_mil_sort"] = df["الرقم العسكري"].apply(get_mil_id_sort_key)
        df = df.sort_values(by=["_rank_weight", "_mil_sort"], ascending=[False, True]).reset_index(drop=True)
        df = df.drop(columns=["_rank_weight", "_mil_sort"], errors="ignore")

        if apply_custom_columns:
            settings = get_app_settings()
            ordered_cols = [col for col in settings.get("columns_order", DEFAULT_TECH_COLUMNS) if col in df.columns]
            # التأكد من إبقاء detachment_id للفلترة
            if "detachment_id" in df.columns and "detachment_id" not in ordered_cols:
                ordered_cols.append("detachment_id")
            df = df[ordered_cols]

    return df

def get_technicians_by_detachment_df(detachment_id, apply_custom_columns=True):
    """إرجاع فنيي مفرزة محددة كـ DataFrame مع الحقول الموسعة"""
    all_df = get_all_technicians_df(apply_custom_columns=False)
    if all_df.empty:
        return pd.DataFrame()
    filtered = all_df[all_df["detachment_id"] == detachment_id].copy()
    
    if apply_custom_columns:
        settings = get_app_settings()
        ordered_cols = [col for col in settings.get("columns_order", DEFAULT_TECH_COLUMNS) if col in filtered.columns]
        filtered = filtered[ordered_cols]
    else:
        filtered = filtered.drop(columns=["detachment_id"], errors="ignore")
        
    return filtered

def get_technician_by_id(military_id):
    """إرجاع بيانات فني محدد برقمه العسكري مع كافة الحقول"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT t.*, d.hospital_name, d.governorate
    FROM technicians t
    LEFT JOIN detachments d ON t.current_detachment_id = d.id
    WHERE t.military_id = ?;
    """, (military_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_technician(military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes):
    """إضافة فني جديد إلى المنظومة مع الحقول الجديدة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes))
        conn.commit()
        success = True
        err = None
    except sqlite3.IntegrityError:
        success = False
        err = "الرقم العسكري مسجل مسبقاً في المنظومة."
    except Exception as e:
        success = False
        err = str(e)
    finally:
        conn.close()
    return success, err

def update_technician(military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes):
    """تعديل بيانات فني موجود بالكامل"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE technicians 
        SET rank = ?, full_name = ?, specialty = ?, primary_category = ?, current_job = ?, residence = ?, current_detachment_id = ?, join_date = ?, phone_number = ?, evaluation_and_notes = ?
        WHERE military_id = ?;
        """, (rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes, military_id))
        conn.commit()
        success = True
        err = None
    except Exception as e:
        success = False
        err = str(e)
    finally:
        conn.close()
    return success, err

def delete_technician(military_id):
    """حذف فني من المنظومة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM technicians WHERE military_id = ?;", (military_id,))
        conn.commit()
        success = True
    except Exception:
        success = False
    finally:
        conn.close()
    return success

def transfer_technician(military_id, to_detachment_id, effective_date, notes=""):
    """
    إجراء حركة نقل لفني:
    1. قراءة المفرزة الحالية.
    2. تحديث المفرزة الحالية وتاريخ الالتحاق للفني.
    3. تسجيل الحركة في جدول Movement_Log.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT current_detachment_id FROM technicians WHERE military_id = ?;", (military_id,))
        row = cursor.fetchone()
        if not row:
            return False, "الفني غير موجود في المنظومة."
        
        from_detachment_id = row["current_detachment_id"]

        if from_detachment_id == to_detachment_id:
            return False, "لا يمكن النقل إلى نفس المفرزة الحالية."

        # تحديث بيانات الفني
        cursor.execute("""
        UPDATE technicians 
        SET current_detachment_id = ?, join_date = ?
        WHERE military_id = ?;
        """, (to_detachment_id, effective_date, military_id))

        # توثيق حركة النقل في السجل
        cursor.execute("""
        INSERT INTO movement_log (technician_military_id, from_detachment_id, to_detachment_id, effective_date, notes)
        VALUES (?, ?, ?, ?, ?);
        """, (military_id, from_detachment_id, to_detachment_id, effective_date, notes))

        conn.commit()
        return True, "تم توثيق حركة النقل وتحديث مرتبات المفرزة بنجاح."
    except Exception as e:
        conn.rollback()
        return False, str(e)
    finally:
        conn.close()

def get_movement_logs_df():
    """إرجاع سجل حركات النقل كـ DataFrame مع أسماء المستشفيات والرتب"""
    conn = get_db_connection()
    query = """
    SELECT 
        m.id as "رقم القيد",
        m.effective_date as "تاريخ النقل",
        t.military_id as "الرقم العسكري",
        t.rank as "الرتبة",
        t.full_name as "اسم الفني",
        COALESCE(t.specialty, '') as "الصنف",
        COALESCE(t.current_job, '') as "المهنة الحالية",
        COALESCE(d_from.hospital_name, 'المركز / غير محدد') as "من مستشفى",
        COALESCE(d_to.hospital_name, 'غير محدد') as "إلى مستشفى",
        m.notes as "ملاحظات أمر النقل"
    FROM movement_log m
    LEFT JOIN technicians t ON m.technician_military_id = t.military_id
    LEFT JOIN detachments d_from ON m.from_detachment_id = d_from.id
    LEFT JOIN detachments d_to ON m.to_detachment_id = d_to.id
    ORDER BY m.id DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_dashboard_stats():
    """إرجاع إحصائيات سريعة للوحة المؤشرات"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM technicians;")
    total_technicians = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detachments;")
    total_detachments = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM movement_log;")
    total_movements = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM detachments WHERE TRIM(COALESCE(staffing_shortages, '')) != '';")
    detachments_with_shortages = cursor.fetchone()[0]

    # التوزيع حسب الصنف
    cursor.execute("""
    SELECT specialty as specialty, COUNT(*) as count 
    FROM technicians 
    GROUP BY specialty 
    ORDER BY count DESC;
    """)
    specialty_distribution = [dict(r) for r in cursor.fetchall()]

    # التوزيع حسب المستشفيات
    cursor.execute("""
    SELECT d.hospital_name, d.governorate, COUNT(t.military_id) as count
    FROM detachments d
    LEFT JOIN technicians t ON d.id = t.current_detachment_id
    GROUP BY d.id
    ORDER BY count DESC;
    """)
    hospital_distribution = [dict(r) for r in cursor.fetchall()]

    # قائمة النواقص
    cursor.execute("""
    SELECT id, hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages
    FROM detachments
    WHERE TRIM(COALESCE(staffing_shortages, '')) != ''
    ORDER BY id ASC;
    """)
    shortages_list = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        "total_technicians": total_technicians,
        "total_detachments": total_detachments,
        "total_movements": total_movements,
        "detachments_with_shortages": detachments_with_shortages,
        "specialty_distribution": specialty_distribution,
        "hospital_distribution": hospital_distribution,
        "shortages_list": shortages_list
    }

def clean_excel_value(val):
    """تنظيف القيم المستخرجة من الإكسل ومعالجة الأرقام والكسور"""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
    return val_str

def clean_excel_date(val):
    """تنظيف وتحويل التواريخ من الإكسل إلى صيغة YYYY-MM-DD"""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return date.today().isoformat()
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.strftime("%Y-%m-%d")
    try:
        parsed = pd.to_datetime(val)
        return parsed.strftime("%Y-%m-%d")
    except Exception:
        return date.today().isoformat()

def generate_technicians_template():
    """إنشاء قالب Excel قياسي لتعبئة واستيراد مرتبات الفنيين"""
    import io
    sample_data = [
        {
            "الرقم العسكري": "100200",
            "الرتبة": "رقيب",
            "الاسم الرباعي": "محمد أحمد إبراهيم خليل",
            "الصنف": "تكييف وتبريد",
            "المهنة الحالية": "مسؤول صيانة التكييف المركزي",
            "مكان السكن": "عمان - طبربور",
            "تاريخ الالتحاق بالمفرزة": "2023-05-10",
            "رقم الهاتف": "0791234567",
            "الملاحظات والتقييم الفني": "فني متميز، جاهزية عالية"
        },
        {
            "الرقم العسكري": "300400",
            "الرتبة": "عريف",
            "الاسم الرباعي": "خالد محمود عبد الله يوسف",
            "الصنف": "كهرباء قوى ومحولات",
            "المهنة الحالية": "فني محولات ولوحات توزيع",
            "مكان السكن": "الزرقاء - حي معصوم",
            "تاريخ الالتحاق بالمفرزة": "2024-01-15",
            "رقم الهاتف": "0789876543",
            "الملاحظات والتقييم الفني": "مناوب لوردية الطوارئ"
        }
    ]
    df_template = pd.DataFrame(sample_data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_template.to_excel(writer, index=False, sheet_name="قالب_الفنيين")
    return output.getvalue()

def detect_column_mapping(df_columns):
    """
    اكتشاف ومطابقة أعمدة ملف الإكسل مع حقول المنظومة بدقة (تطابق تام أولاً ثم جزئي)
    """
    column_mapping_aliases = {
        "military_id": ["الرقم العسكري", "رقم عسكري", "الرقم", "ر.ع", "ر ع", "military_id", "id", "الرقم_العسكري"],
        "rank": ["الرتبة", "رتبة", "الرتبة العسكرية", "rank"],
        "full_name": ["الاسم الرباعي", "الاسم", "اسم الفني", "الاسم الكامل", "اسم الفرد", "الاسم الثلاثي", "full_name", "name"],
        "specialty": ["الصنف", "صنف", "الصنف الفني", "التخصص الفني", "التخصص", "تخصص", "الاختصاص", "اختصاص", "المهنة الفنية", "المسمى الفني", "الحرفة", "الصنعة", "specialty", "category"],
        "current_job": ["المهنة الحالية", "المهنة", "الوظيفة الحالية", "الوظيفة", "طبيعة العمل", "الواجب", "المهنة الفعلية", "current_job", "job"],
        "residence": ["مكان السكن", "السكن", "العنوان", "مكان الإقامة", "المنطقة", "residence", "address"],
        "join_date": ["تاريخ الالتحاق بالمفرزة", "تاريخ الالتحاق", "تاريخ التعيين", "تاريخ النقل", "تاريخ الانفكاك", "التاريخ", "join_date"],
        "phone_number": ["رقم الهاتف", "الهاتف", "رقم الموبايل", "الموبايل", "رقم الجوال", "خلوي", "phone_number", "phone"],
        "evaluation_and_notes": ["الملاحظات والتقييم الفني", "الملاحظات", "ملاحظات", "التقييم", "البيان", "evaluation_and_notes", "notes"]
    }
    
    normalized_cols = {str(col).strip(): col for col in df_columns}
    col_map = {}
    
    # 1. المرحلة الأولى: البحث عن التطابق التام (Exact Match)
    for target_key, aliases in column_mapping_aliases.items():
        for alias in aliases:
            for actual_clean, actual_orig in normalized_cols.items():
                if alias.lower() == actual_clean.lower():
                    col_map[target_key] = actual_orig
                    break
            if target_key in col_map:
                break
                
    # 2. المرحلة الثانية: البحث عن التطابق الجزئي للحقول غير المكتشفة
    for target_key, aliases in column_mapping_aliases.items():
        if target_key in col_map:
            continue
        for alias in aliases:
            for actual_clean, actual_orig in normalized_cols.items():
                if alias.lower() in actual_clean.lower() and actual_orig not in col_map.values():
                    col_map[target_key] = actual_orig
                    break
            if target_key in col_map:
                break
                
    return col_map

def import_technicians_from_df(df, detachment_id, update_existing=True, custom_col_map=None):
    """
    استيراد مرتبات وفنيين من DataFrame إلى مفرزة محددة مع مطابقة مخصصة وذكية للأعمدة
    """
    col_map = custom_col_map if custom_col_map else detect_column_mapping(df.columns)

    if not col_map.get("military_id") or not col_map.get("full_name"):
        return {
            "success": False,
            "total": 0,
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "errors": ["الملف لا يحتوي على عمود محدد لـ (الرقم العسكري) أو (الاسم الرباعي). يرجى التحقق من مطابقة الأعمدة."]
        }

    conn = get_db_connection()
    cursor = conn.cursor()

    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    for index, row in df.iterrows():
        row_num = index + 2  # رقم الصف في الإكسل
        
        mil_id = clean_excel_value(row.get(col_map.get("military_id", "")))
        if not mil_id:
            skipped_count += 1
            errors.append(f"الصف {row_num}: تم تخطيه لعدم وجود رقم عسكري.")
            continue

        name = clean_excel_value(row.get(col_map.get("full_name", "")))
        if not name:
            skipped_count += 1
            errors.append(f"الصف {row_num} (الرقم {mil_id}): تم تخطيه لعدم وجود اسم.")
            continue

        rank = clean_excel_value(row.get(col_map.get("rank", ""))) if col_map.get("rank") else ""
        category = clean_excel_value(row.get(col_map.get("primary_category", ""))) if col_map.get("primary_category") else ""
        specialty = clean_excel_value(row.get(col_map.get("specialty", ""))) if col_map.get("specialty") else ""
        job = clean_excel_value(row.get(col_map.get("current_job", ""))) if col_map.get("current_job") else ""
        residence = clean_excel_value(row.get(col_map.get("residence", ""))) if col_map.get("residence") else ""
        join_d = clean_excel_date(row.get(col_map.get("join_date", ""))) if col_map.get("join_date") else date.today().isoformat()
        phone = clean_excel_value(row.get(col_map.get("phone_number", ""))) if col_map.get("phone_number") else ""
        notes = clean_excel_value(row.get(col_map.get("evaluation_and_notes", ""))) if col_map.get("evaluation_and_notes") else ""

        # التبادل الذكي بين التخصص والمهنة إذا كان أحدهما فقط متوفراً في الملف
        if not specialty and job:
            specialty = job
        elif not job and specialty:
            job = specialty

        # التحقق هل الفني موجود مسبقاً
        cursor.execute("SELECT * FROM technicians WHERE military_id = ?;", (mil_id,))
        existing = cursor.fetchone()

        try:
            if existing:
                if update_existing:
                    final_rank = rank or existing["rank"]
                    final_name = name or existing["full_name"]
                    final_spec = specialty or existing["specialty"]
                    final_cat = category or existing["primary_category"]
                    final_job = job or existing["current_job"]
                    final_res = residence or existing["residence"]
                    final_join = join_d or existing["join_date"]
                    final_phone = phone or existing["phone_number"]
                    final_notes = notes or existing["evaluation_and_notes"]

                    cursor.execute("""
                    UPDATE technicians
                    SET rank = ?, full_name = ?, specialty = ?, primary_category = ?, current_job = ?, 
                        residence = ?, current_detachment_id = ?, join_date = ?, phone_number = ?, evaluation_and_notes = ?
                    WHERE military_id = ?;
                    """, (final_rank, final_name, final_spec, final_cat, final_job, final_res, detachment_id, final_join, final_phone, final_notes, mil_id))
                    updated_count += 1
                else:
                    skipped_count += 1
                    errors.append(f"الصف {row_num} (الرقم {mil_id}): مسجل مسبقاً وتم تخطيه بناءً على خيار عدم التحديث.")
            else:
                final_rank = rank or "جندي أول"
                final_spec = specialty or "صيانة عامة"
                final_cat = category or "سلاح الصيانة الملكي"

                cursor.execute("""
                INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (mil_id, final_rank, name, final_spec, final_cat, job, residence, detachment_id, join_d, phone, notes))
                inserted_count += 1
        except Exception as e:
            skipped_count += 1
            errors.append(f"الصف {row_num} (الرقم {mil_id}): خطأ أثناء الحفظ ({str(e)})")

    conn.commit()
    conn.close()

    return {
        "success": True,
        "total": len(df),
        "inserted": inserted_count,
        "updated": updated_count,
        "skipped": skipped_count,
        "errors": errors
    }
