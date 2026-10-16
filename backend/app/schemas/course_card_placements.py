from uuid import UUID

from pydantic import BaseModel, Field


class CourseCardPlacementInput(BaseModel):
    page_key: str = Field(min_length=1, max_length=80, pattern="^[a-z0-9-]+$")
    section_key: str = Field(min_length=1, max_length=80, pattern="^[a-z0-9-]+$")
    card_key: str = Field(min_length=1, max_length=160, pattern="^[a-z0-9-]+$")
    position: int = Field(ge=0, le=1000)
    visible: bool = True


class CourseCardPlacementRow(CourseCardPlacementInput):
    id: UUID

    model_config = {"from_attributes": True}


class CourseCardPlacementReplace(BaseModel):
    page_key: str = Field(min_length=1, max_length=80, pattern="^[a-z0-9-]+$")
    section_key: str = Field(min_length=1, max_length=80, pattern="^[a-z0-9-]+$")
    placements: list[CourseCardPlacementInput] = Field(max_length=50)
