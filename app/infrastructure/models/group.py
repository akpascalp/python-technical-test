from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from ..db import Base
from .associations import site_group

class GroupType(str, enum.Enum):
    GROUP1 = "group1"
    GROUP2 = "group2" 
    GROUP3 = "group3"

class Group(Base):
    """Group model."""
    
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    type = Column(Enum(GroupType), nullable=True)

    parent_id = Column(Integer, ForeignKey("groups.id"))
    children = relationship("Group", backref="parent", remote_side=[id])

    sites = relationship("Site", secondary=site_group, back_populates="groups")
