from datetime import date
import pytest
from faker import Faker
from httpx import AsyncClient

from infrastructure.models.site import Site

fake = Faker()

# ---- read sites ----
@pytest.mark.asyncio
async def test_get_all_sites(client: AsyncClient, sample_sites: list[Site]):
    """Test getting all sites without filters."""
    response = client.get("/api/v1/sites/")
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    
    site_ids = {site.id for site in sample_sites}
    response_ids = {site["id"] for site in data}
    
    assert site_ids.issubset(response_ids)


@pytest.mark.asyncio
async def test_get_sites_pagination(client: AsyncClient, sample_sites: list[Site]):
    """Test pagination for sites."""
    page = 1
    items_per_page = 3
    
    response = client.get(f"/api/v1/sites/?page={page}&items_per_page={items_per_page}")
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'data' in json_data
    assert 'page' in json_data
    assert 'items_per_page' in json_data
    assert 'total_count' in json_data
    assert 'has_more' in json_data

    assert len(json_data['data']) <= items_per_page
    
    if json_data['has_more']:
        page_2 = 2
        response2 = client.get(f"/api/v1/sites/?page={page_2}&items_per_page={items_per_page}")
        assert response2.status_code == 200
        
        json_data2 = response2.json()

        first_page_ids = {site["id"] for site in json_data['data']}
        second_page_ids = {site["id"] for site in json_data2['data']}
        assert not first_page_ids.intersection(second_page_ids)


@pytest.mark.asyncio
async def test_get_sites_filter_by_name(client: AsyncClient, sample_sites: list[Site]):
    """Test filtering sites by name."""
    if not sample_sites:
        pytest.skip("No sample sites available for testing")
    
    sample_name = sample_sites[0].name
    
    response = client.get(f"/api/v1/sites/?name={sample_name}")
    assert response.status_code == 200

    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    assert len(data) > 0

    for site in data:
        assert sample_name.lower() in site["name"].lower()


@pytest.mark.asyncio
async def test_get_sites_filter_by_installation_date(client: AsyncClient, sample_sites: list[Site]):
    """Test filtering sites by installation date range."""
    dates = sorted([site.installation_date for site in sample_sites if site.installation_date])
    if len(dates) < 2:
        pytest.skip("Not enough sites with installation dates for this test")

    date_from = dates[0].isoformat()
    date_to = dates[-1].isoformat()
    
    response = client.get(
        f"/api/v1/sites/?installation_date_from={date_from}&installation_date_to={date_to}"
    )
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    
    assert len(data) > 0
    
    for site in data:
        if site["installation_date"]:
            assert date_from <= site["installation_date"] <= date_to


@pytest.mark.asyncio
async def test_get_sites_sorting(client: AsyncClient, sample_sites: list[Site]):
    """Test sorting sites by name."""
    response = client.get("/api/v1/sites/?sort_by=name&sort_order=asc")
    assert response.status_code == 200

    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']

    if len(data) < 2:
        pytest.skip("Not enough sites for sorting test")

    names = [site["name"] for site in data]
    assert names == sorted(names)
    
    response = client.get("/api/v1/sites/?sort_by=name&sort_order=desc")
    assert response.status_code == 200

    json_data = response.json()
    data = json_data['data']
    names = [site["name"] for site in data]
    assert names == sorted(names, reverse=True)


@pytest.mark.asyncio
async def test_get_sites_combined_filters_and_sorting(client: AsyncClient, sample_sites: list[Site]):
    """Test combining multiple filters with sorting."""
    response = client.get(
        "/api/v1/sites/?sort_by=name&sort_order=desc&installation_date_from=2020-01-01"
    )
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    
    if not data:
        pytest.skip("No sites match the combined filter criteria")

    names = [site["name"] for site in data]
    assert names == sorted(names, reverse=True)
    
    for site in data:
        if site["installation_date"]:
            assert site["installation_date"] >= "2020-01-01"


# ---- read site by ID ----

@pytest.mark.asyncio
async def test_read_site_success(client: AsyncClient, sample_sites: list[Site]):
    """Test successfully retrieving a site by ID."""
    sample_site = sample_sites[0]

    response = client.get(f"/api/v1/sites/{sample_site.id}")

    assert response.status_code == 200
    result = response.json()
    assert result['id'] == sample_site.id
    assert result['name'] == sample_site.name
    assert result['installation_date'] == str(sample_site.installation_date)
    assert result['max_power_megawatt'] == sample_site.max_power_megawatt
    assert result['min_power_megawatt'] == sample_site.min_power_megawatt
    assert result['useful_energy_at_1_megawatt'] == sample_site.useful_energy_at_1_megawatt


@pytest.mark.asyncio
async def test_read_site_not_found(client: AsyncClient):
    """Test handling of non-existent site ID."""
    non_existent_id = 9999
    response = client.get(f"/api/v1/sites/{non_existent_id}")
    
    assert response.status_code == 404


# ---- create site ----

@pytest.mark.asyncio
async def test_create_site_success(client: AsyncClient):
    """Test new site creation success."""
    site_data = {
        "name": "Site Test",
        "installation_date": date.today().isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=10, max_value=50, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=1, max_value=10, right_digits=2),
        "useful_energy_at_1_megawatt": fake.pyfloat(min_value=10, max_value=50, right_digits=2),
        "groups": []  # TODO test with groups
    }

    response = client.post("/api/v1/sites/", json=site_data)

    assert response.status_code == 201
    
    created_site = response.json()
    assert created_site["name"] == site_data["name"]
    assert created_site["installation_date"] == site_data["installation_date"]
    assert created_site["max_power_megawatt"] == site_data["max_power_megawatt"]
    assert created_site["min_power_megawatt"] == site_data["min_power_megawatt"]
    assert created_site["useful_energy_at_1_megawatt"] == site_data["useful_energy_at_1_megawatt"]
    assert "id" in created_site


@pytest.mark.asyncio
async def test_create_site_invalid_data(client: AsyncClient):
    """Test new site creation failing."""
    # test with missing "name" field data
    invalid_data = {
        "installation_date": date.today().isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=10, max_value=50, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=10, max_value=50, right_digits=2)
    }

    response = client.post("/api/v1/sites/", json=invalid_data)

    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data
    assert any("name" in error["loc"] for error in error_data["detail"])


# ---- update site ----

@pytest.mark.asyncio
async def test_update_site(client: AsyncClient, sample_sites: list[Site]):
    """Test updating a site."""
    sample_site = sample_sites[0]

    update_data = {
        "name": "Updated Site Name"
    }
    
    response = client.patch(f"/api/v1/sites/{sample_site.id}", json=update_data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == sample_site.id
    assert result["name"] == "Updated Site Name"
    assert result["installation_date"] == str(sample_site.installation_date) if sample_site.installation_date else None


# ---- delete site ----

@pytest.mark.asyncio
async def test_delete_site(client: AsyncClient):
    """Test deleting a site with a temporary site created for the test."""
    site_data = {
        "name": "Temporary Site For Deletion",
        "installation_date": date.today().isoformat(),
        "max_power_megawatt": fake.pyfloat(min_value=15, max_value=40, right_digits=2),
        "min_power_megawatt": fake.pyfloat(min_value=3, max_value=10, right_digits=2),
        "useful_energy_at_1_megawatt": fake.pyfloat(min_value=0.7, max_value=0.9, right_digits=2),
        "groups": []
    }

    creation_response = client.post("/api/v1/sites/", json=site_data)
    
    assert creation_response.status_code == 201
    
    created_site = creation_response.json()
    site_id = created_site["id"]
    
    site = client.get(f"/api/v1/sites/{site_id}")
    assert site is not None
    assert site.json()["name"] == site_data["name"]

    delete_response = client.delete(f"/api/v1/sites/{site_id}")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert "message" in data

    get_response = client.get(f"/api/v1/sites/{site_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_site_not_found(client: AsyncClient):
    """Test deleting a non-existent site."""
    non_existent_id = 99999

    response = client.delete(f"/api/v1/sites/{non_existent_id}")
    
    assert response.status_code == 404
