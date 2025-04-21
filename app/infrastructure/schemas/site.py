from datetime import date
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from infrastructure.schemas.group import GroupRead

from pydantic import BaseModel, ConfigDict

from .group import GroupRead


class SiteBase(BaseModel):
    name: str
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None


class SiteRead(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SiteCreate(SiteBase):
    pass


class SiteUpdate(BaseModel):
    name: str | None = None
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None


class Site(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int


class SiteWithGroups(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    groups: list["GroupRead"] = []