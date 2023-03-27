import os
import json
import tensorflow_hub as hub
import numpy as np
import tensorflow_text
import plotly.express as px
import plotly.graph_objects as go
from tqdm import tqdm
from scipy.spatial.distance import pdist

from sklearn.cluster import AgglomerativeClustering
from scipy.cluster.hierarchy import dendrogram, linkage


def read_json(path):
    with open(path) as f:
        result = json.load(f)
    return result


def write_json(path, content):
    with open(path, "w") as f:
        json.dump(content, f, indent=2)


def get_batch(arr, batch_size):
    for i in range(0, len(arr), batch_size):
        yield arr[i : i + batch_size]


embed = hub.load(
    "https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3"
)

claims_path = "data/latest/claim_reviews_raw_recollected.json"


path_claim_reviews_clean = "data/latest/claims_embedding_reviews.json"
if os.path.exists(path_claim_reviews_clean):
    claim_reviews = read_json(path_claim_reviews_clean)
    print("loaded", len(claim_reviews))
else:
    claim_reviews = read_json(claims_path)
    print("loaded", len(claim_reviews))
    claim_reviews = [el for el in claim_reviews if el.get("claimReviewed", None)]
    print("now", len(claim_reviews))
    write_json(path_claim_reviews_clean, claim_reviews)

text_claims = [
    el["claimReviewed"] if "claimReviewed" in el else "" for el in claim_reviews
]
for i, t in enumerate(text_claims):
    if not isinstance(t, str):
        t0 = t[0]
        text_claims[i] = t0
        if not (isinstance(t0, str)):
            print(t)
            raise ValueError(t)


path_claim_embedding = "data/latest/claims_embedding_values.npy"
if os.path.exists(path_claim_embedding):
    texts_embedded = np.load(path_claim_embedding)
    print("loaded claim embedding", len(texts_embedded))
else:
    batch_size = 100
    texts_embedded_batches = []
    for b in tqdm(
        get_batch(text_claims, batch_size), total=len(text_claims) // batch_size
    ):
        # print(b)
        embeddings = embed(b)
        # raise ValueError(123)
        texts_embedded_batches.append(embeddings)
    texts_embedded = np.concatenate(texts_embedded_batches)
    del texts_embedded_batches
    np.save(path_claim_embedding, texts_embedded)


# print('computing similarity matrix')
# similarity_matrix = np.inner(texts_embedded, texts_embedded)
# print('plotting matrix')
# fig = go.Figure(data=[go.Heatmap(z=similarity_matrix)])
# fig.show()


# ward hierarchical clustering
linkage_method = "ward"
similarity_metric = "euclidean"
n_samples = len(text_claims)
sentences_ids = list(range(n_samples))

path_condensed_distance_matrix = "data/latest/claims_condensed_distance_matrix.pk"
if os.path.exists(path_condensed_distance_matrix):
    similarity_condensed = np.load(path_condensed_distance_matrix)
else:
    # computing condensed distance matrix
    similarity_condensed = pdist(texts_embedded, metric=similarity_metric)
    np.save(path_condensed_distance_matrix, similarity_condensed)

print("computing linkage")
path_linkage = "data/latest/claims_linkage.pk"
if os.path.exists(path_linkage):
    Z = np.load(path_linkage)
else:
    Z = linkage(similarity_condensed, linkage_method, similarity_metric)
    print("linkage computed: shape", Z.shape)
    np.save(path_linkage, Z)

raise ValueError(123)

max_distance = Z[-1, 2]
distance_inter = 0.9

# start with every sentence separated, follow the evolution and break when distance is met
# TODO attach the distance to the clusters
filtered_clusters = [[el] for el in sentences_ids] + [[]] * (len(sentences_ids) - 1)
for i, step in tqdm.tqdm(
    enumerate(Z),
    desc="running truncated hierarchical clustering",
    total=len(sentences_ids),
):
    if step[2] > distance_inter:
        break
    # remove from previous cluster
    a_index = int(step[0])
    b_index = int(step[1])
    # add to the current cluster
    a = filtered_clusters[a_index]
    b = filtered_clusters[b_index]
    new_index = i + len(sentences_ids)
    filtered_clusters[new_index] = a + b
    filtered_clusters[a_index] = []
    filtered_clusters[b_index] = []


filtered_clusters = [el for el in filtered_clusters if len(el) >= 2]
