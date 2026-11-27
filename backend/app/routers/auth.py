"""Registration, login (JWT), and role-based access for students, organizations and admins.

Owner: Weam. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""

import os
import re
import smtplib
import secrets
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import bcrypt
import jwt

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models


router = APIRouter(prefix="/auth", tags=["Auth"])

# --------------------------------------------------
# Settings
# --------------------------------------------------

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

OTP_EXPIRE_MINUTES = 10
OTP_MAX_ATTEMPTS = 5

security = HTTPBearer()


# --------------------------------------------------
# Request schemas
# --------------------------------------------------

class StudentRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=20)


class OrganizationRegister(BaseModel):
    organization_name: str = Field(min_length=2, max_length=150)
    industry: str = Field(min_length=2, max_length=100)
    contact_email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=20)


class VerifyOTP(BaseModel):
    email: str
    otp: str = Field(min_length=6, max_length=6)


class LoginRequest(BaseModel):
    email: str
    password: str


# --------------------------------------------------
# Helper functions
# --------------------------------------------------

def validate_email(email: str):
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(pattern, email):
        raise HTTPException(
            status_code=400,
            detail="Please enter a valid email address."
        )


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    if len(password_bytes) > 20:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 20 characters."
        )

    return bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except ValueError:
        return False


def create_access_token(user: models.User) -> str:
    if not JWT_SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Authentication service is not configured. Please contact the administrator."
        )

    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def generate_otp() -> str:
    return f"{secrets.randbelow(1000000):06d}"


def send_otp_email(receiver_email: str, otp: str):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")

    if not smtp_email or not smtp_password:
        raise HTTPException(
            status_code=503,
            detail="Email service is currently unavailable. Please try again later."
        )

    message = EmailMessage()
    message["Subject"] = "Bloom - Email Verification"
    message["From"] = smtp_email
    message["To"] = receiver_email

    message.set_content(
        f"""
Welcome to Bloom!

Your email verification code is:

{otp}

This code expires in {OTP_EXPIRE_MINUTES} minutes.

If you did not create a Bloom account, you can ignore this email.
"""
    )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(smtp_email, smtp_password)
            server.send_message(message)

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to send verification email. Please try again later."
        )


# --------------------------------------------------
# Authentication and role helpers
# --------------------------------------------------


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = int(payload.get("sub"))

    except Exception:
        raise credentials_error

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user or not user.is_active:
        raise credentials_error

    return user



def require_roles(*allowed_roles):
    def role_checker(
        current_user: models.User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this feature."
            )

        return current_user

    return role_checker


# --------------------------------------------------
# Student registration
# --------------------------------------------------

@router.post("/register/student", status_code=201)
def register_student(
    data: StudentRegister,
    db: Session = Depends(get_db)
):
    email = data.email.strip().lower()
    validate_email(email)

    existing_user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="This email address is already registered."
        )

    otp = generate_otp()

    user = models.User(
        email=email,
        password_hash=hash_password(data.password),
        role=models.UserRole.student,
        is_active=False
    )

    user.student_profile = models.StudentProfile(
        full_name=data.full_name.strip()
    )

    verification = models.EmailVerification(
        code_hash=bcrypt.hashpw(
            otp.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8"),
        expires_at=datetime.utcnow() + timedelta(
            minutes=OTP_EXPIRE_MINUTES
        ),
        attempts=0,
        is_used=False
    )

    user_email = user.email
    user_verifications = verification

    try:
        db.add(user)
        db.flush()

        verification.user_id = user.id
        db.add(user_verifications)

        # Send the OTP before committing the registration.
        send_otp_email(user_email, otp)

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Registration successful. Please check your email for the OTP."
    }


# --------------------------------------------------
# Organization registration
# --------------------------------------------------

@router.post("/register/organization", status_code=201)
def register_organization(
    data: OrganizationRegister,
    db: Session = Depends(get_db)
):
    email = data.contact_email.strip().lower()
    validate_email(email)

    existing_user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="This email address is already registered."
        )

    user = models.User(
        email=email,
        password_hash=hash_password(data.password),
        role=models.UserRole.organization,
        is_active=True
    )

    user.organization_profile = models.OrganizationProfile(
        name=data.organization_name.strip(),
        approval_status=models.ReviewStatus.pending
    )

    try:
        db.add(user)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "message": "Organization registration submitted. Your account is pending admin approval."
    }


# --------------------------------------------------
# Verify student email OTP
# --------------------------------------------------

@router.post("/verify-email")
def verify_email(
    data: VerifyOTP,
    db: Session = Depends(get_db)
):
    email = data.email.strip().lower()

    user = db.query(models.User).filter(
        models.User.email == email,
        models.User.role == models.UserRole.student
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Student account not found."
        )

    if user.is_active:
        return {"message": "Email is already verified."}

    verification = db.query(models.EmailVerification).filter(
        models.EmailVerification.user_id == user.id,
        models.EmailVerification.is_used == False
    ).order_by(
        models.EmailVerification.created_at.desc()
    ).first()

    if not verification:
        raise HTTPException(
            status_code=400,
            detail="No active verification code found."
        )

    if verification.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=400,
            detail="OTP has expired. Please register again."
        )

    if verification.attempts >= OTP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=429,
            detail="Too many incorrect attempts."
        )

    if not bcrypt.checkpw(
        data.otp.encode("utf-8"),
        verification.code_hash.encode("utf-8")
    ):
        verification.attempts += 1
        db.commit()

        raise HTTPException(
            status_code=400,
            detail="Incorrect OTP."
        )

    verification.is_used = True
    user.is_active = True

    db.commit()

    return {
        "message": "Email verified successfully. Your account is now active."
    }


# --------------------------------------------------
# Login
# --------------------------------------------------

@router.post("/login")
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    email = data.email.strip().lower()

    user = db.query(models.User).filter(
        models.User.email == email
    ).first()

    if not user or not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Please verify your email before logging in."
        )

    token = create_access_token(user)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value
    }


# --------------------------------------------------
# Current logged-in user
# --------------------------------------------------

@router.get("/me")
def get_my_account(
    current_user: models.User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value
    }


# --------------------------------------------------
# Logout
# --------------------------------------------------

@router.post("/logout")
def logout(
    current_user: models.User = Depends(get_current_user)
):
    return {
        "message": "Logged out successfully. Please remove the token from the client."
    }
