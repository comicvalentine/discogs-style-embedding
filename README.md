# Discogs Style Embedding

Visualizing relationships between music subgenres from **Discogs**.

## Motivation
- Discogs categorizes releases and artists into **15 genres** and **760 styles** (subgenres).  
- Many subgenres co-occur in the same release—similar to how words co-occur in sentences.  
  -  Example: *Post-Rock* and *Shoegaze* often appear together on the same album, showing that these genres are closely related.  
- Can we capture these relationships in a vector space?

## Approach
1. Represent 760 subgenres as low-dimensional vectors using:
   - **Word2Vec** (treating co-occurring styles like co-occurring words)  
   - **Node2Vec** (treating styles as nodes in a co-occurrence graph)  
2. Visualize embeddings with dimensionality reduction (UMAP) in **2D** and **3D**.

## Map Visualizations
| Method | 2D | 3D |
|--------|----|----|
| Word2Vec | [View](https://comicvalentine.github.io/Discogs_style_embedding/style_Word2Vec_masters_umap.html) | [View](https://comicvalentine.github.io/Discogs_style_embedding/style_Word2Vec_masters_umap_3d.html) |
| Node2Vec | [View](https://comicvalentine.github.io/Discogs_style_embedding/style_Node2Vec_masters_umap.html) | [View](https://comicvalentine.github.io/Discogs_style_embedding/style_Node2Vec_masters_umap_3d.html) |

## Data Sources
- **Discogs monthly data dump:** [https://data.discogs.com/](https://data.discogs.com/)  
- **Current version:** 2026-01-01  
- **Note:** `Word2Vec.py` and `counter.py` use `raw_data/discogs_20260101_masters.xml.gz`.  
  > This file is **not included** due to its large size.