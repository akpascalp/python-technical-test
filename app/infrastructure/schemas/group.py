from ..models.group import GroupType

from pydantic import BaseModel, ConfigDict


class GroupBase(BaseModel):
    name: str
    type: GroupType | None = None
    parent_id: int | None = None


class GroupCreate(GroupBase):
    pass


class GroupRead(GroupBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class Group(GroupBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
