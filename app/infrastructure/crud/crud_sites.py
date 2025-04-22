from fastcrud import FastCRUD
from ..models.site import Site, SiteFrance, SiteItaly

site_crud = FastCRUD(Site)
site_france_crud = FastCRUD(SiteFrance)
site_italy_crud = FastCRUD(SiteItaly)
