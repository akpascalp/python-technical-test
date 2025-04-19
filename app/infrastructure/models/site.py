from sqlalchemy import Column, Integer, Float, String, Boolean, Date
from sqlalchemy.orm import relationship

from app.infrastructure.db import Base


class Site(Base):
    """Site model."""
    
    __tablename__ = "sites"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    installation_date = Column(Date, nullable=True)
    max_power_megawatt = Column(Float, nullable=True)
    min_power_megawatt = Column(Float, nullable=True)
    userful_energy_at_1_megawatt = Column(Float, nullable=True)

    groups = relationship("Group", back_populates="site")
