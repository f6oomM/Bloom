
"""Student features: profile, personal calendar, applications, team formation.

Owner: Weam.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from .auth import require_roles


router = APIRouter(prefix="/students", tags=["Students"])


# --------------------------------------------------
# Request Schemas
# --------------------------------------------------

class StudentProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    university: str | None = Field(default=None, max_length=150)
    major: str | None = Field(default=None, max_length=100)
    year_level: int | None = Field(default=None, ge=1, le=10)
    city: str | None = Field(default=None, max_length=100)
    bio: str | None = None
    github_url: str | None = Field(default=None, max_length=255)
    linkedin_url: str | None = Field(default=None, max_length=255)
    looking_for_team: bool | None = None


class ApplicationCreate(BaseModel):
    opportunity_id: int
    message: str | None = None


class SaveEventRequest(BaseModel):
    opportunity_id: int
    remind_at: datetime | None = None


class TeamCreate(BaseModel):
    opportunity_id: int
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    max_members: int = Field(default=4, ge=2, le=20)


class TeamJoinRequestCreate(BaseModel):
    message: str | None = Field(default=None, max_length=500)


# --------------------------------------------------
# Helper Functions
# --------------------------------------------------

def get_student_profile(db: Session, user_id: int):
    profile = db.query(models.StudentProfile).filter(
        models.StudentProfile.user_id == user_id
    ).first()

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Student profile not found."
        )

    return profile


def get_approved_opportunity(db: Session, opportunity_id: int):
    opportunity = db.query(models.Opportunity).filter(
        models.Opportunity.id == opportunity_id,
        models.Opportunity.status == models.ReviewStatus.approved
    ).first()

    if not opportunity:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found or not available."
        )

    organization = db.query(models.OrganizationProfile).filter(
        models.OrganizationProfile.user_id == opportunity.organization_id,
        models.OrganizationProfile.approval_status == models.ReviewStatus.approved
    ).first()

    if not organization:
        raise HTTPException(
            status_code=404,
            detail="Opportunity organization is not approved."
        )

    return opportunity


# --------------------------------------------------
# 1. Student Profile Management
# --------------------------------------------------

@router.get("/me/profile")
def get_my_profile(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    profile = get_student_profile(db, current_user.id)

    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": profile.full_name,
        "university": profile.university,
        "major": profile.major,
        "year_level": profile.year_level,
        "city": profile.city,
        "bio": profile.bio,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "looking_for_team": profile.looking_for_team
    }


@router.put("/me/profile")
def update_my_profile(
    data: StudentProfileUpdate,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    profile = get_student_profile(db, current_user.id)

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    try:
        db.commit()
        db.refresh(profile)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to update student profile."
        )

    return {
        "message": "Student profile updated successfully.",
        "full_name": profile.full_name,
        "university": profile.university,
        "major": profile.major,
        "year_level": profile.year_level,
        "city": profile.city,
        "bio": profile.bio,
        "github_url": profile.github_url,
        "linkedin_url": profile.linkedin_url,
        "looking_for_team": profile.looking_for_team
    }


# --------------------------------------------------
# 2. Application Management
# --------------------------------------------------

@router.post("/applications", status_code=status.HTTP_201_CREATED)
def apply_to_opportunity(
    data: ApplicationCreate,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    get_student_profile(db, current_user.id)

    opportunity = get_approved_opportunity(
        db, data.opportunity_id
    )

    if not opportunity.requires_application:
        raise HTTPException(
            status_code=400,
            detail="This opportunity does not require an application."
        )

    if (
        opportunity.application_deadline
        and opportunity.application_deadline < datetime.utcnow()
    ):
        raise HTTPException(
            status_code=400,
            detail="The application deadline has passed."
        )

    existing_application = db.query(models.Application).filter(
        models.Application.student_id == current_user.id,
        models.Application.opportunity_id == data.opportunity_id
    ).first()

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="You have already applied to this opportunity."
        )

    application = models.Application(
        student_id=current_user.id,
        opportunity_id=data.opportunity_id,
        message=data.message,
        status=models.ApplicationStatus.submitted
    )

    try:
        db.add(application)
        db.commit()
        db.refresh(application)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to submit your application."
        )

    return {
        "message": "Application submitted successfully.",
        "application_id": application.id,
        "opportunity_id": application.opportunity_id,
        "status": application.status.value
    }


@router.get("/applications")
def get_my_applications(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    applications = db.query(models.Application).filter(
        models.Application.student_id == current_user.id
    ).order_by(
        models.Application.applied_at.desc()
    ).all()

    return [
        {
            "application_id": application.id,
            "opportunity_id": application.opportunity_id,
            "opportunity_title": application.opportunity.title,
            "message": application.message,
            "status": application.status.value,
            "applied_at": application.applied_at,
            "status_updated_at": application.status_updated_at
        }
        for application in applications
    ]


# --------------------------------------------------
# 3. Personal Calendar
# --------------------------------------------------

@router.post("/calendar", status_code=status.HTTP_201_CREATED)
def save_event(
    data: SaveEventRequest,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    get_student_profile(db, current_user.id)

    get_approved_opportunity(db, data.opportunity_id)

    existing_event = db.query(models.SavedEvent).filter(
        models.SavedEvent.student_id == current_user.id,
        models.SavedEvent.opportunity_id == data.opportunity_id
    ).first()

    if existing_event:
        raise HTTPException(
            status_code=409,
            detail="This opportunity is already saved in your calendar."
        )

    saved_event = models.SavedEvent(
        student_id=current_user.id,
        opportunity_id=data.opportunity_id,
        remind_at=data.remind_at
    )

    try:
        db.add(saved_event)
        db.commit()
        db.refresh(saved_event)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to save this event."
        )

    return {
        "message": "Event saved to your calendar successfully.",
        "event_id": saved_event.id,
        "opportunity_id": saved_event.opportunity_id
    }


@router.get("/calendar")
def get_my_calendar(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    now = datetime.utcnow()

    events = db.query(models.SavedEvent).join(
        models.Opportunity,
        models.SavedEvent.opportunity_id == models.Opportunity.id
    ).filter(
        models.SavedEvent.student_id == current_user.id,
        (
            (models.Opportunity.start_date == None)
            | (models.Opportunity.start_date >= now)
        )
    ).order_by(
        models.Opportunity.start_date.asc()
    ).all()

    return [
        {
            "event_id": event.id,
            "opportunity_id": event.opportunity_id,
            "title": event.opportunity.title,
            "start_date": event.opportunity.start_date,
            "end_date": event.opportunity.end_date,
            "city": event.opportunity.city,
            "remind_at": event.remind_at
        }
        for event in events
    ]


@router.delete("/calendar/{event_id}")
def remove_calendar_event(
    event_id: int,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    event = db.query(models.SavedEvent).filter(
        models.SavedEvent.id == event_id,
        models.SavedEvent.student_id == current_user.id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Calendar event not found."
        )

    db.delete(event)
    db.commit()

    return {
        "message": "Event removed from your calendar successfully."
    }


# --------------------------------------------------
# 4. Notification Management
# --------------------------------------------------

@router.get("/notifications")
def get_my_notifications(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    notifications = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    ).order_by(
        models.Notification.created_at.desc()
    ).all()

    return [
        {
            "notification_id": notification.id,
            "type": notification.type.value,
            "message": notification.message,
            "opportunity_id": notification.opportunity_id,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
        for notification in notifications
    ]


@router.patch("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found."
        )

    notification.is_read = True
    db.commit()

    return {
        "message": "Notification marked as read."
    }


# --------------------------------------------------
# 5. Team Formation
# --------------------------------------------------

@router.post("/teams", status_code=status.HTTP_201_CREATED)
def create_team(
    data: TeamCreate,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    get_student_profile(db, current_user.id)

    opportunity = get_approved_opportunity(
        db, data.opportunity_id
    )

    if opportunity.max_team_size is not None:
        if data.max_members > opportunity.max_team_size:
            raise HTTPException(
                status_code=400,
                detail="Team size exceeds the opportunity maximum team size."
            )

    team = models.Team(
        opportunity_id=data.opportunity_id,
        name=data.name,
        description=data.description,
        leader_id=current_user.id,
        max_members=data.max_members,
        is_open=True
    )

    try:
        db.add(team)
        db.flush()

        leader_membership = models.TeamMember(
            team_id=team.id,
            student_id=current_user.id,
            role=models.TeamRole.leader
        )

        db.add(leader_membership)
        db.commit()
        db.refresh(team)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to create the team."
        )

    return {
        "message": "Team created successfully.",
        "team_id": team.id,
        "name": team.name,
        "opportunity_id": team.opportunity_id
    }


@router.post("/teams/{team_id}/join-requests", status_code=status.HTTP_201_CREATED)
def request_to_join_team(
    team_id: int,
    data: TeamJoinRequestCreate,
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    get_student_profile(db, current_user.id)

    team = db.query(models.Team).filter(
        models.Team.id == team_id
    ).first()

    if not team:
        raise HTTPException(
            status_code=404,
            detail="Team not found."
        )

    if not team.is_open:
        raise HTTPException(
            status_code=400,
            detail="This team is not accepting new members."
        )

    existing_member = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id,
        models.TeamMember.student_id == current_user.id
    ).first()

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="You are already a member of this team."
        )

    existing_request = db.query(models.TeamJoinRequest).filter(
        models.TeamJoinRequest.team_id == team_id,
        models.TeamJoinRequest.student_id == current_user.id
    ).first()

    if existing_request:
        raise HTTPException(
            status_code=409,
            detail="You have already submitted a request to this team."
        )

    member_count = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id
    ).count()

    if member_count >= team.max_members:
        raise HTTPException(
            status_code=400,
            detail="This team has reached its maximum number of members."
        )

    join_request = models.TeamJoinRequest(
        team_id=team_id,
        student_id=current_user.id,
        message=data.message,
        status=models.JoinRequestStatus.pending
    )

    try:
        db.add(join_request)
        db.commit()
        db.refresh(join_request)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Unable to submit your team join request."
        )

    return {
        "message": "Team join request submitted successfully.",
        "request_id": join_request.id,
        "team_id": team_id,
        "status": join_request.status.value
    }


@router.get("/teams")
def get_my_teams(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    memberships = db.query(models.TeamMember).filter(
        models.TeamMember.student_id == current_user.id
    ).all()

    return [
        {
            "team_id": membership.team.id,
            "name": membership.team.name,
            "description": membership.team.description,
            "opportunity_id": membership.team.opportunity_id,
            "opportunity_title": membership.team.opportunity.title,
            "leader_id": membership.team.leader_id,
            "role": membership.role.value,
            "max_members": membership.team.max_members,
            "is_open": membership.team.is_open
        }
        for membership in memberships
    ]


@router.get("/teams/join-requests")
def get_my_team_requests(
    current_user: models.User = Depends(
        require_roles(models.UserRole.student)
    ),
    db: Session = Depends(get_db)
):
    requests = db.query(models.TeamJoinRequest).filter(
        models.TeamJoinRequest.student_id == current_user.id
    ).order_by(
        models.TeamJoinRequest.created_at.desc()
    ).all()

    return [
        {
            "request_id": request.id,
            "team_id": request.team_id,
            "team_name": request.team.name,
            "status": request.status.value,
            "message": request.message,
            "created_at": request.created_at
        }
        for request in requests
    ]

