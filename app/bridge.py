# ============================================================================
# Puente JS <-> motor GaitSPM (mismo espacio de nombres que engine_web.py).
# Todas las funciones js_* reciben y devuelven JSON (str).
# ============================================================================
import json, base64, traceback
import io as _io

STATE = {}
UPLOAD_PATH = "/upload.bin"


def _safe(fn):
    def wrap(*a):
        try:
            return json.dumps({"ok": True, **fn(*a)}, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"ok": False, "error": str(e),
                               "trace": traceback.format_exc()[-2000:]}, ensure_ascii=False)
    wrap.__name__ = fn.__name__
    return wrap


def _numeric_cols(df, exclude=()):
    out = []
    for c in df.columns:
        if c in exclude:
            continue
        v = _to_numeric(df[c], errors="coerce")
        if v.notna().mean() > 0.8 and v.nunique() > 1:
            out.append(str(c))
    return out


def _store(canon, meta, covs):
    STATE.update(canon=canon, meta=meta, covs=covs, quality=canonical_quality(canon),
                 varmap=classify_variables(sorted(map(str, canon["variable"].unique()))))
    for k in ("results", "bands", "cfg", "tab", "run_rows"):
        STATE.pop(k, None)
    STATE['example'] = None
    # Recognise delivered examples only when IDs, curves and values match exactly
    # (within CSV round-trip precision). Edited patient files never inherit a preset.
    ids=set(canon.subject.astype(str))
    prefix=next(iter(ids), '')[:2]
    candidate=next((d for d in synthetic_catalog() if d['key'][:2]==prefix),None)
    if candidate:
        ref, _, _, _ = synthetic_dataset(candidate['key'])
        if ids==set(ref.subject) and len(ref)==len(canon):
            keys=CANON_COLS[:-1]
            a=canon.astype({k:str for k in keys if k!='node'}).sort_values(keys)
            b=ref.sort_values(keys)
            a['node']=a.node.astype('int64');b['node']=b.node.astype('int64')
            if a[keys].reset_index(drop=True).equals(b[keys].reset_index(drop=True)) and np.allclose(a.value,b.value,atol=1e-7,rtol=0):
                STATE['example']=candidate


def _payload():
    canon, vm = STATE["canon"], STATE["varmap"]
    raw_groups = [g for g in map(str, canon["group"].unique()) if g != "—"]
    groups = [g for g in DEMO_GROUPS if g in raw_groups] + sorted(set(raw_groups) - set(DEMO_GROUPS))
    raw_conds = list(map(str, canon["condition"].unique()))
    conds = [c for c in DEMO_CONDS if c in raw_conds] + sorted(set(raw_conds) - set(DEMO_CONDS))
    return {"n_subj": int(canon["subject"].nunique()),
            "groups": groups,
            "conds": conds,
            "sides": [s for s in sorted(map(str, canon["side"].unique())) if s in ("L", "R")],
            "n_curves": STATE['quality']['curves'],
            "group_counts": canon[['subject','group']].drop_duplicates().groupby('group', observed=True).size().to_dict(),
            "example": STATE.get('example'),
            "quality": STATE["quality"],
            "covs": list(STATE.get("covs") or []),
            "varmap": vm.to_dict("records"),
            "joints": JOINT_ORDER, "planes": PLANE_ORDER,
            "all_vars": sorted(map(str, canon["variable"].unique()))}


def js_ping():
    return json.dumps({"ok": True, "spm1d": spm1d.__version__, "engine": VERSION})


@_safe
def js_load_demo(n=12):
    canon, meta, covs, vm = demo_dataset(int(n))
    _store(canon, meta, covs)
    STATE["varmap"] = vm
    return _payload()


@_safe
def js_parse_upload(name, sheet=""):
    # A failed new upload must never leave an old file available for mapping.
    for k in ('updf','upinfo','canon','meta','varmap','quality','covs','example',
              'results','bands','cfg','tab','run_rows'):
        STATE.pop(k, None)
    with open(UPLOAD_PATH, "rb") as handle:
        data = handle.read()
    df, info = read_upload(data, name, sheet or None)
    STATE["updf"], STATE["upinfo"] = df, info
    est, payload = detect_structure(df)
    blocks = find_curve_blocks(df.columns)
    curve_cols = {c for items in blocks.values() for _, c in items}
    # Limit preview before serialising: wide Vicon files can have thousands of columns.
    prev = df.iloc[:6, :14].astype(str)
    return {"tipo": info.get("tipo"), "sep": info.get("sep"), "decimal": info.get("decimal"),
            "hojas": [str(h) for h in (info.get("hojas") or [])], "hoja": info.get("hoja"),
            "nrows": int(len(df)), "ncols": int(len(df.columns)),
            "columns": list(map(str, df.columns)),
            "preview": {"columns": list(map(str, prev.columns)), "rows": prev.values.tolist()},
            "structure": est,
            "blocks": list(blocks),
            "meta_cols": [str(c) for c in df.columns if c not in curve_cols],
            "node_guess": str(payload) if est == "transposed" else str(df.columns[0]),
            "numeric": _numeric_cols(df)}


@_safe
def js_apply_wide(roles_json):
    roles = {k: v for k, v in json.loads(roles_json).items() if v}
    df = STATE["updf"]
    canon, meta, covs = canon_from_wide(df, find_curve_blocks(df.columns), roles)
    _store(canon, meta, covs)
    return _payload()


@_safe
def js_apply_long(roles_json):
    roles = json.loads(roles_json)
    roles = {k: v for k, v in roles.items() if v or k == "covariates"}
    canon, meta, covs = canon_from_long(STATE["updf"], roles)
    # explicit covariate selection takes precedence over automatic detection heuristics
    df = STATE["updf"]
    want = [c for c in (roles.get("covariates") or []) if c in df.columns]
    missing = [c for c in want if c not in covs]
    if missing:
        add = pd.DataFrame({"subject": _clean_series(df[roles["subject"]])})
        for c in missing:
            add[c] = _to_numeric(df[c], errors="coerce")
        add = add.groupby("subject", as_index=False).mean(numeric_only=True)
        meta = meta.merge(add, on="subject", how="left")
        covs = list(covs) + missing
    _store(canon, meta, covs)
    return _payload()


@_safe
def js_apply_transposed(node_col, delim, roles_json):
    tr = {int(k): v for k, v in json.loads(roles_json).items()}
    canon, meta, covs = canon_from_transposed(STATE["updf"], node_col, delim or "_", tr)
    _store(canon, meta, covs)
    return _payload()


@_safe
def js_set_varmap(records_json):
    recs = json.loads(records_json)
    STATE["varmap"] = pd.DataFrame(recs)[["variable", "joint", "plane"]]
    for k in ('results','cfg','tab','bands'):
        STATE.pop(k,None)
    return {"n": len(recs)}


@_safe
def js_update_style(style_json):
    if "cfg" not in STATE:
        raise ValueError("Ejecuta primero un análisis para aplicar el estilo.")
    requested = json.loads(style_json)
    allowed = set(PLOT_STYLE_DEFAULTS)
    STATE["cfg"].update({k: v for k, v in requested.items() if k in allowed})
    STATE["cfg"].update(plot_style(STATE["cfg"]))
    return {"style": {k: STATE["cfg"][k] for k in allowed}}


@_safe
def js_run_init(cfg_json):
    cfg = json.loads(cfg_json)
    cfg["alpha"] = float(cfg["alpha"])
    cfg["iterations"] = int(cfg.get("iterations", 5000))
    cfg["seed"] = int(cfg.get("seed", 2026))
    cfg["field_correction"] = cfg.get("field_correction", "bonferroni")
    cfg["auto_normality_cutoff"] = float(cfg.get("auto_normality_cutoff", 20))
    cfg["band_k"] = int(cfg.get("band_k", 1))
    cfg.update(plot_style(cfg))
    for k in ("groups", "cond", "cond_levels", "side_levels", "group_filter", "covariate"):
        cfg.setdefault(k, None)
    # Invalidate the previous result even if validation of this run fails.
    for k in ('cfg','results','bands','tab','run_rows'):
        STATE.pop(k, None)
    vm = STATE["varmap"]
    sel = vm[vm["variable"].astype(str).isin(cfg["vars"])].copy()
    validate_analysis(STATE["canon"], sel, cfg)
    cfg["field_count"] = len(sel)
    if cfg.get("side_mode") == "obs":
        raise ValueError("L y R no pueden tratarse como observaciones independientes; usa promedio o un solo lado.")
    dup = sel[sel["joint"].ne("") & sel["plane"].ne("")].groupby(
        ["joint", "plane"])["variable"].agg(list)
    dup = dup[dup.map(len) > 1]
    if len(dup):
        raise ValueError("Hay variables duplicadas en una misma articulación/plano: "
                         + "; ".join(", ".join(map(str, x)) for x in dup))
    collisions = STATE["quality"].get("subject_group_collisions", [])
    if collisions:
        raise ValueError("Un mismo ID aparece en varios grupos: " + ", ".join(collisions[:8]))
    jo = {j: i for i, j in enumerate(JOINT_ORDER)}
    po = {p: i for i, p in enumerate(PLANE_ORDER)}
    sel["_o"] = sel["joint"].map(jo).fillna(9) * 10 + sel["plane"].map(po).fillna(9)
    sel = sel.sort_values("_o").drop(columns="_o")
    STATE["run_rows"] = sel.to_dict("records")
    STATE["cfg"] = cfg
    STATE["results"], STATE["bands"] = {}, {}
    return {"vars": [r["variable"] for r in STATE["run_rows"]]}


@_safe
def js_run_var(var):
    import warnings as _w
    vrow = next(r for r in STATE["run_rows"] if r["variable"] == var)
    canon, meta, cfg = STATE["canon"], STATE["meta"], STATE["cfg"]
    with _w.catch_warnings():
        _w.simplefilter("ignore")
        try:
            r = run_one(canon, meta, vrow, cfg)
        except Exception as e:
            r = {"variable": var, "joint": vrow.get("joint", ""),
                 "plane": vrow.get("plane", ""), "error": str(e)}
        STATE["results"][var] = r
        try:
            STATE["bands"][var] = compute_band(canon, var, cfg)
        except Exception:
            STATE["bands"][var] = None
    if "error" in r:
        return {"var": var, "okv": False, "error": r["error"]}
    return {"var": var, "okv": True, "mode": r["mode_used"],
            "clusters": [{"x0": round(c["x0"], 1), "x1": round(c["x1"], 1),
                          "p": fmt_p(c["p"])} for c in r["clusters"]]}


@_safe
def js_run_done():
    res, cfg = STATE["results"], STATE["cfg"]
    res = apply_field_correction(res, cfg)
    STATE["results"] = res
    tab = results_table(res, cfg["lang"])
    tab = tab.astype(object).where(pd.notna(tab), "")
    STATE["tab"] = tab
    detail, ph = {}, {}
    for v, r in res.items():
        if "error" in r:
            continue
        detail[v] = {"mode": r["mode_used"], "zstar": round(float(r["zstar"]), 2),
                     "stat": r["stat_name"], "df": r["df_str"],
                     "field_p_adj": round(float(r.get("field_p_adj", 1.0)), 4),
                     "field_correction": r.get("field_correction", "none"),
                     "confirmed": bool(confirmed_clusters(r)),
                     "raw_clusters": len(r.get("clusters", [])),
                     "norm": None if r.get("normality_pct") is None
                     else int(round(r["normality_pct"]))}
        if r.get("posthoc"):
            ph[v] = [p["label"] for p in r["posthoc"]["pairs"] if "error" not in p]
    return {"table": {"columns": list(map(str, tab.columns)),
                      "rows": tab.astype(str).values.tolist()},
            "okVars": list(detail), "detail": detail, "posthoc": ph,
            "warnings": [f"{v}: {w}" for v, r in res.items() for w in r.get("warnings", [])],
            "errors": [f"{v}: {r['error']}" for v, r in res.items() if "error" in r],
            "nsig": sum(1 for r in res.values() if confirmed_clusters(r)),
            "nsig_raw": sum(1 for r in res.values() if r.get("clusters")),
            "correction": cfg.get("field_correction", "bonferroni"),
            "ntot": len(res)}


_MIME = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}


def _b64fig(fig, fmt, dpi):
    b = fig_to_bytes(fig, fmt, int(dpi))
    plt.close(fig)
    return base64.b64encode(b).decode()


def _mkreport(include_spm, title):
    res, bands, cfg = STATE["results"], STATE["bands"], STATE["cfg"]
    vm = STATE["varmap"]
    sel = vm[vm["variable"].isin(res.keys())]
    return fig_report(res, bands, sel, cfg["lang"], cfg,
                      include_spm=bool(include_spm), title=title or None)


@_safe
def js_fig_report(dpi, include_spm, title):
    fig, extras = _mkreport(include_spm, title)
    return {"png": _b64fig(fig, "png", dpi), "extras": extras}


@_safe
def js_export_report(fmt, dpi, include_spm, title):
    fig, _ = _mkreport(include_spm, title)
    return {"b64": _b64fig(fig, fmt, dpi), "mime": _MIME[fmt],
            "fname": "gaitspm_informe." + fmt}


@_safe
def js_fig_detail(var, dpi):
    r = STATE["results"][var]
    fig = fig_detail(r, STATE["bands"].get(var), STATE["cfg"]["lang"], STATE["cfg"])
    return {"png": _b64fig(fig, "png", dpi)}


@_safe
def js_export_detail(var, fmt, dpi):
    r = STATE["results"][var]
    fig = fig_detail(r, STATE["bands"].get(var), STATE["cfg"]["lang"], STATE["cfg"])
    return {"b64": _b64fig(fig, fmt, dpi), "mime": _MIME[fmt],
            "fname": "gaitspm_" + var + "." + fmt}


@_safe
def js_fig_pair(var, label, dpi):
    r = STATE["results"][var]
    p = next(q for q in r["posthoc"]["pairs"] if q["label"] == label)
    fig = fig_pair(r, p, STATE["cfg"]["lang"], STATE["cfg"])
    return {"png": _b64fig(fig, "png", dpi)}


@_safe
def js_texts():
    res, cfg = STATE["results"], STATE["cfg"]
    return {"mt_es": methods_text(cfg, res, "es"), "mt_en": methods_text(cfg, res, "en"),
            "rt_es": results_text(res, cfg, "es"), "rt_en": results_text(res, cfg, "en"),
            "citas": CITAS}


@_safe
def js_table_csv():
    csv = STATE["tab"].to_csv(index=False, sep=";", decimal=",")
    return {"b64": base64.b64encode(("\ufeff" + csv).encode("utf-8")).decode(),
            "mime": "text/csv", "fname": "gaitspm_tabla.csv"}


@_safe
def js_table_xlsx():
    buf = _io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        STATE["tab"].to_excel(w, index=False, sheet_name="SPM")
    return {"b64": base64.b64encode(buf.getvalue()).decode(),
            "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "fname": "gaitspm_tabla.xlsx"}


@_safe
def js_templates():
    canon, meta, covs, vm = demo_dataset(2)
    wide = demo_wide_df(canon, meta)
    wide = wide[wide["condicion"].astype(str).isin(["PRE", "POST"])]
    subs = meta["subject"].head(3).tolist()
    ld = canon[canon["subject"].astype(str).isin(subs)
               & (canon["condition"].astype(str) == "PRE")].copy()
    ld = ld.rename(columns={"subject": "sujeto", "group": "grupo",
                            "condition": "condicion", "side": "lado",
                            "node": "punto", "value": "valor"})
    ld["velocidad"] = ld["sujeto"].astype(str).map(meta.set_index("subject")["velocidad"])
    return {"wide": base64.b64encode(wide.to_csv(index=False).encode()).decode(),
            "long": base64.b64encode(ld.to_csv(index=False).encode()).decode()}


# estilo global de figuras (una vez)
apply_matlab_style()
from matplotlib.font_manager import fontManager
_installed_fonts = {f.name for f in fontManager.ttflist}
plt.rcParams["font.family"] = [next((f for f in ("Arial", "Liberation Sans", "DejaVu Sans") if f in _installed_fonts), "sans-serif")]


@_safe
def js_set_language(lang):
    if lang not in ("es", "en"):
        raise ValueError("Invalid language")
    if "cfg" in STATE:
        STATE["cfg"]["lang"] = lang
        if STATE.get("results"):
            STATE["tab"] = results_table(STATE["results"], lang)
    return {"lang": lang}

@_safe
def js_fig_panels(variables_json):
    cfg = STATE["cfg"]
    panels = []
    for v in json.loads(variables_json)[:3]:
        r = STATE["results"].get(v)
        if not r or "error" in r:
            continue
        with plt.rc_context({"font.size": 9, "axes.titlesize": 10, "svg.fonttype": "path"}):
            f, ax = plt.subplots(2, 1, figsize=(4.1, 4.4), gridspec_kw={"height_ratios": [1.1, 1]})
            plot_kin(ax[0], r, STATE["bands"].get(v), cfg["lang"], True, cfg)
            plot_spm(ax[1], r, cfg["lang"], True, cfg)
            f.subplots_adjust(left=.15, right=.97, top=.93, bottom=.1, hspace=.4)
            panels.append({"variable": v, "title": variable_title(r, cfg["lang"]),
                "svg": _b64fig(f, "svg", 110),
                "clusters": [{"x0": c["x0"], "x1": c["x1"], "p": c["p"]} for c in r["clusters"]],
                "confirmed": bool(confirmed_clusters(r))})
    return {"panels": panels}

@_safe
def js_synthetic_catalog():
    return {"datasets": synthetic_catalog()}

@_safe
def js_load_synthetic(key):
    canon, meta, covs, vm = synthetic_dataset(key)
    _store(canon, meta, covs)
    STATE["varmap"] = vm
    return {**_payload(), "synthetic": True, "dataset": next(d for d in synthetic_catalog() if d["key"] == key)}


@_safe
def js_explain():
    """Educational summaries computed from the current result, never canned p-values."""
    cfg=STATE['cfg']; summaries=[]
    for var,r in STATE['results'].items():
        if 'error' in r:
            summaries.append(dict(variable=var,error=r['error']))
            continue
        labels = r.get('direction')
        clusters=[]
        for c in confirmed_clusters(r):
            indices=(NODES>=c['x0']) & (NODES<=c['x1'])
            if not indices.any():
                indices[int(np.clip(round((c['x0']+c['x1'])/2),0,100))]=True
            diff=None
            if r['plot']['type']=='groups' and len(r['plot']['groups'])==2:
                a,b=r['plot']['groups'];diff=float(np.mean(a['mean'][indices]-b['mean'][indices]))
            clusters.append(dict(start=c['x0'],end=c['x1'],p_adjusted=c.get('p_field_adj',c['p']),
                                 mean_difference_deg=diff, direction=labels))
        ns=([{'label':g['label'],'n':g['n']} for g in r['plot']['groups']]
            if r['plot']['type']=='groups' else [{'label':r['plot']['covname'],'n':len(r['plot']['x'])}])
        summaries.append(dict(variable=var,n=r.get('n_included'),samples=ns,
                              excluded=r.get('excluded_subjects',[]),clusters=clusters,
                              statistic=r['stat_name'],mode=r['mode_used'],warnings=r['warnings'],
                              model=r.get('model'), alpha=r['alpha'],
                              effect_count=r.get('effect_count',1), threshold=float(r['zstar']),
                              statistic_field=np.asarray(r['z']).tolist(), raw_clusters=r['clusters']))
    return dict(summaries=summaries,example=STATE.get('example'),configuration=cfg,
                software={'GaitSPM':VERSION,'spm1d':spm1d.__version__})


@_safe
def js_download_example_csv(key):
    c,m,_,_=synthetic_dataset(key)
    keys=['subject','group','condition','side']
    wide=c.pivot(index=keys,columns=['variable','node'],values='value')
    wide.columns=[f'{var}_{node}' for var,node in wide.columns]
    wide=wide.reset_index().merge(m[keys+['technical_score']],on=keys,how='left')
    return {'b64':base64.b64encode(wide.to_csv(index=False).encode('utf-8-sig')).decode(),
            'mime':'text/csv','fname':key+'.csv'}
