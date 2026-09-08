"""
قاعدة بيانات نظام إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية
Database models, SQLite operations, Settings management, and Schema Migration.
"""

import sqlite3
import os
import io
import json
import hashlib
import secrets
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

    # 5. جدول سجلات الموجود الصباحي اليومي للمفارز (Daily Roll Call)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_roll_call (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        detachment_id INTEGER NOT NULL,
        roll_call_date TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'saved',
        saved_by_rank TEXT NOT NULL,
        saved_by_name TEXT NOT NULL,
        saved_at TEXT NOT NULL,
        total_strength INTEGER DEFAULT 0,
        present_count INTEGER DEFAULT 0,
        leave_count INTEGER DEFAULT 0,
        sick_count INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        FOREIGN KEY (detachment_id) REFERENCES detachments (id) ON DELETE CASCADE,
        UNIQUE(detachment_id, roll_call_date)
    );
    """)

    # 6. جدول تفاصيل وبنود الموجود الصباحي لكل فرد (Daily Roll Call Entries)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_roll_call_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_call_id INTEGER NOT NULL,
        military_id TEXT NOT NULL,
        rank TEXT NOT NULL,
        full_name TEXT NOT NULL,
        specialty TEXT,
        status TEXT NOT NULL,
        notes TEXT DEFAULT '',
        FOREIGN KEY (roll_call_id) REFERENCES daily_roll_call (id) ON DELETE CASCADE
    );
    """)

    # 7. جدول المستخدمين وحسابات الدخول والصلاحيات (Users & RBAC)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        rank TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'قائد مفرزة',
        detachment_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at TEXT NOT NULL,
        last_login TEXT,
        permissions_json TEXT DEFAULT '{}',
        FOREIGN KEY (detachment_id) REFERENCES detachments (id) ON DELETE SET NULL
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

    # ضمان تعيين المقدم المهندسة منار قائداً لمفرزة مستشفى الأمير علي بن الحسين (الكرك)
    cursor.execute("SELECT id FROM detachments WHERE hospital_name LIKE '%علي%' OR governorate = 'الكرك' LIMIT 1;")
    karak_det = cursor.fetchone()
    karak_det_id = karak_det[0] if karak_det else 2

    cursor.execute("""
    UPDATE detachments 
    SET supervisor_rank = 'مقدم', supervisor_name = 'المهندسة منار', contact_phone = '0773987654'
    WHERE id = ?;
    """, (karak_det_id,))

    cursor.execute("SELECT COUNT(*) FROM technicians WHERE military_id = '20002' OR full_name LIKE '%منار%';")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT OR REPLACE INTO technicians (
            military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes
        ) VALUES (
            '20002', 'مقدم', 'المهندسة منار', 'هندسة صيانة وتشغيل', 'سلاح الصيانة الملكي', 'قائد مفرزة مستشفى الأمير علي', 'الكرك', ?, '2020-01-01', '0773987654', 'قائد مفرزة مستشفى الأمير علي بن الحسين العسكري'
        );
        """, (karak_det_id,))

    conn.commit()
    conn.close()

    # مزامنة وتثبيت المفارز والفنيين المعتمدين دائماً
    sync_official_master_data(db_path)
    # تهيئة وتحديث الحسابات الافتراضية للمستخدمين
    seed_default_users(db_path)

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
                "رائد",
                "موسى حسن الشناق",
                "0772233445",
                "بحاجة ماسة إلى عدد (2) فني تكييف وتبريد متخصص في غرف العمليات، ونقص فني مولدات ضغط عالي.",
                "مفرزة إقليم الشمال - تغطية شاملة لجميع أقسام الجراحة والباطني."
            ),
            (
                "مستشفى الأمير علي بن الحسين العسكري",
                "الكرك",
                "مقدم",
                "المهندسة منار",
                "0773987654",
                "نقص فني تمديدات صحية وشبكات مياه مركزية لفرع الطوارئ الجديد.",
                "مفرزة إقليم الجنوب - إشراف هندسي وعسكري كامل وجدول مناوبات منتظم."
            ),
            (
                "مستشفى الأمير هاشم بن الحسين العسكري",
                "الزرقاء",
                "وكيل أول",
                "خالد محمود الزيود",
                "0775551234",
                "المفرزة مكتملة العدد حالياً ولا توجد نواقص حرجة لهذا الشهر.",
                "مفرزة الوسط - تم إنهاء صيانة وحدات التبريد المركزية بنجاح."
            ),
            (
                "مستشفى الأميرة هيا بنت الحسين العسكري",
                "جرش / عجلون",
                "وكيل",
                "طارق إبراهيم القضاة",
                "0778889900",
                "بحاجة إلى عدد (1) فني كهرباء قوى ومحولات للوردية الليلية.",
                "مفرزة مشتركة تغطي محافظة جرش ومحافظة عجلون بكفاءة عالية."
            ),
            (
                "مستشفى الملكة علياء العسكري",
                "عمان",
                "نقيب",
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

        # 2. إضافة الفنيين الأوليين
        technicians_data = [
            # مستشفى الأمير راشد (إربد)
            ("984512", "رقيب أول", "عبدالله محمود الخصاونة", "تكييف وتبريد", None, "فني تكييف مركزي وشيلرات", "إربد - لواء بني عبيد (إيدون)", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-01-15", "0795111222", "فني ممتاز، متميز في صيانة الشيلرات المركزية ومحطات الأكسجين."),
            ("874120", "رقيب", "عمر سامي بني هاني", "كهرباء قوى ومحولات", None, "كهربائي لوحات توزيع ومحولات", "إربد - كفر يوبا", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-06-01", "0788222333", "ملتزم جداً وخبرة ممتازة في لوحات التوزيع الرئيسية."),
            ("652198", "عريف", "سامر فؤاد بطاينة", "شبكات مياه وصحي", None, "فني تمديدات ومضخات تحلية", "إربد - حكما", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2024-02-10", "0777333444", "أداء جيد، يتابع مضخات المياه العذبة ومحطة التحلية."),

            # مستشفى الأمير علي (الكرك)
            ("741852", "رقيب أول", "حمزة نايف المجالي", "كهرباء قوى ومحولات", None, "مسؤول صيانة مولدات الطوارئ", "الكرك - لواء القصر", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2022-11-01", "0776444555", "كفاءة فنية عالية، يدير لوحات الطوارئ والمولدات الاحتياطية بنجاح."),
            ("963258", "عريف", "ليث خالد الصرايرة", "تكييف وتبريد", None, "فني سبليت وغرف عناية حثيثة", "الكرك - مؤتة", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2023-09-15", "0799555666", "متخصص في وحدات السبليت وغرف العناية الحثيثة."),

            # مستشفى الأمير هاشم (الزرقاء)
            ("852963", "وكيل", "حسام جمال الغويري", "تكييف وتبريد", None, "رئيس ورشة التكييف والميكانيك", "الزرقاء - حي معصوم", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2021-08-20", "0785666777", "أقدم فني بالمفرزة، خبرة واسعة في جميع أنظمة التبريد والميكانيك."),
            ("369258", "رقيب", "يزن مخلد العموش", "كهرباء قوى ومحولات", None, "فني كهرباء عامة وطوارئ", "المفرق - بلعما", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-03-01", "0774777888", "سرعة استجابة عالية للأعطال الكهربائية الطارئة."),
            ("147852", "جندي أول", "معاذ علي الحنيطي", "شبكات مياه وصحي", None, "سباك صحي ومتابعة خزانات", "عمان - سحاب", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2024-01-10", "0798888999", "فني واعد، منضبط ويؤدي المهام بدقة."),
            ("258147", "عريف", "براء فيصل الخلايلة", "إنشائي عام", None, "فني أعمال قواطع ودهان", "الزرقاء - الهاشمية", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-11-20", "0771999000", "أعمال دهان وصيانة عامة للأبواب والقواطع."),

            # مستشفى الأميرة هيا (جرش / عجلون)
            ("357159", "رقيب", "أنس بسام العتوم", "تكييف وتبريد", None, "فني صيانة غسيل كلى وتبريد", "جرش - سوف", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2023-05-12", "0789111333", "مسؤول صيانة قسم غسيل الكلى والعناية الحثيثة."),
            ("951357", "عريف", "مؤمن أحمد الزغول", "إنشائي عام", None, "فني جبس بورد وألمنيوم", "عجلون - عنجرة", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2024-04-01", "0772222444", "ملم بأعمال الصيانة الإنشائية والجبس بورد والألمنيوم."),

            # مستشفى الملكة علياء (عمان)
            ("159357", "رقيب أول", "رامي ناصر الحديد", "كهرباء قوى ومحولات", None, "خبير صيانة أنظمة UPS وتحكم", "عمان - القويسمة", hospitals["مستشفى الملكة علياء العسكري"], "2022-04-10", "0793333555", "خبير صيانة أنظمة UPS والمحولات الرئيسية."),
            ("753951", "رقيب", "جهاد توفيق المناصير", "شبكات مياه وصحي", None, "مشرف غلايات بخار وشبكات صرف", "عمان - مرج الحمام", hospitals["مستشفى الملكة علياء العسكري"], "2023-07-22", "0784444666", "يشرف على شبكات الصرف وغلايات البخار المركزية.")
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

    # ترحيل وتنظيف تلقائي لأي إعدادات أو بيانات قديمة تحتوي مسميات أسلحة
    try:
        c = conn.cursor()
        c.execute("UPDATE app_settings SET columns_order_json = ? WHERE id = 1;", (json.dumps(DEFAULT_TECH_COLUMNS, ensure_ascii=False),))
        c.execute("""
        UPDATE technicians 
        SET specialty = current_job 
        WHERE (specialty LIKE '%سلاح%' OR specialty LIKE '%الخدمات الطبية%' OR specialty IS NULL OR specialty = '') 
          AND current_job IS NOT NULL AND TRIM(current_job) != '';
        """)
        c.execute("UPDATE technicians SET primary_category = NULL;")
        conn.commit()
    except Exception:
        pass

    conn.close()




OFFICIAL_MASTER_DETACHMENTS = [{'id': 1, 'hospital_name': 'مستشفى الأمير راشد بن الحسن العسكري', 'governorate': 'إربد', 'supervisor_rank': 'رائد', 'supervisor_name': 'موسى حسن الشناق', 'contact_phone': '0772233445', 'staffing_shortages': 'نقص فنيين تبريد وتكييف محدث', 'notes': 'مفرزة إقليم الشمال - تغطية شاملة لجميع أقسام الجراحة والباطني.'}, {'id': 2, 'hospital_name': 'مستشفى الأمير علي بن الحسين العسكري', 'governorate': 'الكرك', 'supervisor_rank': 'مقدم', 'supervisor_name': 'المهندسة منار', 'contact_phone': '0773987654', 'staffing_shortages': 'نقص فني تمديدات صحية وشبكات مياه مركزية لفرع الطوارئ الجديد.', 'notes': 'مفرزة إقليم الجنوب - إشراف هندسي وعسكري كامل وجدول مناوبات منتظم.'}, {'id': 3, 'hospital_name': 'مستشفى الأمير هاشم بن الحسين العسكري', 'governorate': 'الزرقاء', 'supervisor_rank': 'وكيل أول', 'supervisor_name': 'خالد محمود الزيود', 'contact_phone': '0775551234', 'staffing_shortages': 'المفرزة مكتملة العدد حالياً ولا توجد نواقص حرجة لهذا الشهر.', 'notes': 'مفرزة الوسط - تم إنهاء صيانة وحدات التبريد المركزية بنجاح.'}, {'id': 4, 'hospital_name': 'مستشفى الأميرة هيا بنت الحسين العسكري', 'governorate': 'جرش / عجلون', 'supervisor_rank': 'وكيل', 'supervisor_name': 'طارق إبراهيم القضاة', 'contact_phone': '0778889900', 'staffing_shortages': 'بحاجة إلى عدد (1) فني كهرباء قوى ومحولات للوردية الليلية.', 'notes': 'مفرزة مشتركة تغطي محافظة جرش ومحافظة عجلون بكفاءة عالية.'}, {'id': 5, 'hospital_name': 'مستشفى الملكة علياء العسكري', 'governorate': 'عمان', 'supervisor_rank': 'نقيب', 'supervisor_name': 'عمر يوسف العدوان', 'contact_phone': '0771122334', 'staffing_shortages': 'بحاجة إلى دعم إضافي بفني إنشائي عام لأعمال ترميم الأجنحة القديمة.', 'notes': 'المستشفى الميداني والإسناد الهندسي المركزي.'}]

OFFICIAL_MASTER_TECHNICIANS = [{'military_id': '984512', 'rank': 'رقيب أول', 'full_name': 'عبدالله محمود الخصاونة', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 1, 'join_date': '2023-01-15', 'phone_number': '0795111222', 'evaluation_and_notes': 'فني ممتاز، متميز في صيانة الشيلرات المركزية ومحطات الأكسجين.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '874120', 'rank': 'رقيب', 'full_name': 'عمر سامي بني هاني', 'specialty': 'كهرباء قوى ومحولات', 'current_detachment_id': 1, 'join_date': '2023-06-01', 'phone_number': '0788222333', 'evaluation_and_notes': 'ملتزم جداً وخبرة ممتازة في لوحات التوزيع الرئيسية.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '652198', 'rank': 'عريف', 'full_name': 'سامر فؤاد بطاينة', 'specialty': 'شبكات مياه وصحي', 'current_detachment_id': 1, 'join_date': '2024-02-10', 'phone_number': '0777333444', 'evaluation_and_notes': 'أداء جيد، يتابع مضخات المياه العذبة ومحطة التحلية.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '741852', 'rank': 'رقيب أول', 'full_name': 'حمزة نايف المجالي', 'specialty': 'كهرباء قوى ومحولات', 'current_detachment_id': 2, 'join_date': '2022-11-01', 'phone_number': '0776444555', 'evaluation_and_notes': 'كفاءة فنية عالية، يدير لوحات الطوارئ والمولدات الاحتياطية بنجاح.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '963258', 'rank': 'عريف', 'full_name': 'ليث خالد الصرايرة', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 2, 'join_date': '2023-09-15', 'phone_number': '0799555666', 'evaluation_and_notes': 'متخصص في وحدات السبليت وغرف العناية الحثيثة.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '852963', 'rank': 'وكيل', 'full_name': 'حسام جمال الغويري', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 3, 'join_date': '2021-08-20', 'phone_number': '0785666777', 'evaluation_and_notes': 'أقدم فني بالمفرزة، خبرة واسعة في جميع أنظمة التبريد والميكانيك.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '369258', 'rank': 'رقيب', 'full_name': 'يزن مخلد العموش', 'specialty': 'كهرباء قوى ومحولات', 'current_detachment_id': 3, 'join_date': '2023-03-01', 'phone_number': '0774777888', 'evaluation_and_notes': 'سرعة استجابة عالية للأعطال الكهربائية الطارئة.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '147852', 'rank': 'جندي أول', 'full_name': 'معاذ علي الحنيطي', 'specialty': 'شبكات مياه وصحي', 'current_detachment_id': 3, 'join_date': '2024-01-10', 'phone_number': '0798888999', 'evaluation_and_notes': 'فني واعد، منضبط ويؤدي المهام بدقة.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '258147', 'rank': 'عريف', 'full_name': 'براء فيصل الخلايلة', 'specialty': 'إنشائي عام', 'current_detachment_id': 3, 'join_date': '2023-11-20', 'phone_number': '0771999000', 'evaluation_and_notes': 'أعمال دهان وصيانة عامة للأبواب والقواطع.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '357159', 'rank': 'رقيب', 'full_name': 'أنس بسام العتوم', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 4, 'join_date': '2023-05-12', 'phone_number': '0789111333', 'evaluation_and_notes': 'مسؤول صيانة قسم غسيل الكلى والعناية الحثيثة.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '951357', 'rank': 'عريف', 'full_name': 'مؤمن أحمد الزغول', 'specialty': 'إنشائي عام', 'current_detachment_id': 4, 'join_date': '2024-04-01', 'phone_number': '0772222444', 'evaluation_and_notes': 'ملم بأعمال الصيانة الإنشائية والجبس بورد والألمنيوم.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '159357', 'rank': 'رقيب أول', 'full_name': 'رامي ناصر الحديد', 'specialty': 'كهرباء قوى ومحولات', 'current_detachment_id': 5, 'join_date': '2022-04-10', 'phone_number': '0793333555', 'evaluation_and_notes': 'خبير صيانة أنظمة UPS والمحولات الرئيسية.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '753951', 'rank': 'رقيب', 'full_name': 'جهاد توفيق المناصير', 'specialty': 'شبكات مياه وصحي', 'current_detachment_id': 5, 'join_date': '2023-07-22', 'phone_number': '0784444666', 'evaluation_and_notes': 'يشرف على شبكات الصرف وغلايات البخار المركزية.', 'primary_category': None, 'current_job': '', 'residence': ''}, {'military_id': '10001', 'rank': 'مقدم', 'full_name': 'المهندس رامي سبع العيش', 'specialty': 'هندسة صيانة وتشغيل', 'current_detachment_id': None, 'join_date': '2020-01-01', 'phone_number': '0790000001', 'evaluation_and_notes': 'قائد المفرزة - إشراف هندسي وإداري كامل', 'primary_category': None, 'current_job': 'رئيس فرع صيانة المستشفيات', 'residence': 'عمان'}, {'military_id': '46926', 'rank': 'مقدم', 'full_name': 'المهندسة منار', 'specialty': 'مهندسة مدنيه', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0773987654', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الأمير علي', 'residence': 'الكرك'}, {'military_id': '399138', 'rank': 'وكيل أول', 'full_name': 'محمد أحمد الطراونة', 'specialty': 'طريش', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795111222', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'طريش ومستودعات', 'residence': 'الكرك'}, {'military_id': '407424', 'rank': 'وكيل أول', 'full_name': 'خالد يوسف البطوش', 'specialty': 'ادارة مستودعات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795222333', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'إدارة مستودعات', 'residence': 'الكرك'}, {'military_id': '397426', 'rank': 'وكيل أول', 'full_name': 'طارق عبدالحفيظ الصرايرة', 'specialty': 'مراقب محركات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795333444', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مراقب محركات ومولدات', 'residence': 'الكرك'}, {'military_id': '390291', 'rank': 'وكيل أول', 'full_name': 'ياسر محمود المعايطة', 'specialty': 'مراقب محركات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795444555', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مراقب محركات', 'residence': 'الكرك'}, {'military_id': '397092', 'rank': 'وكيل', 'full_name': 'حازم علي المبيضين', 'specialty': 'طريش', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795555666', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'طريش وتشطيبات', 'residence': 'الكرك'}, {'military_id': '384789', 'rank': 'وكيل', 'full_name': 'أيمن سليمان الحباشنة', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795666777', 'evaluation_and_notes': 'عادي', 'primary_category': None, 'current_job': 'مراقب محركات', 'residence': 'الكرك'}, {'military_id': '405030', 'rank': 'وكيل', 'full_name': 'إبراهيم حسن الذنيبات', 'specialty': 'مراقب محركات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795777888', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مراقب محركات', 'residence': 'الكرك'}, {'military_id': '397182', 'rank': 'وكيل', 'full_name': 'سفيان نايف العضايلة', 'specialty': 'مراقب محركات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795888999', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مراقب محركات', 'residence': 'الكرك'}, {'military_id': '414647', 'rank': 'وكيل', 'full_name': 'علاء تيسير المجالي', 'specialty': 'مراقب محركات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0795999000', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مراقب محركات', 'residence': 'الكرك'}, {'military_id': '536857', 'rank': 'وكيل', 'full_name': 'م. سارة موسى الرواشدة', 'specialty': 'مهندسه مدنيه', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788111222', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندسة مدنية', 'residence': 'الكرك'}, {'military_id': '431352', 'rank': 'رقيب أول', 'full_name': 'مجد فيصل القرارعة', 'specialty': 'فني المنيوم', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788222333', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'فني ألمنيوم', 'residence': 'الكرك'}, {'military_id': '531550', 'rank': 'رقيب أول', 'full_name': 'م. معن عاطف الضمور', 'specialty': 'مهندس مدني', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788333444', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندس مدني', 'residence': 'الكرك'}, {'military_id': '530477', 'rank': 'رقيب أول', 'full_name': 'م. ريم زياد النوايسة', 'specialty': 'مهندسه مدنية', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788444555', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندسة مدنية', 'residence': 'الكرك'}, {'military_id': '538207', 'rank': 'رقيب', 'full_name': 'م. عمر سالم القرالة', 'specialty': 'مهندس كهرباء', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788555666', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندس كهرباء', 'residence': 'الكرك'}, {'military_id': '548536', 'rank': 'رقيب', 'full_name': 'م. قيس عبدالله الكساسبة', 'specialty': 'مهندس مدني', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788666777', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندس مدني', 'residence': 'الكرك'}, {'military_id': '546056', 'rank': 'رقيب', 'full_name': 'م. بتول حسين الجعافرة', 'specialty': 'مهندسه مدنيه', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788777888', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندسة مدنية', 'residence': 'الكرك'}, {'military_id': '546004', 'rank': 'رقيب', 'full_name': 'م. هبة أحمد الهلسا', 'specialty': 'مهندسه مدنيه', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788888999', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندسة مدنية', 'residence': 'الكرك'}, {'military_id': '548281', 'rank': 'رقيب', 'full_name': 'م. ديما وليد العمارين', 'specialty': 'مهندسه مدنيه', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0788999000', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندسة مدنية', 'residence': 'الكرك'}, {'military_id': '548414', 'rank': 'رقيب', 'full_name': 'م. رعد فواز البرقان', 'specialty': 'مهندس ميكانيك', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777111222', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مهندس ميكانيك وغازات طبية', 'residence': 'الكرك'}, {'military_id': '394927', 'rank': 'عريف', 'full_name': 'سامر عدنان الرهايفة', 'specialty': 'فني تكييف وتبريد', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777222333', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'فني تكييف وتبريد', 'residence': 'الكرك'}, {'military_id': '520061', 'rank': 'عريف', 'full_name': 'بلال خالد المواجFocus', 'specialty': 'مشاة', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777333444', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'صيانة إنشائية', 'residence': 'الكرك'}, {'military_id': '439527', 'rank': 'مدني', 'full_name': 'سليمان خلف البديرات', 'specialty': 'تكييف وتبريد', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777444555', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'كاتب وسجلات المفرزة', 'residence': 'الكرك'}, {'military_id': '395382', 'rank': 'مدني', 'full_name': 'جمال عيسى الخرشة', 'specialty': 'كهربائي تمديدات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777555666', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'كهربائي تمديدات', 'residence': 'الكرك'}, {'military_id': '429297', 'rank': 'مدني', 'full_name': 'ماجد شاهر الجلامدة', 'specialty': 'بناء طوب', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777666777', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مواسرجي وشبكات مياه', 'residence': 'الكرك'}, {'military_id': '452726', 'rank': 'مدني', 'full_name': 'محمود عبد ربه الشمايلة', 'specialty': 'فني كهربائي تمديدات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777777888', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'فني كهربائي تمديدات', 'residence': 'الكرك'}, {'military_id': '434065', 'rank': 'مدني', 'full_name': 'وليد يوسف القطاونة', 'specialty': 'مواسرجي', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777888999', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مواسرجي وتمديدات صحية', 'residence': 'الكرك'}, {'military_id': '393336', 'rank': 'مدني', 'full_name': 'ضرار محمد السحيمات', 'specialty': 'فني كهرباء', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0777999000', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'فني كهرباء قوى', 'residence': 'الكرك'}, {'military_id': '443377', 'rank': 'مدني', 'full_name': 'خلدون سالم البنوي', 'specialty': 'مواسرجي', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796111222', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مواسرجي وشبكات صحية', 'residence': 'الكرك'}, {'military_id': '444432', 'rank': 'مدني', 'full_name': 'عصام فؤاد العساسفة', 'specialty': 'مواسرجي', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796222333', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مواسرجي', 'residence': 'الكرك'}, {'military_id': '9529', 'rank': 'مدني', 'full_name': 'حاتم جميل العضايلة', 'specialty': 'عامل مياومة', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796333444', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'عامل صيانة ومياومة', 'residence': 'الكرك'}, {'military_id': '427250', 'rank': 'مدني', 'full_name': 'راضي إسماعيل الفقراء', 'specialty': 'مواسرجي', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796444555', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'مواسرجي', 'residence': 'الكرك'}, {'military_id': '394398', 'rank': 'مدني', 'full_name': 'مراد طه التخايمة', 'specialty': 'فني المنيوم', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796555666', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'فني ألمنيوم وتجهيزات', 'residence': 'الكرك'}, {'military_id': '481862', 'rank': 'مدني', 'full_name': 'بشار صالح الحمايدة', 'specialty': 'نجار موبيليا', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796666777', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'نجار موبيليا وقواطع', 'residence': 'الكرك'}, {'military_id': '394074', 'rank': 'مدني', 'full_name': 'منذر عبدالكريم المصاروة', 'specialty': 'كهربائي تمديدات', 'current_detachment_id': 2, 'join_date': '2026-09-07', 'phone_number': '0796777888', 'evaluation_and_notes': '', 'primary_category': None, 'current_job': 'كهربائي تمديدات ومحولات', 'residence': 'الكرك'}, {'military_id': '20001', 'rank': 'رائد', 'full_name': 'موسى حسن الشناق', 'specialty': 'هندسة صيانة وتشغيل', 'current_detachment_id': 1, 'join_date': '2020-01-01', 'phone_number': '0772233445', 'evaluation_and_notes': 'قائد مفرزة مستشفى الأمير راشد بن الحسن العسكري', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الأمير راشد', 'residence': 'إربد'}, {'military_id': '20002', 'rank': 'مقدم', 'full_name': 'المهندسة منار', 'specialty': 'هندسة صيانة وتشغيل', 'current_detachment_id': 2, 'join_date': '2020-01-01', 'phone_number': '0773987654', 'evaluation_and_notes': 'قائد مفرزة مستشفى الأمير علي بن الحسين العسكري', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الأمير علي', 'residence': 'الكرك'}, {'military_id': '20003', 'rank': 'وكيل أول', 'full_name': 'خالد محمود الزيود', 'specialty': 'صيانة عامة', 'current_detachment_id': 3, 'join_date': '2020-01-01', 'phone_number': '0775551234', 'evaluation_and_notes': 'قائد مفرزة مستشفى الأمير هاشم بن الحسين العسكري', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الأمير هاشم', 'residence': 'الزرقاء'}, {'military_id': '20004', 'rank': 'وكيل', 'full_name': 'طارق إبراهيم القضاة', 'specialty': 'صيانة عامة', 'current_detachment_id': 4, 'join_date': '2020-01-01', 'phone_number': '0778889900', 'evaluation_and_notes': 'قائد مفرزة مستشفى الأميرة هيا بنت الحسين العسكري', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الأميرة هيا', 'residence': 'عجلون'}, {'military_id': '20005', 'rank': 'نقيب', 'full_name': 'عمر يوسف العدوان', 'specialty': 'هندسة صيانة وتشغيل', 'current_detachment_id': 5, 'join_date': '2020-01-01', 'phone_number': '0771122334', 'evaluation_and_notes': 'قائد مفرزة مستشفى الملكة علياء العسكري', 'primary_category': None, 'current_job': 'قائد مفرزة مستشفى الملكة علياء', 'residence': 'عمان'}]

def sync_official_master_data(db_path=DB_NAME):
    """مزامنة وتثبيت المفارز وقادتها وكافة الفنيين المعتمدين بصورة دائمة وتلقائية"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # 1. تثبيت المفارز
    for d in OFFICIAL_MASTER_DETACHMENTS:
        cursor.execute('''
        INSERT INTO detachments (id, hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, staffing_shortages, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            hospital_name = excluded.hospital_name,
            governorate = excluded.governorate,
            supervisor_rank = excluded.supervisor_rank,
            supervisor_name = excluded.supervisor_name,
            contact_phone = excluded.contact_phone,
            staffing_shortages = excluded.staffing_shortages,
            notes = excluded.notes;
        ''', (d['id'], d['hospital_name'], d['governorate'], d['supervisor_rank'], d['supervisor_name'], d['contact_phone'], d['staffing_shortages'], d['notes']))

    # 2. تثبيت الفنيين
    for t in OFFICIAL_MASTER_TECHNICIANS:
        cursor.execute('''
        INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(military_id) DO UPDATE SET
            rank = excluded.rank,
            full_name = excluded.full_name,
            specialty = excluded.specialty,
            primary_category = excluded.primary_category,
            current_job = excluded.current_job,
            residence = excluded.residence,
            current_detachment_id = excluded.current_detachment_id,
            join_date = excluded.join_date,
            phone_number = excluded.phone_number,
            evaluation_and_notes = excluded.evaluation_and_notes;
        ''', (t['military_id'], t['rank'], t['full_name'], t['specialty'], t['primary_category'], t['current_job'], t['residence'], t['current_detachment_id'], t['join_date'], t['phone_number'], t['evaluation_and_notes']))

    conn.commit()
    conn.close()

# --- إدارة الإعدادات (Settings API) ---

def sanitize_columns_order(cols):
    """تنقية ترتيب الأعمدة واستبدال أي مسميات قديمة بـ الصنف والمهنة الحالية"""
    if not cols or not isinstance(cols, list):
        return DEFAULT_TECH_COLUMNS
    cleaned = []
    for c in cols:
        if c in ["الصنف الأساسي", "التخصص الفني"]:
            if "الصنف" not in cleaned:
                cleaned.append("الصنف")
        elif c not in cleaned and c in DEFAULT_TECH_COLUMNS:
            cleaned.append(c)
    for def_c in DEFAULT_TECH_COLUMNS:
        if def_c not in cleaned:
            cleaned.append(def_c)
    return cleaned

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
            raw_cols = json.loads(d["columns_order_json"])
            d["columns_order"] = sanitize_columns_order(raw_cols)
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

# أوزان الرتب العسكرية للأقدمية
MILITARY_RANK_SENIORITY = {
    "لواء": 100,
    "عميد": 90,
    "عقيد": 80,
    "مقدم": 70,
    "رائد": 60,
    "نقيب": 50,
    "ملازم/1": 40,
    "ملازم": 30,
    "وكيل أول": 20,
    "وكيل": 15,
    "رقيب أول": 12,
    "رقيب": 10,
    "عريف": 8,
    "جندي أول": 5,
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
    تحديد قائد المفرزة:
    1. القائد المسجل رسمياً في جدول المفارز detachments (الرتبة والاسم والهاتف).
    2. ربط الرقم العسكري من جدول المرتبات إذا وجد.
    3. في حال عدم تعيين قائد في جدول المفارز، يتم استخراجه من المرتبات كأعلى رتبة أو المسمى الوظيفي 'قائد مفرزة'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT supervisor_rank, supervisor_name, contact_phone FROM detachments WHERE id = ?;", (detachment_id,))
    det_row = cursor.fetchone()

    cursor.execute("""
    SELECT t.military_id, t.rank, t.full_name, t.current_job, t.phone_number
    FROM technicians t
    WHERE t.current_detachment_id = ?;
    """, (detachment_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if det_row and det_row["supervisor_name"]:
        # العثور على الرقم العسكري للقائد إذا كان مسجلاً بالمرتبات
        matching_tech = next((r for r in rows if det_row["supervisor_name"] in r["full_name"] or r["full_name"] in det_row["supervisor_name"]), None)
        return {
            "rank": det_row["supervisor_rank"] or "قائد مفرزة",
            "name": det_row["supervisor_name"],
            "military_id": matching_tech["military_id"] if matching_tech else "-",
            "phone": (matching_tech.get("phone_number") if matching_tech and matching_tech.get("phone_number") else None) or det_row["contact_phone"] or ""
        }
    
    if rows:
        # البحث عن فني مسمى وظيفته قائد مفرزة أولاً
        cmd_tech = next((r for r in rows if "قائد" in (r.get("current_job") or "")), None)
        if cmd_tech:
            return {
                "rank": cmd_tech["rank"],
                "name": cmd_tech["full_name"],
                "military_id": cmd_tech["military_id"],
                "phone": cmd_tech.get("phone_number") or ""
            }
        # وإلا الأعلى رتبة
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
        
    return {
        "rank": "غير محدد",
        "name": "غير محدد",
        "military_id": "-",
        "phone": ""
    }

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

def add_technician(military_id, rank, full_name, specialty, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes, *args):
    """إضافة فني جديد إلى المنظومة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?);
        """, (military_id, rank, full_name, specialty, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes))
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

def update_technician(military_id, rank, full_name, specialty, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes, *args):
    """تعديل بيانات فني موجود بالكامل"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE technicians 
        SET rank = ?, full_name = ?, specialty = ?, primary_category = NULL, current_job = ?, residence = ?, current_detachment_id = ?, join_date = ?, phone_number = ?, evaluation_and_notes = ?
        WHERE military_id = ?;
        """, (rank, full_name, specialty, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes, military_id))
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

        # التبادل الذكي وتطهير الصنف من أي مسميات أسلحة
        if any(w in specialty for w in ["سلاح", "الخدمات الطبية", "الصيانة"]):
            if job and not any(w in job for w in ["سلاح", "الخدمات الطبية"]):
                specialty = job
            else:
                specialty = "صنف عام"
        elif not specialty and job:
            specialty = job

        # التحقق هل الفني موجود مسبقاً
        cursor.execute("SELECT * FROM technicians WHERE military_id = ?;", (mil_id,))
        existing = cursor.fetchone()

        try:
            if existing:
                if update_existing:
                    final_rank = rank or existing["rank"]
                    final_name = name or existing["full_name"]
                    final_spec = specialty or existing["specialty"]
                    final_job = job or existing["current_job"]
                    final_res = residence or existing["residence"]
                    final_join = join_d or existing["join_date"]
                    final_phone = phone or existing["phone_number"]
                    final_notes = notes or existing["evaluation_and_notes"]

                    cursor.execute("""
                    UPDATE technicians
                    SET rank = ?, full_name = ?, specialty = ?, primary_category = NULL, current_job = ?, 
                        residence = ?, current_detachment_id = ?, join_date = ?, phone_number = ?, evaluation_and_notes = ?
                    WHERE military_id = ?;
                    """, (final_rank, final_name, final_spec, final_job, final_res, detachment_id, final_join, final_phone, final_notes, mil_id))
                    updated_count += 1
                else:
                    skipped_count += 1
                    errors.append(f"الصف {row_num} (الرقم {mil_id}): مسجل مسبقاً وتم تخطيه بناءً على خيار عدم التحديث.")
            else:
                final_rank = rank or "جندي أول"
                final_spec = specialty or "صنف عام"

                cursor.execute("""
                INSERT INTO technicians (military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes)
                VALUES (?, ?, ?, ?, NULL, ?, ?, ?, ?, ?, ?);
                """, (mil_id, final_rank, name, final_spec, job, residence, detachment_id, join_d, phone, notes))
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

# --- أدوات النسخ الاحتياطي والاستعادة لقاعدة البيانات ---

def get_db_bytes(db_path=DB_NAME):
    """قراءة ملف قاعدة البيانات بالكامل كـ bytes للتنزيل"""
    if os.path.exists(db_path):
        with open(db_path, "rb") as f:
            return f.read()
    return None

def restore_db_bytes(data_bytes, db_path=DB_NAME):
    """استعادة ملف قاعدة البيانات من ملف مرفوع"""
    try:
        with open(db_path, "wb") as f:
            f.write(data_bytes)
        init_db(db_path)
        return True, "تمت استعادة قاعدة البيانات بنجاح!"
    except Exception as e:
        return False, f"حدث خطأ أثناء الاستعادة: {str(e)}"

def export_full_database_excel(db_path=DB_NAME):
    """تصدير قاعدة البيانات بالكامل إلى ملف Excel شامل لكافة الجداول بما فيها الموجود الصباحي"""
    conn = get_db_connection(db_path)
    detachments_df = pd.read_sql_query("SELECT * FROM detachments", conn)
    technicians_df = pd.read_sql_query("SELECT * FROM technicians", conn)
    movements_df = pd.read_sql_query("SELECT * FROM movement_log", conn)
    settings_df = pd.read_sql_query("SELECT * FROM app_settings", conn)
    roll_call_df = pd.read_sql_query("SELECT * FROM daily_roll_call", conn)
    entries_df = pd.read_sql_query("SELECT * FROM daily_roll_call_entries", conn)
    conn.close()

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        detachments_df.to_excel(writer, index=False, sheet_name="المفارز")
        technicians_df.to_excel(writer, index=False, sheet_name="الفنيين")
        movements_df.to_excel(writer, index=False, sheet_name="سجل_حركات_النقل")
        roll_call_df.to_excel(writer, index=False, sheet_name="الموجود_الصباحي_الرئيسي")
        entries_df.to_excel(writer, index=False, sheet_name="تفاصيل_الموجود_اليومي")
        settings_df.to_excel(writer, index=False, sheet_name="الإعدادات")
    return output.getvalue()

# ==============================================================================
# إدارة الموجود الصباحي اليومي (Daily Morning Roll Call)
# ==============================================================================

def get_daily_roll_call(detachment_id, roll_call_date, db_path=DB_NAME):
    """
    جلب سجل الموجود الصباحي لمفرزة في تاريخ محدد مع تفاصيل حالة كل فني
    يرجع (roll_call_record, entries_list) أو (None, []) إذا لم يكن مسجلاً بعد
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, d.hospital_name, d.governorate
        FROM daily_roll_call r
        JOIN detachments d ON r.detachment_id = d.id
        WHERE r.detachment_id = ? AND r.roll_call_date = ?
    """, (detachment_id, roll_call_date))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return None, []

    roll_call = dict(record)

    cursor.execute("""
        SELECT *
        FROM daily_roll_call_entries
        WHERE roll_call_id = ?
        ORDER BY id ASC
    """, (roll_call["id"],))
    entries = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return roll_call, entries

def get_roll_call_by_id(roll_call_id, db_path=DB_NAME):
    """جلب سجل الموجود الصباحي بالمعرف الفريد مع تفاصيل المرتب"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT r.*, d.hospital_name, d.governorate
        FROM daily_roll_call r
        JOIN detachments d ON r.detachment_id = d.id
        WHERE r.id = ?
    """, (roll_call_id,))
    record = cursor.fetchone()

    if not record:
        conn.close()
        return None, []

    roll_call = dict(record)

    cursor.execute("""
        SELECT *
        FROM daily_roll_call_entries
        WHERE roll_call_id = ?
        ORDER BY id ASC
    """, (roll_call_id,))
    entries = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return roll_call, entries

def save_daily_roll_call(detachment_id, roll_call_date, entries, saved_by_rank, saved_by_name, notes="", is_branch_chief=False, db_path=DB_NAME):
    """
    حفظ واعتماد الموجود الصباحي للمفرزة
    القاعدة الصارمة: ما دام تم الحفظ من قبل قائد المفرزة، لا يمكن التعديل إلا إذا كان المستخدم رئيس الفرع.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # فحص إذا كان السجل محفوظاً مسبقاً
        cursor.execute("SELECT id, status FROM daily_roll_call WHERE detachment_id = ? AND roll_call_date = ?", (detachment_id, roll_call_date))
        existing = cursor.fetchone()

        if existing and not is_branch_chief:
            conn.close()
            return False, "⚠️ تم حفظ الموجود الصباحي لهذه المفرزة مسبقاً وهو مقفل ومعتمد. لا يمكن التعديل إلا من قبل رئيس الفرع."

        # حساب الإحصائيات من قائمة البنود
        total_strength = len(entries)
        present_count = sum(1 for e in entries if e.get("status") == "موجود")
        leave_count = sum(1 for e in entries if e.get("status") == "مجاز")
        sick_count = sum(1 for e in entries if e.get("status") in ["مراجعة مرضية", "مراجعة مرضة", "مرضي"])

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing:
            # تعديل (مسموح لرئيس الفرع)
            roll_call_id = existing["id"]
            cursor.execute("""
                UPDATE daily_roll_call
                SET total_strength = ?,
                    present_count = ?,
                    leave_count = ?,
                    sick_count = ?,
                    saved_by_rank = ?,
                    saved_by_name = ?,
                    saved_at = ?,
                    notes = ?,
                    status = 'saved'
                WHERE id = ?
            """, (total_strength, present_count, leave_count, sick_count, saved_by_rank, saved_by_name, now_str, notes, roll_call_id))

            cursor.execute("DELETE FROM daily_roll_call_entries WHERE roll_call_id = ?", (roll_call_id,))
        else:
            # إدخال جديد
            cursor.execute("""
                INSERT INTO daily_roll_call (
                    detachment_id, roll_call_date, status, saved_by_rank, saved_by_name, saved_at,
                    total_strength, present_count, leave_count, sick_count, notes
                ) VALUES (?, ?, 'saved', ?, ?, ?, ?, ?, ?, ?, ?)
            """, (detachment_id, roll_call_date, saved_by_rank, saved_by_name, now_str,
                  total_strength, present_count, leave_count, sick_count, notes))
            roll_call_id = cursor.lastrowid

        # إدراج تفاصيل مرتبات الفنيين
        for entry in entries:
            norm_status = entry.get("status", "موجود")
            if norm_status in ["مراجعة مرضة", "مرضي"]:
                norm_status = "مراجعة مرضية"
            cursor.execute("""
                INSERT INTO daily_roll_call_entries (
                    roll_call_id, military_id, rank, full_name, specialty, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_call_id,
                str(entry.get("military_id", "")),
                str(entry.get("rank", "")),
                str(entry.get("full_name", "")),
                str(entry.get("specialty", "")),
                norm_status,
                str(entry.get("notes", "") or "")
            ))

        conn.commit()
        conn.close()
        return True, "✅ تم حفظ واعتماد الموجود الصباحي للمفرزة بنجاح."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"❌ حدث خطأ أثناء حفظ الموجود الصباحي: {str(e)}"

def update_or_unlock_roll_call(roll_call_id, entries, notes, modified_by_rank, modified_by_name, db_path=DB_NAME):
    """تعديل سجل موجود سابق أو فك القفل (خاص برئيس الفرع فقط)"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        total_strength = len(entries)
        present_count = sum(1 for e in entries if e.get("status") == "موجود")
        leave_count = sum(1 for e in entries if e.get("status") == "مجاز")
        sick_count = sum(1 for e in entries if e.get("status") in ["مراجعة مرضية", "مراجعة مرضة", "مرضي"])
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            UPDATE daily_roll_call
            SET total_strength = ?,
                present_count = ?,
                leave_count = ?,
                sick_count = ?,
                saved_by_rank = ?,
                saved_by_name = ?,
                saved_at = ?,
                notes = ?
            WHERE id = ?
        """, (total_strength, present_count, leave_count, sick_count, modified_by_rank, modified_by_name, now_str, notes, roll_call_id))

        cursor.execute("DELETE FROM daily_roll_call_entries WHERE roll_call_id = ?", (roll_call_id,))

        for entry in entries:
            norm_status = entry.get("status", "موجود")
            if norm_status in ["مراجعة مرضة", "مرضي"]:
                norm_status = "مراجعة مرضية"
            cursor.execute("""
                INSERT INTO daily_roll_call_entries (
                    roll_call_id, military_id, rank, full_name, specialty, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                roll_call_id,
                str(entry.get("military_id", "")),
                str(entry.get("rank", "")),
                str(entry.get("full_name", "")),
                str(entry.get("specialty", "")),
                norm_status,
                str(entry.get("notes", "") or "")
            ))

        conn.commit()
        conn.close()
        return True, "✅ تم تحديث سجل الموجود الصباحي بنجاح بواسطة رئيس الفرع."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"❌ حدث خطأ أثناء تعديل الموجود: {str(e)}"

def delete_daily_roll_call(roll_call_id, db_path=DB_NAME):
    """حذف سجل موجود يومي (صلاحية رئيس الفرع فقط لإعادة الفتح)"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM daily_roll_call WHERE id = ?", (roll_call_id,))
        conn.commit()
        conn.close()
        return True, "تم حذف سجل الموجود وإعادة فتحه للإدخال."
    except Exception as e:
        conn.close()
        return False, f"تعذر حذف السجل: {str(e)}"

def get_roll_call_history_df(detachment_id=None, start_date=None, end_date=None, db_path=DB_NAME):
    """إرجاع تاريخ سجلات الموجود كـ DataFrame مع اسم المستشفى والمحافظة"""
    conn = get_db_connection(db_path)
    query = """
        SELECT 
            r.id as "رقم السجل",
            r.roll_call_date as "التاريخ",
            d.hospital_name as "المستشفى / المفرزة",
            d.governorate as "المحافظة",
            r.total_strength as "القوة الإجمالية",
            r.present_count as "الموجود",
            r.leave_count as "المجاز",
            r.sick_count as "مراجعة مرضية",
            ROUND((CAST(r.present_count AS FLOAT) / NULLIF(r.total_strength, 0)) * 100, 1) as "نسبة الجاهزية %",
            (r.saved_by_rank || ' / ' || r.saved_by_name) as "القائم بالحفظ",
            r.saved_at as "تاريخ ووقت الحفظ",
            r.notes as "ملاحظات الموجود",
            r.detachment_id as "detachment_id"
        FROM daily_roll_call r
        JOIN detachments d ON r.detachment_id = d.id
        WHERE 1=1
    """
    params = []
    if detachment_id:
        query += " AND r.detachment_id = ?"
        params.append(detachment_id)
    if start_date:
        query += " AND r.roll_call_date >= ?"
        params.append(str(start_date))
    if end_date:
        query += " AND r.roll_call_date <= ?"
        params.append(str(end_date))

    query += " ORDER BY r.roll_call_date DESC, d.hospital_name ASC"

    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_consolidated_roll_call_summary(roll_call_date, db_path=DB_NAME):
    """
    إرجاع الموقف العام لكافة المفارز في تاريخ محدد
    يشمل المفارز التي سلّمت الموجود والمفارز المعلقة (لم تسلم بعد)
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # جلب جميع المفارز مع عدد الفنيين الحاليين
    cursor.execute("""
        SELECT 
            d.id,
            d.hospital_name,
            d.governorate,
            d.supervisor_rank,
            d.supervisor_name,
            d.contact_phone,
            COUNT(t.military_id) as actual_technicians_count
        FROM detachments d
        LEFT JOIN technicians t ON d.id = t.current_detachment_id
        GROUP BY d.id
        ORDER BY d.governorate ASC, d.hospital_name ASC
    """)
    detachments = [dict(row) for row in cursor.fetchall()]

    # جلب سجلات الموجود لهذا اليوم
    cursor.execute("""
        SELECT *
        FROM daily_roll_call
        WHERE roll_call_date = ?
    """, (str(roll_call_date),))
    records_by_det_id = {row["detachment_id"]: dict(row) for row in cursor.fetchall()}

    conn.close()

    summary_list = []
    total_strength_sum = 0
    total_present_sum = 0
    total_leave_sum = 0
    total_sick_sum = 0
    submitted_count = 0
    pending_count = 0

    for d in detachments:
        det_id = d["id"]
        rec = records_by_det_id.get(det_id)
        if rec:
            submitted_count += 1
            tot = rec["total_strength"]
            pres = rec["present_count"]
            lea = rec["leave_count"]
            sck = rec["sick_count"]
            readiness = round((pres / tot * 100), 1) if tot > 0 else 100.0

            total_strength_sum += tot
            total_present_sum += pres
            total_leave_sum += lea
            total_sick_sum += sck

            summary_list.append({
                "detachment_id": det_id,
                "record_id": rec["id"],
                "hospital_name": d["hospital_name"],
                "governorate": d["governorate"],
                "supervisor": f"{d['supervisor_rank']} / {d['supervisor_name']}",
                "contact_phone": d["contact_phone"] or "-",
                "is_submitted": True,
                "status_badge": "✅ تم التسليم والاعتماد",
                "total_strength": tot,
                "present_count": pres,
                "leave_count": lea,
                "sick_count": sck,
                "readiness_pct": readiness,
                "saved_by": f"{rec['saved_by_rank']} / {rec['saved_by_name']}",
                "saved_at": rec["saved_at"],
                "notes": rec["notes"] or ""
            })
        else:
            pending_count += 1
            tot = d["actual_technicians_count"]
            total_strength_sum += tot
            summary_list.append({
                "detachment_id": det_id,
                "record_id": None,
                "hospital_name": d["hospital_name"],
                "governorate": d["governorate"],
                "supervisor": f"{d['supervisor_rank']} / {d['supervisor_name']}",
                "contact_phone": d["contact_phone"] or "-",
                "is_submitted": False,
                "status_badge": "⏳ قيد الانتظار (لم يُسلَّم)",
                "total_strength": tot,
                "present_count": 0,
                "leave_count": 0,
                "sick_count": 0,
                "readiness_pct": 0.0,
                "saved_by": "-",
                "saved_at": "-",
                "notes": "لم يتم إدخال الموجود الصباحي من قائد المفرزة بعد"
            })

    return {
        "date": str(roll_call_date),
        "total_detachments": len(detachments),
        "submitted_detachments": submitted_count,
        "pending_detachments": pending_count,
        "total_strength": total_strength_sum,
        "total_present": total_present_sum,
        "total_leave": total_leave_sum,
        "total_sick": total_sick_sum,
        "overall_readiness": round((total_present_sum / total_strength_sum * 100), 1) if total_strength_sum > 0 else 0.0,
        "summary_list": summary_list
    }

def export_roll_call_to_excel(roll_call_meta, entries_list):
    """تصدير كشف الموجود الصباحي لمفرزة أو يوم محدد إلى ملف Excel منسق"""
    meta_df = pd.DataFrame([{
        "المستشفى / المفرزة": roll_call_meta.get("hospital_name", "-"),
        "المحافظة": roll_call_meta.get("governorate", "-"),
        "تاريخ الموجود": roll_call_meta.get("roll_call_date", "-"),
        "القوة الإجمالية": roll_call_meta.get("total_strength", len(entries_list)),
        "الموجود الفعلي": roll_call_meta.get("present_count", sum(1 for e in entries_list if e.get("status") == "موجود")),
        "المجاز": roll_call_meta.get("leave_count", sum(1 for e in entries_list if e.get("status") == "مجاز")),
        "مراجعة مرضية": roll_call_meta.get("sick_count", sum(1 for e in entries_list if e.get("status") == "مراجعة مرضية")),
        "القائم بالاعتماد": f"{roll_call_meta.get('saved_by_rank', '')} / {roll_call_meta.get('saved_by_name', '')}",
        "تاريخ ووقت الحفظ": roll_call_meta.get("saved_at", "-"),
        "الملاحظات": roll_call_meta.get("notes", "-")
    }])

    entries_rows = []
    for i, e in enumerate(entries_list, 1):
        entries_rows.append({
            "م": i,
            "الرقم العسكري": e.get("military_id", ""),
            "الرتبة": e.get("rank", ""),
            "الاسم الرباعي": e.get("full_name", ""),
            "الصنف": e.get("specialty", ""),
            "الحالة": e.get("status", "موجود"),
            "الملاحظات والسبب": e.get("notes", "")
        })
    entries_df = pd.DataFrame(entries_rows)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        meta_df.to_excel(writer, index=False, sheet_name="ملخص_الموجود")
        entries_df.to_excel(writer, index=False, sheet_name="كشف_المرتب_التفصيلي")
    return output.getvalue()


# ==============================================================================
# إدارة المستخدمين، تسجيل الدخول، وتوزيع الصلاحيات (Authentication & RBAC)
# ==============================================================================

def hash_password(password, salt=None):
    """تشفير كلمة المرور مع Salt عشوائي للحماية الأمنية العالية"""
    if salt is None:
        salt = secrets.token_hex(16)
    combined = (str(salt) + str(password)).encode('utf-8')
    pwd_hash = hashlib.sha256(combined).hexdigest()
    return pwd_hash, salt

def authenticate_user(username, password, db_path=DB_NAME):
    """
    التحقق من بيانات الدخول (اسم المستخدم/الرقم العسكري + كلمة المرور)
    يرجع (نجاح/فشل، كائن المستخدم، رسالة الحالة)
    """
    if not username or not password:
        return False, None, "يرجى إدخال رقم التعريف وكلمة المرور."

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, d.hospital_name, d.governorate
        FROM users u
        LEFT JOIN detachments d ON u.detachment_id = d.id
        WHERE LOWER(u.username) = LOWER(?)
    """, (str(username).strip(),))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return False, None, "❌ رقم التعريف / اسم المستخدم غير مسجل في المنظومة."

    user = dict(row)
    if not user.get("is_active", 1):
        conn.close()
        return False, None, "⛔ هذا الحساب مجمد أو موقوف حالياً. يرجى مراجعة رئيس الفرع."

    expected_hash, _ = hash_password(password, user["salt"])
    if expected_hash != user["password_hash"]:
        conn.close()
        return False, None, "❌ كلمة المرور غير صحيحة. يرجى التأكد من كلمة المرور والمحاولة ثانية."

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now_str, user["id"]))
    conn.commit()
    conn.close()

    user["last_login"] = now_str
    return True, user, "✅ تم تسجيل الدخول بنجاح!"

def get_all_users_df(db_path=DB_NAME):
    """إرجاع جدول كافة المستخدمين كـ DataFrame مع بيانات المفرزة المرتبطة"""
    conn = get_db_connection(db_path)
    query = """
    SELECT 
        u.id,
        u.username,
        u.rank,
        u.full_name,
        u.role,
        u.detachment_id,
        d.hospital_name,
        d.governorate,
        u.is_active,
        u.created_at,
        u.last_login
    FROM users u
    LEFT JOIN detachments d ON u.detachment_id = d.id
    ORDER BY 
        CASE WHEN u.role = 'رئيس الفرع' THEN 1 ELSE 2 END,
        u.id ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_user_by_id(user_id, db_path=DB_NAME):
    """جلب بيانات مستخدم محدد بالمعرف"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.*, d.hospital_name, d.governorate
        FROM users u
        LEFT JOIN detachments d ON u.detachment_id = d.id
        WHERE u.id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(username, password, full_name, rank, role, detachment_id=None, permissions=None, db_path=DB_NAME):
    """إنشاء مستخدم جديد مع تشفير كلمة المرور وتعيين الصلاحيات"""
    clean_u = str(username).strip()
    if not clean_u or not password or not full_name:
        return False, "يرجى تعبئة كافة الحقول الإلزامية (اسم المستخدم، كلمة المرور، الاسم الكامل)."

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?);", (clean_u,))
        if cursor.fetchone():
            conn.close()
            return False, f"اسم المستخدم أو رقم التعريف '{clean_u}' مسجل مسبقاً لمستخدم آخر."

        pwd_hash, salt = hash_password(password)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        perm_json = json.dumps(permissions or {}, ensure_ascii=False)

        cursor.execute("""
        INSERT INTO users (
            username, password_hash, salt, full_name, rank, role, detachment_id, is_active, created_at, permissions_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?);
        """, (clean_u, pwd_hash, salt, full_name, rank, role, detachment_id, now_str, perm_json))

        conn.commit()
        conn.close()
        return True, f"✅ تم إنشاء حساب المستخدم '{clean_u}' بنجاح!"
    except Exception as e:
        conn.close()
        return False, f"❌ حدث خطأ أثناء إنشاء المستخدم: {str(e)}"

def update_user(user_id, full_name, rank, role, detachment_id=None, is_active=1, permissions=None, db_path=DB_NAME):
    """تحديث بيانات المستخدم والرتبة والصلاحيات"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        perm_json = json.dumps(permissions or {}, ensure_ascii=False) if permissions is not None else None
        
        if perm_json is not None:
            cursor.execute("""
            UPDATE users
            SET full_name = ?, rank = ?, role = ?, detachment_id = ?, is_active = ?, permissions_json = ?
            WHERE id = ?;
            """, (full_name, rank, role, detachment_id, is_active, perm_json, user_id))
        else:
            cursor.execute("""
            UPDATE users
            SET full_name = ?, rank = ?, role = ?, detachment_id = ?, is_active = ?
            WHERE id = ?;
            """, (full_name, rank, role, detachment_id, is_active, user_id))

        conn.commit()
        conn.close()
        return True, "✅ تم تحديث بيانات المستخدم وصلاحياته بنجاح!"
    except Exception as e:
        conn.close()
        return False, f"❌ حدث خطأ أثناء التحديث: {str(e)}"

def change_user_password(user_id, new_password, db_path=DB_NAME):
    """تغيير أو إعادة ضبط كلمة المرور لمستخدم"""
    if not new_password or len(str(new_password).strip()) < 3:
        return False, "يجب أن تتكون كلمة المرور من 3 خانات على الأقل."

    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        pwd_hash, salt = hash_password(new_password)
        cursor.execute("UPDATE users SET password_hash = ?, salt = ? WHERE id = ?;", (pwd_hash, salt, user_id))
        conn.commit()
        conn.close()
        return True, "✅ تم تغيير كلمة المرور بنجاح!"
    except Exception as e:
        conn.close()
        return False, f"❌ حدث خطأ: {str(e)}"

def delete_user(user_id, db_path=DB_NAME):
    """حذف حساب مستخدم من المنظومة"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()
        conn.close()
        return True, "تم حذف المستخدم بنجاح."
    except Exception as e:
        conn.close()
        return False, f"تعذر حذف المستخدم: {str(e)}"

def seed_default_users(db_path=DB_NAME):
    """تهيئة وتحديث الحسابات الافتراضية بالأرقام العسكرية لرئيس الفرع وقادة المفارز بالمستشفيات"""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # جلب المفارز بالاسم لربط المعرفات بدقة
    cursor.execute("SELECT id, hospital_name FROM detachments;")
    dets_map = {row["hospital_name"]: row["id"] for row in cursor.fetchall()}

    # تحديد معرفات المستشفيات
    karak_id = next((v for k, v in dets_map.items() if "علي" in k or "الكرك" in k), 2)
    irbid_id = next((v for k, v in dets_map.items() if "راشد" in k or "إربد" in k), 1)
    zarqa_id = next((v for k, v in dets_map.items() if "هاشم" in k or "الزرقاء" in k), 3)
    jerash_id = next((v for k, v in dets_map.items() if "هيا" in k or "جرش" in k), 4)
    alia_id = next((v for k, v in dets_map.items() if "علياء" in k or "عمان" in k), 5)

    # تحديث وتثبيت بيانات قادة المفارز الرسمية في جدول detachments
    detachments_official = [
        (irbid_id, "رائد", "موسى حسن الشناق", "0772233445"),
        (karak_id, "مقدم", "المهندسة منار", "0773987654"),
        (zarqa_id, "وكيل أول", "خالد محمود الزيود", "0775551234"),
        (jerash_id, "وكيل", "طارق إبراهيم القضاة", "0778889900"),
        (alia_id, "نقيب", "عمر يوسف العدوان", "0771122334")
    ]
    for d_id, s_rank, s_name, s_phone in detachments_official:
        if d_id:
            cursor.execute("""
            UPDATE detachments 
            SET supervisor_rank = ?, supervisor_name = ?, contact_phone = ?
            WHERE id = ?;
            """, (s_rank, s_name, s_phone, d_id))

    # ضبط فني رئيس الفرع (المقدم المهندس رامي سبع العيش) ليكون بالنطاق العام المركزي (detachment = NULL)
    cursor.execute("""
    UPDATE technicians 
    SET current_detachment_id = NULL, rank = 'مقدم', full_name = 'المهندس رامي سبع العيش', current_job = 'رئيس فرع صيانة المستشفيات', residence = 'عمان', phone_number = '0790000001'
    WHERE military_id = '10001';
    """)

    # قائمة الحسابات الرسمية بالرقم العسكري
    default_accounts = [
        # رئيس الفرع (المقدم المهندس رامي سبع العيش - صلاحية شاملة كاملة)
        ("10001", "123456", "المهندس رامي سبع العيش", "مقدم", "رئيس الفرع", None),
        ("admin", "123456", "المهندس رامي سبع العيش", "مقدم", "رئيس الفرع", None),
        # قائد مفرزة مستشفى الأمير علي بن الحسين - الكرك (المقدم المهندسة منار)
        ("20002", "123456", "المهندسة منار", "مقدم", "قائد مفرزة", karak_id),
        ("cmd_karak", "123456", "المهندسة منار", "مقدم", "قائد مفرزة", karak_id),
        # قادة المفارز بالمستشفيات العسكرية الأخرى
        ("20001", "123456", "موسى حسن الشناق", "رائد", "قائد مفرزة", irbid_id),
        ("cmd_irbid", "123456", "موسى حسن الشناق", "رائد", "قائد مفرزة", irbid_id),
        ("20003", "123456", "خالد محمود الزيود", "وكيل أول", "قائد مفرزة", zarqa_id),
        ("cmd_zarqa", "123456", "خالد محمود الزيود", "وكيل أول", "قائد مفرزة", zarqa_id),
        ("20004", "123456", "طارق إبراهيم القضاة", "وكيل", "قائد مفرزة", jerash_id),
        ("cmd_jerash", "123456", "طارق إبراهيم القضاة", "وكيل", "قائد مفرزة", jerash_id),
        ("20005", "123456", "عمر يوسف العدوان", "نقيب", "قائد مفرزة", alia_id),
        ("cmd_alia", "123456", "عمر يوسف العدوان", "نقيب", "قائد مفرزة", alia_id),
    ]

    for u_name, pwd, f_name, rnk, rol, d_id in default_accounts:
        pwd_hash, salt = hash_password(pwd)
        cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?);", (u_name,))
        existing = cursor.fetchone()
        if existing:
            cursor.execute("""
            UPDATE users
            SET password_hash = ?, salt = ?, full_name = ?, rank = ?, role = ?, detachment_id = ?, is_active = 1
            WHERE id = ?;
            """, (pwd_hash, salt, f_name, rnk, rol, d_id, existing[0]))
        else:
            cursor.execute("""
            INSERT INTO users (
                username, password_hash, salt, full_name, rank, role, detachment_id, is_active, created_at, permissions_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, '{}');
            """, (u_name, pwd_hash, salt, f_name, rnk, rol, d_id, now_str))

    # ضمان وجود قادة المفارز في جدول الفنيين مع مسمياتهم الصحيحة
    commanders_in_techs = [
        ("20001", "رائد", "موسى حسن الشناق", "هندسة صيانة وتشغيل", "سلاح الصيانة الملكي", "قائد مفرزة مستشفى الأمير راشد", "إربد", irbid_id, "2020-01-01", "0772233445", "قائد مفرزة مستشفى الأمير راشد بن الحسن العسكري"),
        ("20002", "مقدم", "المهندسة منار", "هندسة صيانة وتشغيل", "سلاح الصيانة الملكي", "قائد مفرزة مستشفى الأمير علي", "الكرك", karak_id, "2020-01-01", "0773987654", "قائد مفرزة مستشفى الأمير علي بن الحسين العسكري"),
        ("20003", "وكيل أول", "خالد محمود الزيود", "صيانة عامة", "سلاح الصيانة الملكي", "قائد مفرزة مستشفى الأمير هاشم", "الزرقاء", zarqa_id, "2020-01-01", "0775551234", "قائد مفرزة مستشفى الأمير هاشم بن الحسين العسكري"),
        ("20004", "وكيل", "طارق إبراهيم القضاة", "صيانة عامة", "سلاح الصيانة الملكي", "قائد مفرزة مستشفى الأميرة هيا", "عجلون", jerash_id, "2020-01-01", "0778889900", "قائد مفرزة مستشفى الأميرة هيا بنت الحسين العسكري"),
        ("20005", "نقيب", "عمر يوسف العدوان", "هندسة صيانة وتشغيل", "سلاح الصيانة الملكي", "قائد مفرزة مستشفى الملكة علياء", "عمان", alia_id, "2020-01-01", "0771122334", "قائد مفرزة مستشفى الملكة علياء العسكري")
    ]
    for mil_id, rnk, name, spec, cat, job, res, d_id, j_date, ph, notes in commanders_in_techs:
        if d_id:
            cursor.execute("""
            INSERT OR REPLACE INTO technicians (
                military_id, rank, full_name, specialty, primary_category, current_job, residence, current_detachment_id, join_date, phone_number, evaluation_and_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (mil_id, rnk, name, spec, cat, job, res, d_id, j_date, ph, notes))

    conn.commit()
    conn.close()
