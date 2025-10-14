"""
Authentication Enhancements for Wren API

This module provides enhanced authentication features including JWT token management,
session handling, multi-factor authentication, and advanced security features.
"""

import jwt
import hashlib
import secrets
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from passlib.hash import bcrypt
import pyotp
import qrcode
from io import BytesIO
import base64
import logging

from api.utils.loggers import create_logger
from api.utils.settings import settings

logger = create_logger(__name__)

# Security configuration
SECURITY_CONFIG = {
    "JWT_SECRET_KEY": getattr(settings, 'JWT_SECRET_KEY', 'your-secret-key'),
    "JWT_ALGORITHM": "HS256",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES": 30,
    "JWT_REFRESH_TOKEN_EXPIRE_DAYS": 7,
    "PASSWORD_MIN_LENGTH": 8,
    "MAX_LOGIN_ATTEMPTS": 5,
    "LOCKOUT_DURATION_MINUTES": 15,
    "SESSION_TIMEOUT_MINUTES": 60,
    "MFA_ISSUER_NAME": "Wren API"
}

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class TokenManager:
    """JWT token management utilities"""
    
    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=SECURITY_CONFIG["JWT_ACCESS_TOKEN_EXPIRE_MINUTES"]
            )
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            SECURITY_CONFIG["JWT_SECRET_KEY"],
            algorithm=SECURITY_CONFIG["JWT_ALGORITHM"]
        )
        
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=SECURITY_CONFIG["JWT_REFRESH_TOKEN_EXPIRE_DAYS"]
            )
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            SECURITY_CONFIG["JWT_SECRET_KEY"],
            algorithm=SECURITY_CONFIG["JWT_ALGORITHM"]
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                SECURITY_CONFIG["JWT_SECRET_KEY"],
                algorithms=[SECURITY_CONFIG["JWT_ALGORITHM"]]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    @staticmethod
    def create_token_pair(user_id: str, additional_claims: Dict[str, Any] = None) -> Dict[str, str]:
        """Create access and refresh token pair"""
        claims = {"user_id": user_id}
        if additional_claims:
            claims.update(additional_claims)
        
        access_token = TokenManager.create_access_token(claims)
        refresh_token = TokenManager.create_refresh_token(claims)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }


class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        score = 0
        
        # Length check
        if len(password) < SECURITY_CONFIG["PASSWORD_MIN_LENGTH"]:
            errors.append(f"Password must be at least {SECURITY_CONFIG['PASSWORD_MIN_LENGTH']} characters long")
        else:
            score += 1
        
        # Character variety checks
        if any(c.isupper() for c in password):
            score += 1
        else:
            errors.append("Password must contain at least one uppercase letter")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            errors.append("Password must contain at least one lowercase letter")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            errors.append("Password must contain at least one digit")
        
        if any(c in "!@#$%^&*(),.?\":{}|<>" for c in password):
            score += 1
        else:
            errors.append("Password must contain at least one special character")
        
        # Common password check
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "letmein", "welcome", "monkey"
        ]
        
        if password.lower() in common_passwords:
            errors.append("Password is too common")
            score = 0
        
        # Calculate strength
        if score >= 4:
            strength = "strong"
        elif score >= 3:
            strength = "medium"
        elif score >= 2:
            strength = "weak"
        else:
            strength = "very_weak"
        
        return {
            "is_valid": len(errors) == 0,
            "strength": strength,
            "score": score,
            "errors": errors
        }
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate secure random password"""
        import string
        import secrets
        
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure password meets strength requirements
        validation = PasswordManager.validate_password_strength(password)
        if not validation["is_valid"]:
            # Regenerate if not valid
            return PasswordManager.generate_secure_password(length)
        
        return password


class MultiFactorAuth:
    """Multi-factor authentication utilities"""
    
    @staticmethod
    def generate_secret() -> str:
        """Generate TOTP secret"""
        return pyotp.random_base32()
    
    @staticmethod
    def generate_qr_code(secret: str, user_email: str) -> str:
        """Generate QR code for MFA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=SECURITY_CONFIG["MFA_ISSUER_NAME"]
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verify TOTP token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes for MFA"""
        return [secrets.token_hex(4).upper() for _ in range(count)]


class SessionManager:
    """Session management utilities"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = SECURITY_CONFIG["SESSION_TIMEOUT_MINUTES"] * 60
    
    def create_session(self, user_id: str, additional_data: Dict[str, Any] = None) -> str:
        """Create new session"""
        session_id = secrets.token_urlsafe(32)
        
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "ip_address": None,
            "user_agent": None,
            "additional_data": additional_data or {}
        }
        
        self.active_sessions[session_id] = session_data
        logger.info(f"Session created for user {user_id}: {session_id}")
        
        return session_id
    
    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate session and update last activity"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        current_time = time.time()
        
        # Check if session has expired
        if current_time - session["last_activity"] > self.session_timeout:
            del self.active_sessions[session_id]
            logger.info(f"Session expired: {session_id}")
            return None
        
        # Update last activity
        session["last_activity"] = current_time
        
        return session
    
    def destroy_session(self, session_id: str) -> bool:
        """Destroy session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Session destroyed: {session_id}")
            return True
        return False
    
    def destroy_user_sessions(self, user_id: str) -> int:
        """Destroy all sessions for a user"""
        sessions_to_remove = [
            session_id for session_id, session in self.active_sessions.items()
            if session["user_id"] == user_id
        ]
        
        for session_id in sessions_to_remove:
            del self.active_sessions[session_id]
        
        logger.info(f"Destroyed {len(sessions_to_remove)} sessions for user {user_id}")
        return len(sessions_to_remove)
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = time.time()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if current_time - session["last_activity"] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class LoginAttemptManager:
    """Login attempt tracking and rate limiting"""
    
    def __init__(self):
        self.attempts: Dict[str, List[float]] = {}
        self.locked_accounts: Dict[str, float] = {}
    
    def record_attempt(self, identifier: str, success: bool) -> Dict[str, Any]:
        """Record login attempt"""
        current_time = time.time()
        
        if identifier not in self.attempts:
            self.attempts[identifier] = []
        
        self.attempts[identifier].append(current_time)
        
        # Clean old attempts (older than 1 hour)
        cutoff_time = current_time - 3600
        self.attempts[identifier] = [
            attempt_time for attempt_time in self.attempts[identifier]
            if attempt_time > cutoff_time
        ]
        
        # Check if account should be locked
        recent_attempts = [
            attempt_time for attempt_time in self.attempts[identifier]
            if current_time - attempt_time < 3600  # Last hour
        ]
        
        if len(recent_attempts) >= SECURITY_CONFIG["MAX_LOGIN_ATTEMPTS"]:
            self.locked_accounts[identifier] = current_time
            logger.warning(f"Account locked due to too many failed attempts: {identifier}")
        
        return {
            "attempts_count": len(recent_attempts),
            "is_locked": identifier in self.locked_accounts,
            "lockout_remaining": self._get_lockout_remaining(identifier)
        }
    
    def is_locked(self, identifier: str) -> bool:
        """Check if account is locked"""
        if identifier not in self.locked_accounts:
            return False
        
        lockout_duration = SECURITY_CONFIG["LOCKOUT_DURATION_MINUTES"] * 60
        lock_time = self.locked_accounts[identifier]
        
        if time.time() - lock_time > lockout_duration:
            # Unlock account
            del self.locked_accounts[identifier]
            return False
        
        return True
    
    def _get_lockout_remaining(self, identifier: str) -> int:
        """Get remaining lockout time in seconds"""
        if identifier not in self.locked_accounts:
            return 0
        
        lockout_duration = SECURITY_CONFIG["LOCKOUT_DURATION_MINUTES"] * 60
        lock_time = self.locked_accounts[identifier]
        remaining = lockout_duration - (time.time() - lock_time)
        
        return max(0, int(remaining))
    
    def unlock_account(self, identifier: str) -> bool:
        """Manually unlock account"""
        if identifier in self.locked_accounts:
            del self.locked_accounts[identifier]
            logger.info(f"Account manually unlocked: {identifier}")
            return True
        return False


class AuthenticationDependencies:
    """Authentication dependency functions"""
    
    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Get current authenticated user"""
        token = credentials.credentials
        payload = TokenManager.verify_token(token, "access")
        
        # Here you would typically fetch user from database
        # For now, return the payload
        return payload
    
    @staticmethod
    async def get_current_active_user(
        current_user: Dict[str, Any] = Depends(get_current_user)
    ) -> Dict[str, Any]:
        """Get current active user"""
        # Check if user is active
        if not current_user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return current_user
    
    @staticmethod
    async def require_permissions(
        required_permissions: List[str],
        current_user: Dict[str, Any] = Depends(get_current_active_user)
    ) -> Dict[str, Any]:
        """Require specific permissions"""
        user_permissions = current_user.get("permissions", [])
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
        
        return current_user


# Global instances
session_manager = SessionManager()
login_attempt_manager = LoginAttemptManager()


def setup_authentication_enhancements(app):
    """Setup authentication enhancements"""
    
    # Add periodic cleanup task
    import asyncio
    
    async def cleanup_task():
        while True:
            session_manager.cleanup_expired_sessions()
            await asyncio.sleep(300)  # Run every 5 minutes
    
    # Start cleanup task
    asyncio.create_task(cleanup_task())
    
    logger.info("Authentication enhancements setup completed")
