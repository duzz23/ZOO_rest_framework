runserver:
	python manage.py runserver

newapp:
	python manage.py startapp mainapp

makemigrations:
	python manage.py makemigrations

migrate:
	python manage.py migrate

createsuperuser:
	python manage.py createsuperuser

fill_db:
	python manage.py fill_db

test:
	python manage.py test

coverage:
	coverage run --source='.' manage.py test
	coverage report --omit=settings/asgi.py,setting/wsgi.py,manage.py,mainapp/management/* --fail-under=84
	coverage html --omit=settings/asgi.py,setting/wsgi.py,manage.py,mainapp/management/*

# Docker commands
docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-rebuild:
	docker compose down
	docker compose build --no-cache
	docker compose up -d

docker-shell:
	docker compose exec web bash

docker-migrate:
	docker compose exec web python manage.py migrate

docker-makemigrations:
	docker compose exec web python manage.py makemigrations

docker-createsuperuser:
	docker compose exec web python manage.py createsuperuser

docker-pull-ollama-model:
	docker run --rm ollama/ollama pull gemma3:4b
