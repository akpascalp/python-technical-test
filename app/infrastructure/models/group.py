from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.infrastructure.db import Base

class GroupType(enum.Enum):
    GROUP1 = "group1"
    GROUP2 = "group2" 
    GROUP3 = "group3"

class Group(Base):
    """Group model."""
    
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(Enum(GroupType), nullable=True)

    site_id = Column(Integer, ForeignKey("sites.id"))

    site = relationship("Site", back_populates="groups")
    users = relationship("User", back_populates="group")
