FROM apache/airflow:latest-python3.11

USER root

RUN apt-get update && \
    apt-get -y install git && \
    apt-get clean

# Switch to airflow user BEFORE installing poetry
USER airflow

# Install Poetry as airflow user
RUN pip install --no-cache-dir poetry

# Set working directory
WORKDIR /opt/airflow

# Copy project files
COPY pyproject.toml ./

# Install dependencies using Poetry
RUN poetry install --no-root

# Ensure the dags directory exists
RUN mkdir -p /opt/airflow/dags

# Copy DAGs
COPY airflow/dags/ /opt/airflow/dags/
