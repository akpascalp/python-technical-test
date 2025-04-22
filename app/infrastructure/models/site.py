from sqlalchemy import Column, Integer, Float, String, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .associations import site_group
from ..db import Base

class SiteCountry(str, enum.Enum):
    FRANCE = "france"
    ITALY = "italy"


class Site(Base):
    """Site model."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    installation_date = Column(Date, nullable=True)
    max_power_megawatt = Column(Float, nullable=True)
    min_power_megawatt = Column(Float, nullable=True)

    country = Column(Enum(SiteCountry), nullable=False)

    __mapper_args__ = {
        "polymorphic_on": country,
        "polymorphic_identity": None
    }

    groups = relationship("Group", secondary=site_group, back_populates="sites")


class SiteFrance(Site):
    """Site model for France."""
    
    __tablename__ = "sites_france"
    
    id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True)
    useful_energy_at_1_megawatt = Column(Float, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": SiteCountry.FRANCE,
    }

class SiteItaly(Site):
    """Site model for Italy."""
    
    __tablename__ = "sites_italy"
    
    id = Column(Integer, ForeignKey("sites.id", ondelete="CASCADE"), primary_key=True)
    efficiency = Column(Float, nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": SiteCountry.ITALY,
    }
