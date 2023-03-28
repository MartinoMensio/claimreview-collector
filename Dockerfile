FROM python:3.11-slim

RUN pip install pdm
ADD claimreview_scraper /app/claimreview_scraper
# ADD requirements.txt /app/requirements.txt
COPY pyproject.toml pdm.lock README.md /app/

# ADD .env /app/.env
WORKDIR /app

# install dependencies
# gcc needed sometimes for some dependencies
RUN apt-get update && apt-get install -y gcc 
# RUN pip install .
RUN pdm install --prod --no-lock --no-editable

# CMD ["uvicorn", "claimreview_scraper.main:app", "--host", "0.0.0.0"]
# set environment as part of CMD because pdm installs there
CMD . .venv/bin/activate && uvicorn claimreview_scraper.main:app --host 0.0.0.0