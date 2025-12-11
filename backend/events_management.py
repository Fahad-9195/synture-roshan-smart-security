"""
نظام إدارة الفعاليات والأحداث الموسمية
يشمل:
- إدارة الفعاليات (الحج، العمرة، المناسبات الدينية)
- تتبع أجهزة IoT (الأساور، المعرفات الذكية)
- البيانات البيومترية والتعريف الحيوي
- التحكم في الوصول والدخول
- تتبع المشاركين والموقع الجغرافي
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

class EventsManagementDB:
    """قاعدة بيانات إدارة الفعاليات والأحداث الموسمية"""
    
    def __init__(self, db_path: str = "smart_security.db"):
        self.db_path = db_path
        self.init_events_tables()
    
    def get_connection(self):
        """الحصول على اتصال قاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_events_tables(self):
        """إنشء جداول الفعاليات والأحداث"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول الفعاليات الموسمية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS seasonal_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                start_date DATETIME NOT NULL,
                end_date DATETIME NOT NULL,
                location_lat REAL,
                location_lng REAL,
                location_name TEXT,
                max_participants INTEGER,
                current_participants INTEGER DEFAULT 0,
                status TEXT DEFAULT 'planned',
                security_level TEXT DEFAULT 'high',
                requires_biometric BOOLEAN DEFAULT 1,
                requires_iot_device BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول أجهزة IoT والأساور الذكية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS iot_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                device_type TEXT NOT NULL,
                device_name TEXT NOT NULL,
                participant_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                battery_level REAL DEFAULT 100,
                is_active BOOLEAN DEFAULT 1,
                signal_strength REAL,
                last_sync DATETIME,
                firmware_version TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول المشاركين في الفعاليات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS event_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT UNIQUE NOT NULL,
                event_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                national_id TEXT,
                passport_number TEXT,
                phone TEXT,
                email TEXT,
                age INTEGER,
                gender TEXT,
                registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'registered',
                verification_status TEXT DEFAULT 'pending',
                access_level TEXT DEFAULT 'basic',
                is_verified BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول البيانات البيومترية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS biometric_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                fingerprint_hash TEXT,
                facial_recognition_data TEXT,
                iris_scan_data TEXT,
                voice_recognition_data TEXT,
                verification_time DATETIME,
                verification_status TEXT DEFAULT 'pending',
                confidence_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول تتبع الدخول والخروج
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                device_id TEXT,
                access_type TEXT,
                entry_time DATETIME,
                exit_time DATETIME,
                entry_location_lat REAL,
                entry_location_lng REAL,
                exit_location_lat REAL,
                exit_location_lng REAL,
                access_point TEXT,
                status TEXT DEFAULT 'active',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول تتبع الموقع الجغرافي
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS location_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                device_id TEXT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                accuracy REAL,
                altitude REAL,
                speed REAL,
                heading REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول التنبيهات الأمنية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                participant_id TEXT,
                device_id TEXT,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                description TEXT,
                location_lat REAL,
                location_lng REAL,
                action_taken TEXT,
                resolved BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        # جدول محاولات الدخول المزيفة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fraud_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id INTEGER NOT NULL,
                participant_id TEXT,
                device_id TEXT,
                attempt_type TEXT NOT NULL,
                details TEXT,
                location_lat REAL,
                location_lng REAL,
                ip_address TEXT,
                user_agent TEXT,
                severity TEXT DEFAULT 'high',
                action_taken TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول معرفات الدخول الشخصية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participant_id TEXT NOT NULL,
                event_id INTEGER NOT NULL,
                credential_type TEXT NOT NULL,
                credential_data TEXT NOT NULL,
                qr_code TEXT,
                nfc_uid TEXT,
                expiry_date DATETIME,
                is_active BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(event_id) REFERENCES seasonal_events(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ===== عمليات الفعاليات =====
    
    def create_event(self, event_data: Dict[str, Any]) -> int:
        """إنشاء فعالية جديدة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO seasonal_events 
                (event_name, event_type, description, start_date, end_date, 
                 location_lat, location_lng, location_name, max_participants, 
                 security_level, requires_biometric, requires_iot_device, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_data.get('event_name'),
                event_data.get('event_type'),  # hajj, umrah, religious_event, etc.
                event_data.get('description'),
                event_data.get('start_date'),
                event_data.get('end_date'),
                event_data.get('location_lat'),
                event_data.get('location_lng'),
                event_data.get('location_name'),
                event_data.get('max_participants'),
                event_data.get('security_level', 'high'),
                event_data.get('requires_biometric', True),
                event_data.get('requires_iot_device', True),
                event_data.get('status', 'planned')
            ))
            
            event_id = cursor.lastrowid
            conn.commit()
            return event_id
        finally:
            conn.close()
    
    def get_event(self, event_id: int) -> Dict[str, Any]:
        """الحصول على بيانات الفعالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM seasonal_events WHERE id = ?
        ''', (event_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def list_events(self, status: str = None, event_type: str = None) -> List[Dict[str, Any]]:
        """قائمة الفعاليات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM seasonal_events WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if event_type:
            query += ' AND event_type = ?'
            params.append(event_type)
        
        query += ' ORDER BY start_date DESC'
        
        cursor.execute(query, params)
        events = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return events
    
    def update_event(self, event_id: int, event_data: Dict[str, Any]) -> bool:
        """تحديث بيانات الفعالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        allowed_fields = ['event_name', 'description', 'end_date', 'status', 'security_level']
        updates = []
        params = []
        
        for field in allowed_fields:
            if field in event_data:
                updates.append(f'{field} = ?')
                params.append(event_data[field])
        
        if not updates:
            conn.close()
            return False
        
        updates.append('updated_at = CURRENT_TIMESTAMP')
        params.append(event_id)
        
        query = f'UPDATE seasonal_events SET {", ".join(updates)} WHERE id = ?'
        
        try:
            cursor.execute(query, params)
            conn.commit()
            return True
        finally:
            conn.close()
    
    # ===== عمليات أجهزة IoT =====
    
    def register_iot_device(self, device_data: Dict[str, Any]) -> int:
        """تسجيل جهاز IoT جديد"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO iot_devices 
                (device_id, device_type, device_name, participant_id, event_id, 
                 battery_level, firmware_version)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_data.get('device_id'),
                device_data.get('device_type'),  # bracelet, badge, wristband, etc.
                device_data.get('device_name'),
                device_data.get('participant_id'),
                device_data.get('event_id'),
                device_data.get('battery_level', 100),
                device_data.get('firmware_version')
            ))
            
            device_record_id = cursor.lastrowid
            conn.commit()
            return device_record_id
        finally:
            conn.close()
    
    def update_device_status(self, device_id: str, status_data: Dict[str, Any]) -> bool:
        """تحديث حالة جهاز IoT"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE iot_devices 
                SET battery_level = ?, signal_strength = ?, last_sync = CURRENT_TIMESTAMP
                WHERE device_id = ?
            ''', (
                status_data.get('battery_level'),
                status_data.get('signal_strength'),
                device_id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def get_iot_device(self, device_id: str) -> Dict[str, Any]:
        """الحصول على بيانات جهاز IoT"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM iot_devices WHERE device_id = ?
        ''', (device_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # ===== عمليات المشاركين =====
    
    def register_participant(self, participant_data: Dict[str, Any]) -> str:
        """تسجيل مشارك جديد في الفعالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO event_participants 
                (participant_id, event_id, full_name, national_id, passport_number, 
                 phone, email, age, gender, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                participant_data.get('participant_id'),
                participant_data.get('event_id'),
                participant_data.get('full_name'),
                participant_data.get('national_id'),
                participant_data.get('passport_number'),
                participant_data.get('phone'),
                participant_data.get('email'),
                participant_data.get('age'),
                participant_data.get('gender'),
                participant_data.get('status', 'registered')
            ))
            
            participant_id = participant_data.get('participant_id')
            conn.commit()
            return participant_id
        finally:
            conn.close()
    
    def get_participant(self, participant_id: str, event_id: int) -> Dict[str, Any]:
        """الحصول على بيانات المشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM event_participants 
            WHERE participant_id = ? AND event_id = ?
        ''', (participant_id, event_id))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def verify_participant(self, participant_id: str, event_id: int, verification_status: str = 'verified') -> bool:
        """التحقق من بيانات المشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE event_participants 
                SET verification_status = ?, is_verified = 1
                WHERE participant_id = ? AND event_id = ?
            ''', (verification_status, participant_id, event_id))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def list_event_participants(self, event_id: int, status: str = None) -> List[Dict[str, Any]]:
        """قائمة مشاركي الفعالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM event_participants WHERE event_id = ?'
        params = [event_id]
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        query += ' ORDER BY registration_date DESC'
        
        cursor.execute(query, params)
        participants = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return participants
    
    # ===== عمليات البيانات البيومترية =====
    
    def register_biometric(self, biometric_data: Dict[str, Any]) -> int:
        """تسجيل البيانات البيومترية للمشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO biometric_data 
                (participant_id, event_id, fingerprint_hash, facial_recognition_data, 
                 iris_scan_data, voice_recognition_data, verification_status, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                biometric_data.get('participant_id'),
                biometric_data.get('event_id'),
                biometric_data.get('fingerprint_hash'),
                biometric_data.get('facial_recognition_data'),
                biometric_data.get('iris_scan_data'),
                biometric_data.get('voice_recognition_data'),
                biometric_data.get('verification_status', 'pending'),
                biometric_data.get('confidence_score', 0)
            ))
            
            biometric_id = cursor.lastrowid
            conn.commit()
            return biometric_id
        finally:
            conn.close()
    
    def verify_biometric(self, participant_id: str, event_id: int, confidence_score: float) -> bool:
        """التحقق من البيانات البيومترية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            status = 'verified' if confidence_score > 0.85 else 'failed'
            
            cursor.execute('''
                UPDATE biometric_data 
                SET verification_status = ?, confidence_score = ?, verification_time = CURRENT_TIMESTAMP
                WHERE participant_id = ? AND event_id = ?
            ''', (status, confidence_score, participant_id, event_id))
            
            conn.commit()
            return status == 'verified'
        finally:
            conn.close()
    
    # ===== عمليات تتبع الدخول =====
    
    def log_access(self, access_data: Dict[str, Any]) -> int:
        """تسجيل محاولة دخول أو خروج"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO access_logs 
                (participant_id, event_id, device_id, access_type, entry_time,
                 entry_location_lat, entry_location_lng, access_point, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                access_data.get('participant_id'),
                access_data.get('event_id'),
                access_data.get('device_id'),
                access_data.get('access_type'),  # entry, exit
                access_data.get('entry_time'),
                access_data.get('entry_location_lat'),
                access_data.get('entry_location_lng'),
                access_data.get('access_point'),
                access_data.get('status', 'active')
            ))
            
            access_log_id = cursor.lastrowid
            conn.commit()
            return access_log_id
        finally:
            conn.close()
    
    def log_exit(self, access_log_id: int, exit_data: Dict[str, Any]) -> bool:
        """تسجيل الخروج"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE access_logs 
                SET exit_time = ?, exit_location_lat = ?, exit_location_lng = ?, status = 'completed'
                WHERE id = ?
            ''', (
                exit_data.get('exit_time'),
                exit_data.get('exit_location_lat'),
                exit_data.get('exit_location_lng'),
                access_log_id
            ))
            
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    # ===== عمليات تتبع الموقع =====
    
    def track_location(self, location_data: Dict[str, Any]) -> int:
        """تتبع موقع المشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO location_tracking 
                (participant_id, event_id, device_id, latitude, longitude, 
                 accuracy, altitude, speed, heading)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                location_data.get('participant_id'),
                location_data.get('event_id'),
                location_data.get('device_id'),
                location_data.get('latitude'),
                location_data.get('longitude'),
                location_data.get('accuracy'),
                location_data.get('altitude'),
                location_data.get('speed'),
                location_data.get('heading')
            ))
            
            location_id = cursor.lastrowid
            conn.commit()
            return location_id
        finally:
            conn.close()
    
    def get_participant_location_history(self, participant_id: str, event_id: int, 
                                        limit: int = 100) -> List[Dict[str, Any]]:
        """الحصول على سجل مواقع المشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM location_tracking 
            WHERE participant_id = ? AND event_id = ?
            ORDER BY timestamp DESC LIMIT ?
        ''', (participant_id, event_id, limit))
        
        locations = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return locations
    
    # ===== عمليات الأمان والتنبيهات =====
    
    def log_security_alert(self, alert_data: Dict[str, Any]) -> int:
        """تسجيل تنبيه أمني"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO security_alerts 
                (event_id, participant_id, device_id, alert_type, severity, 
                 description, location_lat, location_lng, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                alert_data.get('event_id'),
                alert_data.get('participant_id'),
                alert_data.get('device_id'),
                alert_data.get('alert_type'),
                alert_data.get('severity', 'medium'),
                alert_data.get('description'),
                alert_data.get('location_lat'),
                alert_data.get('location_lng'),
                alert_data.get('action_taken')
            ))
            
            alert_id = cursor.lastrowid
            conn.commit()
            return alert_id
        finally:
            conn.close()
    
    def log_fraud_attempt(self, fraud_data: Dict[str, Any]) -> int:
        """تسجيل محاولة احتيال أو دخول مزيف"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO fraud_attempts 
                (event_id, participant_id, device_id, attempt_type, details,
                 location_lat, location_lng, ip_address, user_agent, severity, action_taken)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                fraud_data.get('event_id'),
                fraud_data.get('participant_id'),
                fraud_data.get('device_id'),
                fraud_data.get('attempt_type'),
                fraud_data.get('details'),
                fraud_data.get('location_lat'),
                fraud_data.get('location_lng'),
                fraud_data.get('ip_address'),
                fraud_data.get('user_agent'),
                fraud_data.get('severity', 'high'),
                fraud_data.get('action_taken')
            ))
            
            fraud_id = cursor.lastrowid
            conn.commit()
            return fraud_id
        finally:
            conn.close()
    
    def get_active_alerts(self, event_id: int) -> List[Dict[str, Any]]:
        """الحصول على التنبيهات النشطة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM security_alerts 
            WHERE event_id = ? AND resolved = 0
            ORDER BY created_at DESC
        ''', (event_id,))
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return alerts
    
    # ===== عمليات معرفات الدخول =====
    
    def create_access_credential(self, credential_data: Dict[str, Any]) -> int:
        """إنشاء معرف دخول للمشارك"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO access_credentials 
                (participant_id, event_id, credential_type, credential_data, 
                 qr_code, nfc_uid, expiry_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                credential_data.get('participant_id'),
                credential_data.get('event_id'),
                credential_data.get('credential_type'),  # qr_code, nfc, rfid, etc.
                credential_data.get('credential_data'),
                credential_data.get('qr_code'),
                credential_data.get('nfc_uid'),
                credential_data.get('expiry_date')
            ))
            
            credential_id = cursor.lastrowid
            conn.commit()
            return credential_id
        finally:
            conn.close()
    
    def verify_credential(self, credential_data: str, event_id: int) -> Dict[str, Any]:
        """التحقق من معرف الدخول"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT ac.*, ep.full_name, ep.participant_id, ep.verification_status
            FROM access_credentials ac
            JOIN event_participants ep ON ac.participant_id = ep.participant_id
            WHERE (ac.qr_code = ? OR ac.nfc_uid = ? OR ac.credential_data = ?)
            AND ac.event_id = ? AND ac.is_active = 1
            AND (ac.expiry_date IS NULL OR ac.expiry_date > CURRENT_TIMESTAMP)
        ''', (credential_data, credential_data, credential_data, event_id))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    # ===== التقارير والإحصائيات =====
    
    def get_event_statistics(self, event_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات الفعالية"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # إجمالي المشاركين
        cursor.execute('SELECT COUNT(*) as total FROM event_participants WHERE event_id = ?', (event_id,))
        total_participants = cursor.fetchone()['total']
        
        # المشاركين المتحققين
        cursor.execute('SELECT COUNT(*) as total FROM event_participants WHERE event_id = ? AND is_verified = 1', 
                      (event_id,))
        verified_participants = cursor.fetchone()['total']
        
        # أجهزة IoT النشطة
        cursor.execute('SELECT COUNT(*) as total FROM iot_devices WHERE event_id = ? AND is_active = 1', 
                      (event_id,))
        active_devices = cursor.fetchone()['total']
        
        # التنبيهات النشطة
        cursor.execute('SELECT COUNT(*) as total FROM security_alerts WHERE event_id = ? AND resolved = 0', 
                      (event_id,))
        active_alerts = cursor.fetchone()['total']
        
        # محاولات الاحتيال
        cursor.execute('SELECT COUNT(*) as total FROM fraud_attempts WHERE event_id = ?', (event_id,))
        fraud_attempts = cursor.fetchone()['total']
        
        # المشاركين الحاليين
        cursor.execute('''
            SELECT COUNT(*) as total FROM access_logs 
            WHERE event_id = ? AND status = 'active'
        ''', (event_id,))
        current_participants_onsite = cursor.fetchone()['total']
        
        conn.close()
        
        return {
            'total_participants': total_participants,
            'verified_participants': verified_participants,
            'active_devices': active_devices,
            'active_alerts': active_alerts,
            'fraud_attempts': fraud_attempts,
            'current_participants_onsite': current_participants_onsite,
            'verification_rate': (verified_participants / total_participants * 100) if total_participants > 0 else 0
        }
    
    def get_fraud_report(self, event_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """تقرير محاولات الاحتيال"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM fraud_attempts 
            WHERE event_id = ?
            ORDER BY created_at DESC LIMIT ?
        ''', (event_id, limit))
        
        frauds = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return frauds
    
    def get_security_report(self, event_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """تقرير الأمان والتنبيهات"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM security_alerts 
            WHERE event_id = ?
            ORDER BY created_at DESC LIMIT ?
        ''', (event_id, limit))
        
        alerts = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return alerts

# إنشاء instance عام للاستخدام
events_db = EventsManagementDB()
