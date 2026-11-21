
"""Admin features for Bloom.

Owner: Ghofrane.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    OrganizationProfile,
    ReviewStatus,
    User,
)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


# ---------- Authentication dependency ----------

def get_current_admin():
    """
    Temporary secure placeholder.

    Replace this with Weam's authenticated
    admin dependency when available.
    """
    raise HTTPException(
        status_code=503,
        detail="Admin authentication is not ready"
    )


# ---------- View pending organizations ----------

@router.get("/organizations/pending")
def list_pending_organizations(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    organizations = (
        db.query(OrganizationProfile)
        .filter(
            OrganizationProfile.approval_status
            == ReviewStatus.pending
        )
        .order_by(OrganizationProfile.created_at.desc())
        .all()
    )

    return [
        {
            "user_id": org.user_id,
            "name": org.name,
            "description": org.description,
            "website": org.website,
            "city": org.city,
            "approval_status": org.approval_status,
            "created_at": org.created_at
        }
        for org in organizations
    ]


# ---------- Approve or reject organizations ----------

from datetime import datetime, timezone
from fastapi import Path
from pydantic import BaseModel, Field


class OrganizationReview(BaseModel):
    decision: ReviewStatus
    rejection_reason: str | None = Field(
        default=None,
        max_length=255
    )


@router.patch("/organizations/{organization_id}/review")
def review_organization(
    data: OrganizationReview,
    organization_id: int = Path(ge=1),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if data.decision not in {
        ReviewStatus.approved,
        ReviewStatus.rejected
    }:
        raise HTTPException(
            status_code=422,
            detail="Decision must be approved or rejected"
        )

    if (
        data.decision == ReviewStatus.rejected
        and not (data.rejection_reason or "").strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Rejection reason is required"
        )

    organization = db.get(
        OrganizationProfile,
        organization_id
    )

    if organization is None:
        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    if organization.approval_status != ReviewStatus.pending:
        raise HTTPException(
            status_code=409,
            detail="Only pending organizations can be reviewed"
        )

    organization.approval_status = data.decision
    organization.reviewed_by = current_user.id
    organization.reviewed_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    organization.rejection_reason = (
        data.rejection_reason.strip()
        if data.decision == ReviewStatus.rejected
        else None
    )

    db.commit()
    db.refresh(organization)

    return {
        "message": "Organization review completed",
        "organization_id": organization.user_id,
        "status": organization.approval_status
    }



# ---------- View pending opportunities ----------

from ..models import Opportunity


@router.get("/opportunities/pending")
def list_pending_opportunities(
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    opportunities = (
        db.query(Opportunity)
        .filter(
            Opportunity.status == ReviewStatus.pending
        )
        .order_by(Opportunity.created_at.desc())
        .all()
    )

    return [
        {
            "id": opportunity.id,
            "organization_id": opportunity.organization_id,
            "title": opportunity.title,
            "description": opportunity.description,
            "type": opportunity.type,
            "city": opportunity.city,
            "start_date": opportunity.start_date,
            "end_date": opportunity.end_date,
            "application_deadline": opportunity.application_deadline,
            "status": opportunity.status,
            "created_at": opportunity.created_at
        }
        for opportunity in opportunities
    ]


# ---------- Approve or reject opportunities ----------

class OpportunityReview(BaseModel):
    decision: ReviewStatus
    rejection_reason: str | None = Field(
        default=None,
        max_length=255
    )


@router.patch("/opportunities/{opportunity_id}/review")
def review_opportunity(
    data: OpportunityReview,
    opportunity_id: int = Path(ge=1),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    if data.decision not in {
        ReviewStatus.approved,
        ReviewStatus.rejected
    }:
        raise HTTPException(
            status_code=422,
            detail="Decision must be approved or rejected"
        )

    if (
        data.decision == ReviewStatus.rejected
        and not (data.rejection_reason or "").strip()
    ):
        raise HTTPException(
            status_code=422,
            detail="Rejection reason is required"
        )

    opportunity = db.get(Opportunity, opportunity_id)

    if opportunity is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    if opportunity.status != ReviewStatus.pending:
        raise HTTPException(
            status_code=409,
            detail="Only pending opportunities can be reviewed"
        )

    if data.decision == ReviewStatus.approved:
        organization = db.get(
            OrganizationProfile,
            opportunity.organization_id
        )

        if (
            organization is None
            or organization.approval_status != ReviewStatus.approved
        ):
            raise HTTPException(
                status_code=409,
                detail="Organization must be approved first"
            )

    opportunity.status = data.decision
    opportunity.reviewed_by = current_user.id
    opportunity.reviewed_at = datetime.now(timezone.utc).replace(
        tzinfo=None
    )
    opportunity.rejection_reason = (
        data.rejection_reason.strip()
        if data.decision == ReviewStatus.rejected
        else None
    )

    db.commit()
    db.refresh(opportunity)

    return {
        "message": "Opportunity review completed",
        "opportunity_id": opportunity.id,
        "status": opportunity.status
    }



# ---------- View registered users ----------

from ..models import UserRole


@router.get("/users")
def list_users(
    role: UserRole | None = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)

    users = query.order_by(User.id).all()

    return [
        {
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at
        }
        for user in users
    ]


# ---------- Activate or deactivate accounts ----------

class UserStatusUpdate(BaseModel):
    is_active: bool


@router.patch("/users/{user_id}/status")
def update_user_status(
    data: UserStatusUpdate,
    user_id: int = Path(ge=1),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    if user.id == current_user.id and not data.is_active:
        raise HTTPException(
            status_code=403,
            detail="You cannot deactivate your own account"
        )

    user.is_active = data.is_active

    db.commit()
    db.refresh(user)

    return {
        "message": "User account status updated successfully",
        "user_id": user.id,
        "is_active": user.is_active
    }
