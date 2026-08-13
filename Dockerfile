# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.9-slim-bookworm

# The GitHub token must be provided at run time (e.g. `docker run --env github_token=...`).
# Never pass it as a build arg or bake it into the image: build args and ENV defaults
# persist in the image history and leak the credential.

ARG config_file="config.yaml"
ARG org_names=[]

# Install Git Client
RUN apt-get -y update && apt-get -y install --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD python3 run.py --config ${config_file} --org ${org_names}
