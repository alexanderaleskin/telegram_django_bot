ARG PYTHON_VERSION=3.9.9-slim-buster

FROM python:${PYTHON_VERSION} as python-stage

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg2 dependencies
  libpq-dev      \
  # git+https
  git \
  python3-dev \
  graphviz \
  libgraphviz-dev \
  pkg-config \
  unixodbc-dev

COPY ./requirements.txt .

RUN pip install --upgrade pip==21.3.1

# Create Python Dependency and Sub-Dependency Wheels.
RUN --mount=type=cache,target=/root/.cache \
  pip wheel --wheel-dir /usr/src/app/wheels  \
  -r requirements.txt


FROM python:${PYTHON_VERSION} as python-run-stage
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /webapp

# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg2 dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  libgeos-dev \
  npm \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY --from=python-stage /usr/src/app/wheels  /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/

RUN npm i -g nodemon

COPY ./docker-entrypoint.sh /docker-entrypoint.sh
RUN sed -i 's/\r$//g' /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh


COPY website_with_polling_bot/configs/commands/ /commands
RUN sed -i 's/\r$//g' /commands/*
RUN chmod +x -R /commands

COPY website_with_polling_bot/configs/confs /configs

#COPY ./configs/uwsgi_fuck /web/uwsgi/

#ENV UWSGI_WORKERS 4
#ENV UWSGI_THREADS 1

# copy application code to WORKDIR
COPY . /webapp

ENTRYPOINT ["/docker-entrypoint.sh"]
