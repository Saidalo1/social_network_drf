# django management commands shortcuts

# Run database migrations
mig:
	@echo "Running database migrations..."
	python manage.py makemigrations
	python manage.py migrate

# Create superuser for the admin panel
adm:
	@echo "Creating superuser..."
	python manage.py createsuperuser

# Run development server
run:
	python manage.py runserver

# Run test suite
test:
	python -m pytest -v

# Format and check code styling (Ruff)
fmt:
	ruff format .
	ruff check . --fix
