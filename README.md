# نظام إدارة القوى البشرية ومرتبات مفارز صيانة المستشفيات العسكرية بالمحافظات

تطبيق ويب تفاعلي محلي مبني باستخدام **Python** و **Streamlit** و **Pandas** و **SQLite**، بواجهة عربية كاملة (RTL) لإدارة مرتبات الفنيين والمفارز وحركات النقل ومتابعة النواقص والاحتياجات البشرية بالمستشفيات العسكرية.

## 🚀 طريقة التشغيل السريع:

```powershell
.\.venv\Scripts\streamlit.exe run app.py
```

أو من خلال Python العام إذا كانت الحزم مثبتة:
```powershell
streamlit run app.py
```

الرابط المحلي للتطبيق: `http://localhost:8501`

## 🗂️ هيكلية الملفات:
- [`app.py`](file:///d:/Rami/maf/app.py): واجهة المستخدم وشاشات Streamlit الأربعة.
- [`database.py`](file:///d:/Rami/maf/database.py): نماذج قاعدة بيانات SQLite، عمليات CRUD، وسجل النقل، والبيانات الأولية.
- [`styles.py`](file:///d:/Rami/maf/styles.py): التنسيقات البصرية والخطوط ودعم RTL الكامل.
- [`requirements.txt`](file:///d:/Rami/maf/requirements.txt): مكتبات وحزم المشروع.
- [`military_maintenance.db`](file:///d:/Rami/maf/military_maintenance.db): قاعدة بيانات SQLite.
