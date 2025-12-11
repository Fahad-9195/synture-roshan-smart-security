from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from functools import lru_cache
import database as db
import auth
import events_management as events_mgmt

# Import configurations and middleware
from config import settings
from logger import logger, log_error, log_security_event
from middleware import (
    ErrorHandlerMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)
security = HTTPBearer()

# ===== Middleware Configuration =====
# Security headers
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting
app.add_middleware(
    RateLimitMiddleware,
    max_requests=settings.RATE_LIMIT_REQUESTS,
    window=settings.RATE_LIMIT_PERIOD
)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Error handling
app.add_middleware(ErrorHandlerMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("✅ Middleware configured successfully")

# ===== Models =====
class Event(BaseModel):
    timestamp: Optional[str] = None
    device_id: str
    type: str
    level: str
    status: str = "open"
    home_id: Optional[str] = None
    absher_id: Optional[str] = None
    location: Optional[Dict[str, Any]] = None

class Officer(BaseModel):
    id: str
    name: str
    badge_number: str
    rank: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    full_name: str
    email: Optional[str] = None
    officer_id: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    full_name: str
    email: Optional[str]
    is_active: bool

# ===== نماذج الفعاليات والأحداث الموسمية =====

class SeasonalEventCreate(BaseModel):
    event_name: str
    event_type: str  # hajj, umrah, religious_event
    description: Optional[str] = None
    start_date: datetime
    end_date: datetime
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    max_participants: int
    security_level: str = "high"
    requires_biometric: bool = True
    requires_iot_device: bool = True

class EventParticipantCreate(BaseModel):
    participant_id: str
    full_name: str
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class IoTDeviceCreate(BaseModel):
    device_id: str
    device_type: str  # bracelet, badge, wristband
    device_name: str
    participant_id: str
    battery_level: float = 100
    firmware_version: Optional[str] = None

class BiometricDataCreate(BaseModel):
    participant_id: str
    fingerprint_hash: Optional[str] = None
    facial_recognition_data: Optional[str] = None
    iris_scan_data: Optional[str] = None
    voice_recognition_data: Optional[str] = None
    confidence_score: Optional[float] = 0

class AccessLogCreate(BaseModel):
    participant_id: str
    device_id: Optional[str] = None
    access_type: str  # entry, exit
    entry_location_lat: Optional[float] = None
    entry_location_lng: Optional[float] = None
    access_point: Optional[str] = None

class LocationTrackCreate(BaseModel):
    participant_id: str
    device_id: Optional[str] = None
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    altitude: Optional[float] = None
    speed: Optional[float] = None
    heading: Optional[float] = None

class SecurityAlertCreate(BaseModel):
    participant_id: Optional[str] = None
    device_id: Optional[str] = None
    alert_type: str
    severity: str = "medium"
    description: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    action_taken: Optional[str] = None

class FraudAttemptCreate(BaseModel):
    participant_id: Optional[str] = None
    device_id: Optional[str] = None
    attempt_type: str
    details: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    severity: str = "high"
    action_taken: Optional[str] = None

# ===== Auth Dependency =====
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = auth.decode_access_token(token)
    
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = auth.get_user_by_id(user_id)
    if not user or not user['is_active']:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

def require_role(*allowed_roles: str):
    """Decorator to require specific role"""
    def role_checker(user: dict = Depends(get_current_user)) -> dict:
        if user['role'] not in allowed_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return role_checker

# ===== Authentication API =====

@app.post("/api/auth/login")
def login(credentials: UserLogin):
    """Login and get JWT token"""
    try:
        logger.info(f"Login attempt for user: {credentials.username}")
        user = auth.authenticate_user(credentials.username, credentials.password)
        
        if not user:
            log_security_event("failed_login", details=f"Username: {credentials.username}")
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        access_token = auth.create_access_token(
            data={"user_id": user['id'], "username": user['username'], "role": user['role']}
        )
        
        # Log activity
        auth.log_activity(user['id'], "login", details=f"User {user['username']} logged in")
        log_security_event("successful_login", user_id=user['id'], details=user['username'])
        
        logger.info(f"✅ User {user['username']} logged in successfully")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "full_name": user['full_name'],
                "email": user['email']
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        log_error(e, "login")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/auth/me")
def get_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return {
        "id": user['id'],
        "username": user['username'],
        "role": user['role'],
        "full_name": user['full_name'],
        "email": user['email']
    }

@app.post("/api/auth/register")
def register(user_data: UserCreate, current_user: dict = Depends(require_role("admin"))):
    """Register new user (admin only)"""
    try:
        user_id = auth.create_user(
            username=user_data.username,
            password=user_data.password,
            role=user_data.role,
            full_name=user_data.full_name,
            email=user_data.email,
            officer_id=user_data.officer_id
        )
        
        auth.log_activity(
            current_user['id'], 
            "create_user", 
            entity_type="user", 
            entity_id=str(user_id),
            details=f"Created user: {user_data.username}"
        )
        
        return {"ok": True, "id": user_id, "message": "User created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users")
def get_users(current_user: dict = Depends(require_role("admin", "supervisor"))):
    """Get all users (admin/supervisor only)"""
    try:
        users = auth.get_all_users()
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== Events API =====

@app.get("/api/events")
def get_events(limit: int = 1000, status: Optional[str] = None):
    """Get all events from database"""
    try:
        events = db.get_events(limit=limit, status=status)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events")
def add_event(ev: Event):
    """Add new event to database"""
    try:
        event_dict = ev.dict()
        event_id = db.add_event(event_dict)
        return {"ok": True, "id": event_id, "message": "Event added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/resolve_all")
def resolve_all():
    """Resolve all open events"""
    try:
        count = db.resolve_all_events()
        return {"resolved": count, "message": f"{count} events marked as resolved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/events/{event_id}")
def update_event(event_id: int, ev: Event):
    """Update an existing event"""
    try:
        event_dict = ev.dict()
        success = db.update_event(event_id, event_dict)
        if success:
            return {"ok": True, "message": "Event updated successfully"}
        else:
            raise HTTPException(status_code=404, detail="Event not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/reset")
@app.post("/reset")
def reset_events():
    """Delete all events"""
    try:
        db.delete_all_events()
        return {"reset": True, "message": "تم مسح جميع الأحداث"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resolutions")
def add_resolution(resolution: dict):
    """Add a resolution record"""
    try:
        resolution_id = db.add_resolution(resolution)
        return {"ok": True, "id": resolution_id, "message": "Resolution recorded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resolutions")
def get_resolutions(limit: int = 100):
    """Get recent resolutions"""
    try:
        resolutions = db.get_resolutions(limit=limit)
        return resolutions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resolutions/stats")
@lru_cache(maxsize=128)
def get_resolution_stats():
    """Get resolution statistics (cached)"""
    try:
        stats = db.get_resolution_stats()
        return stats
    except Exception as e:
        log_error(e, "get_resolution_stats")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
@lru_cache(maxsize=128)
def get_statistics():
    """Get system statistics (cached)"""
    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        log_error(e, "get_statistics")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/officers")
def get_officers():
    """Get all officers"""
    try:
        officers = db.get_officers()
        return officers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/officers")
def add_officer(officer: Officer):
    """Add new officer"""
    try:
        officer_dict = officer.dict()
        officer_id = db.add_officer(officer_dict)
        return {"ok": True, "id": officer_id, "message": "Officer added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/officers/{officer_id}")
def get_officer(officer_id: str):
    """Get single officer"""
    try:
        officer = db.get_officer(officer_id)
        if not officer:
            raise HTTPException(status_code=404, detail="Officer not found")
        return officer
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== static + الواجهة =====

# مجلد الملفات الثابتة (فيه الواجهات)
app.mount("/static", StaticFiles(directory="static"), name="static")

# لما تفتح https://syntrue-absher.onrender.com يرسل لك لوحة "dashboard-absher" مباشرة
@app.get("/")
def root():
    # Show welcome page to choose between civilian and military
    return FileResponse("static/welcome.html")

# ===== API الفعاليات والأحداث الموسمية =====

@app.post("/api/events/seasonal/create")
def create_seasonal_event(event: SeasonalEventCreate):
    """إنشاء فعالية موسمية جديدة (الحج، العمرة، إلخ)"""
    try:
        event_data = event.dict()
        event_id = events_mgmt.events_db.create_event(event_data)
        return {
            "ok": True,
            "event_id": event_id,
            "message": f"تم إنشاء الفعالية: {event.event_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}")
def get_seasonal_event(event_id: int):
    """الحصول على بيانات الفعالية"""
    try:
        event = events_mgmt.events_db.get_event(event_id)
        if not event:
            raise HTTPException(status_code=404, detail="الفعالية غير موجودة")
        return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal")
def list_seasonal_events(event_type: Optional[str] = None, status: Optional[str] = None):
    """قائمة الفعاليات الموسمية"""
    try:
        events = events_mgmt.events_db.list_events(status=status, event_type=event_type)
        return {
            "count": len(events),
            "events": events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/seasonal/{event_id}/participants")
def register_event_participant(event_id: int, participant: EventParticipantCreate):
    """تسجيل مشارك جديد في الفعالية"""
    try:
        participant_data = participant.dict()
        participant_data['event_id'] = event_id
        participant_id = events_mgmt.events_db.register_participant(participant_data)
        return {
            "ok": True,
            "participant_id": participant_id,
            "message": f"تم تسجيل المشارك: {participant.full_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/participants")
def list_event_participants(event_id: int, status: Optional[str] = None):
    """قائمة مشاركي الفعالية"""
    try:
        participants = events_mgmt.events_db.list_event_participants(event_id, status=status)
        return {
            "count": len(participants),
            "participants": participants
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/participants/{participant_id}")
def get_event_participant(event_id: int, participant_id: str):
    """الحصول على بيانات المشارك"""
    try:
        participant = events_mgmt.events_db.get_participant(participant_id, event_id)
        if not participant:
            raise HTTPException(status_code=404, detail="المشارك غير موجود")
        return participant
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/seasonal/{event_id}/participants/{participant_id}/verify")
def verify_participant(event_id: int, participant_id: str, verification_status: str = "verified"):
    """التحقق من بيانات المشارك"""
    try:
        success = events_mgmt.events_db.verify_participant(
            participant_id, event_id, verification_status
        )
        if success:
            return {"ok": True, "message": "تم التحقق من المشارك بنجاح"}
        else:
            raise HTTPException(status_code=404, detail="المشارك غير موجود")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API أجهزة IoT =====

@app.post("/api/events/seasonal/{event_id}/iot-devices")
def register_iot_device(event_id: int, device: IoTDeviceCreate):
    """تسجيل جهاز IoT جديد (أسورة، معرف ذكي)"""
    try:
        device_data = device.dict()
        device_data['event_id'] = event_id
        device_record_id = events_mgmt.events_db.register_iot_device(device_data)
        return {
            "ok": True,
            "device_record_id": device_record_id,
            "message": f"تم تسجيل جهاز: {device.device_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/iot-devices/{device_id}")
def get_iot_device(event_id: int, device_id: str):
    """الحصول على بيانات جهاز IoT"""
    try:
        device = events_mgmt.events_db.get_iot_device(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="الجهاز غير موجود")
        return device
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/events/seasonal/{event_id}/iot-devices/{device_id}/status")
def update_iot_device_status(event_id: int, device_id: str, status_data: dict):
    """تحديث حالة جهاز IoT (البطارية، جودة الإشارة)"""
    try:
        success = events_mgmt.events_db.update_device_status(device_id, status_data)
        if success:
            return {"ok": True, "message": "تم تحديث حالة الجهاز"}
        else:
            raise HTTPException(status_code=404, detail="الجهاز غير موجود")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API البيانات البيومترية =====

@app.post("/api/events/seasonal/{event_id}/participants/{participant_id}/biometric")
def register_biometric(event_id: int, participant_id: str, biometric: BiometricDataCreate):
    """تسجيل البيانات البيومترية (بصمات، تعرف الوجه، المسح الدقيق)"""
    try:
        biometric_data = biometric.dict()
        biometric_data['event_id'] = event_id
        biometric_data['participant_id'] = participant_id
        biometric_id = events_mgmt.events_db.register_biometric(biometric_data)
        return {
            "ok": True,
            "biometric_id": biometric_id,
            "message": "تم تسجيل البيانات البيومترية"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/seasonal/{event_id}/participants/{participant_id}/verify-biometric")
def verify_biometric(event_id: int, participant_id: str, confidence_score: float):
    """التحقق من البيانات البيومترية"""
    try:
        is_verified = events_mgmt.events_db.verify_biometric(
            participant_id, event_id, confidence_score
        )
        status = "تم التحقق" if is_verified else "فشل التحقق"
        return {
            "ok": is_verified,
            "message": status,
            "confidence_score": confidence_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API تتبع الوصول والدخول =====

@app.post("/api/events/seasonal/{event_id}/access-log")
def log_participant_access(event_id: int, access_log: AccessLogCreate):
    """تسجيل دخول/خروج المشارك"""
    try:
        access_data = access_log.dict()
        access_data['event_id'] = event_id
        access_log_id = events_mgmt.events_db.log_access(access_data)
        return {
            "ok": True,
            "access_log_id": access_log_id,
            "message": "تم تسجيل الدخول بنجاح"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API تتبع الموقع الجغرافي =====

@app.post("/api/events/seasonal/{event_id}/location-track")
def track_participant_location(event_id: int, location: LocationTrackCreate):
    """تتبع موقع المشارك في الفعالية"""
    try:
        location_data = location.dict()
        location_data['event_id'] = event_id
        location_id = events_mgmt.events_db.track_location(location_data)
        return {
            "ok": True,
            "location_id": location_id,
            "message": "تم تسجيل الموقع"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/participants/{participant_id}/location-history")
def get_participant_location_history(event_id: int, participant_id: str, limit: int = 100):
    """الحصول على سجل مواقع المشارك"""
    try:
        locations = events_mgmt.events_db.get_participant_location_history(
            participant_id, event_id, limit
        )
        return {
            "count": len(locations),
            "locations": locations
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API الأمان والتنبيهات =====

@app.post("/api/events/seasonal/{event_id}/security-alert")
def log_security_alert(event_id: int, alert: SecurityAlertCreate):
    """تسجيل تنبيه أمني (دخول غير مصرح، جهاز معطل)"""
    try:
        alert_data = alert.dict()
        alert_data['event_id'] = event_id
        alert_id = events_mgmt.events_db.log_security_alert(alert_data)
        return {
            "ok": True,
            "alert_id": alert_id,
            "message": "تم تسجيل التنبيه الأمني"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/seasonal/{event_id}/fraud-attempt")
def log_fraud_attempt(event_id: int, fraud: FraudAttemptCreate):
    """تسجيل محاولة احتيال أو دخول مزيف"""
    try:
        fraud_data = fraud.dict()
        fraud_data['event_id'] = event_id
        fraud_id = events_mgmt.events_db.log_fraud_attempt(fraud_data)
        return {
            "ok": True,
            "fraud_id": fraud_id,
            "message": "تم تسجيل محاولة الاحتيال"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/active-alerts")
def get_event_active_alerts(event_id: int):
    """الحصول على التنبيهات النشطة للفعالية"""
    try:
        alerts = events_mgmt.events_db.get_active_alerts(event_id)
        return {
            "count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== API معرفات الدخول =====

@app.post("/api/events/seasonal/{event_id}/access-credentials")
def create_access_credential(event_id: int, credential_data: dict):
    """إنشاء معرف دخول للمشارك (QR Code، NFC، RFID)"""
    try:
        credential_data['event_id'] = event_id
        credential_id = events_mgmt.events_db.create_access_credential(credential_data)
        return {
            "ok": True,
            "credential_id": credential_id,
            "message": "تم إنشاء معرف الدخول"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/events/seasonal/{event_id}/verify-credential")
def verify_access_credential(event_id: int, credential_data: dict):
    """التحقق من معرف الدخول"""
    try:
        credential_value = credential_data.get('credential')
        result = events_mgmt.events_db.verify_credential(credential_value, event_id)
        
        if result:
            return {
                "ok": True,
                "participant_id": result.get('participant_id'),
                "full_name": result.get('full_name'),
                "verification_status": result.get('verification_status'),
                "message": "معرف الدخول صحيح"
            }
        else:
            return {
                "ok": False,
                "message": "معرف الدخول غير صحيح أو منتهي الصلاحية"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== التقارير والإحصائيات =====

@app.get("/api/events/seasonal/{event_id}/statistics")
def get_event_statistics(event_id: int):
    """الحصول على إحصائيات الفعالية"""
    try:
        stats = events_mgmt.events_db.get_event_statistics(event_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/fraud-report")
def get_fraud_report(event_id: int, limit: int = 100):
    """تقرير محاولات الاحتيال"""
    try:
        frauds = events_mgmt.events_db.get_fraud_report(event_id, limit)
        return {
            "count": len(frauds),
            "frauds": frauds
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/events/seasonal/{event_id}/security-report")
def get_security_report(event_id: int, limit: int = 100):
    """تقرير الأمان والتنبيهات"""
    try:
        alerts = events_mgmt.events_db.get_security_report(event_id, limit)
        return {
            "count": len(alerts),
            "alerts": alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "app": settings.APP_NAME
    }

@app.get("/api/version")
def get_version():
    """Get application version"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    }

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get the directory where main.py is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(current_dir)
    
    # Log startup
    logger.info("=" * 60)
    logger.info(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"🌐 Production URL: {settings.PRODUCTION_URL}")
    logger.info(f"📁 Working Directory: {current_dir}")
    logger.info(f"🔧 Debug Mode: {settings.DEBUG}")
    logger.info("=" * 60)
    
    print("\n" + "="*60)
    print(f"  🚀 {settings.APP_NAME}")
    print(f"  📊 Version: {settings.APP_VERSION}")
    print("="*60)
    print(f"\n✅ Database initialized successfully")
    print(f"🚀 Starting server on http://0.0.0.0:8000")
    print(f"\n📊 Dashboard: {settings.PRODUCTION_URL}")
    print(f"🗺️  Operations Center: {settings.PRODUCTION_URL}/static/operations-center.html")
    print(f"📱 Officer Device: {settings.PRODUCTION_URL}/static/officer-device.html?id=officer_1")
    print(f"📈 Analytics: {settings.PRODUCTION_URL}/static/analytics.html")
    print(f"🌐 Welcome Page: {settings.PRODUCTION_URL}/static/welcome.html")
    print("\n" + "="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

