
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
