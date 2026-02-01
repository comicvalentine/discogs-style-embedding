from collections import Counter
import pickle
import numpy as np
import pandas as pd
import networkx as nx
from node2vec import Node2Vec

search_type = "masters"

with open(f"./embedding_data/pair_counter_{search_type}.pkl", 'rb') as f:
    pair_counter = pickle.load(f)
with open(f"./embedding_data/single_counter_{search_type}.pkl", 'rb') as f:
    single_counter = pickle.load(f)

edge_lst = []
for (a, b), cnt in pair_counter.items():
    a_pop = single_counter[a]
    b_pop = single_counter[b]
    edge_lst.append({'src':a, 'dst':b, 'weight':cnt/a_pop})
    edge_lst.append({'src':b, 'dst':a, 'weight':cnt/b_pop})

edge_df = pd.DataFrame(edge_lst)
edge_df.to_csv(f"./embedding_data/Node2Vec/edge_{search_type}.csv")

G = nx.from_pandas_edgelist(
    edge_df,
    source = "src",
    target = "dst",
    edge_attr = "weight",
    create_using=nx.DiGraph()
)

with open(f"./embedding_data/Node2Vec/network_{search_type}.pkl","wb") as f:
    pickle.dump(G, f)

node2vec = Node2Vec(
    G,
    dimensions=32,
    walk_length=80,
    num_walks=10,
    p=1,
    q=1,
    workers=1,
    weight_key="weight",
    quiet=False
)

model = node2vec.fit(
    window=10,
    min_count=1,
    batch_words=4
)


model.wv.save(f"./embedding_data/Node2Vec/embedding_{search_type}.kv")

wv = model.wv
emb_df = pd.DataFrame(
    wv.vectors,
    index=wv.index_to_key
)
emb_df.index.name = "style"
emb_df.to_csv(f"./embedding_data/Node2Vec/embedding_df_{search_type}.csv")