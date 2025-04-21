from sqlalchemy import Column, Integer, Float, String, Date
from sqlalchemy.orm import relationship

from .associations import site_group
from ..db import Base


class Site(Base):
    """Site model."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    installation_date = Column(Date, nullable=True)
    max_power_megawatt = Column(Float, nullable=True)
    min_power_megawatt = Column(Float, nullable=True)
    useful_energy_at_1_megawatt = Column(Float, nullable=True)

    groups = relationship("Group", secondary=site_group, back_populates="sites")
