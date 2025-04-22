from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.schemas.group import GroupRead

from pydantic import BaseModel, ConfigDict
from infrastructure.models.site import SiteCountry

from .group import GroupRead


class SiteBase(BaseModel):
    name: str
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    country: SiteCountry | None = None


class SiteFranceBase(SiteBase):
    country: SiteCountry = SiteCountry.france
    useful_energy_at_1_megawatt: float | None = None


class SiteItalyBase(SiteBase):
    country: SiteCountry = SiteCountry.italy
    efficiency: float | None = None


class SiteFranceRead(SiteFranceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SiteItalyRead(SiteItalyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class SiteFranceCreate(SiteFranceBase):
    pass


class SiteItalyCreate(SiteItalyBase):
    pass


SiteCreate = SiteFranceCreate | SiteItalyCreate
class SiteRead(SiteFranceRead, SiteItalyRead):
    pass


class SiteUpdate(BaseModel):
    name: str | None = None
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None


class Site(SiteBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None


class SiteWithGroups(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    country: SiteCountry
    useful_energy_at_1_megawatt: float | None = None
    efficiency: float | None = None
    groups: list["GroupRead"] = []
