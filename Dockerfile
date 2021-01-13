FROM python:latest

ADD claimreview_scraper /app/claimreview_scraper
ADD setup.py /app/setup.py
ADD .env /app/.env
WORKDIR /app
RUN pip install -e .

CMD ["uvicorn", "claimreview_scraper.main:app", "--host", "0.0.0.0"]