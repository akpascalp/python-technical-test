import pytest
from faker import Faker
from httpx import AsyncClient

from infrastructure.models.site import Site

fake = Faker()


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
