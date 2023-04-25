import json
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from claimreview_collector.processing import utils

data_path = "/Users/mm35626/Downloads/2022_02_28/claim_reviews.json"

data = utils.read_json(data_path)

print(len(data))
keyword_list = ["ukraine", "ucraina", "ucrania"]

# date latest add top level
for el in data:
    dates = [r["date_published"] for r in el["reviews"]]
    if len(dates) == 0:
        date = None
    else:
        date = max(dates)
    el["date_published"] = date

with_ukraine = [
    el
    for el in data
    if any(
        keyword in " ".join(el["claim_text"] + [el["review_url"]]).lower()
        for keyword in keyword_list
    )
]
print(len(with_ukraine))

# go.Figure(data=[go.Histogram(x=with_ukraine)])

df = pd.DataFrame(with_ukraine)
fig = px.histogram(df, x="date_published")
fig.show()

with_ukraine = sorted(with_ukraine, key=lambda x: x["date_published"])

utils.write_json_with_path(with_ukraine, Path(""), "with_ukrane.json")

result = []
for el in with_ukraine:
    r = {
        "date_published": el["date_published"],
        "review_url": el["review_url"],
        "label": el["label"],
    }
    for i, a in enumerate(el.get("appearances", [])):
        r[f"appearance_{i}"] = a
    result.append(r)
    all_k

writer = csv.DictWriter(
    open("claim_reviews_with_ukraine.csv", "w"), fieldnames=result[0].keys()
)
