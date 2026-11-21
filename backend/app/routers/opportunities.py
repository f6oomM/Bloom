
"""Browse, search and filter Bloom opportunities.

Owner: Ghofrane.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db


from ..models import (
    Interest,
    Opportunity,
    OpportunityType,
    OrganizationProfile,
    ReviewStatus,
)


router = APIRouter(
    prefix="/opportunities",
    tags=["Opportunities"]
)






# ---------- View, search and filter approved opportunities ----------

@router.get("/")
def list_approved_opportunities(
    search: str | None = Query(default=None, max_length=100),
    city: str | None = Query(default=None, max_length=100),
    type: OpportunityType | None = None,
    interest: str | None = Query(default=None, max_length=80),
    db: Session = Depends(get_db)
):
    query = (
        db.query(Opportunity)
        .join(
            OrganizationProfile,
            Opportunity.organization_id == OrganizationProfile.user_id
        )
        .filter(
            Opportunity.status == ReviewStatus.approved,
            OrganizationProfile.approval_status == ReviewStatus.approved
        )
    )

    if search and search.strip():
        keyword = search.strip()
        query = query.filter(
            Opportunity.title.ilike(f"%{keyword}%")
            | Opportunity.description.ilike(f"%{keyword}%")
        )

    if city and city.strip():
        query = query.filter(
            Opportunity.city.ilike(city.strip())
        )

    if type is not None:
        query = query.filter(Opportunity.type == type)

    if interest and interest.strip():
        query = query.filter(
            Opportunity.interests.any(
                Interest.name.ilike(interest.strip())
            )
        )

    opportunities = query.order_by(
        Opportunity.created_at.desc()
    ).limit(100).all()

    return [
        {
            "id": opportunity.id,
            "title": opportunity.title,
            "description": opportunity.description,
            "type": opportunity.type,
            "city": opportunity.city,
            "is_online": opportunity.is_online,
            "start_date": opportunity.start_date,
            "end_date": opportunity.end_date,
            "application_deadline": opportunity.application_deadline,
            "organization_id": opportunity.organization_id
        }
        for opportunity in opportunities
    ]


# ---------- View one opportunity's details ----------

from fastapi import Path


@router.get("/{opportunity_id}")
def get_opportunity_details(
    opportunity_id: int = Path(ge=1),
    db: Session = Depends(get_db)
):
    opportunity = (
        db.query(Opportunity)
        .join(
            OrganizationProfile,
            Opportunity.organization_id == OrganizationProfile.user_id
        )
        .filter(
            Opportunity.id == opportunity_id,
            Opportunity.status == ReviewStatus.approved,
            OrganizationProfile.approval_status == ReviewStatus.approved
        )
        .first()
    )

    if opportunity is None:
        raise HTTPException(
            status_code=404,
            detail="Opportunity not found"
        )

    return {
        "id": opportunity.id,
        "title": opportunity.title,
        "description": opportunity.description,
        "type": opportunity.type,
        "city": opportunity.city,
        "is_online": opportunity.is_online,
        "start_date": opportunity.start_date,
        "end_date": opportunity.end_date,
        "application_deadline": opportunity.application_deadline,
        "requires_application": opportunity.requires_application,
        "max_team_size": opportunity.max_team_size,
        "organization_id": opportunity.organization_id,
        "organization_name": opportunity.organization.name,
        "interests": [
            interest.name for interest in opportunity.interests
        ]
    }

