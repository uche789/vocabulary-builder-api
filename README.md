# Vocabulary builder api 

A simple Web API to generate vocabulary locally

## Prerequisites
- Python
- Fastapi
- SQLAlchemy
- psycopg2 (Postgres)

## Installations

Commands: 
```bash
# Instal requirements
pip install -r requirements.txt

#Install fastapi
pip install "fastapi[standard]"

# Save requirements
pip freeze > requirements.txt

## build docker container
docker-compose up --build

## remove docker container and volumes
docker-compose down -v

## remove docker container
docker-compose down

# docker production
docker-compose -f docker-compose.yml up --build
```


## Run application locally
Command: `fastapi dev main.py`

Application should be running is running at http://127.0.0.1:8000/ and the OpenAPI docs is accessible at http://127.0.0.1:8000/docs.

## Migrations

Migrations is done using albemic

https://alembic.sqlalchemy.org/en/latest/autogenerate.html

## References
- https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg2
- https://stackoverflow.com/questions/59811370/how-to-use-psycopg2-binary-in-python
- https://www.psycopg.org/docs/install.html#install-from-source
- https://fastapi.tiangolo.com/tutorial/security/
