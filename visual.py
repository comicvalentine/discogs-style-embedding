import pandas as pd
import pickle
import plotly.express as px
import umap.umap_ as umap
from dataclasses import dataclass

###### Dimensionality reduction using UMAP #######
# Hyperparameters are controlled via umap_kwargs

DEFAULT_UMAP_KWARGS = dict(n_neighbors=15,
                           min_dist=0.1,
                           metric="cosine",
                           random_state=42)

def umap_project(
    X,
    n_components: int,
    umap_kwargs: dict | None = None
):
    assert n_components in [2, 3], f"n_components must be 2 or 3, got {n_components}"

    kwargs = DEFAULT_UMAP_KWARGS.copy()
    if umap_kwargs:
        kwargs.update(umap_kwargs)

    reducer = umap.UMAP(
        n_components=n_components,
        **kwargs
    )

    return reducer.fit_transform(X)


###### Plotly Visualization #######
# Visual settings are managed by VisualConfig
@dataclass
class VisualConfig:
    fig_width: int = 900
    fig_height: int = 700

    marker_size: int = 6
    marker_opacity: float = 0.8

    font_size: int = 8
    text_position: str = "top center"

    init_mode:str = "markers"
    init_dragmode:str = "pan"
    init_style: str | None=None
    init_margin: int | None=None

    color_palette = px.colors.qualitative.Dark24

def visual(emb_df, 
            tag_dict, 
            save_dir, 
            n_components: int, 
            tag_name="Main Genre", 
            post_script:str = "", 
            umap_kwargs=None,
            visual_cfg: VisualConfig | None=None):
    
    if visual_cfg is None:
        visual_cfg = VisualConfig()
    
    assert visual_cfg.init_dragmode in ["zoom", "pan"], \
        f"init_dragmode must be 'zoom' or 'pan', got {visual_cfg.init_dragmode}"    
    
    emb_df = emb_df.copy()
    
    coords = umap_project(emb_df.drop(columns=["style"]), n_components=n_components, umap_kwargs = umap_kwargs)

    for i in range(n_components):
        emb_df[f"dim_{i}"] = coords[:, i]
    
    # Determine axes (x, y) or (x, y, z) based on n_components
    axis_kwargs = {axis: f"dim_{i}"
                for i, axis in enumerate(["x", "y", "z"][:n_components])}

    # Style and genre names use "_" as spacers; replace with spaces for better readability
    emb_df[tag_name] = [tag_dict.get(style, "Unknown").replace("_", " ") for style in emb_df["style"]]
    emb_df['style'] = [style.replace("_", " ") for style in emb_df["style"]]

    if n_components == 3:
        px.scatter = px.scatter_3d

    fig = px.scatter(
        emb_df,
        text="style",
        hover_name = "style",
        color=tag_name,
        color_discrete_sequence=visual_cfg.color_palette,
        **axis_kwargs
    )

    fig.update_traces(
        marker=dict(size=visual_cfg.marker_size, opacity=visual_cfg.marker_opacity),
        textposition=visual_cfg.text_position,
        textfont=dict(size=visual_cfg.font_size),
        mode=visual_cfg.init_mode
    )


    # Set initial interaction mode (e.g., 'pan' or 'zoom')    
    fig.update_layout(
        dragmode=visual_cfg.init_dragmode
    )

    if visual_cfg.init_style is not None:
        # 1. 대상 스타일 행 찾기
        target_row = emb_df[emb_df['style'].str.contains(visual_cfg.init_style, case=False, na=False)]
        
        if not target_row.empty:

            ratio = (visual_cfg.init_margin / 100.0) if visual_cfg.init_margin else 1
            
            update_layout_kwargs = {}
            scene_kwargs = {}

            for i, axis in enumerate(["xaxis", "yaxis", "zaxis"][:n_components]):
                col = f"dim_{i}"
                full_min, full_max = emb_df[col].min(), emb_df[col].max()
                full_range = full_max - full_min
                center_val = target_row[col].mean()
                
                half_display_range = (full_range * ratio) / 2
                new_min = center_val - half_display_range
                new_max = center_val + half_display_range
                
                if n_components == 3:
                    scene_kwargs[axis] = dict(range=[new_min, new_max])
                else:
                    update_layout_kwargs[f"{axis}.range"] = [new_min, new_max]

            if n_components == 3:
                fig.update_layout(scene=scene_kwargs)
            else:
                fig.update_layout(update_layout_kwargs)

    json_data = emb_df.to_json(orient='records')
    full_script = f"var search_data = {json_data}; \n {post_script}"

    fig.write_html(
        save_dir,
        include_plotlyjs="cdn",
        post_script = full_script
    )

import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--search_type",
        type=str,
        default="masters",
        help="Discogs search type (e.g. masters, releases)"
    )
    parser.add_argument(
        "--algo",
        type=str,
        default="Node2Vec",
        help="Embedding algorithm name"
    )
    return parser.parse_args()

if __name__ == "__main__":

    args = parse_args()

    search_type = args.search_type
    algo = args.algo

    emb_df = pd.read_csv(f"./embedding_data/{algo}/embedding_df_{search_type}.csv")

    with open(f"./embedding_data/max_genre_counter_{search_type}.pkl", "rb") as f:
        max_genre_counter = pickle.load(f)

    style_to_main_genre = {
        st: cnt.most_common(1)[0][0]
        for st, cnt in max_genre_counter.items()
    }

    save_dir = f"./docs/style_{algo}_{search_type}_umap"

    try:
        with open("post_script.js", "r", encoding="utf-8") as f:
            post_script = f.read()
    except Exception as e:
        post_script = ""
    
    visual(emb_df=emb_df, 
           tag_dict=style_to_main_genre, 
           save_dir = f"{save_dir}.html", 
           n_components=2, 
           tag_name="Main Genre", 
           umap_kwargs=None,
           post_script=post_script,
           visual_cfg=VisualConfig(fig_width=1600, fig_height=1200, init_style="New Wave", init_dragmode="pan", init_margin=20, init_mode="markers+text"))
    
    visual(emb_df=emb_df, 
           tag_dict=style_to_main_genre, 
           save_dir = f"{save_dir}_3d.html", 
           n_components=3, 
           tag_name="Main Genre",
           umap_kwargs=None,
           post_script=post_script,
           visual_cfg=VisualConfig(fig_width=1600, fig_height=1200, init_margin=10))
