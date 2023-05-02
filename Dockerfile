FROM python:3.11-alpine as base
# move to edge, removes a lot of vulnerabilities
RUN sed -i -e 's/v[^/]*/edge/g' /etc/apk/repositories && \
    apk update && \
    apk upgrade && \
    apk add libgcc openblas libstdc++
# libgcc openblas libstdc++ are needed for jellifish and scipy
WORKDIR /app

# builder stage
FROM base as builder

# install dependencies
RUN pip install pdm
# gcc may be needed for some dependencies
# RUN apt-get update && apt-get install -y gcc
# RUN apk --no-cache add musl-dev linux-headers g++ cargo
# dependencies for building wheel of scipy and jellyfish (extra: cargo)
RUN apk --no-cache --update-cache add gcc gfortran python3 python3-dev py-pip build-base wget freetype-dev libpng-dev openblas-dev cargo
RUN ln -s /usr/include/locale.h /usr/include/xlocale.h

# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock README.md /app/
# create .venv and install anaconda dependencies (otherwise it takes ages to build wheels)
RUN virtualenv .venv && . .venv/bin/activate && pip install --pre -i https://pypi.anaconda.org/scipy-wheels-nightly/simple scipy numpy
# this task takes ~50 minutes because of building wheels of numpy, scipy and jellyfish
RUN pdm install --prod --no-lock --no-editable

# run stage
# FROM python:3.11-slim as production
FROM base as production
# FROM python:3.11-alpine as production

# pip and setuptools have open vulnerabilities
RUN pip uninstall setuptools pip -y
COPY --from=builder /app /app
COPY claimreview_collector /app/claimreview_collector
# CMD ["uvicorn", "claimreview_collector.main:app", "--host", "0.0.0.0"]
# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && uvicorn claimreview_collector.main:app --host 0.0.0.0