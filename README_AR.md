# TrustPay Platform - النسخة السحابية الجاهزة

هذا المشروع يشغّل:
- بوت TrustPay الرئيسي.
- بوت TrustPay KYC للتوثيق.
- لوحة إدارة للمراجعة والقبول والرفض.
- قاعدة بيانات SQLite.
- رفع صور الهوية والسيلفي.
- طلبات إيداع وسحب ودعم.

> مهم جداً: لا تضع توكنات البوت داخل GitHub. ضعها فقط في Environment Variables داخل Render أو Railway.

---

## 1) قبل كل شيء: غيّر التوكنات المكشوفة
لأن التوكنات ظهرت في المحادثة، افتح BotFather الآن:
https://t.me/BotFather

ثم:
1. اكتب `/mybots`
2. اختر البوت الأول TrustPay_Bot
3. Bot Settings
4. API Token
5. Revoke current token
6. انسخ التوكن الجديد واحفظه عندك فقط
7. كرر نفس الشيء مع TrustPayKYC_Bot

---

## 2) أسماء البوتات المقترحة
- البوت الرئيسي: `@TrustPay_Bot`
- بوت التوثيق: `@TrustPayKYC_Bot`
- اسم المنصة: `TrustPay`
- لوحة الإدارة: `/admin/login`

---

## 3) الحصول على Telegram ID حقك
افتح هذا البوت:
https://t.me/userinfobot

انسخ الرقم الذي يظهر لك، وضعه لاحقاً في المتغير:
`ADMIN_IDS`

مثال:
`ADMIN_IDS=123456789`

إذا عندك أكثر من مشرف:
`ADMIN_IDS=123456789,987654321`

---

## 4) رفع المشروع إلى GitHub من الجوال
1. افتح GitHub:
   https://github.com
2. اضغط + ثم New repository
3. الاسم مثلاً:
   `trustpay-platform`
4. اجعله Private أفضل
5. ارفع ملفات المشروع كلها

لا ترفع ملف `.env` أبداً.

---

# الطريقة الأولى والأسهل: Render مجاناً
رابط Render:
https://render.com

## خطوات Render من الجوال
1. سجل دخول Render بحساب GitHub.
2. اضغط New +
3. اختر Web Service.
4. اختر Repository الذي رفعت فيه المشروع.
5. Render سيقرأ Dockerfile تلقائياً.
6. في Environment أضف المتغيرات التالية:

```env
MAIN_BOT_TOKEN=التوكن_الجديد_للبوت_الرئيسي
KYC_BOT_TOKEN=التوكن_الجديد_لبوت_التوثيق
ADMIN_IDS=ايدي_حسابك_في_تلجرام
ADMIN_USERNAME=admin
ADMIN_PASSWORD=كلمة_مرور_قوية
BRAND_NAME=TrustPay
PUBLIC_BASE_URL=https://اسم-الخدمة.onrender.com
WHATSAPP_URL=https://wa.me/9677XXXXXXXX
DATABASE_PATH=/app/data/trustpay.db
UPLOAD_DIR=/app/data/uploads
```

7. اضغط Deploy.
8. بعد التشغيل افتح:
`https://اسم-الخدمة.onrender.com/admin/login`

وسجل دخول بـ:
- username من `ADMIN_USERNAME`
- password من `ADMIN_PASSWORD`

ملاحظة: خطة Render المجانية قد تنام إذا لم يكن هناك استخدام. إذا أردت تشغيل أقوى 24 ساعة فعلياً، استخدم Railway أو VPS لاحقاً.

---

# الطريقة الثانية: Railway
رابط Railway:
https://railway.app

## خطوات Railway
1. سجل دخول بحساب GitHub.
2. New Project.
3. Deploy from GitHub repo.
4. اختر المشروع.
5. افتح Variables وأضف نفس المتغيرات:

```env
MAIN_BOT_TOKEN=التوكن_الجديد_للبوت_الرئيسي
KYC_BOT_TOKEN=التوكن_الجديد_لبوت_التوثيق
ADMIN_IDS=ايدي_حسابك_في_تلجرام
ADMIN_USERNAME=admin
ADMIN_PASSWORD=كلمة_مرور_قوية
BRAND_NAME=TrustPay
PUBLIC_BASE_URL=https://رابط-railway.app
WHATSAPP_URL=https://wa.me/9677XXXXXXXX
DATABASE_PATH=/app/data/trustpay.db
UPLOAD_DIR=/app/data/uploads
```

6. اضغط Deploy.
7. افتح الرابط الذي يعطيك Railway.
8. لوحة الإدارة:
`/admin/login`

---

## 5) تشغيل واختبار البوت
بعد Deploy:
1. افتح `@TrustPay_Bot`
2. اضغط Start
3. سيقول لك أن الحساب يحتاج توثيق
4. اضغط توثيق الحساب
5. سينقلك إلى `@TrustPayKYC_Bot`
6. أكمل البيانات والصور
7. افتح لوحة الإدارة
8. ادخل على طلب KYC
9. اضغط قبول
10. ارجع للبوت الرئيسي واضغط Start
11. ستظهر خدمات الإيداع والسحب

---

## 6) ماذا تفعل لوحة الإدارة؟
- مشاهدة طلبات KYC.
- قبول أو رفض التوثيق.
- تفعيل المستخدم تلقائياً عند القبول.
- مشاهدة طلبات الإيداع والسحب.
- حفظ سجل العمليات.

---

## 7) نص مهم للأمان والقانون
إذا ستقدم خدمات بيع وشراء USDT أو تحويل أموال، تأكد من القوانين والتراخيص في بلدك. لا تستخدم بيانات الهوية إلا لغرض التحقق، ولا تشاركها مع أحد.

---

## 8) تطويرات المرحلة التالية
بعد تشغيل النسخة الأولى، يمكن إضافة:
- Telegram Mini App بواجهة أجمل.
- PostgreSQL بدل SQLite.
- Cloud Storage مشفر للصور.
- نظام إحالات.
- مستويات VIP.
- حاسبة سعر USDT.
- كشف حساب PDF.
- إشعارات أسعار.
