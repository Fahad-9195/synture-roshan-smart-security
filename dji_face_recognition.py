import cv2
import numpy as np
from pathlib import Path
import sys
import time
import ctypes
from tkinter import Tk, filedialog
import shutil

# Try to use face_recognition if available, otherwise fall back to OpenCV-based matcher
try:
    import face_recognition
    HAS_FACE_RECOG = True
except Exception:
    HAS_FACE_RECOG = False

# تحديد مسار الصورة مقابل مكان السكربت
HERE = Path(__file__).parent
face_path = HERE / "face.png"
AUTH_DIR = HERE / "authorized"

# Ensure authorized dir exists
AUTH_DIR.mkdir(exist_ok=True)

# إذا لم توجد صورة، افتح نافذة اختيار الملف مباشرة
if not face_path.exists() and len(list(AUTH_DIR.glob('*.png')) + list(AUTH_DIR.glob('*.jpg')) + list(AUTH_DIR.glob('*.jpeg'))) == 0:
    print("="*60)
    print("لم يتم العثور على صورة مصرح بها.")
    print("سيتم فتح نافذة لاختيار صورة وجهك من جهازك...")
    print("="*60)
    
    # فتح نافذة اختيار ملف مباشرة
    print("\nافتح نافذة اختيار الملف...")
    root = Tk()
    root.withdraw()  # إخفاء النافذة الرئيسية
    root.attributes('-topmost', True)  # جعل النافذة في المقدمة
    
    file_path = filedialog.askopenfilename(
        title="اختر صورة وجهك المصرح به",
        filetypes=[
            ("Image files", "*.png *.jpg *.jpeg *.bmp"),
            ("All files", "*.*")
        ]
    )
    root.destroy()
    
    if file_path:
        # نسخ الصورة المختارة
        shutil.copy(file_path, str(face_path))
        print(f"\n✓ تم حفظ الصورة بنجاح!")
        print(f"  الصورة: {face_path.name}")
        print(f"  من: {file_path}")
        print("\nسيبدأ البرنامج الآن في مراقبة الكاميرا...")
        print("="*60)
    else:
        print("\n✗ لم يتم اختيار صورة!")
        print("يجب اختيار صورة لتشغيل البرنامج.")
        sys.exit(1)

# تحميل صور مصرح بها متعددة من المجلد 'authorized' أو الافتراضي face.png
authorized_encodings = []
authorized_orb_list = []  # list of (kp, des)

# prepare cascade and orb for fallback
cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(cascade_path)
orb = cv2.ORB_create(nfeatures=500)

# collect files: prefer files in AUTH_DIR, but fallback to face.png if AUTH_DIR empty
files = list(AUTH_DIR.glob('*.png')) + list(AUTH_DIR.glob('*.jpg')) + list(AUTH_DIR.glob('*.jpeg'))
if not files and face_path.exists():
    files = [face_path]

if not files:
    print(f"لم يتم العثور على أي صور مصرح بها في: {AUTH_DIR} ولا توجد face.png")
    sys.exit(1)

print("جاري تحميل الصور المصرح بها...")
for f in files:
    try:
        if HAS_FACE_RECOG:
            img = face_recognition.load_image_file(str(f))
            # كشف الوجوه فقط
            face_locs = face_recognition.face_locations(img, model="hog")
            if face_locs:
                encs = face_recognition.face_encodings(img, face_locs)
                if encs:
                    authorized_encodings.append(encs[0])
                    print(f"  ✓ تم تحميل وجه من: {f.name}")
        # OpenCV fallback: التركيز على الوجه فقط
        data = f.read_bytes()
        arr = np.frombuffer(data, dtype=np.uint8)
        img_cv = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img_cv is None:
            continue
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        # استخدام معاملات أفضل لكشف الوجه فقط
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.05, minNeighbors=6, minSize=(30, 30))
        if len(faces) == 0:
            continue
        # استخدام أكبر وجه مكتشف (الأقرب للكاميرا)
        faces_sorted = sorted(faces, key=lambda x: x[2] * x[3], reverse=True)
        x, y, w, h = faces_sorted[0]
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (200, 200))
        kp, des = orb.detectAndCompute(face_roi, None)
        if des is not None:
            authorized_orb_list.append((kp, des))
    except Exception as e:
        continue

if HAS_FACE_RECOG and not authorized_encodings:
    print("⚠ تحذير: لم يتم اكتشاف وجه في الصور — تأكد من وجود وجه واضح")

if not authorized_orb_list:
    print("⚠ تحذير: وضع OpenCV الاحتياطي قد لا يعمل بدقة")

print(f"\n✓ تم تحميل {len(authorized_encodings) if HAS_FACE_RECOG else len(authorized_orb_list)} وجه مصرح به")
print("="*60)

# الكاميرا ما تفتح تلقائياً - المستخدم يتحكم
video_capture = None
camera_active = False
window_created = False  # تتبع إنشاء النافذة

print("\n" + "="*60)
print("التحكم بالكاميرا:")
print("  اضغط 's' = تشغيل/فتح الكاميرا")
print("  اضغط 'p' = إيقاف/إغلاق الكاميرا")
print("  اضغط 'q' = خروج من البرنامج")
print("="*60)
print("\nجاهز - اضغط 's' لتشغيل الكاميرا...\n")

# إنشاء نافذة واحدة فقط
cv2.namedWindow('Face Recognition - S:تشغيل | P:إيقاف | Q:خروج', cv2.WINDOW_NORMAL)
window_created = True

# حالة التنبيه: إظهار تحذير واحد لكل حالة حضور مستمر
authorized_alerted = False
unauthorized_alerted = False
presence_reset_time = 15.0  # ثانية: وقت أطول قبل إعادة التهيئة
last_presence_time = 0.0
# تتبع للوجوه غير المعروفة: لتجنّب التنبيه أكثر من مرة لنفس الوجه
unknown_encodings = []            # for face_recognition mode
unknown_enc_last_seen = []
unknown_enc_alerted = []

unknown_orb_db = []               # list of descriptors for ORB fallback
unknown_orb_last_seen = []
unknown_orb_alerted = []

unknown_cleanup_time = 60.0  # وقت أطول لتنظيف الوجوه القديمة
alert_cooldown = 10.0  # وقت انتظار أطول بين التحذيرات (10 ثواني)
last_alert_time = 0.0

# متغيرات للتأكد من الوجه قبل التحذير
face_detection_frames = {}  # تتبع عدد الإطارات لكل وجه
min_frames_for_alert = 8  # تقليل العدد للاستجابة الأسرع

while True:
    # التحكم بالكاميرا
    key = cv2.waitKey(1) & 0xFF
    
    # تشغيل الكاميرا
    if key == ord('s') and not camera_active:
        print("\n⏳ جاري فتح الكاميرا...")
        print("محاولة فتح الكاميرا الخارجية...")
        
        # محاولة فتح الكاميرات المتاحة بالترتيب (1 للخارجية، 0 للمدمجة)
        camera_found = False
        for camera_index in [1, 0, 2]:  # جرب الكاميرا الخارجية أولاً
            print(f"  جاري اختبار الكاميرا رقم {camera_index}...")
            video_capture = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
            if video_capture.isOpened():
                # اختبار قراءة إطار للتأكد من عمل الكاميرا
                ret, test_frame = video_capture.read()
                if ret and test_frame is not None:
                    camera_active = True
                    camera_found = True
                    print(f"✅ تم فتح الكاميرا رقم {camera_index} بنجاح")
                    break
                else:
                    video_capture.release()
            
        if not camera_found:
            print("❌ خطأ: لا يمكن فتح أي كاميرا")
            video_capture = None
            continue
        
        print("✅ الكاميرا تعمل الآن - جاري كشف الوجوه...")
    
    # إيقاف الكاميرا
    elif key == ord('p') and camera_active:
        print("\n⏸️  إيقاف الكاميرا...")
        if video_capture is not None:
            video_capture.release()
        # لا نغلق النافذة - فقط نعرض شاشة سوداء
        camera_active = False
        video_capture = None
        print("✅ تم إيقاف الكاميرا")
        print("اضغط 's' لإعادة التشغيل...\n")
        continue
    
    # الخروج
    elif key == ord('q'):
        print("\n👋 إغلاق البرنامج...")
        break
    
    # إذا الكاميرا مو شغالة، انتظر وعرض شاشة فارغة
    if not camera_active or video_capture is None:
        # عرض شاشة سوداء مع رسالة
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, "Camera OFF - Press 'S' to start", (120, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Face Recognition - S:تشغيل | P:إيقاف | Q:خروج', blank)
        time.sleep(0.1)
        continue
    
    ret, frame = video_capture.read()
    if not ret or frame is None:
        print("⚠️  خطأ في قراءة الكاميرا")
        time.sleep(0.1)
        continue
    
    rgb_frame = frame[:, :, ::-1]  # تحويل BGR إلى RGB

    # تتبع ما إذا وجدنا وجهاً مصرحاً أو غير مصرح به في هذه الإطار
    found_authorized = False
    found_unauthorized = False
    if HAS_FACE_RECOG:
        # كشف الوجوه فقط مع نموذج HOG (أسرع وأفضل)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        
        # فلتر: تجاهل المناطق الصغيرة جداً أو الكبيرة جداً (ليست وجوه)
        valid_face_locations = []
        for (top, right, bottom, left) in face_locations:
            height = bottom - top
            width = right - left
            aspect_ratio = width / height if height > 0 else 0
            area = width * height
            
            # فلاتر مرنة للوجه الحقيقي
            # تقبل نطاق واسع من الأحجام والأشكال
            if (0.6 < aspect_ratio < 1.4 and        # نسبة طبيعية واسعة
                2000 < area < 120000 and            # مساحة واسعة جداً
                width > 40 and height > 40):        # حجم أدنى صغير
                valid_face_locations.append((top, right, bottom, left))
        
        if not valid_face_locations:
            face_locations = []
        else:
            face_locations = valid_face_locations
        
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            authorized = False
            if authorized_encodings:
                # مقارنة مرنة تتحمل اختلاف الإضاءة والزوايا
                matches = face_recognition.compare_faces(authorized_encodings, face_encoding, tolerance=0.65)
                face_distances = face_recognition.face_distance(authorized_encodings, face_encoding)
                # يعتبر مطابق إذا كانت المسافة معقولة (أكثر مرونة)
                authorized = any(matches) or (len(face_distances) > 0 and min(face_distances) < 0.65)
            # ارسم مستطيل ووسم على الإطار (frame) بالوضع BGR
            color = (0, 255, 0) if authorized else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            label = "مصرح" if authorized else "غير مصرح"
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

            if authorized:
                found_authorized = True
            else:
                # Handle unknown face deduplication + alert once
                found_unauthorized = True
                now = time.time()
                matched = False
                # compare against existing unknown encodings
                for i, uenc in enumerate(unknown_encodings):
                    try:
                        dist = face_recognition.face_distance([uenc], face_encoding)[0]
                    except Exception:
                        dist = 1.0
                    if dist < 0.6:
                        # same unknown face
                        unknown_enc_last_seen[i] = now
                        matched = True
                        # لا نحذر هنا - سيتم في نظام العداد الموحد
                        break
                if not matched:
                    # new unknown face -> add but DON'T alert yet
                    unknown_encodings.append(face_encoding)
                    unknown_enc_last_seen.append(now)
                    unknown_enc_alerted.append(False)  # لم يتم التحذير بعد
                    # سيتم التحذير في القسم التالي بعد التأكد
    else:
        # كشف الوجوه فقط باستخدام Haar Cascade مع فلترة قوية
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # إعدادات مرنة لكشف الوجوه في ظروف مختلفة
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1,         # أسرع وأكثر مرونة
            minNeighbors=5,          # أقل صرامة
            minSize=(50, 50),        # حجم أدنى صغير
            maxSize=(500, 500),      # حجم أقصى أكبر
            flags=cv2.CASCADE_SCALE_IMAGE
        )
        
        # فلتر مرن جداً: قبول نطاق واسع من الوجوه
        valid_faces = []
        for (x, y, w, h) in faces:
            aspect_ratio = w / h if h > 0 else 0
            area = w * h
            # قبول نطاق واسع من الأشكال والأحجام
            if (0.6 < aspect_ratio < 1.5 and     # نسبة واسعة جداً
                area > 2500):                    # مساحة صغيرة (50x50)
                valid_faces.append((x, y, w, h))
        
        faces = valid_faces
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            face_roi = cv2.resize(face_roi, (200, 200))
            kp, des = orb.detectAndCompute(face_roi, None)
            match_ratio = 0.0
            if des is not None and authorized_orb_list:
                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                best_ratio = 0.0
                for (auth_kp, auth_des) in authorized_orb_list:
                    if auth_des is None or len(auth_des) == 0:
                        continue
                    if des is None or len(des) == 0:
                        continue
                    try:
                        matches = bf.match(auth_des, des)
                    except Exception:
                        continue
                    good = [m for m in matches if m.distance < 60]
                    denom = max(1, min(len(auth_kp) if auth_kp is not None else 0, len(kp) if kp is not None else 0))
                    ratio = len(good) / denom if denom > 0 else 0.0
                    if ratio > best_ratio:
                        best_ratio = ratio
                match_ratio = best_ratio

            COOLDOWN = 5.0
            if 'last_alert' not in globals():
                last_alert = 0.0

            # عتبة مرنة جداً للمطابقة
            authorized = match_ratio > 0.15
            color = (0, 255, 0) if authorized else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            label = "مصرح" if authorized else "غير مصرح"
            cv2.putText(frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA)

            if authorized:
                found_authorized = True
            else:
                # unknown face detected (OpenCV fallback) -> deduplicate against unknown_orb_db
                found_unauthorized = True
                now = time.time()
                matched = False
                if des is not None:
                    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                    for i, (u_kp, u_des) in enumerate(unknown_orb_db):
                        if u_des is None or len(u_des) == 0:
                            continue
                        try:
                            m = bf.match(u_des, des)
                        except Exception:
                            continue
                        good = [x for x in m if x.distance < 60]
                        denom = max(1, min(len(u_kp) if u_kp is not None else 0, len(kp) if kp is not None else 0))
                        ratio = len(good) / denom if denom > 0 else 0.0
                        # عتبة محسّنة للتطابق
                        if ratio > 0.35:
                            # same unknown
                            unknown_orb_last_seen[i] = now
                            matched = True
                            # لا نحذر هنا - سيتم في نظام العداد الموحد
                            break
                if not matched:
                    # add as new unknown but DON'T alert yet
                    unknown_orb_db.append((kp, des))
                    unknown_orb_last_seen.append(now)
                    unknown_orb_alerted.append(False)  # لم يتم التحذير بعد

    # عرض تنبيه واحد عندما يبدأ ظهور الوجه، وإعادة التهيئة بعد اختفاء الوجه لفترة
    now = time.time()
    # حدّث وقت الوجود في كل إطار يتم فيه اكتشاف وجه
    if found_authorized or found_unauthorized:
        last_presence_time = now

    # التحقق من cooldown قبل عرض تنبيهات جديدة
    now = time.time()
    can_alert = (now - last_alert_time) > alert_cooldown
    
    # عرض رسالة للوجه المصرح به فقط بعد ثباته لعدد إطارات كافٍ
    if found_authorized:
        face_key = 'authorized'
        face_detection_frames[face_key] = face_detection_frames.get(face_key, 0) + 1

        if face_detection_frames[face_key] >= min_frames_for_alert and not authorized_alerted and can_alert:
            try:
                ctypes.windll.user32.MessageBoxW(0, "تم التعرف على الوجه المصرح به", "تأكيد", 0x40)
            except Exception:
                pass
            authorized_alerted = True
            unauthorized_alerted = False
            last_alert_time = now
            face_detection_frames[face_key] = 0  # إعادة تعيين العداد بعد الإشعار

        # إعادة تعيين عداد الوجوه غير المصرح بها إن وجد
        if 'unauthorized' in face_detection_frames:
            face_detection_frames['unauthorized'] = 0
    elif found_unauthorized and not found_authorized:
        # نظام عد الإقارات: لا نحذر إلا بعد رؤية الوجه عدة مرات
        face_key = 'unauthorized'  # مفتاح عام للوجوه غير المصرح بها
        
        if face_key not in face_detection_frames:
            face_detection_frames[face_key] = 0
        
        face_detection_frames[face_key] += 1
        
        # فقط بعد رؤية الوجه 15 إطار متتالية
        if face_detection_frames[face_key] >= min_frames_for_alert and not unauthorized_alerted and can_alert:
            try:
                ctypes.windll.user32.MessageBoxW(0, "تحذير: تم رصد وجه غير مصرح به!", "تحذير", 0x30)
            except Exception:
                pass
            unauthorized_alerted = True
            authorized_alerted = False
            last_alert_time = now
            face_detection_frames[face_key] = 0  # إعادة تعيين بعد التحذير لمنع التكرار
            print("تحذير: وجه غير مصرح به!")
    else:
        # إعادة تعيين العدادات إذا لم يظهر وجه
        if 'unauthorized' in face_detection_frames:
            face_detection_frames['unauthorized'] = 0
        if 'authorized' in face_detection_frames:
            face_detection_frames['authorized'] = 0

    # إذا لم يُر أي وجه لفترة أطول من presence_reset_time نعيد حالة التنبيه
    if not (found_authorized or found_unauthorized):
        if now - last_presence_time > presence_reset_time:
            authorized_alerted = False
            unauthorized_alerted = False
            face_detection_frames.clear()  # إعادة تعيين العداد

    # تنظيف قواعد البيانات للوجوه غير المعروفة بعد مدة طويلة
    # نقوم بإزالة أي سجل لم يُر منذ أكثر من unknown_cleanup_time ثانية
    now = time.time()
    # face_recognition unknowns
    i = 0
    while i < len(unknown_encodings):
        if now - unknown_enc_last_seen[i] > unknown_cleanup_time:
            unknown_encodings.pop(i)
            unknown_enc_last_seen.pop(i)
            unknown_enc_alerted.pop(i)
        else:
            i += 1
    # ORB unknowns
    i = 0
    while i < len(unknown_orb_db):
        if now - unknown_orb_last_seen[i] > unknown_cleanup_time:
            unknown_orb_db.pop(i)
            unknown_orb_last_seen.pop(i)
            unknown_orb_alerted.pop(i)
        else:
            i += 1

    # عرض الكاميرا في نافذة واحدة
    cv2.imshow('Face Recognition - S:تشغيل | P:إيقاف | Q:خروج', frame)

# تنظيف عند الخروج
if video_capture is not None:
    video_capture.release()
cv2.destroyAllWindows()
print("✅ تم إغلاق البرنامج بنجاح")