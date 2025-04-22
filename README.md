# python-technical-test

In this project, we manage data related to `sites` and `groups`. Sites represent individual installations, each with its own unique characteristics and attributes. On the other hand, groups serve as organizational units, grouping together sites based on common characteristics or functionalities.

By effectively managing both sites and groups within our system, we can efficiently organize and analyze data, enabling better decision-making and optimization of operations.

**Candidates are encouraged to feel free to use libraries of their choice and are welcome to include any additional enhancements they deem necessary or beneficial, such as unit tests, documentation, or performance optimizations. All additions that improve the overall quality and maintainability of the codebase are highly appreciated.**

## Project Description

### 1. Create the necessary models

**At least** two models are required:

#### Sites
- `id` (integer)
- `name` (string)
- `installation_date` (date)
- `max_power_megawatt` (float)
- `min_power_megawatt` (float)
- `useful_energy_at_1_megawatt` (float)

#### Groups
- `id` (integer)
- `name` (string)
- `type` (enum [group1, group2, group3])


A site can belong to multiple groups.  
A group can contain multiple sites.  
A group can contain multiple groups.

### 2. Create the necessary CRUD routes

We require the follwing routes:
- GET / POST / PATCH / DELETE `/sites`
- GET / POST / PATCH / DELETE `/groups`

Candidates are encouraged to implement filtering and sorting options in these routes to enhance the usability and flexibility of the API.

### 3. Additional Requirements

Currently, we only have french sites, but we want to add italian sites. These italian sites do not use the field `useful_energy_at_1_megawatt`. Instead, they have a field `efficiency` (float) specific to Italy.

Integrate these new Italian sites. (Many new countries with specific fields might be added in the future).

### 4. Integrate Business Logics
- Only one French site can be installed per day.
- Italian sites must be installed on weekends.
- No site can be associated with `group.type == "group3"`.

## Development

### Prerequisites
- `docker` for installation
- `poetry` (https://python-poetry.org/) can be useful to manage dependencies (but not mandatory) 


### Run the project

Create the `.env` file in the root folder then run:
```
docker compose up
```

The project should be available at `http://localhost:8000/docs`.

You can find some other useful commands in the Makefile.


## Additional

### CRUD
FastCRUD library is used to handle CRUD operations:

```
FastCRUD is a Python package for FastAPI, offering robust async CRUD operations and flexible endpoint creation utilities, streamlined through advanced features like auto-detected join conditions, dynamic sorting, and offset and cursor pagination.
```

`https://igorbenav.github.io/fastcrud/` & `https://github.com/igorbenav/FastAPI-boilerplate/tree/main`

### PGAdmin

A PGAdmin service had been set in `docker-compose.yml`.

PGAdmin is an administration and development platform for PostgreSQL.

Credentials should be added in the `.env` file, according to `.env.example`.

Then, PGAdmin panel is accessible at `http://localhost:5050/browser/`.

### Unit tests

Units tests are performed using `pytest` and `faker`. To run tests in Docker container:

```
docker exec -it technical-test-api python -m pytest tests
```

### Architecture

```
python-technical-test/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── groups.py       # Routes for groups
│   │       └── sites.py        # Routes for sites (France/Italy)
│   ├── infrastructure/
│   │   ├── crud/
│   │   │   ├── __init__.py
│   │   │   ├── crud_groups.py  # CRUD for groups
│   │   │   └── crud_sites.py   # CRUD for sites (polymorphic)
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   └── session.py      # Database session configuration
│   │   ├── migrations/
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── associations.py # Association tables
│   │   │   ├── group.py        # Group model
│   │   │   └── site.py         # Site models (base, France, Italy)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── group.py        # Pydantic schemas for groups
│   │   │   └── site.py         # Pydantic schemas for sites (base, France, Italy)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── site_service.py # Business logic for site operations
│   │   └── validators.py       # Business rules validation
│   ├── scripts/
│   │   └── init_db.py          # Seed database
│   ├── tests/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── test_groups.py
│   │   │       └── test_sites.py
│   │   └── conftest.py         # Tests configuration
│   ├── config.py               # App configuration
│   └── main.py                 # App entry point
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Dockerfile configuration
├── requirements.txt            # Project dependencies
├── .env.example                # Environment variable example
├── alembic.ini                 # Alembic configuration (migrations)
├── Makefile                    # Command utilities
├── .gitignore                  # git ignore file
├── pytest.ini                  # pytest configuration
├── pyproject.toml              # Project configuration
└── README.md                   # Project documentation
```
