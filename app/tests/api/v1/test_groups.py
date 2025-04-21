import pytest
from faker import Faker
from httpx import AsyncClient

from infrastructure.models.group import Group, GroupType

fake = Faker()

# ---- read groups ----
@pytest.mark.asyncio
async def test_get_all_groups(client: AsyncClient, sample_groups: list[Group]):
    """Test getting all groups without filters."""
    response = client.get("/api/v1/groups/")
    assert response.status_code == 200
    
    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    
    group_ids = {group.id for group in sample_groups}
    response_ids = {group["id"] for group in data}
    
    assert group_ids.issubset(response_ids)


@pytest.mark.asyncio
async def test_get_groups_pagination(client: AsyncClient):
    """Test pagination for groups."""
    page = 1
    items_per_page = 3
    
    response = client.get(f"/api/v1/groups/?page={page}&items_per_page={items_per_page}")
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
        response2 = client.get(f"/api/v1/groups/?page={page_2}&items_per_page={items_per_page}")
        assert response2.status_code == 200
        
        json_data2 = response2.json()

        first_page_ids = {group["id"] for group in json_data['data']}
        second_page_ids = {group["id"] for group in json_data2['data']}
        assert not first_page_ids.intersection(second_page_ids)


@pytest.mark.asyncio
async def test_get_groups_filter_by_name(client: AsyncClient, sample_groups: list[Group]):
    """Test filtering groups by name."""
    if not sample_groups:
        pytest.skip("No sample groups available for testing")
    
    sample_name = sample_groups[0].name
    
    response = client.get(f"/api/v1/groups/?name={sample_name}")
    assert response.status_code == 200

    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']
    assert len(data) > 0

    for group in data:
        assert sample_name.lower() in group["name"].lower()


@pytest.mark.asyncio
async def test_get_groups_sorting(client: AsyncClient, sample_groups: list[Group]):
    """Test sorting groups by name."""
    response = client.get("/api/v1/groups/?sort_by=name&sort_order=asc")
    assert response.status_code == 200

    json_data = response.json()
    assert 'data' in json_data
    data = json_data['data']

    if len(data) < 2:
        pytest.skip("Not enough groups for sorting test")

    names = [group["name"] for group in data]
    assert names == sorted(names)
    
    response = client.get("/api/v1/groups/?sort_by=name&sort_order=desc")
    assert response.status_code == 200

    json_data = response.json()
    data = json_data['data']
    names = [group["name"] for group in data]
    assert names == sorted(names, reverse=True)


# ---- read group by ID ----

@pytest.mark.asyncio
async def test_read_group_success(client: AsyncClient, sample_groups: list[Group]):
    """Test successfully retrieving a group by ID."""
    sample_group = sample_groups[0]

    response = client.get(f"/api/v1/groups/{sample_group.id}")

    assert response.status_code == 200
    result = response.json()
    assert result['id'] == sample_group.id
    assert result['name'] == sample_group.name
    assert result['type'] == sample_group.type.value


@pytest.mark.asyncio
async def test_read_group_not_found(client: AsyncClient):
    """Test handling of non-existent group ID."""
    non_existent_id = 9999
    response = client.get(f"/api/v1/groups/{non_existent_id}")
    
    assert response.status_code == 404

# ---- create group ----

@pytest.mark.asyncio
async def test_create_group_success(client: AsyncClient):
    """Test new group creation success."""
    group_data = {
        "name": "Group Test",
        "type": fake.random_element(elements=(GroupType.GROUP1.value, GroupType.GROUP2.value, GroupType.GROUP3.value))
    }

    response = client.post("/api/v1/groups/", json=group_data)

    assert response.status_code == 201
    
    created_group = response.json()
    assert created_group["name"] == group_data["name"]
    assert created_group["type"] == group_data["type"]
    assert "id" in created_group


@pytest.mark.asyncio
async def test_create_group_invalid_data(client: AsyncClient):
    """Test new group creation failing."""
    # test with missing "name" field data
    invalid_data = {
        "type": fake.random_element(elements=(GroupType.GROUP1.value, GroupType.GROUP2.value, GroupType.GROUP3.value))
    }

    response = client.post("/api/v1/groups/", json=invalid_data)

    assert response.status_code == 422
    error_data = response.json()
    assert "detail" in error_data
    assert any("name" in error["loc"] for error in error_data["detail"])


# # ---- update group ---- TODO

# @pytest.mark.asyncio
# async def test_update_group(client: AsyncClient, sample_groups: list[Group]):
#     """Test updating a group."""
#     sample_group = sample_groups[0]

#     update_data = {
#         "name": "Updated Group Name"
#     }
    
#     response = client.patch(f"/api/v1/groups/{sample_group.id}", json=update_data)
    
#     assert response.status_code == 200
#     result = response.json()
#     assert result["id"] == sample_group.id
#     assert result["name"] == "Updated Group Name"
#     assert result["type"] == sample_group.type


# ---- delete group ----

@pytest.mark.asyncio
async def test_delete_group(client: AsyncClient):
    """Test deleting a group with a temporary group created for the test."""
    group_data = {
        "name": "Temporary Group For Deletion",
        "type": GroupType.GROUP1.value
    }

    creation_response = client.post("/api/v1/groups/", json=group_data)
    
    assert creation_response.status_code == 201
    
    created_group = creation_response.json()
    group_id = created_group["id"]
    
    group = client.get(f"/api/v1/groups/{group_id}")
    assert group is not None
    assert group.json()["name"] == group_data["name"]

    delete_response = client.delete(f"/api/v1/groups/{group_id}")
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert "message" in data

    get_response = client.get(f"/api/v1/groups/{group_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_group_not_found(client: AsyncClient):
    """Test deleting a non-existent group."""
    non_existent_id = 99999

    response = client.delete(f"/api/v1/groups/{non_existent_id}")
    
    assert response.status_code == 404
