# تشغيل TalkinChat على Altare — Python 3.13 + Node.js 22

## إعدادات Altare

- Docker image: `ghcr.io/parkervcp/yolks:python_3.13`
- `PY_FILE=bot.py`
- `REQUIREMENTS_FILE=requirements.txt`
- Startup command: `bash start.sh`
- Python: 3.13

لا تغيّر صورة Python الحالية إذا كانت تشغّل الاتصال بالغرف بشكل صحيح. يقوم `start.sh` بفحص Node.js الموجود، ثم يستخدم Node.js 22+ إذا كان متاحاً. إذا لم يجده، ينزّل أحدث إصدار مستقر من سلسلة Node 22 من `nodejs.org`، ويتحقق من SHA-256 قبل تشغيل البوت، ويضعه في `.runtime/node22`.

يحتاج التثبيت الأول فقط إلى اتصال صادر بـ `nodejs.org`. بعد نجاحه يُعاد استخدام الملف المحلي في التشغيلات التالية ما دامت ملفات `.runtime` محفوظة على مساحة التخزين.

## متغيرات ENV

استمر باستخدام متغيرات TalkinChat الحالية دون تغيير. متغيرات الموسيقى المهمة:

- `YOUTUBE_COOKIES`: محتوى Netscape Cookies كنص سري (اختياري، لكنه موصى به عند طلب YouTube التحقق).
- `YOUTUBE_COOKIES_FILE`: مسار ملف Netscape Cookies مركّب (بديل عن النص).
- `YOUTUBE_COOKIES_2`: حساب Cookies إضافي اختياري.
- `MUSIC_MAX_SECONDS`: الحد الأقصى لطول المقطع، الافتراضي 900.
- `MUSIC_MAX_MB`: الحد الأقصى لحجم الملف، الافتراضي 64.
- `PUBLIC_MEDIA_URL`: رابط HTTPS/HTTP العام الذي يستخدمه نظام إرسال الوسائط الحالي.
- `NODE_BINARY`: اختياري؛ مسار مطلق إلى Node.js 22+ إذا كان مثبتاً خارج PATH.
- `NODE_RUNTIME_DIR`: اختياري؛ مكان حفظ Node.js الذي يثبته البرنامج تلقائياً، الافتراضي `.runtime/node22`.

لا تضع قيم Cookies داخل `start.sh` أو `requirements.txt` أو ملفات المشروع المرفوعة. أضفها كمتغيرات سرية في Altare.

## اختبار التشغيل

1. ارفع ZIP كاملاً واستخرج محتوياته في مجلد الخدمة.
2. تأكد أن `requirements.txt` يُستخدم لتثبيت المتطلبات.
3. اضبط Startup command إلى `bash start.sh`.
4. شغّل الخدمة وانتظر رسائل `[NODE] Ready` ثم `[START] Node: v22...`.
5. في سجل البوت، ابحث عن `[MEDIA_DIAGNOSTICS]` وتأكد من ظهور `yt_dlp=...` و`JS=node=v22...` و`ffmpeg=yes`.
6. اختبر أولاً رابط YouTube عام، ثم جرّب اسم أغنية. اختبر إرسال الصوت في غرفة TalkinChat كما اعتدت.
7. عند الفشل، احتفظ بسجل `[MUSIC][YOUTUBE_DOWNLOAD]` و`[MEDIA_DIAGNOSTICS]`؛ لا ترسل محتوى Cookies في السجل.

## ملاحظات مهمة

- لم يتغير بروتوكول TalkinChat ولا `send_room_media`.
- Node.js هو محرك JavaScript الأول لـ yt-dlp/EJS؛ Deno يبقى احتياطاً برمجياً إن توفر.
- يبقى مسار التنزيل القديم ومصادر SoundCloud/Audius/Jamendo/Internet Archive كما هي.
- لا يتطلب المشروع `npm install` أو `node_modules`؛ لا توجد ملفات JavaScript خاصة بالمشروع.
- يجب أن تكون مساحة `.runtime` قابلة للكتابة. إذا كانت مساحة الحاوية مؤقتة، قد يُعاد تنزيل Node عند إعادة إنشاء الحاوية.
## حفظ ملفات الأغاني على قرص Altare
اضبط متغير البيئة `BOT_DATA_DIR=data` بعد إنشاء مجلد `data` بجوار `bot.py` في قسم **Files**. سيحفظ البوت ملفات الأغاني وبيانات آخر أغنية داخل هذا المجلد، لا في RAM. لا تحذف هذا المجلد عند تحديث الكود؛ راجع `ALTARE_DATA_STORAGE_AR.md` لتفاصيل الإعداد والنسخ الاحتياطي.
