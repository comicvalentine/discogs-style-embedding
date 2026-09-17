import pandas as pd
import pickle
import json
from pathlib import Path
import plotly.express as px
from dataclasses import dataclass
from collections import defaultdict

WEB_DIR = Path(__file__).parent / "web"
GENRE_HUE_START = 355  # slot 0 lands on red, see PRIORITY_ANCHORS below

# A flat hue rotation wasn't distinct enough at 15 categories (adjacent hues
# 24deg apart, e.g. Electronic/Classical/Folk all landed in the same green
# band). Three bands of lightness/saturation, cycled instead of alternated,
# add a second and third channel of separation on top of hue.
GENRE_LIGHT_BANDS = (38, 56, 47)
GENRE_SAT_BANDS = (64, 50, 58)

# Rock / Electronic / Pop are the three genres users compare most, so they get
# fixed slots exactly n/3 apart on the 15-slot wheel (0, 5, 10 -> 0deg, 120deg,
# 240deg from GENRE_HUE_START) instead of falling wherever frequency-interleave
# happens to put them. 0/5/10 also land on three different bands (0, 2, 1 mod
# 3), so these three differ in lightness/saturation as well as hue. The
# remaining 12 genres fill the leftover slots by frequency, as before.
PRIORITY_ANCHORS = {"Rock": 0, "Electronic": 5, "Pop": 10}


def genre_palette(genres: list[str]) -> dict[str, dict[str, int]]:
    from collections import Counter
    counts = Counter(genres)
    n = len(counts) or 1

    anchors = {g: slot for g, slot in PRIORITY_ANCHORS.items() if g in counts and slot < n}
    taken_slots = set(anchors.values())
    remaining_slots = [s for s in range(n) if s not in taken_slots]

    by_freq = [g for g, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True) if g not in anchors]

    # Evenly-spaced hues give every pair its guaranteed minimum (24deg at
    # n=15), but the two rank-adjacent genres always get the *tightest* gap.
    # Interleaving front/back of the frequency ranking means that tightest
    # gap almost always falls between a common genre and a rare one, instead
    # of between two genres that are both common enough to visually compete.
    ordered = []
    lo, hi = 0, len(by_freq) - 1
    take_front = True
    while lo <= hi:
        if take_front:
            ordered.append(by_freq[lo])
            lo += 1
        else:
            ordered.append(by_freq[hi])
            hi -= 1
        take_front = not take_front

    slot_of = dict(anchors)
    slot_of.update(zip(ordered, remaining_slots))

    palette = {}
    for g, slot in slot_of.items():
        palette[g] = {
            "hue": (GENRE_HUE_START + round(slot * 360 / n)) % 360,
            "sat": GENRE_SAT_BANDS[slot % 3],
            "light": GENRE_LIGHT_BANDS[slot % 3],
        }
    return palette


def render_map_2d(algo, tag_dict, save_dir, hover_data, search_type,
                   init_style="hardcore", init_margin_pct=0.12, umap_kwargs=None):
    """Renders the 2D UMAP scatter as a self-contained D3 page (no plotly)."""

    EMB_UMAP_DIR = f"./embedding_data/{algo}/embedding_df_{search_type}_umap_2D.csv"
    try:
        emb_df = pd.read_csv(EMB_UMAP_DIR)
    except FileNotFoundError:
        print("umap not conducted")
        from umap_project import umap_project
        EMB_DIR = f"./embedding_data/{algo}/embedding_df_{search_type}.csv"
        emb_df = pd.read_csv(EMB_DIR)
        coords = umap_project(emb_df.drop(columns=["style"]), n_components=2, umap_kwargs=umap_kwargs)
        emb_df["dim_0"] = coords[:, 0]
        emb_df["dim_1"] = coords[:, 1]
        emb_df.to_csv(EMB_UMAP_DIR)

    genres = [tag_dict.get(style, "Unknown") for style in emb_df["style"]]
    palette = genre_palette(genres)

    points = []
    for style_key, genre, dim0, dim1 in zip(emb_df["style"], genres, emb_df["dim_0"], emb_df["dim_1"]):
        props = hover_data.get(style_key, {}) if hover_data else {}
        points.append({
            "style": style_key.replace("_", " "),
            "dim0": float(dim0),
            "dim1": float(dim1),
            "genre": genre.replace("_", " "),
            "hover": [[g, p] for g, p in props.items()],
        })

    palette = {g.replace("_", " "): v for g, v in palette.items()}

    payload = {
        "points": points,
        "genreHue": palette,
        "init": {"style": init_style, "marginPct": init_margin_pct},
    }

    template = (WEB_DIR / "map.template.html").read_text(encoding="utf-8")
    css = (WEB_DIR / "map.css").read_text(encoding="utf-8")
    script = (WEB_DIR / "map.js").read_text(encoding="utf-8")
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html = (template
            .replace("__TITLE__", f"Discogs Style Map — {algo}")
            .replace("/*__STYLE__*/", css)
            .replace("/*__DATA__*/", data_json)
            .replace("/*__SCRIPT__*/", script))

    Path(save_dir).write_text(html, encoding="utf-8")


###### Plotly Visualization (kept for the 3D view only, for now) #######
# Visual settings are managed by VisualConfig
@dataclass
class VisualConfig:
    fig_width: int = 900
    fig_height: int = 700

    marker_size: int = 6
    marker_opacity: float = 0.8

    font_size: int = 10
    text_position: str = "top center"

    init_mode:str = "markers"
    init_dragmode:str = "pan"
    init_style: str | None=None
    init_margin: int | None=None

    color_palette = px.colors.qualitative.Light24

    paper_bgcolor = "white"
    plot_bgcolor = "white"
    grid_color = '#E9E9E9'


def visual(algo, 
            tag_dict, 
            save_dir, 
            n_components: int, 
            tag_name="Main Genre", 
            post_script:str = "", 
            hover_data: dict | None = None,
            umap_kwargs=None,
            visual_cfg: VisualConfig | None=None):
    
    if visual_cfg is None:
        visual_cfg = VisualConfig()
    
    assert visual_cfg.init_dragmode in ["zoom", "pan"], \
        f"init_dragmode must be 'zoom' or 'pan', got {visual_cfg.init_dragmode}"    
    
    EMB_UMAP_DIR = f"./embedding_data/{algo}/embedding_df_{search_type}_umap_{n_components}D.csv"
        
    try:
        emb_df = pd.read_csv(EMB_UMAP_DIR)

    except FileNotFoundError:
        print("umap not conducted")
        from umap_project import umap_project
        EMB_DIR = f"./embedding_data/{algo}/embedding_df_{search_type}.csv"
        emb_df = pd.read_csv(EMB_DIR)
        coords = umap_project(emb_df.drop(columns=["style"]), n_components=n_components, umap_kwargs = umap_kwargs)

        for i in range(n_components):
            emb_df[f"dim_{i}"] = coords[:, i]
        emb_df.to_csv(EMB_UMAP_DIR)

    # Determine axes (x, y) or (x, y, z) based on n_components
    axis_kwargs = {axis: f"dim_{i}"
                for i, axis in enumerate(["x", "y", "z"][:n_components])}

    # Style and genre names use "_" as spacers; replace with spaces for better readability
    emb_df[tag_name] = [tag_dict.get(style, "Unknown").replace("_", " ") for style in emb_df["style"]]
    if hover_data:
        def format_hover(style_key):
            props = hover_data.get(style_key.replace(" ", "_"), {}) 
            return "<br>".join([f"{k}: {v:.1%}" for k, v in props.items()])
        emb_df["hover_text"] = [format_hover(s) for s in emb_df['style']]
                
    emb_df['style'] = [style.replace("_", " ") for style in emb_df["style"]]
    
    if n_components == 3:
        px.scatter = px.scatter_3d

    fig = px.scatter(
        emb_df,
        text="style",
        color=tag_name,
        color_discrete_sequence=visual_cfg.color_palette,
        hover_data={"hover_text": True, "style": True},
        **axis_kwargs
    )
    fig.update_layout(
        paper_bgcolor = VisualConfig.paper_bgcolor,
        plot_bgcolor=VisualConfig.plot_bgcolor,
        legend=dict(
            x=0.98,
            y=0.98,
            xanchor="right",
            yanchor="top",
            bgcolor="rgba(255, 255, 255, 0.88)",
            bordercolor="rgba(16, 16, 16, 0.10)",
            borderwidth=1,
            font=dict(color="#101010"),
            title=dict(font=dict(color="#101010"))
        ),
    )
    grid_style = dict(
        showgrid=True, 
        gridwidth=0.5, 
        gridcolor=VisualConfig.grid_color,
        zeroline=False
    )

    fig.update_xaxes(**grid_style)
    fig.update_yaxes(**grid_style)
    

    if hover_data:
        fig.update_traces(
            hovertemplate="<b>%{text}</b><br><br>%{customdata[0]}<extra></extra>"
        )
    
    fig.update_traces(
        marker=dict(size=visual_cfg.marker_size, opacity=visual_cfg.marker_opacity),
        textposition=visual_cfg.text_position,
        textfont=dict(size=visual_cfg.font_size),
        mode=visual_cfg.init_mode
    )

    # Set initial interaction mode (e.g., 'pan' or 'zoom')    
    fig.update_layout(
        dragmode=visual_cfg.init_dragmode,
    )

    fig.update_layout(
        xaxis_title=None, 
        yaxis_title=None,
        xaxis=dict(
                showticklabels=False,
                zeroline=False
            ),
        yaxis=dict(
                showticklabels=False,
                zeroline=False
            ),
        scene=dict(
        xaxis=dict(title='', showticklabels=False),
        yaxis=dict(title='', showticklabels=False),
        zaxis=dict(title='', showticklabels=False)
        ) if n_components == 3 else None)

    if visual_cfg.init_style is not None:
        for idx, row in emb_df.iterrows():
            if visual_cfg.init_style.lower().replace(" ", "") == row["style"].lower().replace(" ", ""):
                target_row = row
                break
        
        if not target_row.empty:

            ratio = (visual_cfg.init_margin / 100.0) if visual_cfg.init_margin else 1
            
            update_layout_kwargs = {}
            scene_kwargs = {}

            for i, axis in enumerate(["xaxis", "yaxis", "zaxis"][:n_components]):
                col = f"dim_{i}"
                full_min, full_max = emb_df[col].min(), emb_df[col].max()
                full_range = full_max - full_min
                center_val = target_row[col]
                
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
    
    emb_df.rename(columns = {"Main Genre":"main_genre"}, inplace=True)
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

    with open(f"./embedding_data/max_genre_counter_{search_type}.pkl", "rb") as f:
        max_genre_counter = pickle.load(f)
    
    style_to_main_genre = {
        st: cnt.most_common(1)[0][0]
        for st, cnt in max_genre_counter.items()
    }

    genre_prop = defaultdict(dict)
    for st, cnt in max_genre_counter.items():
        st_pop = sum(cnt.values())
        for ord, genre in enumerate(sorted(cnt, key = lambda x: cnt[x], reverse=True)[:3]):
            genre_prop[st][genre.replace("_", " ")] = cnt[genre]/st_pop

    save_dir = f"./docs/style_{algo}_{search_type}_umap"

    try:
        with open("post_script.js", "r", encoding="utf-8") as f:
            post_script = f.read()
    except Exception as e:
        post_script = ""
    
    render_map_2d(algo=algo,
                  tag_dict=style_to_main_genre,
                  save_dir=f"{save_dir}.html",
                  hover_data=genre_prop,
                  search_type=search_type,
                  init_style="hardcore",
                  init_margin_pct=0.12,
                  umap_kwargs={"min_dist": 0.5, "spread": 0.6})


    visual(algo = algo, 
           tag_dict=style_to_main_genre, 
           save_dir = f"{save_dir}_3d.html", 
           n_components=3, 
           tag_name="Main Genre",
           hover_data = genre_prop,
           umap_kwargs=None,
           post_script=post_script,
           visual_cfg=VisualConfig(fig_width=1600, fig_height=1200, init_margin=10))
