import gzip
import xml.etree.ElementTree as ET
from gensim.models import Word2Vec
import pandas as pd

ver = "20260101"
search_type = "masters"
path = f"./raw_data/discogs_{ver}_{search_type}.xml.gz"

class Corpus:
    def __iter__(self):
        with gzip.open(path, "rb") as f:
            context = ET.iterparse(f, events=("end",))
            for _, elem in context:
                if elem.tag != "master":
                    continue
                styles = [s.text.replace(" ", "_") for s in elem.findall("./styles/style")]
                if len(styles) >= 2:
                    yield styles
                elem.clear()

model = Word2Vec(
    sentences=Corpus(),
    vector_size=32,
    window=10,
    min_count=5,
    workers=8,
    epochs=5
)

model.wv.save(f"./embedding_data/Word2Vec/embedding_{search_type}.kv")

wv = model.wv
emb_df = pd.DataFrame(
    wv.vectors,
    index=wv.index_to_key
)
emb_df.index.name = "style"
emb_df.to_csv(f"./embedding_data/Word2Vec/embedding_df_{search_type}.csv")