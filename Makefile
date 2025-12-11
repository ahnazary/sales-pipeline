IMAGE_NAME := coding-challenge-amir
CONTAINER_NAME := distance-calculator
DOCKER_TAG := latest

# Default target
.DEFAULT_GOAL := help

# Help target to display available commands
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  build    - Build the container image"
	@echo "  docker-compose - Run the application with using docker-compose"
	@echo "  test     - Run tests locally"
	@echo "  run-docker      - Launch the batch job locally using the built docker image"
	@echo "  run      - Launch the batch job locally without docker"
	@echo "  clean    - Clean up containers and images"

# Build the container image
.PHONY: build
build:
	@echo "Building container image: $(IMAGE_NAME):$(DOCKER_TAG)"
	docker build -t $(IMAGE_NAME):$(DOCKER_TAG) .
	@echo "Build completed successfully"

# Run the application with using docker-compose
.PHONY: docker-compose
docker-compose:
	@echo "Starting application using docker-compose ..."
	docker-compose down --volumes --remove-orphans
	docker-compose up -d
	@echo "Waiting for Airflow to be ready..."
	@echo "This may take a few minutes on first startup..."
	@while ! docker exec airflow-standalone airflow version >/dev/null 2>&1; do \
		echo "Waiting for Airflow to start..."; \
		sleep 5; \
	done
	@echo "Airflow is ready!"
	@echo "Creating airflow user for local access..."
	docker exec -it airflow-standalone airflow users create \
		--username airflow \
		--password airflow \
		--firstname Airflow \
		--lastname Admin \
		--role Admin \
		--email airflow@example.com
	@echo "Starting the Airflow webserver..."
	sleep 15
	@echo "Application started. Access Airflow UI at http://localhost:8080"
	@echo "Login with username: airflow, password: airflow"

# Run tests locally
.PHONY: test
test:
	@echo "Running tests locally ..."
	pip install -r requirements_tests.txt
	pytest --cov=dags/src dags/tests -k "not test_clickhouse_interface.py"
	@echo "Tests completed"

# Launch the batch job locally using the built docker image
.PHONY: run-docker
run-docker:
	@echo "Checking if Docker image $(IMAGE_NAME):$(DOCKER_TAG) exists..."
	@if ! docker image inspect $(IMAGE_NAME):$(DOCKER_TAG) >/dev/null 2>&1; then \
		echo "Image not found. Building image first..."; \
		$(MAKE) build; \
	else \
		echo "Image found. Proceeding with container run..."; \
	fi
	@echo "Running the batch job in container: $(CONTAINER_NAME)-test"
	docker run --name $(CONTAINER_NAME)-test --rm \
		-v $(PWD)/dags:/opt/airflow/dags \
		-v $(PWD)/input:/opt/airflow/input \
		-v $(PWD)/output:/opt/airflow/output \
		-e PYTHONPATH=/opt/airflow/dags \
		$(IMAGE_NAME):$(DOCKER_TAG) python dags/src/calc_distance_pandas.py
	@echo "Batch job completed"

# Launch the batch job locally without docker
.PHONY: run-local
run:
	@echo "Running the batch job locally without docker ..."
	pip install -r requirements.txt
	PYTHONPATH=$$PWD/dags python dags/src/calc_distance_pandas.py
	@echo "Batch job completed"

# Clean up containers and images
.PHONY: clean
clean:
	@echo "Cleaning up containers and images..."
	-docker stop $(CONTAINER_NAME) $(CONTAINER_NAME)-test 2>/dev/null
	-docker rm $(CONTAINER_NAME) $(CONTAINER_NAME)-test 2>/dev/null
	-docker rmi $(IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null
	-docker-compose down --volumes --remove-orphans
	@echo "Cleanup completed"


# Check if required files exist
.PHONY: check
check:
	@echo "Checking required files..."
	@test -f Dockerfile || (echo "ERROR: Dockerfile not found" && exit 1)
	@test -f requirements.txt || (echo "ERROR: requirements.txt not found" && exit 1)
	@test -d input || (echo "ERROR: input directory not found" && exit 1)
	@test -d dags/src || (echo "ERROR: dags/src directory not found" && exit 1)
	@test -d dags/tests || (echo "ERROR: dags/tests directory not found" && exit 1)
	@echo "All required files and directories found"