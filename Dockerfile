FROM python:3.11 as builder

WORKDIR /app
# install dependencies
RUN pip install pdm
# gcc may be needed for some dependencies
RUN apt-get update && apt-get install -y gcc
# RUN apk --no-cache add musl-dev linux-headers g++ cargo

# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock README.md /app/
# RUN pip install .
# install pdm in .venv by default
RUN pdm install --prod --no-lock --no-editable

# run stage (cannot use alpine because scipy and jellyfish fail compilation)
FROM python:3.11-slim as production
# FROM python:3.11-alpine as production
# pip and setuptools have open vulnerabilities
RUN pip uninstall setuptools pip -y
WORKDIR /app
COPY --from=builder /app /app
COPY claimreview_scraper /app/claimreview_scraper
# CMD ["uvicorn", "claimreview_scraper.main:app", "--host", "0.0.0.0"]
# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && uvicorn claimreview_scraper.main:app --host 0.0.0.0