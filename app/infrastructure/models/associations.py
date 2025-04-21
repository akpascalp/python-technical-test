from sqlalchemy import Table, Column, ForeignKey
from ..db import Base

site_group = Table(
    'site_group', Base.metadata,
    Column('site_id', ForeignKey('sites.id'), primary_key=True),
    Column('group_id', ForeignKey('groups.id'), primary_key=True)
)
