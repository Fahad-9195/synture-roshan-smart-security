// نظام الترجمة الاحترافي - عربي/إنجليزي
const translations = {
    ar: {
        // صفحة الترحيب
        welcome_title: "نظام الأمان الذكي",
        welcome_subtitle: "مرحباً بك في منصة أبشر المتكاملة",
        welcome_tagline: "للأمن المدني والعمليات الميدانية",
        welcome_powered: "تطوير فريق",
        choose_account: "اختر نوع الحساب",
        choose_subtitle: "الرجاء تحديد نوع حسابك المناسب",
        
        // قسم الأفراد
        home_title: "أفراد",
        home_description: "نظام الأمان المنزلي الذكي للأفراد والعائلات",
        home_feature1: "مراقبة منزلك على مدار الساعة",
        home_feature2: "تنبيهات فورية للأحداث الأمنية",
        home_feature3: "إرسال بلاغات الشرطة",
        home_feature4: "خرائط تفاعلية للأجهزة",
        home_feature5: "تقارير المشكلات المتقدم",
        home_login: "تحويل للأفراد",
        
        // قسم الأمن الميداني
        military_title: "الأمن الميداني",
        military_description: "نظام إدارة الدوريات والعمليات الأمنية الميدانية",
        military_feature1: "متابعة الدوريات الأمنية",
        military_feature2: "إدارة الحالات الطارئة",
        military_feature3: "تتبع GPS للدوريات",
        military_feature4: "تحليل أوقات الاستجابة",
        military_feature5: "مركز العمليات الميداني",
        military_login: "تحويل للعسكريين",
        
        // أزرار مشتركة
        events_dashboard: "تتبع الاستعدادات الموسمية",
        
        // لوحة التحكم المدنية
        dashboard_title: "لوحة التحكم",
        dashboard_welcome: "مرحباً بك",
        dashboard_home_security: "أمان المنزل",
        system_status: "حالة النظام",
        all_systems: "جميع الأنظمة",
        operational: "تعمل بشكل سليم",
        devices: "الأجهزة",
        active_devices: "جهاز نشط",
        last_24h: "آخر 24 ساعة",
        alerts: "التنبيهات",
        pending_alerts: "تنبيه معلق",
        requires_attention: "يتطلب الاهتمام",
        events: "الأحداث",
        recorded_events: "حدث مسجل",
        this_week: "هذا الأسبوع",
        
        // الأجهزة
        device_id: "رقم الجهاز",
        device_type: "نوع الجهاز",
        location: "الموقع",
        status: "الحالة",
        battery: "البطارية",
        last_update: "آخر تحديث",
        active: "نشط",
        inactive: "غير نشط",
        
        // أنواع الأجهزة
        camera: "كاميرا",
        door_sensor: "مستشعر باب",
        motion_sensor: "مستشعر حركة",
        smoke_detector: "كاشف دخان",
        
        // المواقع
        main_entrance: "المدخل الرئيسي",
        living_room: "غرفة المعيشة",
        backyard: "الفناء الخلفي",
        kitchen: "المطبخ",
        garage: "الجراج",
        bedroom: "غرفة النوم",
        
        // الأحداث الأخيرة
        recent_events: "الأحداث الأخيرة",
        event_time: "الوقت",
        event_device: "الجهاز",
        event_type: "نوع الحدث",
        event_description: "الوصف",
        motion_detected: "تم اكتشاف حركة",
        door_opened: "تم فتح الباب",
        camera_activated: "تم تفعيل الكاميرا",
        smoke_alarm: "إنذار دخان",
        
        // التنبيهات
        alert_pending: "معلق",
        alert_resolved: "تم الحل",
        high_priority: "أولوية عالية",
        medium_priority: "أولوية متوسطة",
        low_priority: "أولوية منخفضة",
        
        // الإجراءات
        view_details: "عرض التفاصيل",
        mark_resolved: "وضع علامة كمحلول",
        delete: "حذف",
        export_data: "تصدير البيانات",
        import_data: "استيراد البيانات",
        generate_report: "إنشاء تقرير",
        
        // مركز العمليات
        operations_center: "مركز العمليات الميدانية",
        operations_welcome: "مرحباً بك في",
        field_security: "الأمن الميداني",
        patrol_tracking: "تتبع الدوريات",
        officers_on_duty: "ضابط في الخدمة",
        active_patrols: "دورية نشطة",
        avg_response: "متوسط الاستجابة",
        response_time: "دقيقة",
        incidents_today: "حادث اليوم",
        total_incidents: "إجمالي الحوادث",
        
        // ضباط الدورية
        patrol_officers: "ضباط الدورية",
        officer_id: "رقم الضابط",
        officer_name: "اسم الضابط",
        officer_status: "الحالة",
        officer_location: "الموقع",
        last_reported: "آخر بلاغ",
        on_patrol: "في دورية",
        available: "متاح",
        off_duty: "خارج الخدمة",
        
        // الحوادث
        recent_incidents: "الحوادث الأخيرة",
        incident_id: "رقم الحادث",
        incident_type: "نوع الحادث",
        incident_priority: "الأولوية",
        incident_status: "الحالة",
        incident_officer: "الضابط المكلف",
        incident_time: "الوقت",
        
        // أنواع الحوادث
        theft: "سرقة",
        vandalism: "تخريب",
        suspicious_activity: "نشاط مشبوه",
        traffic_violation: "مخالفة مرورية",
        emergency: "طارئ",
        
        // صفحة تسجيل الدخول
        login_title: "تسجيل الدخول",
        login_subtitle: "مركز العمليات الميدانية",
        username: "اسم المستخدم",
        password: "كلمة المرور",
        login_button: "تسجيل الدخول",
        back_to_home: "العودة للرئيسية",
        
        // الأزرار العامة
        logout: "تسجيل الخروج",
        refresh: "تحديث",
        settings: "الإعدادات",
        help: "مساعدة",
        about: "عن النظام",
        
        // الرسائل
        loading: "جاري التحميل...",
        no_data: "لا توجد بيانات",
        error: "خطأ في تحميل البيانات",
        success: "تمت العملية بنجاح",
        confirm_delete: "هل أنت متأكد من الحذف؟",
        
        // الأيام والأوقات
        monday: "الإثنين",
        tuesday: "الثلاثاء",
        wednesday: "الأربعاء",
        thursday: "الخميس",
        friday: "الجمعة",
        saturday: "السبت",
        sunday: "الأحد",
        
        today: "اليوم",
        yesterday: "أمس",
        this_month: "هذا الشهر",
        
        // وحدات القياس
        minutes: "دقائق",
        hours: "ساعات",
        days: "أيام",
        meters: "متر",
        kilometers: "كيلومتر"
    },
    
    en: {
        // Welcome Page
        welcome_title: "Smart Security System",
        welcome_subtitle: "Welcome to Absher Integrated Platform",
        welcome_tagline: "For Civil Security and Field Operations",
        welcome_powered: "Powered by",
        choose_account: "Choose Account Type",
        choose_subtitle: "Please select your appropriate account type",
        
        // Civilian Section
        home_title: "Civilians",
        home_description: "Smart Home Security System for Individuals and Families",
        home_feature1: "Monitor your home 24/7",
        home_feature2: "Instant alerts for security events",
        home_feature3: "Police report submission",
        home_feature4: "Interactive device maps",
        home_feature5: "Advanced incident reports",
        home_login: "Civilian Access",
        
        // Field Security Section
        military_title: "Field Security",
        military_description: "Patrol Management and Field Security Operations System",
        military_feature1: "Security patrol monitoring",
        military_feature2: "Emergency incident management",
        military_feature3: "GPS patrol tracking",
        military_feature4: "Response time analysis",
        military_feature5: "Field operations center",
        military_login: "Military Access",
        
        // Common Buttons
        events_dashboard: "Track Seasonal Preparations",
        
        // Civilian Dashboard
        dashboard_title: "Dashboard",
        dashboard_welcome: "Welcome",
        dashboard_home_security: "Home Security",
        system_status: "System Status",
        all_systems: "All Systems",
        operational: "Operational",
        devices: "Devices",
        active_devices: "Active Devices",
        last_24h: "Last 24 Hours",
        alerts: "Alerts",
        pending_alerts: "Pending Alerts",
        requires_attention: "Requires Attention",
        events: "Events",
        recorded_events: "Recorded Events",
        this_week: "This Week",
        
        // Devices
        device_id: "Device ID",
        device_type: "Type",
        location: "Location",
        status: "Status",
        battery: "Battery",
        last_update: "Last Update",
        active: "Active",
        inactive: "Inactive",
        
        // Device Types
        camera: "Camera",
        door_sensor: "Door Sensor",
        motion_sensor: "Motion Sensor",
        smoke_detector: "Smoke Detector",
        
        // Locations
        main_entrance: "Main Entrance",
        living_room: "Living Room",
        backyard: "Backyard",
        kitchen: "Kitchen",
        garage: "Garage",
        bedroom: "Bedroom",
        
        // Recent Events
        recent_events: "Recent Events",
        event_time: "Time",
        event_device: "Device",
        event_type: "Event Type",
        event_description: "Description",
        motion_detected: "Motion Detected",
        door_opened: "Door Opened",
        camera_activated: "Camera Activated",
        smoke_alarm: "Smoke Alarm",
        
        // Alerts
        alert_pending: "Pending",
        alert_resolved: "Resolved",
        high_priority: "High Priority",
        medium_priority: "Medium Priority",
        low_priority: "Low Priority",
        
        // Actions
        view_details: "View Details",
        mark_resolved: "Mark as Resolved",
        delete: "Delete",
        export_data: "Export Data",
        import_data: "Import Data",
        generate_report: "Generate Report",
        
        // Operations Center
        operations_center: "Field Operations Center",
        operations_welcome: "Welcome to",
        field_security: "Field Security",
        patrol_tracking: "Patrol Tracking",
        officers_on_duty: "Officers on Duty",
        active_patrols: "Active Patrols",
        avg_response: "Avg Response",
        response_time: "Minutes",
        incidents_today: "Incidents Today",
        total_incidents: "Total Incidents",
        
        // Patrol Officers
        patrol_officers: "Patrol Officers",
        officer_id: "Officer ID",
        officer_name: "Name",
        officer_status: "Status",
        officer_location: "Location",
        last_reported: "Last Reported",
        on_patrol: "On Patrol",
        available: "Available",
        off_duty: "Off Duty",
        
        // Incidents
        recent_incidents: "Recent Incidents",
        incident_id: "Incident ID",
        incident_type: "Type",
        incident_priority: "Priority",
        incident_status: "Status",
        incident_officer: "Assigned Officer",
        incident_time: "Time",
        
        // Incident Types
        theft: "Theft",
        vandalism: "Vandalism",
        suspicious_activity: "Suspicious Activity",
        traffic_violation: "Traffic Violation",
        emergency: "Emergency",
        
        // Login Page
        login_title: "Login",
        login_subtitle: "Field Operations Center",
        username: "Username",
        password: "Password",
        login_button: "Login",
        back_to_home: "Back to Home",
        
        // General Buttons
        logout: "Logout",
        refresh: "Refresh",
        settings: "Settings",
        help: "Help",
        about: "About",
        
        // Messages
        loading: "Loading...",
        no_data: "No data available",
        error: "Error loading data",
        success: "Operation completed successfully",
        confirm_delete: "Are you sure you want to delete?",
        
        // Days and Times
        monday: "Monday",
        tuesday: "Tuesday",
        wednesday: "Wednesday",
        thursday: "Thursday",
        friday: "Friday",
        saturday: "Saturday",
        sunday: "Sunday",
        
        today: "Today",
        yesterday: "Yesterday",
        this_month: "This Month",
        
        // Units
        minutes: "Minutes",
        hours: "Hours",
        days: "Days",
        meters: "Meters",
        kilometers: "Kilometers"
    }
};

// Language Manager Class
class LanguageManager {
    constructor() {
        this.currentLang = localStorage.getItem('preferredLanguage') || 'ar';
        this.init();
    }
    
    init() {
        // Set initial language
        this.setLanguage(this.currentLang);
        
        // Add language toggle button if not exists
        this.addLanguageToggle();
    }
    
    setLanguage(lang) {
        this.currentLang = lang;
        localStorage.setItem('preferredLanguage', lang);
        document.documentElement.lang = lang;
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
        this.updatePageContent();
        this.updateToggleButton();
    }
    
    toggleLanguage() {
        const newLang = this.currentLang === 'ar' ? 'en' : 'ar';
        this.setLanguage(newLang);
    }
    
    translate(key) {
        return translations[this.currentLang][key] || key;
    }
    
    updatePageContent() {
        // Update all elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            const translation = this.translate(key);
            
            if (element.tagName === 'INPUT' && element.placeholder) {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });
        
        // Update placeholders
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            element.placeholder = this.translate(key);
        });
        
        // Update titles
        document.querySelectorAll('[data-translate-title]').forEach(element => {
            const key = element.getAttribute('data-translate-title');
            element.title = this.translate(key);
        });
    }
    
    addLanguageToggle() {
        // Check if toggle already exists
        if (document.getElementById('langToggle')) return;
        
        // Create language toggle button
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'langToggle';
        toggleBtn.className = 'language-toggle';
        toggleBtn.innerHTML = `
            <i class="fas fa-globe"></i>
            <span class="lang-text"></span>
        `;
        toggleBtn.onclick = () => this.toggleLanguage();
        
        // Add to body
        document.body.appendChild(toggleBtn);
        
        // Update button text
        this.updateToggleButton();
    }
    
    updateToggleButton() {
        const toggleBtn = document.getElementById('langToggle');
        if (toggleBtn) {
            const langText = toggleBtn.querySelector('.lang-text');
            if (langText) {
                langText.textContent = this.currentLang === 'ar' ? 'EN' : 'ع';
            }
        }
    }
}

// Initialize Language Manager when DOM is ready
let langManager;
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        langManager = new LanguageManager();
    });
} else {
    langManager = new LanguageManager();
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LanguageManager, translations };
}
