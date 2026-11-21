
"""Organization features for Bloom.

Owner: Ghofrane.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import OrganizationProfile, ReviewStatus

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"]
)


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    name: str
    description: str | None
    website: str | None
    city: str | None
    logo_url: str | None
    approval_status: ReviewStatus




# ---------- Organization opportunity creation ----------

from datetime import datetime
from pydantic import Field
from ..models import Opportunity, OpportunityType


class OpportunityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    type: OpportunityType
    city: str | None = Field(default=None, max_length=100)
    is_online: bool = False
    start_date: datetime | None = None
    end_date: datetime | None = None
    application_deadline: datetime | None = None
    requires_application: bool = True
    max_team_size: int | None = Field(
        default=None, ge=1, le=32767
    )



# ---------- Opportunity date validation ----------

from fastapi import HTTPException


def validate_opportunity_dates(data: OpportunityCreate):
    if (
        data.start_date is not None
        and data.end_date is not None
        and data.end_date < data.start_date
    ):
        raise HTTPException(
            status_code=422,
            detail="End date cannot be earlier than start date"
        )

    if (
        data.application_deadline is not None
        and data.start_date is not None
        and data.application_deadline > data.start_date
    ):
        raise HTTPException(
            status_code=422,
            detail="Application deadline cannot be after start date"
        )



# ---------- Create opportunity endpoint ----------

from fastapi import status
from ..models import User


def get_current_organization():
    """
    Temporary secure placeholder.

    Replace with Weam's authenticated organization
    dependency when the login system is ready.
    """
    raise HTTPException(
        status_code=503,
        detail="Organization authentication is not ready"
    )


@router.post("/opportunities", status_code=status.HTTP_201_CREATED)
def create_opportunity(
    data: OpportunityCreate,
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    organization = db.get(OrganizationProfile, current_user.id)

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization profile not found"
        )

    if organization.approval_status != ReviewStatus.approved:
        raise HTTPException(
            status_code=403,
            detail="Organization is not approved"
        )

    validate_opportunity_dates(data)

    opportunity = Opportunity(
        **data.model_dump(),
        organization_id=current_user.id,
        status=ReviewStatus.pending
    )

    db.add(opportunity)
    db.commit()
    db.refresh(opportunity)

    return {
        "message": "Opportunity submitted for admin approval",
        "opportunity_id": opportunity.id,
        "status": opportunity.status
    }


# ---------- View organization's opportunities ----------

@router.get("/me/opportunities")
def list_my_opportunities(
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    organization = db.get(
        OrganizationProfile,
        current_user.id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization profile not found"
        )

    opportunities = (
        db.query(Opportunity)
        .filter(Opportunity.organization_id == current_user.id)
        .order_by(Opportunity.created_at.desc())
        .all()
    )

    return [
        {
            "id": opportunity.id,
            "title": opportunity.title,
            "description": opportunity.description,
            "type": opportunity.type,
            "city": opportunity.city,
            "start_date": opportunity.start_date,
            "end_date": opportunity.end_date,
            "application_deadline": opportunity.application_deadline,
            "status": opportunity.status,
            "rejection_reason": opportunity.rejection_reason
        }
        for opportunity in opportunities
    ]


# ---------- Edit an organization's opportunity ----------

from fastapi import Path


@router.put("/me/opportunities/{opportunity_id}")
def update_my_opportunity(
    data: OpportunityCreate,
    opportunity_id: int = Path(ge=1),
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    opportunity = db.get(Opportunity, opportunity_id)

    if (
        opportunity is None
        or opportunity.organization_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    organization = db.get(
        OrganizationProfile,
        current_user.id
    )

    if (
        organization is None
        or organization.approval_status != ReviewStatus.approved
    ):
        raise HTTPException(
            status_code=403,
            detail="Organization is not approved"
        )

    validate_opportunity_dates(data)

    for field, value in data.model_dump().items():
        setattr(opportunity, field, value)

    # Edited opportunities must be reviewed again.
    opportunity.status = ReviewStatus.pending
    opportunity.reviewed_by = None
    opportunity.reviewed_at = None
    opportunity.rejection_reason = None

    db.commit()
    db.refresh(opportunity)

    return {
        "message": "Opportunity updated and submitted for approval",
        "opportunity_id": opportunity.id,
        "status": opportunity.status
    }


# ---------- Delete an organization's opportunity ----------

@router.delete("/me/opportunities/{opportunity_id}")
def delete_my_opportunity(
    opportunity_id: int = Path(ge=1),
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    organization = db.get(
        OrganizationProfile,
        current_user.id
    )

    if (
        organization is None
        or organization.approval_status != ReviewStatus.approved
    ):
        raise HTTPException(
            status_code=403,
            detail="Organization is not approved"
        )

    opportunity = db.get(Opportunity, opportunity_id)

    if (
        opportunity is None
        or opportunity.organization_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    db.delete(opportunity)
    db.commit()

    return {
        "message": "Opportunity deleted successfully"
    }


# ---------- View student applications ----------

from ..models import Application, StudentProfile


@router.get("/me/opportunities/{opportunity_id}/applications")
def list_opportunity_applications(
    opportunity_id: int = Path(ge=1),
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    opportunity = db.get(Opportunity, opportunity_id)

    if (
        opportunity is None
        or opportunity.organization_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    applications = (
        db.query(Application, StudentProfile)
        .join(
            StudentProfile,
            Application.student_id == StudentProfile.user_id
        )
        .filter(Application.opportunity_id == opportunity_id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    return [
        {
            "application_id": application.id,
            "student_id": student.user_id,
            "student_name": student.full_name,
            "university": student.university,
            "major": student.major,
            "message": application.message,
            "status": application.status,
            "applied_at": application.applied_at
        }
        for application, student in applications
    ]


# ---------- Update student application status ----------

from pydantic import Field
from ..models import ApplicationStatus


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


@router.patch("/me/applications/{application_id}/status")
def update_application_status(
    data: ApplicationStatusUpdate,
    application_id: int = Path(ge=1),
    current_user: User = Depends(get_current_organization),
    db: Session = Depends(get_db)
):
    application = db.get(Application, application_id)

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    opportunity = db.get(
        Opportunity,
        application.opportunity_id
    )

    if (
        opportunity is None
        or opportunity.organization_id != current_user.id
    ):
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    allowed_statuses = {
        ApplicationStatus.under_review,
        ApplicationStatus.accepted,
        ApplicationStatus.rejected
    }

    if data.status not in allowed_statuses:
        raise HTTPException(
            status_code=422,
            detail="Organizations can only set under_review, accepted, or rejected"
        )

    application.status = data.status
    application.status_updated_at = datetime.utcnow()

    db.commit()
    db.refresh(application)

    return {
        "message": "Application status updated successfully",
        "application_id": application.id,
        "status": application.status
    }


@router.get("/{organization_id}", response_model=OrganizationResponse)
def get_organization(
    organization_id: int,
    db: Session = Depends(get_db)
):
    organization = db.get(OrganizationProfile, organization_id)

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    if organization.approval_status != ReviewStatus.approved:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    return organization