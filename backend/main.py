from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import database as db
import auth

app = FastAPI(title="Smart Security System - Absher", version="2.0")
security = HTTPBearer()

# ===== CORS عشان يسمح للـ HTML يتصل بالـ API محلياً =====
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        user = auth.authenticate_user(credentials.username, credentials.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        
        # Create access token
        access_token = auth.create_access_token(
            data={"user_id": user['id'], "username": user['username'], "role": user['role']}
        )
        
        # Log activity
        auth.log_activity(user['id'], "login", details=f"User {user['username']} logged in")
        
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
def get_resolution_stats():
    """Get resolution statistics"""
    try:
        stats = db.get_resolution_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics")
def get_statistics():
    """Get system statistics"""
    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
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

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Smart Security System - Absher Edition")
    print("📊 Dashboard: https://syntrue-absher.onrender.com")
    print("🗺️  Operations Center: https://syntrue-absher.onrender.com/static/operations-center.html")
    print("📱 Officer Device: https://syntrue-absher.onrender.com/static/officer-device.html?id=officer_1")
    print("📈 Analytics: https://syntrue-absher.onrender.com/static/analytics.html")
    uvicorn.run(app, host="0.0.0.0", port=8000)

