from datetime import date, timedelta
import pytest
from faker import Faker
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload, with_polymorphic

from infrastructure.models.site import Site, SiteFrance, SiteItaly
from infrastructure.models.group import Group

fake = Faker()


# ---- read sites ----
@pytest.mark.asyncio
async def test_get_all_sites(client: AsyncClient, sample_sites: list[Site]):
    """Test getting all sites without filters."""
    response = client.get("/api/v1/sites/")
    assert response.status_code == 200

    json_data = response.json()
    assert "data" in json_data
    data = json_data["data"]

    site_ids = {site.id for site in sample_sites}
    response_ids = {site["id"] for site in data}

    assert site_ids.issubset(response_ids)


@pytest.mark.asyncio
async def test_get_sites_pagination(client: AsyncClient):
    """Test pagination for sites."""
    page = 1
    items_per_page = 3

    response = client.get(f"/api/v1/sites/?page={page}&items_per_page={items_per_page}")
    assert response.status_code == 200

    json_data = response.json()
    assert "data" in json_data
    assert "page" in json_data
    assert "items_per_page" in json_data
    assert "total_count" in json_data
    assert "has_more" in json_data

    assert len(json_data["data"]) <= items_per_page

    if json_data["has_more"]:
        page_2 = 2
        response2 = client.get(f"/api/v1/sites/?page={page_2}&items_per_page={items_per_page}")
        assert response2.status_code == 200

        json_data2 = response2.json()

        first_page_ids = {site["id"] for site in json_data["data"]}
        second_page_ids = {site["id"] for site in json_data2["data"]}
        assert not first_page_ids.intersection(second_page_ids)


@pytest.mark.asyncio
async def test_get_sites_filter_by_name(client: AsyncClient):
    """Test filtering sites by name."""
    # if not sample_sites:
    #     pytest.skip("No sample sites available for testing")

    # sample_name = sample_sites[0].name
    sample_name = "Site France 0"

    response = client.get(f"/api/v1/sites/?name={sample_name}")
    assert response.status_code == 200

    json_data = response.json()
    assert "data" in json_data
    data = json_data["data"]
    assert len(data) > 0

    for site in data:
        assert sample_name.lower() in site["name"].lower()


@pytest.mark.asyncio
async def test_get_sites_filter_by_installation_date(client: AsyncClient):
    """Test filtering sites by installation date range."""
    sample_french_sites = client.get("/api/v1/sites/?country=france").json()["data"]
    dates = sorted(
        [site["installation_date"] for site in sample_french_sites if site["installation_date"]]
    )
    if len(dates) < 2:
        pytest.skip("Not enough sites with installation dates for this test")

    date_from = dates[0]
    date_to = dates[-1]

    response = client.get(
        f"/api/v1/sites/?installation_date_from={date_from}&installation_date_to={date_to}"
    )
    assert response.status_code == 200

    json_data = response.json()
    assert "data" in json_data
    data = json_data["data"]

    assert len(data) > 0

    for site in data:
        if site["installation_date"]:
            assert date_from <= site["installation_date"] <= date_to


@pytest.mark.asyncio
async def test_get_sites_sorting(client: AsyncClient):
    """Test sorting sites by name."""
    response = client.get("/api/v1/sites/?sort_by=name&sort_order=asc")
    assert response.status_code == 200

    json_data = response.json()
    assert "data" in json_data
    data = json_data["data"]

    if len(data) < 2:
        pytest.skip("Not enough sites for sorting test")

    names = [site["name"] for site in data]
    assert names == sorted(names)

    response = client.get("/api/v1/sites/?sort_by=name&sort_order=desc")
    assert response.status_code == 200

    json_data = response.json()
    data = json_data["data"]
    names = [site["name"] for site in data]
    assert names == sorted(names, reverse=True)


# ---- read site by ID ----

# @pytest.mark.asyncio
# async def test_read_site_france_success(client: AsyncClient, db: AsyncSession):
#     """Test successfully retrieving a French site by ID."""
#     site_france = client.get(f"/api/v1/sites/?country=france").json()["data"]

#     if not site_france:
#         pytest.skip("No French sites available for testing")

#     response = client.get(f"/api/v1/sites/{site_france.id}")
#     assert response.status_code == 200

#     result = response.json()
#     assert result['id'] == site_france.id
#     assert result['name'] == site_france.name
#     assert result['country'] == "france"
#     assert result['useful_energy_at_1_megawatt'] == site_france.useful_energy_at_1_megawatt
#     assert 'efficiency' in result
#     assert result['efficiency'] is None


# @pytest.mark.asyncio
# async def test_read_site_italy_success(client: AsyncClient, db: AsyncSession):
#     """Test successfully retrieving an Italian site by ID."""
#     # Récupérer un site italien
#     result = await db.execute(select(SiteItaly))
#     site_italy = result.scalar_one_or_none()

#     if not site_italy:
#         pytest.skip("No Italian sites available for testing")

#     response = client.get(f"/api/v1/sites/{site_italy.id}")
#     assert response.status_code == 200

#     result = response.json()
#     assert result['id'] == site_italy.id
#     assert result['name'] == site_italy.name
#     assert result['country'] == "italy"
#     assert result['efficiency'] == site_italy.efficiency
#     assert 'useful_energy_at_1_megawatt' in result
#     assert result['useful_energy_at_1_megawatt'] is None


@pytest.mark.asyncio
async def test_read_site_not_found(client: AsyncClient):
    """Test handling of non-existent site ID."""
    non_existent_id = 9999
    response = client.get(f"/api/v1/sites/{non_existent_id}")

    assert response.status_code == 404


# ---- create site ----


@pytest.mark.asyncio
async def test_create_site_france_success(client: AsyncClient):
    """Test new French site creation success."""
    today = date.today()

    response_check = client.get(
        f"/api/v1/sites/?installation_date_from={today}&installation_date_to={today}"
    )
    json_data = response_check.json()
    data = json_data["data"]

    test_date = today
    while any(
        site["country"] == "france" and site["installation_date"] == test_date.isoformat()
        for site in data
    ):
        test_date += timedelta(days=1)

    site_data = {
        "name": "Site Test France",
        "installation_date": test_date.isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=10, max_value=50, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=1, max_value=10, right_digits=2),
        "useful_energy_at_1_megawatt": fake.pyfloat(min_value=0.7, max_value=0.95, right_digits=2),
    }

    response = client.post("/api/v1/sites/france", json=site_data)
    assert response.status_code == 201

    created_site = response.json()
    assert created_site["name"] == site_data["name"]
    assert created_site["installation_date"] == site_data["installation_date"]
    assert created_site["max_power_megawatt"] == site_data["max_power_megawatt"]
    assert created_site["min_power_megawatt"] == site_data["min_power_megawatt"]
    assert created_site["useful_energy_at_1_megawatt"] == site_data["useful_energy_at_1_megawatt"]
    assert created_site["country"] == "france"
    assert "id" in created_site


@pytest.mark.asyncio
async def test_create_site_italy_success(client: AsyncClient):
    """Test new Italian site creation success."""
    today = date.today()
    weekday = today.weekday()
    days_until_saturday = (5 - weekday) % 7
    weekend_date = today + timedelta(days=days_until_saturday)

    site_data = {
        "name": "Site Test Italy",
        "installation_date": weekend_date.isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=15, max_value=60, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=2, max_value=8, right_digits=2),
        "efficiency": fake.pyfloat(min_value=0.6, max_value=0.9, right_digits=2),
    }

    response = client.post("/api/v1/sites/italy", json=site_data)
    assert response.status_code == 201

    created_site = response.json()
    assert created_site["name"] == site_data["name"]
    assert created_site["installation_date"] == site_data["installation_date"]
    assert created_site["max_power_megawatt"] == site_data["max_power_megawatt"]
    assert created_site["min_power_megawatt"] == site_data["min_power_megawatt"]
    assert created_site["efficiency"] == site_data["efficiency"]
    assert created_site["country"] == "italy"
    assert "id" in created_site


# @pytest.mark.asyncio
# async def test_create_site_france_validation_error(client: AsyncClient, db: AsyncSession):
#     """Test validation of French site creation with duplicate installation date."""
#     result = await db.execute(select(SiteFrance))
#     site_france = result.scalar_one_or_none()

#     if not site_france or not site_france.installation_date:
#         pytest.skip("No French sites with installation date available for testing")

#     site_data = {
#         "name": "Site Test France With Duplicate Date",
#         "installation_date": site_france.installation_date.isoformat(),
#         "max_power_megawatt": 25.5,
#         "min_power_megawatt": 5.5,
#         "useful_energy_at_1_megawatt": 0.85
#     }

#     response = client.post("/api/v1/sites/france", json=site_data)
#     assert response.status_code == 422
#     assert "Only one French site can be installed per day" in response.text


# @pytest.mark.asyncio
# async def test_create_site_italy_validation_error(client: AsyncClient):
#     """Test validation of Italian site creation with non-weekend installation date."""
#     # Trouver une date qui n'est pas un week-end
#     today = date.today()
#     weekday = today.weekday()

#     if weekday >= 5:  # 5=samedi, 6=dimanche
#         # Si on est déjà le week-end, prendre lundi prochain
#         days_until_monday = 8 - weekday  # 8-6=2 jours jusqu'à lundi si on est dimanche
#         test_date = today + timedelta(days=days_until_monday)
#     else:
#         # On est déjà en semaine
#         test_date = today

#     site_data = {
#         "name": "Site Test Italy With Invalid Date",
#         "installation_date": test_date.isoformat(),
#         "max_power_megawatt": 35.5,
#         "min_power_megawatt": 5.5,
#         "efficiency": 0.75
#     }

#     response = client.post("/api/v1/sites/italy", json=site_data)
#     assert response.status_code == 422
#     assert "Italian sites must be installed on weekends" in response.text


# # ---- update site ----

# @pytest.mark.asyncio
# async def test_update_site_france(client: AsyncClient, db: AsyncSession):
#     """Test updating a French site."""
#     # Récupérer un site français
#     result = await db.execute(select(SiteFrance))
#     site_france = result.scalar_one_or_none()

#     if not site_france:
#         pytest.skip("No French sites available for testing")

#     update_data = {
#         "name": "Updated French Site Name",
#         "useful_energy_at_1_megawatt": 0.88
#     }

#     response = client.patch(f"/api/v1/sites/{site_france.id}", json=update_data)
#     assert response.status_code == 200

#     result = response.json()
#     assert result["id"] == site_france.id
#     assert result["name"] == "Updated French Site Name"
#     assert result["useful_energy_at_1_megawatt"] == 0.88
#     assert result["country"] == "france"


# @pytest.mark.asyncio
# async def test_update_site_italy(client: AsyncClient, db: AsyncSession):
#     """Test updating an Italian site."""
#     # Récupérer un site italien
#     result = await db.execute(select(SiteItaly))
#     site_italy = result.scalar_one_or_none()

#     if not site_italy:
#         pytest.skip("No Italian sites available for testing")

#     update_data = {
#         "name": "Updated Italian Site Name",
#         "efficiency": 0.82
#     }

#     response = client.patch(f"/api/v1/sites/{site_italy.id}", json=update_data)
#     assert response.status_code == 200

#     result = response.json()
#     assert result["id"] == site_italy.id
#     assert result["name"] == "Updated Italian Site Name"
#     assert result["efficiency"] == 0.82
#     assert result["country"] == "italy"


# @pytest.mark.asyncio
# async def test_update_site_date_validation(client: AsyncClient, db: AsyncSession):
#     """Test validation rules when updating site dates."""
#     # Cas 1: Site français avec date déjà utilisée
#     result_france = await db.execute(select(SiteFrance).limit(2))
#     sites_france = result_france.scalars().all()

#     if len(sites_france) < 2:
#         pytest.skip("Not enough French sites for this test")

#     # Essayer de mettre à jour avec la date d'un autre site
#     update_data = {
#         "installation_date": sites_france[1].installation_date.isoformat()
#     }

#     response = client.patch(f"/api/v1/sites/{sites_france[0].id}", json=update_data)
#     assert response.status_code == 422
#     assert "Only one French site can be installed per day" in response.text

#     # Cas 2: Site italien avec date en semaine
#     result_italy = await db.execute(select(SiteItaly))
#     site_italy = result_italy.scalar_one_or_none()

#     if not site_italy:
#         pytest.skip("No Italian sites available for testing")

#     # Trouver une date qui n'est pas un week-end
#     today = date.today()
#     weekday = today.weekday()

#     if weekday >= 5:  # 5=samedi, 6=dimanche
#         # Si on est déjà le week-end, prendre lundi prochain
#         days_until_monday = 8 - weekday
#         test_date = today + timedelta(days=days_until_monday)
#     else:
#         # On est déjà en semaine
#         test_date = today

#     update_data = {
#         "installation_date": test_date.isoformat()
#     }

#     response = client.patch(f"/api/v1/sites/{site_italy.id}", json=update_data)
#     assert response.status_code == 422
#     assert "Italian sites must be installed on weekends" in response.text


# ---- delete site ----


@pytest.mark.asyncio
async def test_delete_site_france(client: AsyncClient):
    """Test deleting a French site with a temporary site created for the test."""
    today = date.today()
    test_date = today + timedelta(days=30)

    site_data = {
        "name": "Temporary French Site For Deletion",
        "installation_date": test_date.isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=15, max_value=40, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=3, max_value=10, right_digits=2),
        "useful_energy_at_1_megawatt": fake.pyfloat(min_value=0.7, max_value=0.9, right_digits=2),
    }

    creation_response = client.post("/api/v1/sites/france", json=site_data)
    assert creation_response.status_code == 201

    created_site = creation_response.json()
    site_id = created_site["id"]

    delete_response = client.delete(f"/api/v1/sites/{site_id}")
    assert delete_response.status_code == 200

    get_response = client.get(f"/api/v1/sites/{site_id}")
    assert get_response.status_code == 404


# @pytest.mark.asyncio
# async def test_delete_site_italy(client: AsyncClient):
#     """Test deleting an Italian site with a temporary site created for the test."""
#     today = date.today()
#     weekday = today.weekday()
#     days_until_saturday = (5 - weekday) % 7 + 30
#     weekend_date = today + timedelta(days=days_until_saturday)

#     site_data = {
#         "name": "Temporary Italian Site For Deletion",
#         "installation_date": weekend_date.isoformat(),
#         "max_power_megawatt": fake.pyfloat(min_value=15, max_value=60, right_digits=2),
#         "min_power_megawatt": fake.pyfloat(min_value=2, max_value=8, right_digits=2),
#         "efficiency": fake.pyfloat(min_value=0.6, max_value=0.9, right_digits=2)
#     }

#     creation_response = client.post("/api/v1/sites/italy", json=site_data)
#     assert creation_response.status_code == 201

#     created_site = creation_response.json()
#     site_id = created_site["id"]

#     delete_response = client.delete(f"/api/v1/sites/{site_id}")
#     assert delete_response.status_code == 200

#     get_response = client.get(f"/api/v1/sites/{site_id}")
#     assert get_response.status_code == 404


# ---- add site to group ----

# @pytest.mark.asyncio
# async def test_add_site_to_group_success(client: AsyncClient, db: AsyncSession, sample_sites: list[Site], sample_groups: list[Group]):
#     """Test adding a site to a group successfully."""
#     site = sample_sites[0]
#     group = sample_groups[0]

#     query = select(Site).options(joinedload(Site.groups)).where(Site.id == site.id)
#     result = await db.execute(query)
#     site_with_groups = result.unique().scalar_one()
    
#     if group in site_with_groups.groups:
#         site_with_groups.groups.remove(group)
#         await db.commit()
    
#     response = client.post(f"/api/v1/sites/{site.id}/groups/{group.id}")
#     await db.refresh(site_with_groups)
#     assert response.status_code == 204

#     result = await db.execute(
#         select(Site).options(selectinload(Site.groups)).where(Site.id == site.id)
#     )
#     updated_site = result.unique().scalar_one_or_none()
    
#     assert any(g.id == group.id for g in updated_site.groups)
