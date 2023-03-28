FROM python:3.11 as builder

RUN pip install pdm
# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock /app/

# ADD .env /app/.env
WORKDIR /app

# install dependencies
# gcc may be needed for some dependencies
RUN apt-get update && apt-get install -y gcc 
# RUN pip install .
# install pdm in .venv by default
RUN pdm install --prod --no-lock --no-editable

# run stage
FROM python:3.11-slim as production
WORKDIR /app
COPY --from=builder /app /app
COPY claimreview_scraper /app/claimreview_scraper
# CMD ["uvicorn", "claimreview_scraper.main:app", "--host", "0.0.0.0"]
# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && uvicorn claimreview_scraper.main:app --host 0.0.0.0