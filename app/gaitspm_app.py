# -*- coding: utf-8 -*-
"""
GaitSPM: gait analysis dashboard for normalized kinematic curves (0–100%).

Import consolidated Excel/CSV data, map variables to joints and planes,
and run spm1d analyses. Outputs include MATLAB-style mean/SD and SPM plots,
cluster tables, effect sizes, normality checks, corrected post hoc comparisons,
and Methods/Results text in English or Spanish.

Start the browser interface with `python launch.py` from the repository root.
The optional Streamlit interface uses `streamlit run streamlit_app.py`.
"""
from __future__ import annotations

import io
import re
import itertools
import warnings
import datetime

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.lines import Line2D
from matplotlib import cm as mpl_cm
from matplotlib.colors import Normalize, is_color_like
import scipy.stats as sps
try:
    import spm1d
except ModuleNotFoundError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'vendor'))
    import spm1d
import streamlit as st

VERSION = "1.5.0.dev0"
NODES = np.arange(101)

# ----------------------------------------------------------------------------
# MATLAB styling
# ----------------------------------------------------------------------------
MATLAB_COLORS = [
    (0.0000, 0.4470, 0.7410),
    (0.8500, 0.3250, 0.0980),
    (0.9290, 0.6940, 0.1250),
    (0.4940, 0.1840, 0.5560),
    (0.4660, 0.6740, 0.1880),
    (0.3010, 0.7450, 0.9330),
    (0.6350, 0.0780, 0.1840),
]
MATLAB_HEX = ["#0072BD", "#D95319", "#EDB120", "#7E2F8E",
              "#77AC30", "#4DBEEE", "#A2142F"]
GREY_BAND = (0.86, 0.86, 0.86)
CLUSTER_FILL = (0.86, 0.24, 0.15)
THRESH_COLOR = (0.75, 0.10, 0.10)

PLOT_STYLE_DEFAULTS = {
    "line_colors": MATLAB_HEX,
    "band_colors": MATLAB_HEX,
    "reference_band_color": "#DBDBDB",
    "interval_mode": "sd",
    "interval_alpha": 0.18,
    "show_interval_edges": False,
    "cluster_fill_color": "#DB3D26",
    "cluster_fill_alpha": 0.55,
    "show_cluster_bars": False,
}

JOINT_ORDER = ["pelvis", "hip", "knee", "ankle"]
PLANE_ORDER = ["sagittal", "frontal", "transverse"]


def apply_matlab_style():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 9.5,
        "axes.titlesize": 10.5,
        "axes.titleweight": "bold",
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "axes.linewidth": 0.9,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "axes.grid": True,
        "grid.color": "0.88",
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "legend.frameon": True,
        "legend.edgecolor": "0.25",
        "legend.framealpha": 1.0,
        "legend.fancybox": False,
        "legend.fontsize": 8.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "mathtext.default": "regular",
    })


# ----------------------------------------------------------------------------
# Figure labels (ES/EN)
# ----------------------------------------------------------------------------
LBL = {
    "es": {
        "joint": {"pelvis": "Pelvis", "hip": "Cadera", "knee": "Rodilla", "ankle": "Tobillo"},
        "plane": {"sagittal": "Sagital", "frontal": "Frontal", "transverse": "Transversal"},
        "xlabel": "% del ciclo de la marcha",
        "ylabel": "Ángulo (°)",
        "band": "Banda de referencia",
        "cov_note": "color ∝ {cov}",
        "effect_d": "d de Cohen",
        "effect_dz": "d$_z$ de Cohen",
        "effect_r": "r (correlación)",
        "effect_eta": "η² (por nodo)",
        "effect_eta_p": "ηp² (por nodo)",
        "ns": "sin clústeres significativos",
    },
    "en": {
        "joint": {"pelvis": "Pelvis", "hip": "Hip", "knee": "Knee", "ankle": "Ankle"},
        "plane": {"sagittal": "Sagittal", "frontal": "Frontal", "transverse": "Transverse"},
        "xlabel": "Gait cycle (%)",
        "ylabel": "Angle (deg)",
        "band": "Reference band",
        "cov_note": "colour ∝ {cov}",
        "effect_d": "Cohen's d",
        "effect_dz": "Cohen's d$_z$",
        "effect_r": "r (correlation)",
        "effect_eta": "η² (node-wise)",
        "effect_eta_p": "partial η² (node-wise)",
        "ns": "no significant clusters",
    },
}

DESIGNS = {
    "ttest2": "Comparar 2 grupos independientes (SPM{t})",
    "paired_cond": "Comparar 2 condiciones pareadas, p. ej. pre-post (SPM{t})",
    "paired_side": "Comparar lados I vs D, pareado (SPM{t})",
    "ancova": "ANCOVA · 2 groups + covariates (SPM{t})",
    "glm": "GLM · numeric predictors + t contrast",
    "anova2": "Two-way ANOVA · independent group × condition",
    "anova2onerm": "Mixed ANOVA · group × repeated condition",
    "anova1": "Comparar ≥3 grupos independientes (SPM{F})",
    "anova1rm": "Comparar ≥3 condiciones intra-sujeto, RM-ANOVA (SPM{F})",
    "regress": "Asociación con covariable continua, regresión (SPM{t})",
}


def fmt_p(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def _clean_series(s: pd.Series, default: str = "—") -> pd.Series:
    out = s.astype(str).str.strip()
    out = out.replace({"": default, "nan": default, "None": default, "NaN": default})
    return out


# ----------------------------------------------------------------------------
# File reading and structure detection
# ----------------------------------------------------------------------------
def sniff_csv(text: str):
    """Use the header/CSV grammar, never counts of decimal commas in the body."""
    import csv
    lines = text.splitlines()
    header = next((line for line in lines if line.strip()), '')
    candidates = []
    for sep in [';', '\t', ',', '|']:
        try:
            rows = list(csv.reader(lines[:30], delimiter=sep))
            width = len(next(csv.reader([header], delimiter=sep)))
            consistent = sum(len(row) == width for row in rows)
            candidates.append((consistent / max(len(rows), 1), width, sep))
        except csv.Error:
            continue
    candidates = [x for x in candidates if x[1] > 1]
    if not candidates:
        raise ValueError('No se reconoce el separador CSV / CSV separator not recognised.')
    sep = max(candidates)[2]
    dec = ',' if sep != ',' and re.search(r'\d,\d', '\n'.join(lines[1:30])) else '.'
    return sep, dec
@st.cache_data(show_spinner=False)
def read_upload(data: bytes, name: str, sheet=None):
    """Lee CSV/XLSX y devuelve (df, info)."""
    name = (name or "").lower()
    if name.endswith(".xls"):
        raise ValueError("El formato Excel binario .xls no está soportado. Guarda el archivo como .xlsx o CSV.")
    if name.endswith((".xlsx", ".xlsm")):
        xls = pd.ExcelFile(io.BytesIO(data))
        sh = sheet if sheet in xls.sheet_names else ("Curves_Wide" if "Curves_Wide" in xls.sheet_names else xls.sheet_names[0])
        header = pd.read_excel(xls, sheet_name=sh, header=None, nrows=1, keep_default_na=False).iloc[0].tolist()
        df = pd.read_excel(xls, sheet_name=sh, dtype=object, keep_default_na=False)
        info = {"tipo": "excel", "hoja": sh, "hojas": xls.sheet_names}
    else:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("latin-1")
        sep, dec = sniff_csv(text)
        import csv
        header = next(row for row in csv.reader(io.StringIO(text), delimiter=sep) if row)
        # Preserve identity fields (001 differs from 1; NA can be a subject ID).
        # Numeric conversion is deferred until the user maps roles.
        df = pd.read_csv(io.StringIO(text), sep=sep, dtype=str, keep_default_na=False)
        info = {"tipo": "csv", "sep": sep, "decimal": dec, "hojas": None}
    names = [str(c).strip() for c in header if str(c).strip()]
    if len(names) != len(set(names)):
        raise ValueError('Cabeceras duplicadas / duplicate column names: rename columns before importing.')
    df.columns = [str(c).strip() for c in df.columns]
    df.attrs['decimal'] = info.get('decimal', '.')
    return df, info


def _to_numeric(values, errors='coerce'):
    """Convert mapped measurements without modifying original identity fields."""
    if getattr(values, 'attrs', {}).get('decimal') == ',':
        values = values.astype(str).str.replace(',', '.', regex=False)
    return pd.to_numeric(values, errors=errors)


def find_curve_blocks(cols):
    """Column blocks 'Variable_0 … Variable_100' (wide format)."""
    pat = re.compile(r"^(?P<base>.*?)[\s_\-\.]*?(?P<idx>\d{1,3})$")
    groups = {}
    for c in cols:
        m = pat.match(str(c).strip())
        if m and m.group("base").strip(" _-."):
            groups.setdefault(m.group("base").strip(" _-."), []).append((int(m.group("idx")), c))
    blocks = {}
    for base, items in groups.items():
        idxs = sorted({i for i, _ in items})
        if len(items) >= 30 and len(idxs) == len(items) and (max(idxs) - min(idxs) + 1) == len(idxs):
            blocks[base] = sorted(items)
    return blocks


def detect_structure(df: pd.DataFrame):
    """Devuelve ('wide'|'transposed'|'long'|'unknown', payload)."""
    blocks = find_curve_blocks(df.columns)
    if blocks:
        return "wide", blocks
    if 40 <= len(df) <= 250:
        c0 = _to_numeric(df.iloc[:, 0], errors="coerce")
        if c0.notna().mean() > 0.95:
            v = c0.dropna().to_numpy()
            if np.all(np.diff(v) >= 0) and v.min() <= 2 and v.max() >= 90:
                return "transposed", df.columns[0]
    for c in df.columns:
        v = _to_numeric(df[c], errors="coerce")
        u = v.dropna().unique()
        if 40 <= len(u) <= 202 and np.nanmin(u) >= -0.5 and np.nanmax(u) <= 101.5 and len(df) > 4 * len(u):
            return "long", c
    return "unknown", None


def resample1(x, y):
    """Resample a curve onto the 0–100 grid (101 nodes)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    x, y = x[ok], y[ok]
    if len(x) < 10:
        return np.full(101, np.nan)
    o = np.argsort(x)
    x, y = x[o], y[o]
    if np.any(np.diff(x) == 0):
        raise ValueError("Nodos duplicados / duplicate nodes: identifica los ensayos antes de importar.")
    if x.max() > 100 and x.max() > x.min():
        x = (x - x.min()) / (x.max() - x.min()) * 100.0
    out = np.interp(NODES, x, y, left=np.nan, right=np.nan)
    for a, b in zip(x[:-1], x[1:]):
        if b-a > 10:
            out[(NODES > a) & (NODES < b)] = np.nan
    return out


def resample_rows(idxs, M):
    """Resample each row of M (observations × points) to 101 nodes."""
    idxs = np.asarray(idxs, float)
    if idxs.max() > 100 and idxs.max() > idxs.min():
        x = (idxs - idxs.min()) / (idxs.max() - idxs.min()) * 100.0
    else:
        x = idxs
    same = (M.shape[1] == 101) and np.allclose(x, NODES)
    out = np.full((M.shape[0], 101), np.nan)
    for i in range(M.shape[0]):
        y = M[i]
        ok = np.isfinite(y)
        if ok.sum() < 10:
            continue
        out[i] = y if (same and ok.all()) else resample1(x, y)
    return out


# ---------------------------- side and classification ---------------------------
_SIDE_L = {"l", "left", "izq", "izda", "izquierda", "izquierdo", "i"}
_SIDE_R = {"r", "right", "der", "dcha", "derecha", "derecho", "d"}


def split_side(name: str):
    """('L'|'R'|None, nombre_sin_lado). Soporta PiG ('LHipAngles') y tokens."""
    n = str(name).strip()
    m = re.match(r"^([LR])(?=[A-Z])", n)
    if m:
        return m.group(1), n[1:]
    toks = re.split(r"[\s_\-\.]+", n)
    for i, t in enumerate(toks):
        tl = t.lower()
        if tl in _SIDE_L or tl in _SIDE_R:
            side = "L" if tl in _SIDE_L else "R"
            base = "_".join(toks[:i] + toks[i + 1:]) or n
            return side, base
    return None, n


def merge_side_tokens(canon: pd.DataFrame):
    """Extract the side encoded in a variable name."""
    ren, sides = {}, {}
    for v in canon["variable"].unique():
        s, base = split_side(v)
        if s:
            ren[v], sides[v] = base, s
    if ren:
        side_map = canon["variable"].map(sides)
        declared = canon['side'].astype(str).str.strip().str.lower().map(
            {**{x:'L' for x in _SIDE_L}, **{x:'R' for x in _SIDE_R}})
        conflict = declared.notna() & side_map.notna() & declared.ne(side_map)
        if conflict.any():
            raise ValueError('Lado de columna y variable contradictorios / conflicting side labels.')
        need = canon["side"].eq("—") & side_map.notna()
        canon.loc[need, "side"] = side_map[need]
        canon["variable"] = canon["variable"].replace(ren)
    return canon


def guess_joint(v: str) -> str:
    s = str(v).lower()
    for j, p in [("pelvis", r"pelv"), ("hip", r"hip|cadera|coxo"),
                 ("knee", r"knee|rodil"), ("ankle", r"ankle|tobil|foot|pie|subtal")]:
        if re.search(p, s):
            return j
    return ""


def guess_plane(v: str) -> str:
    s = str(v).lower()
    if re.search(r"rot(?!ul)|transv|footprog|progres|axial", s) or re.search(r"(^|[_\s\-])z$", s):
        return "transverse"
    if re.search(r"front|abd|add|obli|var(?:o|us)|valg|inver|ever|coron", s) or re.search(r"(^|[_\s\-])y$", s):
        return "frontal"
    if re.search(r"sagit|flex|exten|tilt|dorsi|plant", s) or re.search(r"(^|[_\s\-])x$", s):
        return "sagittal"
    return ""


def classify_variables(varnames):
    return pd.DataFrame({
        "variable": list(varnames),
        "joint": [guess_joint(v) for v in varnames],
        "plane": [guess_plane(v) for v in varnames],
    })


# ---------------------------- canonical constructors ------------------------
CANON_COLS = ["subject", "group", "condition", "side", "variable", "node", "value"]


def validate_subject_column(df, roles):
    used = [v for k, v in roles.items() if isinstance(v, str) and v and k != 'covariates']
    if len(used) != len(set(used)):
        raise ValueError('Una columna no puede tener varios roles / columns must have unique roles.')
    if any(v not in df.columns for v in used):
        raise ValueError('Columna de mapeo inexistente / mapping column missing.')
    col = roles.get("subject")
    if col not in df or df[col].isna().any() or df[col].astype(str).str.strip().eq("").any():
        raise ValueError("ID de sujeto obligatorio y no vacío / nonempty subject ID required.")


def validate_analysis(canon, varmap, cfg):
    if len(varmap) == 0 or varmap.variable.duplicated().any():
        raise ValueError("Selecciona variables únicas / select unique variables.")
    mapped = varmap[varmap.joint.ne("") & varmap.plane.ne("")]
    if len(mapped) != len(varmap):
        raise ValueError("Mapea articulación y plano de todas las variables / map every selected variable.")
    if mapped.duplicated(["joint", "plane"]).any():
        raise ValueError("Mapeo articulación/plano duplicado / duplicate joint-plane mapping.")
    if canonical_quality(canon)["subject_group_collisions"]:
        raise ValueError("ID compartido entre grupos / subject ID occurs in multiple groups.")
    if not 0 < float(cfg["alpha"]) < 1:
        raise ValueError("alpha must lie between 0 and 1.")
    if cfg.get("field_correction", "bonferroni") not in ("none", "bonferroni"):
        raise ValueError("Use Bonferroni or none; Holm/FDR cluster-minimum adjustment was removed.")
    d = cfg["design"]
    if d not in DESIGNS or cfg.get('mode') not in ('param', 'nonparam', 'auto'):
        raise ValueError('Diseño o modo inválido / invalid design or mode.')
    if cfg.get('side_mode', 'mean') not in ('mean', 'L', 'R'):
        raise ValueError('Modo de lado inválido / invalid side mode.')
    if not set(varmap.variable.astype(str)).issubset(set(canon.variable.astype(str))):
        raise ValueError('Variable ausente / missing variable.')
    if not varmap.joint.isin(JOINT_ORDER).all() or not varmap.plane.isin(PLANE_ORDER).all():
        raise ValueError('Articulación/plano inválidos / invalid joint or plane.')
    if d == 'paired_side' and (not cfg.get('side_levels') or len(set(cfg['side_levels'])) != 2):
        raise ValueError('Selecciona dos lados distintos / select two distinct sides.')
    if cfg.get('group_filter') is not None and str(cfg['group_filter']) not in set(canon.group.astype(str)):
        raise ValueError('Grupo de filtro ausente / filter group missing.')
    levels = cfg.get("groups") if d in ("ttest2", "anova1") else cfg.get("cond_levels")
    if d in ("ttest2", "paired_cond") and (not levels or len(set(levels)) != 2):
        raise ValueError("Este diseño requiere dos niveles distintos / two distinct levels required.")
    if d in ("anova1", "anova1rm") and (not levels or len(set(levels)) < 3):
        raise ValueError("ANOVA requiere al menos tres niveles / at least three levels required.")
    if d in ("ttest2", "anova1", "regress", "paired_side") and cfg.get("cond") is None and canon.condition.nunique() > 1:
        raise ValueError("Selecciona una condición / select one condition.")


def _finalize_canon(canon: pd.DataFrame):
    canon = canon.copy()
    if canon.empty:
        raise ValueError('No se encontraron curvas / no curves found.')
    # Retain missing values until whole-curve validation; never stitch partial trials.
    canon.loc[~np.isfinite(canon['value']), 'value'] = np.nan
    sides = canon['side'].astype(str).str.strip().str.lower()
    canon.loc[sides.isin(_SIDE_L), 'side'] = 'L'
    canon.loc[sides.isin(_SIDE_R), 'side'] = 'R' 
    canon["node"] = canon["node"].astype(np.int16)
    for c in ["subject", "group", "condition", "side", "variable"]:
        canon[c] = canon[c].astype("category")
    # average repeated trials (subject/condition/side/variable/node mean)
    canon = (canon.groupby(["subject", "group", "condition", "side", "variable", "node"],
                           observed=True, as_index=False)["value"].agg(lambda x: x.mean() if x.notna().all() else np.nan))
    return canon


def canonical_quality(canon: pd.DataFrame):
    """Quality indicators to review before analysis."""
    keys = ["subject", "group", "condition", "side", "variable"]
    curves = (canon.groupby(keys, observed=True)['node']
              .agg(n_nodes='nunique', node_min='min', node_max='max'))
    valid = canon[np.isfinite(canon.value)].groupby(keys, observed=True).node.nunique()
    curves['n_nodes'] = valid.reindex(curves.index, fill_value=0)
    complete = ((curves["n_nodes"] == 101) & (curves["node_min"] == 0)
                & (curves["node_max"] == 100))
    groups = canon[["subject", "group"]].drop_duplicates()
    groups = groups[groups["group"].astype(str) != "—"]
    collisions = (groups.assign(subject=groups["subject"].astype(str),
                                group=groups["group"].astype(str))
                  .groupby("subject")["group"].nunique())
    collision_ids = collisions[collisions > 1].index.tolist()
    return {
        "curves": int(len(curves)),
        "complete_curves": int(complete.sum()),
        "incomplete_curves": int((~complete).sum()),
        "completeness_pct": float(100 * complete.mean()) if len(complete) else 0.0,
        "subject_group_collisions": collision_ids,
        "node_range_ok": bool(len(curves) and (curves["node_min"].min() == 0)
                              and (curves["node_max"].max() == 100)),
    }


def _covariate_meta(df, roles, exclude_cols):
    cov_cols = []
    for c in df.columns:
        if c in exclude_cols or c in roles.values():
            continue
        v = _to_numeric(df[c], errors="coerce")
        if v.notna().mean() > 0.8 and v.nunique() > 1:
            cov_cols.append(c)
    subj = _clean_series(df[roles["subject"]])
    meta = pd.DataFrame({"subject": subj})
    for r in ["group", "condition", "side"]:
        meta[r] = _clean_series(df[roles[r]]) if roles.get(r) else "—"
    for c in cov_cols:
        meta[c] = _to_numeric(df[c], errors="coerce")
    keys = ["subject", "group", "condition", "side"]
    if cov_cols and (meta.groupby(keys, observed=True)[cov_cols].nunique() > 1).any().any():
        raise ValueError('Conflicting covariate values within participant/condition/side.')
    meta = meta.groupby(keys, as_index=False).mean(numeric_only=True)
    return meta, cov_cols


def canon_from_wide(df: pd.DataFrame, blocks: dict, roles: dict):
    validate_subject_column(df, roles)
    key_cols = [roles[r] for r in ("subject", "group", "condition", "side", "trial") if roles.get(r)]
    if df.duplicated(key_cols).any():
        raise ValueError("Filas de sujeto repetidas: usa formato largo con trial / duplicate subject rows; use long format with trial IDs.")
    curve_cols = {c for items in blocks.values() for _, c in items}
    n = len(df)

    def role_arr(role, default="—"):
        c = roles.get(role)
        if c and c in df.columns:
            return _clean_series(df[c], default).to_numpy(dtype=object)
        return np.array([default] * n, dtype=object)

    subj = role_arr("subject", "S1")
    grp, cond, side = role_arr("group"), role_arr("condition"), role_arr("side")
    frames = []
    for var, items in blocks.items():
        idxs = np.array([i for i, _ in items], float)
        cols = [c for _, c in items]
        M = df[cols].apply(_to_numeric, errors="coerce").to_numpy(float)
        M101 = resample_rows(idxs, M)
        frames.append(pd.DataFrame({
            "subject": np.repeat(subj, 101), "group": np.repeat(grp, 101),
            "condition": np.repeat(cond, 101), "side": np.repeat(side, 101),
            "variable": var, "node": np.tile(NODES, n), "value": M101.ravel(),
        }))
    canon = merge_side_tokens(pd.concat(frames, ignore_index=True))
    meta, covs = _covariate_meta(df, roles, curve_cols)
    return _finalize_canon(canon), meta, covs


def canon_from_long(df: pd.DataFrame, roles: dict):
    validate_subject_column(df, roles)
    r = roles
    base = pd.DataFrame({
        "subject": _clean_series(df[r["subject"]], "S1"),
        "group": _clean_series(df[r["group"]]) if r.get("group") else "—",
        "condition": _clean_series(df[r["condition"]]) if r.get("condition") else "—",
        "side": _clean_series(df[r["side"]]) if r.get("side") else "—",
        "trial": _clean_series(df[r["trial"]]) if r.get("trial") else "—",
        "node_raw": _to_numeric(df[r["node"]], errors="coerce"),
        "value": _to_numeric(df[r["value"]], errors="coerce"),
    })
    if r.get("variable"):
        base["variable"] = _clean_series(df[r["variable"]], "var")
    else:
        base["variable"] = (_clean_series(df[r["joint"]], "") + "_" + _clean_series(df[r["plane"]], ""))
    keys = ["subject", "group", "condition", "side", "variable", "trial"]

    def _res(g):
        return pd.Series(resample1(g["node_raw"].to_numpy(), g["value"].to_numpy()))

    W = base.groupby(keys, observed=True).apply(_res, include_groups=False)
    W.columns = NODES
    canon = W.reset_index().melt(id_vars=keys, var_name="node", value_name="value").drop(columns=["trial"])
    canon = merge_side_tokens(canon)
    cov_sel = r.get("covariates") or []
    roles_flat = {k: v for k, v in r.items() if isinstance(v, str)}
    meta_src = df[[c for c in {r["subject"], *(roles_flat.get(k) for k in ("group", "condition", "side") if roles_flat.get(k)), *cov_sel} if c in df.columns]].copy()
    meta, covs = _covariate_meta(meta_src, roles_flat, exclude_cols=set())
    covs = [c for c in covs if (not cov_sel) or c in cov_sel]
    return _finalize_canon(canon), meta, covs


def canon_from_transposed(df: pd.DataFrame, node_col: str, delim: str, token_roles: dict):
    assigned = [r for r in token_roles.values() if r not in ('variable','ignorar')]
    if len(assigned) != len(set(assigned)):
        raise ValueError('Roles de tokens duplicados / duplicate token roles.')
    if node_col not in df or any(i < 0 for i in token_roles):
        raise ValueError('Mapeo transpuesto inválido / invalid transposed mapping.')
    if "subject" not in token_roles.values():
        raise ValueError("Mapea el token subject / subject token is required.")
    """token_roles: {posición(int): 'variable'|'subject'|'side'|'condition'|'group'|'ignorar'}"""
    node_raw = _to_numeric(df[node_col], errors="coerce").to_numpy()
    frames = []
    for c in df.columns:
        if c == node_col:
            continue
        toks = re.split(re.escape(delim) if delim else r"[\s_\-\.]+", str(c).strip())
        for i, role in token_roles.items():
            if role not in ('variable','ignorar') and (i >= len(toks) or not toks[i].strip()):
                raise ValueError('Falta un token de identidad / missing identity token: '+str(c))
        rec = {"subject": "S1", "group": "—", "condition": "—", "side": "—", "variable": str(c)}
        vparts = []
        for i, t in enumerate(toks):
            role = token_roles.get(i, "variable")
            if role == "variable":
                vparts.append(t)
            elif role in ("subject", "group", "condition", "side"):
                rec[role] = t
        if vparts:
            rec["variable"] = "_".join(vparts)
        y = resample1(node_raw, _to_numeric(df[c], errors="coerce").to_numpy())
        frames.append(pd.DataFrame({**{k: [v] * 101 for k, v in rec.items()},
                                    "node": NODES, "value": y}))
    canon = merge_side_tokens(pd.concat(frames, ignore_index=True))
    meta = canon[["subject", "group", "condition", "side"]].drop_duplicates().reset_index(drop=True)
    return _finalize_canon(canon), meta, []


# ----------------------------------------------------------------------------
# Statistical engine (spm1d)
# ----------------------------------------------------------------------------
def _subject_curves(canon, variable, cond=None, group=None, side_mode="mean", side=None):
    d = canon[canon["variable"].astype(str) == str(variable)]
    if cond is not None:
        d = d[d["condition"].astype(str) == str(cond)]
    if group is not None:
        d = d[d["group"].astype(str) == str(group)]
    d = d.copy()
    if side is not None:
        d = d[d["side"].astype(str) == str(side)]
        d["_s"] = d["subject"].astype(str)
    elif side_mode in ("L", "R"):
        d = d[d["side"].astype(str) == side_mode]
        d["_s"] = d["subject"].astype(str)
    elif side_mode == "obs":
        raise ValueError("L/R no son sujetos independientes / L/R are not independent subjects.")
    else:  # 'mean'
        d["_s"] = d["subject"].astype(str)
    # Remove the entire subject if any selected limb has a missing node. Otherwise
    # complementary L/R gaps could create a falsely complete averaged curve.
    by_limb = d.groupby(['_s', 'side'], observed=True).apply(
        lambda g: g.loc[np.isfinite(g.value), 'node'].nunique() == 101, include_groups=False)
    bad_ids = set(by_limb[~by_limb].index.get_level_values(0))
    P = d.pivot_table(index="_s", columns="node", values="value", aggfunc="mean").reindex(columns=NODES)
    if bad_ids:
        P.loc[P.index.isin(bad_ids), :] = np.nan
    complete = np.isfinite(P).all(axis=1)
    dropped = list(P.index[~complete])
    P = P[complete]
    return list(P.index), P.to_numpy(float), dropped


def prepare_between(canon, variable, groups_sel, cond, side_mode):
    out, dropped = [], []
    for g in groups_sel:
        s, Y, dr = _subject_curves(canon, variable, cond=cond, group=g, side_mode=side_mode)
        out.append({"label": str(g), "subjects": s, "Y": Y})
        dropped += dr
    return out, dropped


def prepare_levels(canon, variable, factor, levels, cond, group, side_mode):
    """Align shared participants across paired levels (condition or side)."""
    mats = {}
    for lv in levels:
        if factor == "condition":
            s, Y, _ = _subject_curves(canon, variable, cond=lv, group=group, side_mode=side_mode)
        else:  # side
            s, Y, _ = _subject_curves(canon, variable, cond=cond, group=group, side=lv)
        mats[lv] = (dict(zip(s, range(len(s)))), Y)
    common = [s for s in mats[levels[0]][0] if all(s in mats[lv][0] for lv in levels[1:])]
    Ys = [mats[lv][1][[mats[lv][0][s] for s in common]] for lv in levels]
    return common, Ys


def prepare_regress(canon, meta, variable, cov, cond, group, side_mode):
    s, Y, _ = _subject_curves(canon, variable, cond=cond, group=group, side_mode=side_mode)
    mm = meta.copy()
    if cov not in mm:
        raise ValueError('Covariable ausente / missing covariate.')
    if group is not None and 'group' in mm:
        mm = mm[mm['group'].astype(str).eq(str(group))]
    if side_mode in ('L', 'R') and 'side' in mm:
        mm = mm[mm['side'].astype(str).eq(side_mode)]
    mm["subject"] = mm["subject"].astype(str)
    if cond is not None and "condition" in mm.columns:
        sub = mm[mm["condition"].astype(str) == str(cond)]
        mm = sub
    if (mm.groupby('subject')[cov].nunique() > 1).any():
        raise ValueError('Covariable cambia dentro del sujeto seleccionado / covariate varies within subject.')
    xmap = mm.groupby("subject")[cov].mean()
    x = np.array([xmap.get(si, np.nan) for si in s], float)
    ok = np.isfinite(x)
    return [si for si, o in zip(s, ok) if o], Y[ok], x[ok]


def _np_infer(snpm, alpha, two_tailed=None, iterations=5000, seed=2026):
    import threading
    lock = globals().setdefault("_PERMUTATION_LOCK", threading.RLock())
    iterations = int(iterations)
    if not 10 <= iterations <= 50000:
        raise ValueError("Permutaciones / permutations: 10–50000.")
    unique = getattr(snpm, "nPermUnique", -1)
    actual = min(iterations, unique) if unique > 0 else iterations
    if actual < np.ceil(1 / alpha):
        raise ValueError("Resolución insuficiente de permutaciones para α / insufficient permutation resolution for alpha.")
    kw = {"iterations": -1 if 0 < unique <= iterations else iterations,
          "force_iterations": actual > 10000}
    if two_tailed is not None:
        kw["two_tailed"] = bool(two_tailed)
    with lock:
        state = np.random.get_state()
        try:
            np.random.seed(int(seed))
            result = snpm.inference(alpha, **kw)
            result.gaitspm_iterations_actual = int(actual)
            return result
        finally:
            np.random.set_state(state)


def extract_clusters(spmi, z):
    cl = []
    for c in (getattr(spmi, "clusters", None) or []):
        try:
            x0, x1 = float(c.endpoints[0]), float(c.endpoints[1])
        except Exception:
            continue
        i0, i1 = int(max(0, np.floor(x0))), int(min(100, np.ceil(x1)))
        seg = z[i0:i1 + 1]
        if seg.size:
            ip = int(np.argmax(np.abs(seg)))
            peak, xpeak = float(seg[ip]), i0 + ip
        else:
            peak, xpeak = float("nan"), i0
        cl.append({"p": float(getattr(c, "P", np.nan)), "x0": x0, "x1": x1,
                   "peak": peak, "xpeak": xpeak, "sign": int(np.sign(peak)) if np.isfinite(peak) else 1})
    cl.sort(key=lambda d: d["x0"])
    return cl


# --------------------------- effect sizes ------------------------------
def cohens_d_ind(YA, YB):
    nA, nB = len(YA), len(YB)
    sp = np.sqrt(((nA - 1) * YA.std(0, ddof=1) ** 2 + (nB - 1) * YB.std(0, ddof=1) ** 2) / (nA + nB - 2))
    with np.errstate(divide="ignore", invalid="ignore"):
        return (YA.mean(0) - YB.mean(0)) / sp


def cohens_dz(D):
    with np.errstate(divide="ignore", invalid="ignore"):
        return D.mean(0) / D.std(0, ddof=1)


def r_curve(Y, x):
    xc = x - x.mean()
    Yc = Y - Y.mean(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (Yc * xc[:, None]).sum(0) / (np.sqrt((xc ** 2).sum()) * np.sqrt((Yc ** 2).sum(0)))


def eta2_curve(Ys):
    allY = np.vstack(Ys)
    grand = allY.mean(0)
    ssb = np.sum([len(Y) * (Y.mean(0) - grand) ** 2 for Y in Ys], axis=0)
    sst = ((allY - grand) ** 2).sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        return ssb / sst


def eta2p_rm_curve(Ys):
    """Nodewise partial eta squared for a one-way within-subject design.

    ``Ys`` contains one participants×nodes matrix per condition and must be
    aligned by participant. The denominator excludes stable between-subject
    variability: SS_condition / (SS_condition + SS_error).
    """
    X = np.stack(Ys, axis=1)  # sujetos × condiciones × nodos
    grand = X.mean(axis=(0, 1), keepdims=True)
    cond_mean = X.mean(axis=0, keepdims=True)
    subj_mean = X.mean(axis=1, keepdims=True)
    ss_condition = X.shape[0] * ((cond_mean - grand) ** 2).sum(axis=1).squeeze(0)
    resid = X - cond_mean - subj_mean + grand
    ss_error = (resid ** 2).sum(axis=(0, 1))
    with np.errstate(divide="ignore", invalid="ignore"):
        return ss_condition / (ss_condition + ss_error)


def rm_model_residuals(Ys):
    """RM model residuals after removing condition and participant effects."""
    X = np.stack(Ys, axis=1)
    grand = X.mean(axis=(0, 1), keepdims=True)
    cond_mean = X.mean(axis=0, keepdims=True)
    subj_mean = X.mean(axis=1, keepdims=True)
    return (X - cond_mean - subj_mean + grand).reshape(-1, X.shape[-1])


def normality_pct(res_matrix):
    R = res_matrix[np.isfinite(res_matrix).all(axis=1)]
    if R.shape[0] < 8:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        p = sps.normaltest(R, axis=0).pvalue
    return float(np.mean(p < 0.05) * 100)


def decide_mode(cfg, npct, nmin, warns):
    if cfg["mode"] == "param":
        return "param"
    if cfg["mode"] == "nonparam":
        return "nonparam"
    if nmin < 8:
        warns.append("n < 8: se aplica SnPM no paramétrico (permutaciones).")
        return "nonparam"
    cutoff = float(cfg.get("auto_normality_cutoff", 20))
    if npct is not None and npct > cutoff:
        warns.append(f"Normalidad dudosa en {npct:.0f}% de nodos (D'Agostino-Pearson; "
                     f"regla exploratoria >{cutoff:g}%): se aplica SnPM.")
        return "nonparam"
    return "param"


def _df_str(spm_obj, spmi, mode, iterations):
    if mode == "param":
        df = getattr(spm_obj, "df", None) or getattr(spmi, "df", None)
        if df is not None:
            return "gl = (" + ", ".join(f"{d:g}" for d in np.atleast_1d(df)) + ")"
        return ""
    n = getattr(spmi, "gaitspm_iterations_actual", None) or getattr(spmi, "nPerm", None) or iterations
    return f"{int(n)} permutaciones"


def _summ(label, Y):
    return {"label": str(label), "n": int(len(Y)), "mean": Y.mean(0), "sd": Y.std(0, ddof=1)}


# ------------------------------- analysis ------------------------------------
ADVANCED_DESIGNS = ("ancova", "glm", "anova2", "anova2onerm")


def prepare_model(canon, meta, variable, cfg):
    """Build explicit subject-aligned inputs; never use metadata row order."""
    design = cfg['design']
    side = cfg.get('side_mode', 'mean')
    if design in ('ancova', 'glm'):
        covs = cfg.get('covariates') or [cfg.get('covariate')]
        if not covs or any(not c for c in covs) or len(set(covs)) != len(covs):
            raise ValueError('Select unique numeric covariates / selecciona covariables únicas.')
        data = canon
        if design == 'ancova':
            levels = cfg.get('groups') or []
            if len(levels) != 2 or len(set(levels)) != 2:
                raise ValueError('ANCOVA requires exactly two groups.')
            data = canon[canon.group.astype(str).isin(levels)]
        ids, Y, _ = _subject_curves(data, variable, cond=cfg.get('cond'),
                                  group=cfg.get('group_filter'), side_mode=side)
        aligned = []
        for cov in covs:
            subs, _, x = prepare_regress(data, meta, variable, cov, cfg.get('cond'),
                                        cfg.get('group_filter'), side)
            aligned.append(dict(zip(subs, x)))
        keep = [i for i, sub in enumerate(ids) if all(sub in a for a in aligned)]
        ids, Y = [ids[i] for i in keep], Y[keep]
        columns, names = [np.ones(len(ids))], ['intercept']
        if design == 'ancova':
            membership = data.groupby('subject', observed=True).group.first().to_dict()
            g = np.array([str(membership[sub]) == str(levels[1]) for sub in ids], float)
            if min(np.sum(g == 0), np.sum(g == 1)) < 3:
                raise ValueError('ANCOVA requires at least three complete subjects per group.')
            columns.append(g); names.append(str(levels[1]) + ' - ' + str(levels[0]))
        for cov, a in zip(covs, aligned):
            x = np.array([a[sub] for sub in ids], float)
            columns.append(x - x.mean() if len(x) else x); names.append(cov + ' (centered)')
        X = np.column_stack(columns)
        contrast = np.asarray(([0, 1] + [0]*len(covs)) if design == 'ancova'
                              else cfg.get('contrast', []), dtype=float)
        if contrast.shape != (X.shape[1],) or not np.isfinite(contrast).all() or not np.any(contrast):
            raise ValueError('Contrast must be finite, nonzero and match [intercept, predictors].')
        if len(Y) <= X.shape[1] + 1 or np.linalg.matrix_rank(X) != X.shape[1]:
            raise ValueError('Rank-deficient model or insufficient residual degrees of freedom.')
        return dict(Y=Y, X=X, contrast=contrast, subjects=ids, columns=names)
    levels, conditions = cfg.get('groups') or [], cfg.get('cond_levels') or []
    if len(set(levels)) < 2 or len(set(conditions)) < 2 or len(set(levels)) != len(levels) or len(set(conditions)) != len(conditions):
        raise ValueError('Two distinct groups and conditions are required (or more).')
    mats, aa, bb, subjects, summaries, sizes = [], [], [], [], [], []
    for a, group in enumerate(levels):
        if design == 'anova2onerm':
            ids, Ys = prepare_levels(canon, variable, 'condition', conditions, None, group, side)
            cells = [(ids, y) for y in Ys]
        else:
            cells = [_subject_curves(canon, variable, cond=c, group=group, side_mode=side)[:2]
                     for c in conditions]
        for b, (ids, Y) in enumerate(cells):
            if len(ids) < 3:
                raise ValueError('Every cell requires at least three complete subjects.')
            mats.append(Y); sizes.append(len(Y)); subjects.extend(ids)
            aa.extend([a]*len(Y)); bb.extend([b]*len(Y))
            summaries.append(_summ(str(group) + ' / ' + str(conditions[b]), Y))
    if len(set(sizes)) != 1:
        raise ValueError('This release requires balanced two-way designs after complete-case exclusion.')
    if design == 'anova2' and len(set(subjects)) != len(subjects):
        raise ValueError('Repeated subject IDs: use mixed ANOVA / usa ANOVA mixto.')
    subject_codes = {sub: i for i, sub in enumerate(sorted(set(subjects)))}
    return dict(Y=np.vstack(mats), A=np.array(aa), B=np.array(bb),
                SUBJ=np.array([subject_codes[sub] for sub in subjects]),
                subjects=sorted(set(subjects)), summaries=summaries)



def infer_model_fields(model, cfg, effects=None):
    """Shared production inference for prepared models (also used by simulations).

    This does not replace participant alignment or model validation in prepare_model.
    Factorial families always contain three effects, including when only one is shown.
    """
    design = cfg['design']
    if design not in ADVANCED_DESIGNS or cfg.get('mode') != 'param' or not cfg.get('equal_var', True):
        raise ValueError('Advanced designs require parametric inference and equal variance.')
    factorial = design in ('anova2', 'anova2onerm')
    names = ('group', 'condition', 'interaction') if factorial else ('contrast',)
    selected = names if effects is None else tuple(effects)
    if not selected or any(e not in names for e in selected):
        raise ValueError('Unknown model effect.')
    method = cfg.get('field_correction', 'bonferroni')
    if method not in ('none', 'bonferroni'):
        raise ValueError('Use Bonferroni or none.')
    m = max(1, int(cfg.get('field_count', 1))) if method == 'bonferroni' else 1
    alpha = float(cfg['alpha']) / (m * len(names))
    if factorial:
        args = [model['Y'], model['A'], model['B']]
        if design == 'anova2onerm':
            args.append(model['SUBJ'])
        fields = dict(zip(names, getattr(spm1d.stats, design)(*args, equal_var=True)))
    else:
        fields = {'contrast': spm1d.stats.glm(model['Y'], model['X'], model['contrast'])}
    inferred = {}
    for name in selected:
        field = fields[name]
        inference = field.inference(alpha, interp=True, **({} if factorial else {'two_tailed': bool(cfg['two_tailed'])}))
        inferred[name] = (field, inference)
    return inferred, alpha, len(names)


def run_model(canon, meta, vrow, cfg):
    design = cfg['design']
    if cfg.get('mode') != 'param' or not cfg.get('equal_var', True):
        raise ValueError('Advanced designs require parametric inference and equal variance.')
    if design in ('ancova', 'glm') and cfg.get('cond') is None and canon.condition.nunique() > 1:
        raise ValueError('Select one condition for independent GLM/ANCOVA observations.')
    model = prepare_model(canon, meta, vrow['variable'], cfg)
    Y = model['Y']
    factorial = design in ('anova2', 'anova2onerm')
    effect = cfg.get('factor_effect', 'interaction')
    if factorial and effect not in ('group', 'condition', 'interaction'):
        raise ValueError('Select group, condition or interaction.')
    m = max(1, int(cfg.get('field_count', 1))) if cfg.get('field_correction', 'bonferroni') == 'bonferroni' else 1
    inferred, alpha, effect_count = infer_model_fields(model, cfg, [effect if factorial else 'contrast'])
    spm, spmi = inferred[effect if factorial else 'contrast']
    if factorial:
        plot = dict(type='groups', groups=model['summaries'])
        detail = dict(effect=effect, groups=cfg['groups'], conditions=cfg['cond_levels'])
    else:
        plot = dict(type='groups', groups=[_summ('Complete cases (unadjusted)', Y)])
        detail = dict(columns=model['columns'], contrast=model['contrast'].tolist(),
                      design_matrix=model['X'].tolist())
    z = np.asarray(spmi.z, float)
    if not np.isfinite(z).all(): raise ValueError('Nonfinite model statistic.')
    eligible = canon[canon.variable.astype(str).eq(str(vrow['variable']))]
    if cfg.get('groups') and design != 'glm': eligible = eligible[eligible.group.astype(str).isin(cfg['groups'])]
    if cfg.get('group_filter'): eligible = eligible[eligible.group.astype(str).eq(str(cfg['group_filter']))]
    if factorial: eligible = eligible[eligible.condition.astype(str).isin(cfg['cond_levels'])]
    elif cfg.get('cond') is not None: eligible = eligible[eligible.condition.astype(str).eq(str(cfg['cond']))]
    excluded = sorted(set(eligible.subject.astype(str)) - set(model['subjects']))
    warns = ['Equal variance assumed; parametric inference only.']
    if factorial: warns.append('Bonferroni across all three factorial effects (alpha/3), in addition to across-variable correction.')
    if design == 'anova2onerm': warns.append('Sphericity assumed; no nonsphericity correction. One averaged response per subject/condition; spm1d approximate residuals may apply.')
    if design == 'ancova': warns.append('Common covariate slopes assumed; contrast is second group minus first. Mean plot is unadjusted.')
    if excluded: warns.append('Complete-case exclusions: ' + ', '.join(excluded))
    return dict(variable=vrow['variable'], joint=vrow['joint'], plane=vrow['plane'], design=design,
                two_tailed=False if factorial else bool(cfg['two_tailed']), alpha=alpha,
                family_alpha=float(cfg['alpha']), field_count=m, effect_count=effect_count,
                posthoc=None, normality_pct=None, test_label='SPM{F} · '+effect if factorial else 'SPM{t} · '+design,
                stat_name='F' if factorial else 't', effect=None, plot=plot,
                direction=None, n_included=len(model['subjects']), excluded_subjects=excluded,
                model={**detail, 'subjects':model['subjects']}, z=z, zstar=float(spmi.zstar),
                h0reject=bool(spmi.h0reject), clusters=extract_clusters(spmi,z), mode_used='param',
                df_str=_df_str(spm,spmi,'param',cfg['iterations']), warnings=warns, seed=None,
                iterations_actual=None)


def run_one(canon, meta, vrow, cfg):
    if cfg["design"] in ADVANCED_DESIGNS:
        return run_model(canon, meta, vrow, cfg)
    method = cfg.get("field_correction", "bonferroni")
    if method not in ("none", "bonferroni"):
        raise ValueError("Selecciona Bonferroni o sin ajuste; Holm/FDR sobre mínimos de clúster se ha retirado.")
    m = max(1, int(cfg.get("field_count", 1))) if method == "bonferroni" else 1
    var = vrow["variable"]
    warns, res = [], {"variable": var, "joint": vrow["joint"], "plane": vrow["plane"],
                      "design": cfg["design"], "two_tailed": bool(cfg["two_tailed"]),
                      "alpha": float(cfg["alpha"]), "posthoc": None, "normality_pct": None}
    design, alpha, tt, it = cfg["design"], cfg["alpha"], cfg["two_tailed"], cfg["iterations"]
    alpha = float(alpha) / m
    res.update(alpha=alpha, family_alpha=float(cfg["alpha"]), field_count=m)
    seed = int(cfg.get("seed", 2026))
    q = canonical_quality(canon[canon.variable.astype(str).eq(str(var))])
    if q["incomplete_curves"]:
        warns.append("Curvas incompletas excluidas; revisa n por grupo / incomplete curves excluded; review group n.")
    if cfg.get("side_mode") == "obs":
        raise ValueError("L y R no pueden tratarse como observaciones independientes. "
                         "Promedia ambos lados o analiza uno de ellos.")

    if design == "ttest2":
        groups, _ = prepare_between(canon, var, cfg["groups"], cfg["cond"], cfg["side_mode"])
        YA, YB = groups[0]["Y"], groups[1]["Y"]
        if min(len(YA), len(YB)) < 3:
            raise ValueError("n insuficiente por grupo (mínimo 3).")
        resid = np.vstack([YA - YA.mean(0), YB - YB.mean(0)])
        res["normality_pct"] = normality_pct(resid)
        mode = decide_mode(cfg, res["normality_pct"], min(len(YA), len(YB)), warns)
        if mode == "param":
            spm = spm1d.stats.ttest2(YA, YB, equal_var=cfg["equal_var"])
            spmi = spm.inference(alpha, two_tailed=tt, interp=True)
        else:
            spm = spm1d.stats.nonparam.ttest2(YA, YB)
            spmi = _np_infer(spm, alpha, two_tailed=tt, iterations=it, seed=seed)
        res.update(test_label="SPM{t}", stat_name="t",
                   effect={"name": "d", "curve": cohens_d_ind(YA, YB)},
                   plot={"type": "groups", "groups": [_summ(g["label"], g["Y"]) for g in groups]},
                   direction=(groups[0]["label"], groups[1]["label"]))

    elif design in ("paired_cond", "paired_side"):
        factor = "condition" if design == "paired_cond" else "side"
        levels = cfg["cond_levels"] if factor == "condition" else cfg["side_levels"]
        common, Ys = prepare_levels(canon, var, factor, levels,
                                    cond=cfg.get("cond"), group=cfg.get("group_filter"),
                                    side_mode=cfg["side_mode"])
        YA, YB = Ys
        if len(common) < 3:
            raise ValueError("menos de 3 sujetos con datos pareados completos.")
        D = YA - YB
        resid = D - D.mean(0)
        res["normality_pct"] = normality_pct(resid)
        mode = decide_mode(cfg, res["normality_pct"], len(common), warns)
        if mode == "param":
            spm = spm1d.stats.ttest_paired(YA, YB)
            spmi = spm.inference(alpha, two_tailed=tt, interp=True)
        else:
            spm = spm1d.stats.nonparam.ttest_paired(YA, YB)
            spmi = _np_infer(spm, alpha, two_tailed=tt, iterations=it, seed=seed)
        res.update(test_label="SPM{t}", stat_name="t",
                   effect={"name": "dz", "curve": cohens_dz(D)},
                   plot={"type": "groups", "groups": [_summ(levels[0], YA), _summ(levels[1], YB)]},
                   direction=(str(levels[0]), str(levels[1])), n_paired=len(common))

    elif design in ("anova1", "anova1rm"):
        tt = False
        res["two_tailed"] = False
        if design == "anova1":
            levels = cfg["groups"]
            groups, _ = prepare_between(canon, var, levels, cfg["cond"], cfg["side_mode"])
            Ys = [g["Y"] for g in groups]
            labels = [g["label"] for g in groups]
        else:
            levels = cfg["cond_levels"]
            common, Ys = prepare_levels(canon, var, "condition", levels,
                                        cond=None, group=cfg.get("group_filter"),
                                        side_mode=cfg["side_mode"])
            labels = [str(l) for l in levels]
            if len(common) < 3:
                raise ValueError("menos de 3 sujetos completos en todas las condiciones.")
            res["n_paired"] = len(common)
        if min(len(Y) for Y in Ys) < 3:
            raise ValueError("n insuficiente por nivel (mínimo 3).")
        Yst = np.vstack(Ys)
        A = np.concatenate([np.full(len(Y), i) for i, Y in enumerate(Ys)])
        resid = (np.vstack([Y - Y.mean(0) for Y in Ys])
                 if design == "anova1" else rm_model_residuals(Ys))
        res["normality_pct"] = normality_pct(resid)
        mode = decide_mode(cfg, res["normality_pct"], min(len(Y) for Y in Ys), warns)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if design == "anova1":
                if mode == "param":
                    spm = spm1d.stats.anova1(Yst, A, equal_var=cfg["equal_var"])
                    spmi = spm.inference(alpha, interp=True)
                else:
                    spm = spm1d.stats.nonparam.anova1(Yst, A)
                    spmi = _np_infer(spm, alpha, iterations=it, seed=seed)
            else:
                SUBJ = np.tile(np.arange(len(Ys[0])), len(Ys))
                if mode == "param":
                    spm = spm1d.stats.anova1rm(Yst, A, SUBJ)
                    spmi = spm.inference(alpha, interp=True)
                else:
                    spm = spm1d.stats.nonparam.anova1rm(Yst, A, SUBJ)
                    spmi = _np_infer(spm, alpha, iterations=it, seed=seed)
        res.update(test_label="SPM{F}", stat_name="F",
                   effect={"name": "eta2" if design == "anova1" else "eta2p",
                           "curve": eta2_curve(Ys) if design == "anova1" else eta2p_rm_curve(Ys)},
                   plot={"type": "groups", "groups": [_summ(l, Y) for l, Y in zip(labels, Ys)]},
                   direction=None)
        # pairwise post hoc (Bonferroni)
        if cfg.get("posthoc", True) and bool(spmi.h0reject):
            pairs = list(itertools.combinations(range(len(labels)), 2))
            a_adj = alpha / len(pairs)
            ph = []
            for i, j in pairs:
                try:
                    if design == "anova1":
                        if mode == "param":
                            s2 = spm1d.stats.ttest2(Ys[i], Ys[j], equal_var=cfg["equal_var"])
                            s2i = s2.inference(a_adj, two_tailed=True, interp=True)
                        else:
                            s2 = spm1d.stats.nonparam.ttest2(Ys[i], Ys[j])
                            s2i = _np_infer(s2, a_adj, two_tailed=True, iterations=it, seed=seed + i * 101 + j)
                    else:
                        if mode == "param":
                            s2 = spm1d.stats.ttest_paired(Ys[i], Ys[j])
                            s2i = s2.inference(a_adj, two_tailed=True, interp=True)
                        else:
                            s2 = spm1d.stats.nonparam.ttest_paired(Ys[i], Ys[j])
                            s2i = _np_infer(s2, a_adj, two_tailed=True, iterations=it, seed=seed + i * 101 + j)
                    z2 = np.asarray(s2i.z, float)
                    ph.append({"label": f"{labels[i]} vs {labels[j]}", "alpha": a_adj,
                               "zstar": float(s2i.zstar), "z": z2,
                               "clusters": extract_clusters(s2i, z2),
                               "h0reject": bool(s2i.h0reject),
                               "pair": (labels[i], labels[j])})
                except Exception as e:  # pragma: no cover
                    ph.append({"label": f"{labels[i]} vs {labels[j]}", "error": str(e)})
            res["posthoc"] = {"alpha_adj": a_adj, "pairs": ph}

    elif design == "regress":
        subs, Y, x = prepare_regress(canon, meta, var, cfg["covariate"],
                                     cfg["cond"], cfg.get("group_filter"), cfg["side_mode"])
        if len(x) < 5:
            raise ValueError("menos de 5 sujetos con covariable válida.")
        if np.ptp(x) <= np.finfo(float).eps:
            raise ValueError("Covariable constante / constant covariate.")
        xc = x - x.mean()
        b = (Y * xc[:, None]).sum(0) / (xc ** 2).sum()
        resid = (Y - Y.mean(0)) - np.outer(xc, b)
        res["normality_pct"] = normality_pct(resid)
        mode = decide_mode(cfg, res["normality_pct"], len(x), warns)
        if mode == "param":
            spm = spm1d.stats.regress(Y, x)
            spmi = spm.inference(alpha, two_tailed=tt, interp=True)
        else:
            spm = spm1d.stats.nonparam.regress(Y, x)
            spmi = _np_infer(spm, alpha, two_tailed=tt, iterations=it, seed=seed)
        res.update(test_label="SPM{t}", stat_name="t",
                   effect={"name": "r", "curve": r_curve(Y, x)},
                   plot={"type": "regress", "Y": Y, "x": x, "covname": cfg["covariate"],
                         "mean": Y.mean(0)},
                   direction=("+", "−"), n_paired=len(x))
    else:
        raise ValueError(f"diseño desconocido: {design}")

    z = np.asarray(spmi.z, float)
    if not np.isfinite(z).all():
        raise ValueError("Estadístico no finito: revisa varianza y datos / nonfinite statistic.")
    if design == "anova1rm":
        warns.append("RM-ANOVA: esfericidad asumida, sin corrección / sphericity assumed, uncorrected.")
    if mode == 'nonparam' and design in ('ttest2', 'anova1') and not cfg.get('equal_var', True):
        warns.append('SnPM usa permutaciones de etiquetas, no Welch: requiere intercambiabilidad entre grupos / label-permutation SnPM is not Welch and requires exchangeability.')
    if mode == "nonparam":
        warns.append("SnPM requiere intercambiabilidad válida / SnPM requires valid exchangeability.")
    eligible = canon[canon.variable.astype(str).eq(str(var))]
    if cfg.get('group_filter'):
        eligible = eligible[eligible.group.astype(str).eq(str(cfg['group_filter']))]
    if design in ('paired_cond', 'paired_side', 'anova1rm'):
        included = list(common)
    elif design == 'regress':
        included = list(subs)
    else:
        included = [s for g in groups for s in g['subjects']]
        eligible = eligible[eligible.group.astype(str).isin(cfg.get('groups') or [])]
    if cfg.get('cond') is not None:
        eligible = eligible[eligible.condition.astype(str).eq(str(cfg['cond']))]
    excluded = sorted(set(eligible.subject.astype(str)) - set(included))
    res.update(n_included=len(included), excluded_subjects=excluded)
    if excluded:
        warns.append(f'{len(excluded)} sujetos excluidos por datos incompletos o no emparejados / excluded for incomplete or unmatched data: ' + ', '.join(excluded))
    res.update(z=z, zstar=float(spmi.zstar), h0reject=bool(spmi.h0reject),
               clusters=extract_clusters(spmi, z), mode_used=mode,
               df_str=_df_str(spm, spmi, mode, it), warnings=warns,
               seed=seed if mode == "nonparam" else None,
               iterations_actual=getattr(spmi, "gaitspm_iterations_actual", None))
    return res


def compute_band(canon, var, cfg):
    if cfg["design"] in ADVANCED_DESIGNS:
        return None  # no ambiguous pooled-condition reference band
    if not cfg.get("band_group"):
        return None
    cond = cfg.get("cond") if cfg["design"] in ("ttest2", "anova1", "regress", "paired_side") else None
    _, Yb, _ = _subject_curves(canon, var, cond=cond, group=cfg["band_group"],
                               side_mode=cfg["side_mode"] if cfg["side_mode"] != "obs" else "mean")
    if len(Yb) < 3:
        return None
    return {"mean": Yb.mean(0), "sd": Yb.std(0, ddof=1), "k": float(cfg.get("band_k", 1)),
            "label": str(cfg["band_group"])}


def adjust_pvalues(pvalues, method="holm"):
    """Adjust a family of p-values without external dependencies."""
    p = np.asarray(pvalues, float)
    if method == "none" or len(p) == 0:
        return np.clip(p, 0, 1)
    order = np.argsort(p)
    ps = p[order]
    m = len(ps)
    if method == "holm":
        adj_sorted = np.maximum.accumulate((m - np.arange(m)) * ps)
    elif method == "fdr_bh":
        raw = ps * m / (np.arange(m) + 1)
        adj_sorted = np.minimum.accumulate(raw[::-1])[::-1]
    else:
        raise ValueError(f"corrección entre variables desconocida: {method}")
    out = np.empty_like(adj_sorted)
    out[order] = np.clip(adj_sorted, 0, 1)
    return out


def apply_field_correction(results, cfg):
    """Annotate inference already performed at alpha/m; never recycle an unadjusted threshold."""
    method = cfg.get("field_correction", "bonferroni")
    if method not in ("none", "bonferroni"):
        raise ValueError("Use Bonferroni or none; legacy Holm/FDR cluster-minimum adjustment is unsupported.")
    m = max(1, int(cfg.get("field_count", len(results)))) if method == "bonferroni" else 1
    alpha = float(cfg.get("alpha", .05))
    for res in results.values():
        if "error" in res:
            continue
        factor = m * res.get("effect_count", 1)
        if not np.isclose(res["alpha"], alpha/factor):
            raise ValueError("Reejecuta la inferencia con α/m / rerun inference with alpha/m.")
        res["field_correction"] = method
        for cluster in res.get("clusters", []):
            cluster["p_field_adj"] = float(min(1, factor * cluster["p"]))
        res["field_p_raw"] = min((c["p"] for c in res.get("clusters", [])), default=1.)
        res["field_p_adj"] = min((c["p_field_adj"] for c in res.get("clusters", [])), default=1.)
        res["field_significant"] = bool(confirmed_clusters(res))
        pairs = (res.get("posthoc") or {}).get("pairs", [])
        for pair in pairs:
            for c in pair.get("clusters", []):
                c["p_field_adj"] = float(min(1, m * len(pairs) * c["p"]))
    return results


def confirmed_clusters(res):
    """Clusters retaining significance under the selected familywise inference."""
    if res.get("field_correction", "none") == "none" and res.get("effect_count", 1) == 1:
        return res.get("clusters", [])
    return [c for c in res.get("clusters", [])
            if c.get("p_field_adj", 1) <= res.get("family_alpha", .05)]


def run_analysis(canon, meta, varmap_sel, cfg, progress=None):
    validate_analysis(canon, varmap_sel, cfg)
    cfg["field_count"] = len(varmap_sel)
    results, bands = {}, {}
    rows = varmap_sel.to_dict("records")
    for i, vrow in enumerate(rows):
        var = vrow["variable"]
        try:
            results[var] = run_one(canon, meta, vrow, cfg)
        except Exception as e:
            results[var] = {"variable": var, "joint": vrow["joint"], "plane": vrow["plane"],
                            "error": str(e)}
        try:
            bands[var] = compute_band(canon, var, cfg)
        except Exception:
            bands[var] = None
        if progress:
            progress((i + 1) / len(rows), var)
    return apply_field_correction(results, cfg), bands


# ----------------------------------------------------------------------------
# MATLAB-style figures
# ----------------------------------------------------------------------------
def _safe_plot_color(value, fallback):
    """Devuelve un color Matplotlib válido y evita valores manipulados."""
    return value if isinstance(value, str) and is_color_like(value) else fallback


def _bounded_style_float(value, fallback):
    try:
        return float(np.clip(float(value), 0, 1)) if np.isfinite(float(value)) else float(fallback)
    except (TypeError, ValueError):
        return float(fallback)


def plot_style(cfg=None):
    """Normalize figure options while retaining the default MATLAB styling."""
    cfg = cfg or {}
    supplied = cfg.get("line_colors")
    if not isinstance(supplied, (list, tuple)):
        supplied = MATLAB_HEX
    colors = []
    for i in range(max(len(MATLAB_HEX), len(supplied))):
        fallback = MATLAB_HEX[i % len(MATLAB_HEX)]
        value = supplied[i] if i < len(supplied) else fallback
        colors.append(_safe_plot_color(value, fallback))
    mode = cfg.get("interval_mode", "sd")
    return {
        "line_colors": colors,
        "band_colors": [_safe_plot_color(c, colors[i % len(colors)]) for i, c in enumerate(cfg.get("band_colors") or colors)],
        "reference_band_color": _safe_plot_color(
            cfg.get("reference_band_color"), PLOT_STYLE_DEFAULTS["reference_band_color"]),
        "interval_mode": mode if mode in ("sd", "ci95") else "sd",
        "interval_alpha": _bounded_style_float(
            cfg.get("interval_alpha"), PLOT_STYLE_DEFAULTS["interval_alpha"]),
        "show_interval_edges": bool(cfg.get("show_interval_edges", False)),
        "cluster_fill_color": _safe_plot_color(
            cfg.get("cluster_fill_color"), PLOT_STYLE_DEFAULTS["cluster_fill_color"]),
        "cluster_fill_alpha": _bounded_style_float(
            cfg.get("cluster_fill_alpha"), PLOT_STYLE_DEFAULTS["cluster_fill_alpha"]),
        "show_cluster_bars": bool(cfg.get("show_cluster_bars", False)),
    }


def _interval_halfwidth(group, mode):
    """Band half-width: descriptive SD or 95% confidence interval for the mean."""
    sd = np.asarray(group["sd"], float)
    n = int(group.get("n", 0))
    if mode != "ci95" or n < 2:
        return sd
    return sps.t.ppf(0.975, n - 1) * sd / np.sqrt(n)


def variable_title(res, lang):
    j, p = res.get("joint", ""), res.get("plane", "")
    if j and p:
        return f"{LBL[lang]['joint'].get(j, j)} · {LBL[lang]['plane'].get(p, p)}"
    return str(res.get("variable", ""))


def plot_kin(ax, res, band, lang, show_legend=False, cfg=None):
    T = LBL[lang]
    style = plot_style(cfg)
    if band is not None:
        lo = band["mean"] - band["k"] * band["sd"]
        hi = band["mean"] + band["k"] * band["sd"]
        ax.fill_between(NODES, lo, hi, color=style["reference_band_color"], lw=0, zorder=1,
                        label=f"{T['band']} ({band['label']}, ±{band['k']:g} {'SD' if lang == 'en' else 'DE'})" if show_legend else None)
    pl = res["plot"]
    if pl["type"] == "regress":
        norm = Normalize(vmin=np.min(pl["x"]), vmax=np.max(pl["x"]))
        cmap = plt.get_cmap("viridis")
        for yi, xi in zip(pl["Y"], pl["x"]):
            ax.plot(NODES, yi, color=cmap(norm(xi)), lw=0.7, alpha=0.85, zorder=2)
        ax.plot(NODES, pl["mean"], color=style["line_colors"][0], lw=1.9, zorder=3)
        ax.text(0.985, 0.04, T["cov_note"].format(cov=pl["covname"]), transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7.2, color="0.25")
    else:
        for gi, g in enumerate(pl["groups"]):
            c = style["line_colors"][gi % len(style["line_colors"])]
            bc = style["band_colors"][gi % len(style["band_colors"])]
            half = _interval_halfwidth(g, style["interval_mode"])
            lo, hi = g["mean"] - half, g["mean"] + half
            ax.fill_between(NODES, lo, hi, color=bc, alpha=style["interval_alpha"],
                            lw=0, zorder=2)
            if style["show_interval_edges"]:
                edge_alpha = min(1.0, 0.45 + style["interval_alpha"])
                ax.plot(NODES, lo, color=bc, lw=0.75, alpha=edge_alpha, zorder=2.5)
                ax.plot(NODES, hi, color=bc, lw=0.75, alpha=edge_alpha, zorder=2.5)
            ax.plot(NODES, g["mean"], color=c, lw=1.8, zorder=3,
                    label=f"{g['label']} (n={g['n']})")
    ax.axhline(0, color="0.45", lw=0.6, zorder=1)
    ax.set_xlim(0, 100)
    ax.set_ylabel(T["ylabel"])
    ax.set_title(variable_title(res, lang), pad=4)
    if show_legend and pl["type"] != "regress":
        ax.legend(loc="best", fontsize=7.6)


def plot_spm(ax, res, lang, show_xlabel=True, cfg=None):
    T = LBL[lang]
    style = plot_style(cfg)
    z, zs = res["z"], res["zstar"]
    two = bool(res["two_tailed"])
    ax.plot(NODES, z, color="k", lw=1.4, zorder=3)
    ax.axhline(0, color="0.55", lw=0.6, zorder=1)
    for thr in ([zs, -zs] if two else [zs]):
        ax.axhline(thr, color=THRESH_COLOR, ls="--", lw=1.0, zorder=2)
    ax.fill_between(NODES, zs, np.maximum(z, zs), where=z >= zs,
                    color=style["cluster_fill_color"], alpha=style["cluster_fill_alpha"],
                    lw=0, zorder=2)
    if two:
        ax.fill_between(NODES, -zs, np.minimum(z, -zs), where=z <= -zs,
                        color=style["cluster_fill_color"], alpha=style["cluster_fill_alpha"],
                        lw=0, zorder=2)
    zmax = np.nanmax(np.abs(z)) if np.isfinite(z).any() else zs
    m = max(zmax, zs)
    if two:
        ylo, yhi = -1.35 * m, 1.45 * m
    elif res["stat_name"] == "F":
        ylo, yhi = 0.0, 1.45 * m
    else:
        ylo, yhi = min(-0.15 * m, float(np.nanmin(z)) * 1.1), 1.45 * m
    ax.set_ylim(ylo, yhi)
    rng = yhi - ylo
    for c in res["clusters"]:
        xm = float(np.clip(0.5 * (c["x0"] + c["x1"]), 5, 95))
        up = c["sign"] >= 0
        ytxt = min(c["peak"], yhi - 0.28 * rng) if up else max(c["peak"], ylo + 0.28 * rng)
        ax.annotate(fmt_p(c["p"]), (xm, ytxt), textcoords="offset points",
                    xytext=(0, 3 if up else -3), ha="center",
                    va="bottom" if up else "top", fontsize=7.4, zorder=5,
                    bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
        if style["show_cluster_bars"]:
            lane = 1.08 if up else 1.22
            trans = ax.get_xaxis_transform()
            ax.plot([c["x0"], c["x1"]], [lane, lane], transform=trans,
                    color=style["cluster_fill_color"], lw=3.0, solid_capstyle="butt",
                    zorder=6, clip_on=False)
            ax.plot([c["x0"], c["x1"]], [lane, lane], transform=trans,
                    color=style["cluster_fill_color"], lw=0, marker="|", markersize=6,
                    markeredgewidth=1.2, zorder=6, clip_on=False)
            label_y = lane + 0.025
            ax.text(xm, label_y, f"{c['x0']:.1f}–{c['x1']:.1f} %",
                    transform=trans, ha="center", va="bottom",
                    fontsize=6.4, color=style["cluster_fill_color"], zorder=6,
                    bbox=dict(fc="white", ec="none", alpha=0.82, pad=0.4))
    ax.text(0.02, 0.97, f"{res['stat_name']}* = {zs:.2f}", transform=ax.transAxes,
            fontsize=7.2, va="top", color="0.2", zorder=5,
            bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
    if res.get("field_correction", "none") != "none" or res.get("effect_count", 1) > 1:
        denominator = "3m" if res.get("effect_count", 1) > 1 else "m"
        ax.text(0.98, 0.97, f"α / {denominator} = {res['alpha']:.4f}",
                transform=ax.transAxes, fontsize=7.0, va="top", ha="right", color="0.25",
                zorder=5, bbox=dict(fc="white", ec="none", alpha=0.75, pad=0.6))
    ax.set_xlim(0, 100)
    ax.set_ylabel(res["test_label"])
    if show_xlabel:
        ax.set_xlabel(T["xlabel"])


def plot_effect(ax, res, lang, show_xlabel=True):
    T = LBL[lang]
    eff = res.get("effect")
    if not eff or eff.get("curve") is None:
        ax.axis("off")
        return
    cur = eff["curve"]
    ax.plot(NODES, cur, color=MATLAB_COLORS[3], lw=1.5)
    ax.axhline(0, color="0.55", lw=0.6)
    if eff["name"] in ("d", "dz"):
        for h in (0.2, 0.5, 0.8):
            ax.axhline(h, color="0.7", ls=":", lw=0.7)
            ax.axhline(-h, color="0.7", ls=":", lw=0.7)
        ax.set_ylabel(T["effect_d"] if eff["name"] == "d" else T["effect_dz"])
    elif eff["name"] == "r":
        ax.set_ylim(-1, 1)
        ax.set_ylabel(T["effect_r"])
    elif eff["name"] == "eta2":
        ax.set_ylim(0, max(0.35, float(np.nanmax(cur)) * 1.2))
        ax.set_ylabel(T["effect_eta"])
    else:
        ax.set_ylim(0, max(0.35, float(np.nanmax(cur)) * 1.2))
        ax.set_ylabel(T["effect_eta_p"])
    ax.set_xlim(0, 100)
    if show_xlabel:
        ax.set_xlabel(T["xlabel"])


def _legend_handles(results, cfg=None):
    style = plot_style(cfg)
    for res in results.values():
        if "error" in res:
            continue
        pl = res["plot"]
        if pl["type"] == "groups":
            return [Line2D([0], [0], color=style["line_colors"][i % len(style["line_colors"])], lw=2.2,
                           label=f"{g['label']} (n={g['n']})") for i, g in enumerate(pl["groups"])]
    return []


def fig_report(results, bands, varmap_sel, lang, cfg, include_spm=True, title=None):
    apply_matlab_style()
    assigned = {}
    for v, r in results.items():
        if r.get("joint") and r.get("plane"):
            assigned.setdefault((r["joint"], r["plane"]), []).append(v)
    duplicates = {k: v for k, v in assigned.items() if len(v) > 1}
    if duplicates:
        detail = "; ".join(f"{j}/{p}: {', '.join(vs)}" for (j, p), vs in duplicates.items())
        raise ValueError("Hay más de una variable asignada a la misma celda anatómica: " + detail)
    have = {k: vs[0] for k, vs in assigned.items()}
    joints = [j for j in JOINT_ORDER if any(k[0] == j for k in have)]
    extras = [v for v, r in results.items() if not (r.get("joint") and r.get("plane"))]
    nrows = max(1, len(joints))
    rowh = 3.85 if include_spm else 2.55
    H = rowh * nrows + 1.55
    fig = plt.figure(figsize=(12.8, H))
    gs = gridspec.GridSpec(nrows, 3, figure=fig, hspace=0.42, wspace=0.26,
                           top=1 - 0.95 / H, bottom=0.95 / H)
    for r, joint in enumerate(joints):
        for cc, plane in enumerate(PLANE_ORDER):
            var = have.get((joint, plane))
            if var is None:
                ax = fig.add_subplot(gs[r, cc])
                ax.axis("off")
                continue
            res = results[var]
            last_row = (r == nrows - 1)
            if "error" in res:
                ax = fig.add_subplot(gs[r, cc])
                ax.set_title(f"{LBL[lang]['joint'][joint]} · {LBL[lang]['plane'][plane]}")
                ax.text(0.5, 0.5, f"⚠ {res['error']}", ha="center", va="center",
                        fontsize=8, wrap=True, transform=ax.transAxes)
                ax.set_xticks([]); ax.set_yticks([])
                continue
            if include_spm:
                sub = gs[r, cc].subgridspec(2, 1, height_ratios=[1.55, 1], hspace=0.09)
                axk = fig.add_subplot(sub[0])
                axs = fig.add_subplot(sub[1], sharex=axk)
                plot_kin(axk, res, bands.get(var), lang, cfg=cfg)
                axk.tick_params(labelbottom=False)
                plot_spm(axs, res, lang, show_xlabel=last_row, cfg=cfg)
            else:
                axk = fig.add_subplot(gs[r, cc])
                plot_kin(axk, res, bands.get(var), lang, cfg=cfg)
                if last_row:
                    axk.set_xlabel(LBL[lang]["xlabel"])
    handles = _legend_handles(results, cfg)
    if handles:
        fig.legend(handles=handles, loc="lower center", ncol=min(len(handles), 5),
                   bbox_to_anchor=(0.5, 0.005), fontsize=9)
    fig.suptitle(title or cfg.get("title", "GaitSPM"), fontsize=13, fontweight="bold", y=0.995)
    return fig, extras


def fig_detail(res, band, lang, cfg):
    apply_matlab_style()
    has_eff = res.get("effect") and res["effect"].get("curve") is not None
    n = 3 if has_eff else 2
    fig = plt.figure(figsize=(7.6, 3.1 * n + 0.8))
    hr = [1.9, 1.1, 1.0][:n]
    gs = gridspec.GridSpec(n, 1, figure=fig, height_ratios=hr, hspace=0.3,
                           top=0.93, bottom=0.09, left=0.11, right=0.97)
    axk = fig.add_subplot(gs[0])
    plot_kin(axk, res, band, lang, show_legend=True, cfg=cfg)
    if res["plot"]["type"] == "regress":
        sm = mpl_cm.ScalarMappable(norm=Normalize(np.min(res["plot"]["x"]), np.max(res["plot"]["x"])),
                                   cmap="viridis")
        fig.colorbar(sm, ax=axk, pad=0.01, fraction=0.045, label=res["plot"]["covname"])
    axs = fig.add_subplot(gs[1], sharex=axk)
    plot_spm(axs, res, lang, show_xlabel=(n == 2), cfg=cfg)
    if has_eff:
        axe = fig.add_subplot(gs[2], sharex=axk)
        plot_effect(axe, res, lang, show_xlabel=True)
    fig.suptitle(f"{variable_title(res, lang)}  —  {res['variable']}", fontsize=12, fontweight="bold")
    return fig


def fig_pair(res, ph, lang, cfg=None):
    """Post hoc contrast figure (pair means and their SPM{t})."""
    apply_matlab_style()
    fig = plt.figure(figsize=(7.6, 6.2))
    gs = gridspec.GridSpec(2, 1, figure=fig, height_ratios=[1.6, 1], hspace=0.12,
                           top=0.9, bottom=0.1, left=0.11, right=0.97)
    axk = fig.add_subplot(gs[0])
    pairset = set(map(str, ph["pair"]))
    sub = {"variable": res["variable"], "joint": res["joint"], "plane": res["plane"],
           "plot": {"type": "groups",
                    "groups": [g for g in res["plot"]["groups"] if str(g["label"]) in pairset]}}
    plot_kin(axk, sub, None, lang, show_legend=True, cfg=cfg)
    axk.tick_params(labelbottom=False)
    axs = fig.add_subplot(gs[1], sharex=axk)
    fake = {"z": ph["z"], "zstar": ph["zstar"], "two_tailed": True, "stat_name": "t",
            "test_label": "SPM{t}", "clusters": ph["clusters"]}
    plot_spm(axs, fake, lang, show_xlabel=True, cfg=cfg)
    fig.suptitle(f"Post-hoc: {ph['label']}   (α Bonferroni = {ph['alpha']:.4f})",
                 fontsize=11, fontweight="bold")
    return fig


def fig_to_bytes(fig, fmt="png", dpi=300):
    buf = io.BytesIO()
    fig.savefig(buf, format=fmt, dpi=dpi, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


# ----------------------------------------------------------------------------
# Results table
# ----------------------------------------------------------------------------
def results_table(results, lang):
    rows = []
    for var, res in results.items():
        base = {"Articulación": LBL[lang]["joint"].get(res.get("joint", ""), res.get("joint", "")),
                "Plano": LBL[lang]["plane"].get(res.get("plane", ""), res.get("plane", "")),
                "Variable": var}
        if "error" in res:
            rows.append({**base, "Test": "ERROR", "Info": res["error"]})
            continue
        info = {"Test": res["test_label"],
                "Modo": "paramétrico" if res["mode_used"] == "param" else "SnPM",
                "Info": res["df_str"], "α": res["alpha"],
                "Umbral": round(res["zstar"], 3),
                "Corrección campos": {"none": "Sin ajuste", "bonferroni": "Bonferroni", "holm": "Holm",
                                        "fdr_bh": "FDR-BH"}.get(res.get("field_correction"), ""),
                "p campo ajustada": round(res.get("field_p_adj", 1.0), 4),
                "Confirmado": "Sí" if res.get("field_significant", False) else "No"}
        if res["clusters"]:
            for k, c in enumerate(res["clusters"], 1):
                rows.append({**base, **info, "Clúster": k,
                             "p campo ajustada": round(c.get("p_field_adj", c["p"]), 6),
                             "Confirmado": "Sí" if c in confirmed_clusters(res) else "No",
                             "Inicio (%)": round(c["x0"], 1), "Fin (%)": round(c["x1"], 1),
                             "p": "<0.001" if c["p"] < 0.001 else round(c["p"], 4),
                             "Pico": round(c["peak"], 2), "Pico en (%)": c["xpeak"]})
        else:
            rows.append({**base, **info, "Clúster": "—", "p": "n.s."})
        if res.get("posthoc"):
            for ph in res["posthoc"]["pairs"]:
                if "error" in ph:
                    continue
                pinfo = {"Test": f"Post-hoc {ph['label']}", "Modo": info["Modo"],
                         "α": round(ph["alpha"], 4), "Umbral": round(ph["zstar"], 3),
                         "Corrección campos": info["Corrección campos"],
                         "p campo ajustada": 1., "Confirmado": "No"}
                if ph["clusters"]:
                    for k, c in enumerate(ph["clusters"], 1):
                        rows.append({**base, **pinfo, "Clúster": k,
                                     "p campo ajustada": round(c.get("p_field_adj", c["p"]), 6),
                                     "Confirmado": "Sí" if c.get("p_field_adj", c["p"]) <= res.get("family_alpha", .05) else "No",
                                     "Inicio (%)": round(c["x0"], 1), "Fin (%)": round(c["x1"], 1),
                                     "p": "<0.001" if c["p"] < 0.001 else round(c["p"], 4),
                                     "Pico": round(c["peak"], 2), "Pico en (%)": c["xpeak"]})
                else:
                    rows.append({**base, **pinfo, "Clúster": "—", "p": "n.s."})
    cols = ["Articulación", "Plano", "Variable", "Test", "Modo", "Info", "α", "Umbral",
            "Clúster", "Inicio (%)", "Fin (%)", "p", "Corrección campos",
            "p campo ajustada", "Confirmado", "Pico", "Pico en (%)"]
    df = pd.DataFrame(rows)
    df = df.reindex(columns=[c for c in cols if c in df.columns])
    if "Clúster" in df:
        df["Clúster"] = _to_numeric(df["Clúster"], errors="coerce").astype("Int64")
    if "p" in df:
        df["p"] = df["p"].map(lambda x: "" if pd.isna(x) else str(x))
    if lang == "en":
        df = df.replace({"Sí": "Yes", "Sin ajuste": "Unadjusted", "paramétrico": "parametric"})
        if "Info" in df:
            df["Info"] = df["Info"].str.replace("gl =", "df =", regex=False).str.replace("permutaciones", "permutations", regex=False)
        df = df.rename(columns={"Articulación":"Joint", "Plano":"Plane", "Modo":"Mode",
            "Umbral":"Threshold", "Clúster":"Cluster", "Inicio (%)":"Start (%)", "Fin (%)":"End (%)",
            "Corrección campos":"Across-variable correction", "p campo ajustada":"Adjusted cluster p",
            "Confirmado":"Confirmed", "Pico":"Peak", "Pico en (%)":"Peak at (%)"})
    return df


# ----------------------------------------------------------------------------
# Methods / Results text (ES/EN)
# ----------------------------------------------------------------------------
_DESIGN_TXT = {
    "es": {
        "ttest2": "una prueba t de dos muestras independientes SPM{{t}} ({a} vs {b})",
        "paired_cond": "una prueba t pareada SPM{{t}} ({a} vs {b})",
        "paired_side": "una prueba t pareada SPM{{t}} entre lados ({a} vs {b})",
        "anova1": "un ANOVA de una vía SPM{{F}} ({lv})",
        "anova1rm": "un ANOVA de medidas repetidas SPM{{F}} ({lv})",
        "regress": "una regresión lineal SPM{{t}} sobre la covariable «{cov}»",
    },
    "en": {
        "ttest2": "a two-sample SPM{{t}} t-test ({a} vs {b})",
        "paired_cond": "a paired SPM{{t}} t-test ({a} vs {b})",
        "paired_side": "a paired SPM{{t}} t-test between limbs ({a} vs {b})",
        "anova1": "a one-way SPM{{F}} ANOVA ({lv})",
        "anova1rm": "a repeated-measures SPM{{F}} ANOVA ({lv})",
        "regress": "SPM{{t}} linear regression on the covariate '{cov}'",
    },
}

CITAS = [
    "Pataky TC. Generalized n-dimensional biomechanical field analysis using statistical parametric mapping. J Biomech. 2010;43(10):1976-82.",
    "Pataky TC. One-dimensional statistical parametric mapping in Python. Comput Methods Biomech Biomed Engin. 2012;15(3):295-301.",
    "Pataky TC, Vanrenterghem J, Robinson MA. Zero- vs. one-dimensional, parametric vs. non-parametric, and confidence interval vs. hypothesis testing procedures in one-dimensional biomechanical trajectory analysis. J Biomech. 2015;48(7):1277-85.",
    "Nichols TE, Holmes AP. Nonparametric permutation tests for functional neuroimaging: a primer with examples. Hum Brain Mapp. 2002;15(1):1-25.",
]


def _design_phrase(cfg, lang):
    d = cfg["design"]
    if d in ADVANCED_DESIGNS:
        if d in ('anova2', 'anova2onerm'):
            return f"{d}: group × condition, {cfg.get('factor_effect', 'interaction')}; equal variance; Bonferroni across 3 effects" + ("; sphericity assumed, approximate residual inference for one response per cell" if d == "anova2onerm" else "")
        return f"{d}: covariates {cfg.get('covariates') or [cfg.get('covariate')]}; contrast {cfg.get('contrast') if d == 'glm' else 'second group minus first'}, equal variance assumed"
    if d == "ttest2":
        return _DESIGN_TXT[lang][d].format(a=cfg["groups"][0], b=cfg["groups"][1])
    if d == "paired_cond":
        return _DESIGN_TXT[lang][d].format(a=cfg["cond_levels"][0], b=cfg["cond_levels"][1])
    if d == "paired_side":
        return _DESIGN_TXT[lang][d].format(a=cfg["side_levels"][0], b=cfg["side_levels"][1])
    if d == "anova1":
        return _DESIGN_TXT[lang][d].format(lv=", ".join(map(str, cfg["groups"])))
    if d == "anova1rm":
        return _DESIGN_TXT[lang][d].format(lv=", ".join(map(str, cfg["cond_levels"])))
    return _DESIGN_TXT[lang][d].format(cov=cfg.get("covariate", ""))


def methods_text(cfg, results, lang="en"):
    n_ok = [r for r in results.values() if "error" not in r]
    modes = {r.get("mode_used") for r in n_ok}
    any_np, any_p = "nonparam" in modes, "param" in modes
    npcts = [r["normality_pct"] for r in n_ok if r.get("normality_pct") is not None]
    if lang == "en":
        s = (f"Kinematic waveforms were time-normalized to 101 nodes (0-100% of the gait cycle) "
             f"and analysed with one-dimensional Statistical Parametric Mapping (SPM1D v{spm1d.__version__}; "
             f"Pataky, 2010, 2012) in Python. For each variable we applied {_design_phrase(cfg, lang)} "
             f"with alpha = {cfg['alpha']:g}"
             + (", two-tailed. " if cfg["two_tailed"] else ". "))
        if any_p:
            s += ("The critical threshold was computed with Random Field Theory, and the probability of each "
                  "supra-threshold cluster was reported together with its temporal extent (% of the gait cycle). ")
        if npcts:
            s += "Normality of the node-wise residuals was screened with the D'Agostino-Pearson K2 test. "
        if any_np:
            s += (f"The selected non-parametric permutation "
                  f"equivalent (SnPM; Nichols & Holmes, 2002; Pataky et al., 2015) was used with "
                  f"up to {cfg['iterations']} iterations and random seed {cfg.get('seed', 2026)}. ")
        if cfg.get("mode") == "auto":
            s += (f"The exploratory automatic rule selected SnPM when the smallest sample was <8 or when "
                  f">{cfg.get('auto_normality_cutoff', 20):g}% of nodes had K2 p<0.05. ")
        corr = cfg.get("field_correction", "bonferroni")
        if corr != "none":
            s += (f"Inference used Bonferroni alpha/m across {cfg.get('field_count', len(results))} prespecified waveforms, "
                  "including failed outcomes in the family size. Reported adjusted cluster p-values are capped at one; "
                  "they are not omnibus waveform p-values. ")
        else:
            s += "Waveforms were treated as separate outcomes and no multiplicity correction was applied across variables. "
        side_phrase = {"mean": "Left and right waveforms were averaged within participant. ",
                       "L": "Only left-side waveforms were analysed. ",
                       "R": "Only right-side waveforms were analysed. "}.get(cfg.get("side_mode"), "")
        s += side_phrase
        s += ("Shaded group bands represent pointwise 95% confidence intervals of the mean, not simultaneous bands. "
              if cfg.get("interval_mode", "sd") == "ci95"
              else "Shaded group bands represent mean ± standard deviation. ")
        if cfg["design"] in ("ttest2", "anova1"):
            s += ("Equal variances were assumed. " if cfg.get("equal_var", True)
                  else "Unequal variances were allowed. ")
        if cfg["design"] in ("anova1", "anova1rm") and cfg.get("posthoc", True):
            s += ("Significant omnibus effects were followed by pairwise SPM{t} post-hoc tests with "
                  "Bonferroni-adjusted alpha. ")
        if cfg["design"] == "anova1rm":
            s += "Sphericity was assumed (not corrected) in the repeated-measures model. "
        eff = {"d": "Cohen's d", "dz": "Cohen's dz", "r": "Pearson's r",
               "eta2": "eta-squared", "eta2p": "partial eta-squared"}
        effs = sorted({eff[r["effect"]["name"]] for r in n_ok if r.get("effect")})
        if effs:
            s += "Node-wise effect sizes (" + ", ".join(effs) + ") were computed descriptively."
        return s
    s = (f"Las curvas cinemáticas se normalizaron temporalmente a 101 nodos (0–100 % del ciclo de la marcha) "
         f"y se analizaron mediante Statistical Parametric Mapping unidimensional (SPM1D v{spm1d.__version__}; "
         f"Pataky, 2010, 2012) en Python. Para cada variable se aplicó {_design_phrase(cfg, lang)} "
         f"con α = {cfg['alpha']:g}"
         + (", bilateral. " if cfg["two_tailed"] else ". "))
    if any_p:
        s += ("El umbral crítico se calculó mediante la teoría de campos aleatorios (RFT), informando la "
              "probabilidad de cada clúster supraumbral junto con su extensión temporal (% del ciclo). ")
    if npcts:
        s += "La normalidad de los residuos nodo a nodo se exploró con la prueba K2 de D'Agostino-Pearson. "
    if any_np:
        s += (f"Se empleó el método seleccionado no paramétrico "
              f"por permutaciones (SnPM; Nichols y Holmes, 2002; Pataky et al., 2015) con "
              f"hasta {cfg['iterations']} iteraciones y semilla aleatoria {cfg.get('seed', 2026)}. ")
    if cfg.get("mode") == "auto":
        s += (f"La regla automática exploratoria seleccionó SnPM cuando el menor tamaño muestral fue <8 o "
              f"cuando >{cfg.get('auto_normality_cutoff', 20):g}% de los nodos presentó K2 p<0,05. ")
    corr = cfg.get("field_correction", "bonferroni")
    if corr != "none":
        s += (f"La inferencia usó α/m de Bonferroni entre {cfg.get('field_count', len(results))} waveforms preespecificadas, "
              "incluyendo los outcomes fallidos en el tamaño de familia. Los p ajustados de clúster se limitan a uno "
              "y no son p ómnibus de cada waveform. ")
    else:
        s += "Las waveforms se trataron como outcomes independientes, sin ajuste entre variables. "
    side_phrase = {"mean": "Las curvas izquierda y derecha se promediaron dentro de cada participante. ",
                   "L": "Solo se analizaron las curvas del lado izquierdo. ",
                   "R": "Solo se analizaron las curvas del lado derecho. "}.get(cfg.get("side_mode"), "")
    s += side_phrase
    s += ("Las bandas sombreadas representan IC 95 % puntuales de la media, no bandas simultáneas. "
          if cfg.get("interval_mode", "sd") == "ci95"
          else "Las bandas sombreadas de cada grupo representan media ± desviación estándar. ")
    if cfg["design"] in ("ttest2", "anova1"):
        s += ("Se asumieron varianzas iguales. " if cfg.get("equal_var", True)
              else "No se asumieron varianzas iguales. ")
    if cfg["design"] in ("anova1", "anova1rm") and cfg.get("posthoc", True):
        s += ("Los efectos ómnibus significativos se siguieron de contrastes post-hoc SPM{t} por pares con "
              "α ajustada por Bonferroni. ")
    if cfg["design"] == "anova1rm":
        s += "Se asumió esfericidad (sin corrección) en el modelo de medidas repetidas. "
    eff = {"d": "d de Cohen", "dz": "dz de Cohen", "r": "r de Pearson",
           "eta2": "eta cuadrado", "eta2p": "eta cuadrado parcial"}
    effs = sorted({eff[r["effect"]["name"]] for r in n_ok if r.get("effect")})
    if effs:
        s += "Se calcularon descriptivamente effect sizes nodo a nodo (" + ", ".join(effs) + ")."
    return s


def _cluster_phrase(c, res, lang):
    rng = f"{c['x0']:.1f}–{c['x1']:.1f}"
    stat = f"{res['stat_name']} = {abs(c['peak']):.2f}"
    if lang == "en":
        return f"{rng}% of the gait cycle (peak {stat} at {c['xpeak']}%, {fmt_p(c['p'])})"
    return f"{rng} % del ciclo (pico {stat} en {c['xpeak']} %, {fmt_p(c['p'])})"


def results_text(results, cfg, lang="en"):
    lines, ns, not_confirmed = [], [], []
    for var, res in results.items():
        if "error" in res:
            continue
        name = f"{variable_title(res, lang)} ({var})"
        clusters = confirmed_clusters(res)
        if not clusters:
            if res.get("clusters") and res.get("field_correction", "none") != "none":
                not_confirmed.append(name)
            else:
                ns.append(name)
            continue
        for c in clusters:
            if res["design"] in ADVANCED_DESIGNS:
                lines.append(f"{name}: {res['test_label']} at {_cluster_phrase(c, res, lang)}. "
                             + ("Contrast sign: " + str(c['sign']) if res['stat_name'] == 't' else ''))
            elif res["design"] in ("anova1", "anova1rm"):
                if lang == "en":
                    lines.append(f"A significant main effect was found for {name} at {_cluster_phrase(c, res, lang)}.")
                else:
                    lines.append(f"Se halló un efecto principal significativo en {name} en {_cluster_phrase(c, res, lang)}.")
            elif res["design"] == "regress":
                pos = c["sign"] > 0
                if lang == "en":
                    lines.append(f"{name} showed a {'positive' if pos else 'negative'} association with "
                                 f"{cfg.get('covariate')} at {_cluster_phrase(c, res, lang)}.")
                else:
                    lines.append(f"{name} mostró una asociación {'positiva' if pos else 'negativa'} con "
                                 f"{cfg.get('covariate')} en {_cluster_phrase(c, res, lang)}.")
            else:
                a, b = res["direction"]
                hi, lo = (a, b) if c["sign"] > 0 else (b, a)
                if lang == "en":
                    lines.append(f"{name}: '{hi}' showed greater values than '{lo}' at {_cluster_phrase(c, res, lang)}.")
                else:
                    lines.append(f"{name}: «{hi}» mostró valores mayores que «{lo}» en {_cluster_phrase(c, res, lang)}.")
        if res.get("posthoc") and (res.get("field_correction", "none") == "none"
                                   or res.get("field_significant", False)):
            for ph in res["posthoc"]["pairs"]:
                for c in ph.get("clusters", []):
                    if c.get("p_field_adj", c["p"]) > res.get("family_alpha", cfg["alpha"]):
                        continue
                    if lang == "en":
                        lines.append(f"  Post-hoc {ph['label']}: significant at {c['x0']:.1f}–{c['x1']:.1f}% "
                                     f"({fmt_p(c['p'])}, Bonferroni alpha = {ph['alpha']:.4f}).")
                    else:
                        lines.append(f"  Post-hoc {ph['label']}: significativo en {c['x0']:.1f}–{c['x1']:.1f} % "
                                     f"({fmt_p(c['p'])}, α Bonferroni = {ph['alpha']:.4f}).")
    if ns:
        if lang == "en":
            lines.append("No significant clusters were detected for: " + "; ".join(ns) + ".")
        else:
            lines.append("No se detectaron clústeres significativos en: " + "; ".join(ns) + ".")
    if not_confirmed:
        corr = "Bonferroni" if cfg.get("field_correction") == "bonferroni" else "sin ajuste / unadjusted"
        if lang == "en":
            lines.append("Within-waveform clusters did not remain significant after " + corr
                         + " correction across variables for: " + "; ".join(not_confirmed) + ".")
        else:
            lines.append("Los clústeres significativos dentro de cada waveform no se mantuvieron tras la "
                         "corrección " + corr + " entre variables en: " + "; ".join(not_confirmed) + ".")
    return "\n".join(lines)


# ----------------------------------------------------------------------------
# Demonstration data: cam FAI versus controls (literature-informed effects)
# ----------------------------------------------------------------------------
DEMO_GROUPS = ["Control", "Cam asintomático", "FAI cam"]
DEMO_CONDS = ["PRE", "POST", "SEG"]


def demo_dataset(n_per_group=12, seed=42):
    """Synthetic gait demonstration (12 PiG variables × 3 groups × 3 conditions × 2 sides).

    Effects injected into «FAI cam» (half the magnitude in «Cam asintomático»):
      · ↓ terminal hip extension (~40–65% of the cycle)
      · ↓ hip adduction during stance (~15–40%)
      · ↓ hip internal rotation during stance
      · slight constant anterior pelvic tilt
    Other effects: POST/SEG ↑ dorsiflexion (~45%); side R ↑ swing-phase knee
    flexion; «velocidad» scales peak knee flexion during swing.
    """
    from scipy.ndimage import gaussian_filter1d
    rng = np.random.default_rng(seed)
    t = NODES.astype(float)
    g1 = lambda mu, s: np.exp(-((t - mu) / s) ** 2)
    base = {
        "PelvisTilt":        12 + 1.5 * np.sin(2 * np.pi * t / 50 + 0.5),
        "PelvisObliquity":   3.5 * np.sin(4 * np.pi * t / 100),
        "PelvisRotation":    5.0 * np.sin(2 * np.pi * t / 100 + np.pi),
        "HipFlexion":        22 * np.cos(2 * np.pi * t / 100) + 8 + 6 * g1(82, 9),
        "HipAdduction":      5 * g1(25, 14) - 4 * g1(75, 15),
        "HipRotation":       2 + 3 * np.sin(2 * np.pi * t / 100 + 1),
        "KneeFlexion":       12 * g1(15, 7.5) + 62 * g1(73, 9.5) + 4,
        "KneeAdduction":     2 * np.sin(2 * np.pi * t / 100) + 1,
        "KneeRotation":      3 * np.sin(2 * np.pi * t / 100 + 2),
        "AnkleDorsiflexion": -3 + 12 * g1(42, 17) - 20 * g1(62, 5) + 4 * g1(85, 10),
        "AnkleInversion":    3 * np.sin(2 * np.pi * t / 100 + 0.8) + 1,
        "FootProgression":   -9 + 2 * np.sin(2 * np.pi * t / 100),
    }
    fai_fx = {
        "HipFlexion":   +5.5 * g1(52, 9),
        "HipAdduction": -2.6 * g1(26, 13),
        "HipRotation":  -4.2 * g1(35, 22),
        "PelvisTilt":   +1.5 * np.ones_like(t),
    }
    cond_fx = {"PRE": 0.0, "POST": 4.5, "SEG": 6.0}
    recs, meta_rows, sid = [], [], 0
    for gi, grp in enumerate(DEMO_GROUPS):
        scale = (0.0, 0.5, 1.0)[gi]
        for _ in range(n_per_group):
            sid += 1
            subj = f"S{sid:02d}"
            speed = float(rng.normal(1.32, 0.14))
            meta_rows.append({"subject": subj, "group": grp, "condition": "—",
                              "side": "—", "velocidad": round(speed, 3)})
            off = {v: rng.normal(0, 1.8) for v in base}
            amp = {v: rng.normal(1, 0.06) for v in base}
            for cond in DEMO_CONDS:
                for side in ("L", "R"):
                    for var, mu in base.items():
                        y = amp[var] * mu + off[var] + scale * fai_fx.get(var, 0)
                        if var == "AnkleDorsiflexion":
                            y = y + cond_fx[cond] * g1(45, 13)
                        if var == "KneeFlexion":
                            y = y + (speed - 1.32) * 30 * g1(73, 9.5)
                            if side == "R":
                                y = y + 3.5 * g1(73, 9)
                        y = y + gaussian_filter1d(rng.normal(0, 1.6, 101), 4, mode="nearest")
                        recs.append((subj, grp, cond, side, var, y))
    frames = [pd.DataFrame({"subject": s, "group": g, "condition": c, "side": sd,
                            "variable": v, "node": NODES, "value": y})
              for (s, g, c, sd, v, y) in recs]
    canon = _finalize_canon(pd.concat(frames, ignore_index=True))
    meta = pd.DataFrame(meta_rows)
    varmap = classify_variables(sorted(base))
    return canon, meta, ["velocidad"], varmap


def demo_wide_df(canon, meta):
    """Export the demo in wide format (one row per participant/condition/side)."""
    piv = canon.pivot_table(index=["subject", "group", "condition", "side"],
                            columns=["variable", "node"], values="value", observed=True)
    piv.columns = [f"{v}_{n}" for v, n in piv.columns]
    out = piv.reset_index().rename(columns={"subject": "sujeto", "group": "grupo",
                                            "condition": "condicion", "side": "lado"})
    sp = meta.set_index("subject")["velocidad"]
    out.insert(4, "velocidad", out["sujeto"].astype(str).map(sp).round(3))
    return out


# ----------------------------------------------------------------------------
# Streamlit interface
# ----------------------------------------------------------------------------
def main():
    import sys
    from gaitspm_ui import main as laboratory_main
    laboratory_main(sys.modules[__name__])


def _selftest(outdir="out_demo"):
    import os, time
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    canon, meta, covs, vm = demo_dataset()
    print(f"[demo] {len(canon):,} filas · {canon['subject'].nunique()} sujetos · "
          f"{canon['variable'].nunique()} variables")
    base = dict(alpha=0.05, two_tailed=True, mode="param", iterations=400, seed=2026,
                auto_normality_cutoff=20, field_correction="none", equal_var=True,
                side_mode="mean", posthoc=True, band_group="Control", band_k=1, lang="es",
                groups=None, cond=None, cond_levels=None, side_levels=None,
                group_filter=None, covariate=None)

    def run(design, vmap=vm, data=None, mdata=None, **kw):
        cfg = {**base, **kw, "design": design}
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res, bands = run_analysis(data if data is not None else canon,
                                      mdata if mdata is not None else meta, vmap, cfg)
        errs = {v: r["error"] for v, r in res.items() if "error" in r}
        assert not errs, errs
        return cfg, res, bands

    # 1 · independent t-test: Control vs FAI cam (PRE)
    cfg, res, bands = run("ttest2", groups=["Control", "FAI cam"], cond="PRE")
    for v in ("HipFlexion", "HipRotation", "HipAdduction", "PelvisTilt"):
        cl = res[v]["clusters"]
        print(f"  t2 {v}: " + (", ".join(f"{c['x0']:.1f}–{c['x1']:.1f}% {fmt_p(c['p'])}" for c in cl) if cl else "n.s."))
    assert res["HipFlexion"]["clusters"] and res["HipRotation"]["clusters"], "faltan clústeres de cadera"
    fig, _ = fig_report(res, bands, vm, "es", cfg,
                        title="FAI cam vs Control · condición PRE · SPM{t} (α = 0.05)")
    fig.savefig(f"{outdir}/informe_FAIcam_vs_Control.png", dpi=200, bbox_inches="tight")
    plt.close(fig)
    tab = results_table(res, "es")
    tab.to_csv(f"{outdir}/tabla_FAIcam_vs_Control.csv", index=False, sep=";", decimal=",")
    with pd.ExcelWriter(f"{outdir}/tabla_FAIcam_vs_Control.xlsx", engine="openpyxl") as w:
        tab.to_excel(w, index=False, sheet_name="SPM")
    figd = fig_detail(res["HipRotation"], bands.get("HipRotation"), "es", cfg)
    figd.savefig(f"{outdir}/detalle_HipRotation.png", dpi=200, bbox_inches="tight")
    plt.close(figd)
    custom_cfg = {**cfg, "line_colors": ["#0B2545", "#2E7D8A"],
                  "interval_mode": "ci95", "interval_alpha": 0.24,
                  "show_interval_edges": True, "cluster_fill_color": "#6B2D5C",
                  "cluster_fill_alpha": 0.72, "show_cluster_bars": True}
    sty = plot_style(custom_cfg)
    assert sty["line_colors"][:2] == ["#0B2545", "#2E7D8A"]
    g0 = res["HipRotation"]["plot"]["groups"][0]
    assert np.nanmean(_interval_halfwidth(g0, "ci95")) < np.nanmean(g0["sd"])
    figc = fig_detail(res["HipRotation"], bands.get("HipRotation"), "es", custom_cfg)
    line_colors = {matplotlib.colors.to_hex(line.get_color()).upper()
                   for ax in figc.axes for line in ax.lines}
    assert "#0B2545" in line_colors and "#2E7D8A" in line_colors
    assert any("%" in text.get_text() and "–" in text.get_text()
               for ax in figc.axes for text in ax.texts), "faltan barras de clúster"
    figc.savefig(f"{outdir}/detalle_HipRotation_personalizado.png", dpi=200,
                 bbox_inches="tight")
    plt.close(figc)
    with open(f"{outdir}/textos_FAI.txt", "w", encoding="utf-8") as fh:
        fh.write("MÉTODOS (ES)\n" + methods_text(cfg, res, "es")
                 + "\n\nMETHODS (EN)\n" + methods_text(cfg, res, "en")
                 + "\n\nRESULTADOS (ES)\n" + results_text(res, cfg, "es")
                 + "\n\nRESULTS (EN)\n" + results_text(res, cfg, "en") + "\n")

    # 2 · paired PRE versus POST
    _, r2, _ = run("paired_cond", cond_levels=["PRE", "POST"])
    assert r2["AnkleDorsiflexion"]["clusters"], "PRE-POST tobillo"
    # 3 · L vs R
    _, r3, _ = run("paired_side", side_levels=["L", "R"], cond="PRE")
    assert r3["KneeFlexion"]["clusters"], "L-R rodilla"
    # 4 · three-group ANOVA + post hoc
    cfg4, r4, _ = run("anova1", groups=DEMO_GROUPS, cond="PRE")
    assert r4["HipRotation"]["clusters"] or r4["HipFlexion"]["clusters"], "ANOVA cadera"
    phvar = next((v for v in ("HipRotation", "HipFlexion") if r4[v].get("posthoc")), None)
    assert phvar and r4[phvar]["posthoc"]["pairs"], "post-hoc"
    php = next((p for p in r4[phvar]["posthoc"]["pairs"] if p.get("clusters")),
               r4[phvar]["posthoc"]["pairs"][0])
    figp = fig_pair(r4[phvar], php, "es", cfg4)
    figp.savefig(f"{outdir}/posthoc_{phvar}.png", dpi=200, bbox_inches="tight")
    plt.close(figp)
    # 5 · three-condition RM-ANOVA
    _, r5, _ = run("anova1rm", cond_levels=DEMO_CONDS)
    assert r5["AnkleDorsiflexion"]["clusters"], "RM tobillo"
    assert r5["AnkleDorsiflexion"]["effect"]["name"] == "eta2p"
    assert np.nanmin(r5["AnkleDorsiflexion"]["effect"]["curve"]) >= 0
    assert np.nanmax(r5["AnkleDorsiflexion"]["effect"]["curve"]) <= 1
    # 6 · regression with speed
    cfg6, r6, b6 = run("regress", covariate="velocidad", cond="PRE")
    assert r6["KneeFlexion"]["clusters"], "regresión rodilla"
    figr = fig_detail(r6["KneeFlexion"], b6.get("KneeFlexion"), "es", cfg6)
    figr.savefig(f"{outdir}/detalle_regresion_KneeFlexion.png", dpi=200, bbox_inches="tight")
    plt.close(figr)
    # 7 · quick nonparametric test
    vm2 = vm[vm["variable"].isin(["HipFlexion", "KneeAdduction"])]
    _, r7, _ = run("ttest2", vmap=vm2, groups=["Control", "FAI cam"], cond="PRE",
                   mode="nonparam", iterations=300)
    assert r7["HipFlexion"]["mode_used"] == "nonparam" and r7["HipFlexion"]["clusters"], "SnPM"
    _, r7b, _ = run("ttest2", vmap=vm2, groups=["Control", "FAI cam"], cond="PRE",
                    mode="nonparam", iterations=300)
    a7, b7 = r7["HipFlexion"], r7b["HipFlexion"]
    assert np.isclose(a7["zstar"], b7["zstar"]), "umbral SnPM no reproducible"
    assert [c["p"] for c in a7["clusters"]] == [c["p"] for c in b7["clusters"]], \
        "p de clúster SnPM no reproducibles"
    # 7b · correction across fields
    _, rc, _ = run("ttest2", groups=["Control", "FAI cam"], cond="PRE", field_correction="bonferroni")
    padj = [r["field_p_adj"] for r in rc.values() if "error" not in r]
    assert all(0 <= p <= 1 for p in padj), padj
    # 8 · text
    for lg in ("es", "en"):
        assert len(methods_text(cfg, res, lg)) > 200 and len(results_text(res, cfg, lg)) > 50
    # 9 · CSV examples + parser round trip
    wide = demo_wide_df(canon, meta)
    wide.to_csv(f"{outdir}/ejemplo_marcha_ancho.csv", index=False)
    subs = (meta[meta["group"] == "Control"]["subject"].head(3).tolist()
            + meta[meta["group"] == "FAI cam"]["subject"].head(3).tolist())
    ld = canon[canon["subject"].astype(str).isin(subs)
               & (canon["condition"].astype(str) == "PRE")].copy()
    ld = ld.rename(columns={"subject": "sujeto", "group": "grupo", "condition": "condicion",
                            "side": "lado", "node": "punto", "value": "valor"})
    ld["velocidad"] = ld["sujeto"].astype(str).map(meta.set_index("subject")["velocidad"])
    ld.to_csv(f"{outdir}/ejemplo_marcha_largo.csv", index=False)
    blocks = find_curve_blocks(wide.columns)
    assert len(blocks) == 12, f"bloques: {len(blocks)}"
    c2_, m2_, cov2_ = canon_from_wide(wide, blocks, {"subject": "sujeto", "group": "grupo",
                                                     "condition": "condicion", "side": "lado"})
    assert "velocidad" in cov2_, cov2_
    vm_rt = classify_variables(sorted(map(str, c2_["variable"].unique())))
    _, rr2, _ = run("ttest2", vmap=vm_rt[vm_rt["variable"] == "HipFlexion"],
                    data=c2_, mdata=m2_, groups=["Control", "FAI cam"], cond="PRE")
    assert rr2["HipFlexion"].get("clusters"), "roundtrip parser ancho"
    quality = canonical_quality(c2_)
    assert quality["completeness_pct"] == 100 and not quality["subject_group_collisions"]
    assert str(results_table(res, "es")["Clúster"].dtype) == "Int64"
    print(f"[SELFTEST OK] {time.time() - t0:.1f}s → {outdir}/")


def _in_streamlit():
    try:
        return st.runtime.exists()
    except Exception:  # pragma: no cover
        return False


if _in_streamlit():
    main()
