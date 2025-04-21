from datetime import date

from pydantic import BaseModel, ConfigDict


class SiteBase(BaseModel):
    name: str
    installation_date: date | None = None
    max_power_megawatt: float | None = None
    min_power_megawatt: float | None = None
    useful_energy_at_1_megawatt: float | None = None
    groups: list[int] | None = None


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
