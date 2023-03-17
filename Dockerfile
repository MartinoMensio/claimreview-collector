FROM python:3.11-slim

ADD claimreview_scraper /app/claimreview_scraper
ADD requirements.txt /app/requirements.txt
ADD .env /app/.env
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["uvicorn", "claimreview_scraper.main:app", "--host", "0.0.0.0"]