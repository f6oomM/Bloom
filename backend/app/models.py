"""SQLAlchemy models for Bloom. Keep in sync with backend/database/schema.sql."""
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, SmallInteger,
    String, Table, Text, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def _enum(py_enum, name):
    # store the lowercase values ('student', 'pending', ...) exactly as in schema.sql
    return Enum(py_enum, name=name, values_callable=lambda e: [m.value for m in e])


class UserRole(str, enum.Enum):
    student = "student"
    organization = "organization"
    admin = "admin"


class ReviewStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class OpportunityType(str, enum.Enum):
    hackathon = "hackathon"
    internship = "internship"
    coop = "coop"
    volunteer = "volunteer"
    workshop = "workshop"
    seminar = "seminar"


class ApplicationStatus(str, enum.Enum):
    submitted = "submitted"
    under_review = "under_review"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class TeamRole(str, enum.Enum):
    leader = "leader"
    member = "member"


class JoinRequestStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"


class NotificationType(str, enum.Enum):
    application_update = "application_update"
    event_reminder = "event_reminder"
    team_request = "team_request"
    team_update = "team_update"
    approval_update = "approval_update"


# ---------- many-to-many link tables ----------
student_interests = Table(
    "student_interests", Base.metadata,
    Column("student_id", ForeignKey("student_profiles.user_id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)

student_skills = Table(
    "student_skills", Base.metadata,
    Column("student_id", ForeignKey("student_profiles.user_id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

opportunity_interests = Table(
    "opportunity_interests", Base.metadata,
    Column("opportunity_id", ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True),
    Column("interest_id", ForeignKey("interests.id", ondelete="CASCADE"), primary_key=True),
)


# ---------- accounts and profiles ----------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(_enum(UserRole, "user_role"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False,
                                   cascade="all, delete-orphan")
    organization_profile = relationship("OrganizationProfile", back_populates="user", uselist=False,
                                        foreign_keys="OrganizationProfile.user_id",
                                        cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Interest(Base):
    __tablename__ = "interests"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    university: Mapped[str | None] = mapped_column(String(150))
    major: Mapped[str | None] = mapped_column(String(100))
    year_level: Mapped[int | None] = mapped_column(SmallInteger)
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    bio: Mapped[str | None] = mapped_column(Text)
    github_url: Mapped[str | None] = mapped_column(String(255))
    linkedin_url: Mapped[str | None] = mapped_column(String(255))
    looking_for_team: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False,
                                                   server_default="0", index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now(),
                                                 onupdate=func.now())

    user = relationship("User", back_populates="student_profile")
    interests = relationship("Interest", secondary=student_interests)
    skills = relationship("Skill", secondary=student_skills)
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    saved_events = relationship("SavedEvent", back_populates="student", cascade="all, delete-orphan")


class OrganizationProfile(Base):
    __tablename__ = "organization_profiles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    logo_url: Mapped[str | None] = mapped_column(String(255))
    approval_status: Mapped[ReviewStatus] = mapped_column(_enum(ReviewStatus, "org_approval_status"),
                                                          nullable=False, default=ReviewStatus.pending,
                                                          index=True)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="organization_profile", foreign_keys=[user_id])
    opportunities = relationship("Opportunity", back_populates="organization", cascade="all, delete-orphan")


# ---------- opportunities ----------
class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        Index("idx_opp_status_type", "status", "type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organization_profiles.user_id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[OpportunityType] = mapped_column(_enum(OpportunityType, "opportunity_type"), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), index=True)
    is_online: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    start_date: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime)
    application_deadline: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    requires_application: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True,
                                                       server_default="1")
    max_team_size: Mapped[int | None] = mapped_column(SmallInteger)
    status: Mapped[ReviewStatus] = mapped_column(_enum(ReviewStatus, "opportunity_status"),
                                                 nullable=False, default=ReviewStatus.pending)
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)
    rejection_reason: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    organization = relationship("OrganizationProfile", back_populates="opportunities")
    interests = relationship("Interest", secondary=opportunity_interests)
    applications = relationship("Application", back_populates="opportunity", cascade="all, delete-orphan")
    teams = relationship("Team", back_populates="opportunity", cascade="all, delete-orphan")


# ---------- student actions ----------
class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("opportunity_id", "student_id", name="uq_app"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"),
                                                nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
                                            nullable=False, index=True)
    message: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ApplicationStatus] = mapped_column(_enum(ApplicationStatus, "application_status"),
                                                      nullable=False, default=ApplicationStatus.submitted,
                                                      index=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())
    status_updated_at: Mapped[datetime | None] = mapped_column(DateTime)

    opportunity = relationship("Opportunity", back_populates="applications")
    student = relationship("StudentProfile", back_populates="applications")


class SavedEvent(Base):
    """A student's personal calendar entry."""
    __tablename__ = "saved_events"
    __table_args__ = (UniqueConstraint("student_id", "opportunity_id", name="uq_se"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
                                            nullable=False)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"),
                                                nullable=False)
    remind_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    student = relationship("StudentProfile", back_populates="saved_events")
    opportunity = relationship("Opportunity")


# ---------- teams ----------
class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    opportunity_id: Mapped[int] = mapped_column(ForeignKey("opportunities.id", ondelete="CASCADE"),
                                                nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    leader_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
                                           nullable=False)
    max_members: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=4, server_default="4")
    is_open: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    opportunity = relationship("Opportunity", back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    join_requests = relationship("TeamJoinRequest", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    __tablename__ = "team_members"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
                                            primary_key=True)
    role: Mapped[TeamRole] = mapped_column(_enum(TeamRole, "team_role"), nullable=False,
                                           default=TeamRole.member)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    team = relationship("Team", back_populates="members")
    student = relationship("StudentProfile")


class TeamJoinRequest(Base):
    __tablename__ = "team_join_requests"
    __table_args__ = (UniqueConstraint("team_id", "student_id", name="uq_tjr"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("student_profiles.user_id", ondelete="CASCADE"),
                                            nullable=False)
    message: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[JoinRequestStatus] = mapped_column(_enum(JoinRequestStatus, "join_request_status"),
                                                      nullable=False, default=JoinRequestStatus.pending,
                                                      index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    team = relationship("Team", back_populates="join_requests")
    student = relationship("StudentProfile")


# ---------- notifications ----------
class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("idx_n_user_read", "user_id", "is_read"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[NotificationType] = mapped_column(_enum(NotificationType, "notification_type"),
                                                   nullable=False)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id", ondelete="SET NULL"))
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class EmailVerification(Base):
    """One-time password (OTP) sent to a student's email when registering."""
 
    __tablename__ = "email_verifications"
    __table_args__ = (Index("idx_ev_user", "user_id", "is_used"),)
 
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)  # hashed, never plain text
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attempts: Mapped[int] = mapped_column(TINYINT, nullable=False, default=0)
    is_used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )