"""
قاعدة بيانات نظام إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية
Database models, SQLite operations, and seed data initialization.
"""

import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_NAME = "military_maintenance.db"

def get_db_connection(db_path=DB_NAME):
    """إرجاع اتصال بقاعدة بيانات SQLite مع دعم الصفوف كقواميس"""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path=DB_NAME):
    """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة"""
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

    conn.commit()
    conn.close()

    # التحقق من وجود بيانات أولية، إذا كانت فارغة يتم حقن البيانات التجريبية
    seed_if_empty(db_path)

def seed_if_empty(db_path=DB_NAME):
    """حقن بيانات تجريبية في حال كانت الجداول فارغة"""
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

        # 2. إضافة الفنيين الأوليين
        technicians_data = [
            # مستشفى الأمير راشد (إربد)
            ("984512", "رقيب أول", "عبدالله محمود الخصاونة", "تكييف وتبريد", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-01-15", "0795111222", "فني ممتاز، متميز في صيانة الشيلرات المركزية ومحطات الأكسجين."),
            ("874120", "رقيب", "عمر سامي بني هاني", "كهرباء قوى ومحولات", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-06-01", "0788222333", "ملتزم جداً وخبرة ممتازة في لوحات التوزيع الرئيسية."),
            ("652198", "عريف", "سامر فؤاد بطاينة", "شبكات مياه وصحي", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2024-02-10", "0777333444", "أداء جيد، يتابع مضخات المياه العذبة ومحطة التحلية."),

            # مستشفى الأمير علي (الكرك)
            ("741852", "رقيب أول", "حمزة نايف المجالي", "كهرباء قوى ومحولات", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2022-11-01", "0776444555", "كفاءة فنية عالية، يدير لوحات الطوارئ والمولدات الاحتياطية بنجاح."),
            ("963258", "عريف", "ليث خالد الصرايرة", "تكييف وتبريد", hospitals["مستشفى الأمير علي بن الحسين العسكري"], "2023-09-15", "0799555666", "متخصص في وحدات السبليت وغرف العناية الحثيثة."),

            # مستشفى الأمير هاشم (الزرقاء)
            ("852963", "وكيل", "حسام جمال الغويري", "تكييف وتبريد", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2021-08-20", "0785666777", "أقدم فني بالمفرزة، خبرة واسعة في جميع أنظمة التبريد والميكانيك."),
            ("369258", "رقيب", "يزن مخلد العموش", "كهرباء قوى ومحولات", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-03-01", "0774777888", "سرعة استجابة عالية للأعطال الكهربائية الطارئة."),
            ("147852", "جندي أول", "معاذ علي الحنيطي", "شبكات مياه وصحي", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2024-01-10", "0798888999", "فني واعد، منضبط ويؤدي المهام بدقة."),
            ("258147", "عريف", "براء فيصل الخلايلة", "إنشائي عام", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2023-11-20", "0771999000", "أعمال دهان وصيانة عامة للأبواب والقواطع."),

            # مستشفى الأميرة هيا (جرش / عجلون)
            ("357159", "رقيب", "أنس بسام العتوم", "تكييف وتبريد", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2023-05-12", "0789111333", "مسؤول صيانة قسم غسيل الكلى والعناية الحثيثة."),
            ("951357", "عريف", "مؤمن أحمد الزغول", "إنشائي عام", hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2024-04-01", "0772222444", "ملم بأعمال الصيانة الإنشائية والجبس بورد والألمنيوم."),

            # مستشفى الملكة علياء (عمان)
            ("159357", "رقيب أول", "رامي ناصر الحديد", "كهرباء قوى ومحولات", hospitals["مستشفى الملكة علياء العسكري"], "2022-04-10", "0793333555", "خبير صيانة أنظمة UPS والمحولات الرئيسية."),
            ("753951", "رقيب", "جهاد توفيق المناصير", "شبكات مياه وصحي", hospitals["مستشفى الملكة علياء العسكري"], "2023-07-22", "0784444666", "يشرف على شبكات الصرف وغلايات البخار المركزية.")
        ]

        cursor.executemany("""
        INSERT INTO technicians (military_id, rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, technicians_data)
        conn.commit()

        # 3. إضافة سجلات حركات نقل تجريبية سابقة
        movements_data = [
            ("984512", hospitals["مستشفى الملكة علياء العسكري"], hospitals["مستشفى الأمير راشد بن الحسن العسكري"], "2023-01-15", "نقل لسد النقص في صيانة التكييف المركزي بإربد"),
            ("852963", hospitals["مستشفى الأمير راشد بن الحسن العسكري"], hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], "2021-08-20", "نقل بناءً على مقتضيات المصلحة العامة والخبرة الميدانية"),
            ("357159", hospitals["مستشفى الأمير هاشم بن الحسين العسكري"], hospitals["مستشفى الأميرة هيا بنت الحسين العسكري"], "2023-05-12", "نقل لتعزيز كادر المفرزة في مستشفى الأميرة هيا")
        ]

        cursor.executemany("""
        INSERT INTO movement_log (technician_military_id, from_detachment_id, to_detachment_id, effective_date, notes)
        VALUES (?, ?, ?, ?, ?);
        """, movements_data)
        conn.commit()

    conn.close()

# --- دوال الاستعلام والبيانات (Queries) ---

def get_detachments_list():
    """إرجاع قائمة بجميع المفارز كقواميس"""
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
    return rows

def get_detachments_df():
    """إرجاع جدول المفارز كـ DataFrame مع إحصائية عدد الفنيين"""
    conn = get_db_connection()
    query = """
    SELECT 
        d.id as "المعرف",
        d.hospital_name as "اسم المستشفى العسكري",
        d.governorate as "المحافظة",
        d.supervisor_rank as "رتبة المسؤول",
        d.supervisor_name as "اسم مسؤول المفرزة",
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
    """إرجاع بيانات مفرزة محددة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detachments WHERE id = ?;", (detachment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_detachment_shortages(detachment_id, shortages_text):
    """تحديث حقل النواقص والاحتياجات البشرية للمفرزة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE detachments SET staffing_shortages = ? WHERE id = ?;", (shortages_text, detachment_id))
    conn.commit()
    conn.close()
    return True

def update_detachment_info(detachment_id, hospital_name, governorate, supervisor_rank, supervisor_name, contact_phone, notes):
    """تحديث البيانات الأساسية للمفرزة"""
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

def get_all_technicians_df():
    """إرجاع جدول جميع الفنيين مع تفاصيل المستشفى والمحافظة كـ DataFrame"""
    conn = get_db_connection()
    query = """
    SELECT 
        t.military_id as "الرقم العسكري",
        t.rank as "الرتبة",
        t.full_name as "الاسم الرباعي",
        t.specialty as "التخصص الفني",
        COALESCE(d.hospital_name, 'غير محدد') as "المستشفى الحالي",
        COALESCE(d.governorate, 'غير محدد') as "المحافظة",
        t.join_date as "تاريخ الالتحاق بالمفرزة",
        t.phone_number as "رقم الهاتف",
        t.evaluation_and_notes as "الملاحظات والتقييم الفني",
        t.current_detachment_id as detachment_id
    FROM technicians t
    LEFT JOIN detachments d ON t.current_detachment_id = d.id
    ORDER BY t.rank ASC, t.full_name ASC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_technicians_by_detachment_df(detachment_id):
    """إرجاع فنيي مفرزة محددة كـ DataFrame"""
    conn = get_db_connection()
    query = """
    SELECT 
        t.military_id as "الرقم العسكري",
        t.rank as "الرتبة",
        t.full_name as "الاسم الرباعي",
        t.specialty as "التخصص الفني",
        t.join_date as "تاريخ الالتحاق بالمفرزة",
        t.phone_number as "رقم الهاتف",
        t.evaluation_and_notes as "الملاحظات والتقييم الفني"
    FROM technicians t
    WHERE t.current_detachment_id = ?
    ORDER BY t.rank ASC, t.full_name ASC;
    """
    df = pd.read_sql_query(query, conn, params=(detachment_id,))
    conn.close()
    return df

def get_technician_by_id(military_id):
    """إرجاع بيانات فني محدد برقمه العسكري"""
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

def add_technician(military_id, rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes):
    """إضافة فني جديد إلى المنظومة"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO technicians (military_id, rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (military_id, rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes))
        conn.commit()
        success = True
        err = None
    except sqlite3.IntegrityError as e:
        success = False
        err = "الرقم العسكري مسجل مسبقاً في المنظومة."
    except Exception as e:
        success = False
        err = str(e)
    finally:
        conn.close()
    return success, err

def update_technician(military_id, rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes):
    """تعديل بيانات فني موجود"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        UPDATE technicians 
        SET rank = ?, full_name = ?, specialty = ?, current_detachment_id = ?, join_date = ?, phone_number = ?, evaluation_and_notes = ?
        WHERE military_id = ?;
        """, (rank, full_name, specialty, current_detachment_id, join_date, phone_number, evaluation_and_notes, military_id))
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
    except Exception as e:
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
        # قراءة المفرزة الحالية
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
        t.specialty as "التخصص الفني",
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

    # التوزيع حسب التخصص
    cursor.execute("""
    SELECT specialty, COUNT(*) as count 
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
