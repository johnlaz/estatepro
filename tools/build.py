"""
Zip Market Explorer - build script.

Reads the realtor.com Inventory Core Metrics *History* CSVs in raw/ and writes
compact JSON for the static site into site/d/.

    python build.py            # full build + validation report
    python build.py --quick    # skip the zip file (fast iteration on the small files)

The build exits with a non-zero status if any validation check fails.
"""
from __future__ import annotations

import csv
import json
import os
import random
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
SITE = ROOT / "site"
OUT = SITE / "d"

FILES = {
    "zip": "RDC_Inventory_Core_Metrics_Zip_History.csv",
    "county": "RDC_Inventory_Core_Metrics_County_History.csv",
    "metro": "RDC_Inventory_Core_Metrics_Metro_History.csv",
    "state": "RDC_Inventory_Core_Metrics_State_History.csv",
    "us": "RDC_Inventory_Core_Metrics_Country_History.csv",
}

# short key -> (source column, scale). Values are stored as round(value * scale).
METRICS = {
    "p": ("median_listing_price", 1),
    "a": ("average_listing_price", 1),
    "f": ("median_listing_price_per_square_foot", 1),
    "s": ("median_square_feet", 1),
    "al": ("active_listing_count", 1),
    "nl": ("new_listing_count", 1),
    "pl": ("pending_listing_count", 1),
    "tl": ("total_listing_count", 1),
    "dom": ("median_days_on_market", 1),
    "prs": ("price_reduced_share", 10000),
    "pis": ("price_increased_share", 10000),
    "pr": ("pending_ratio", 10000),
    "q": ("quality_flag", 1),
}
SCALE = {k: sc for k, (_, sc) in METRICS.items() if sc != 1}
RANK_KEYS = ["p", "f", "al", "dom", "prs", "pr"]
ZIP_SHARD_MB_WARN = 12
SITE_MB_LIMIT = 500

STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT", "10": "DE",
    "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD", "25": "MA", "26": "MI", "27": "MN",
    "28": "MS", "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ", "35": "NM",
    "36": "NY", "37": "NC", "38": "ND", "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA",
    "54": "WV", "55": "WI", "56": "WY", "72": "PR",
}

problems: list[str] = []   # validation failures -> non-zero exit
warnings: list[str] = []   # worth knowing, not fatal


def log(msg: str) -> None:
    print(msg, flush=True)


# ---------------------------------------------------------------- reading
_resolved: dict[str, Path | None] = {}


def resolve(kind: str) -> Path | None:
    """Exact file name, or else the newest browser-renamed copy such as 'name (1).csv'."""
    if kind in _resolved:
        return _resolved[kind]
    exact = RAW / FILES[kind]
    path = exact if exact.exists() else None
    if path is None:
        stem = exact.stem
        copies = sorted(RAW.glob(f"{stem} (*).csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if copies:
            path = copies[0]
            warnings.append(f"using '{path.name}' - rename it to '{exact.name}'")
    _resolved[kind] = path
    return path


def read_history(kind: str, key_col: str, extra_cols: list[str]) -> pd.DataFrame | None:
    """Read one History CSV safely: strings in, footnote rows dropped, metrics numeric."""
    path = resolve(kind)
    if path is None:
        return None
    t0 = time.time()
    metric_cols = [c for c, _ in METRICS.values()]
    header = pd.read_csv(path, nrows=0).columns.tolist()
    missing = [c for c in metric_cols + [key_col] if c not in header]
    if missing:
        problems.append(f"{path.name}: missing columns {missing}")
        return None
    use = ["month_date_yyyymm", key_col] + [c for c in extra_cols if c in header] + metric_cols
    parts, dropped = [], 0
    # Everything is read as text first so a stray footnote row can never break the dtypes.
    for chunk in pd.read_csv(path, usecols=use, dtype=str, chunksize=500_000,
                             keep_default_na=False, na_values=[""]):
        month = pd.to_numeric(chunk["month_date_yyyymm"], errors="coerce")
        ok = month.notna() & (month >= 190001) & (month <= 299912)
        dropped += int((~ok).sum())
        chunk = chunk[ok].copy()
        chunk["month"] = month[ok].astype(int)
        for c in metric_cols:
            chunk[c] = pd.to_numeric(chunk[c], errors="coerce")
        parts.append(chunk.drop(columns=["month_date_yyyymm"]))
    df = pd.concat(parts, ignore_index=True)
    df[key_col] = df[key_col].astype(str).str.strip()
    if kind == "zip":
        df[key_col] = df[key_col].str.zfill(5)
    if kind == "county":
        df[key_col] = df[key_col].str.zfill(5)
    if kind == "metro":
        df[key_col] = df[key_col].str.replace(r"\.0$", "", regex=True)
    dupes = int(df.duplicated([key_col, "month"]).sum())
    if dupes:
        warnings.append(f"{path.name}: {dupes} duplicate (key, month) rows - kept the last one")
        df = df.drop_duplicates([key_col, "month"], keep="last")
    df.attrs.update(rows=len(df), dropped=dropped, secs=time.time() - t0, file=path.name)
    log(f"  read {path.name}: {len(df):,} rows, {dropped} non-data rows dropped ({time.time() - t0:.0f}s)")
    return df


# ---------------------------------------------------------------- names
def title_place(name: str | None) -> str | None:
    """'tucker, ga' -> 'Tucker, GA'; 'fulton, ga' -> 'Fulton, GA'."""
    if not isinstance(name, str) or not name.strip():
        return None
    name = name.strip()
    if "," in name:
        place, st = name.rsplit(",", 1)
        st = st.strip().upper()
    else:
        place, st = name, ""
    words = []
    for w in place.split(" "):
        words.append("-".join(p[:1].upper() + p[1:] for p in w.split("-")))
    out = " ".join(words)
    return f"{out}, {st}" if st else out


def state_of(name: str | None) -> str | None:
    if not isinstance(name, str) or "," not in name:
        return None
    st = name.rsplit(",", 1)[1].strip().upper()
    return st[:2] if len(st) >= 2 and st[:2].isalpha() else None


def latest_names(df: pd.DataFrame, key_col: str, name_col: str) -> pd.Series:
    """Latest non-blank name per key."""
    named = df[[key_col, "month", name_col]].dropna(subset=[name_col])
    named = named[named[name_col].str.strip() != ""]
    return named.sort_values("month").groupby(key_col)[name_col].last()


# ---------------------------------------------------------------- encoding
def encode(df: pd.DataFrame, key_col: str, months: list[int]) -> dict[str, dict[str, str]]:
    """Return {key: {metric: 'v,,v,...'}} aligned to the global month list."""
    keys = np.sort(df[key_col].unique())
    kpos = {k: i for i, k in enumerate(keys)}
    mpos = {m: i for i, m in enumerate(months)}
    ki = df[key_col].map(kpos).to_numpy()
    mi = df["month"].map(mpos).to_numpy()
    out: dict[str, dict[str, str]] = {k: {} for k in keys}
    for short, (col, sc) in METRICS.items():
        mat = np.full((len(keys), len(months)), np.nan)
        mat[ki, mi] = df[col].to_numpy(dtype=float) * sc
        present = ~np.isnan(mat)
        if short == "q" and not np.nansum(mat):
            continue  # all-zero quality flags carry no information
        ints = np.where(present, np.rint(np.nan_to_num(mat)), 0).astype(np.int64).astype(str)
        ints[~present] = ""
        any_row = present.any(axis=1)
        for i, k in enumerate(keys):
            if any_row[i]:
                out[k][short] = ",".join(ints[i])
    return out


def decode_value(enc: dict[str, str], short: str, month_idx: int) -> float | None:
    s = enc.get(short)
    if s is None:
        return None
    v = s.split(",")[month_idx]
    return None if v == "" else int(v) / METRICS[short][1]


# ---------------------------------------------------------------- ranks
def pct_ranks(latest: pd.DataFrame, key_col: str, group_col: str) -> dict[str, dict[str, int]]:
    """Percentile (0-100, 100 = highest) of each key within its group for RANK_KEYS."""
    out: dict[str, dict[str, int]] = {}
    for short in RANK_KEYS:
        col = METRICS[short][0]
        sub = latest[[key_col, group_col, col]].dropna()
        if sub.empty:
            continue
        r = sub.groupby(group_col)[col].rank(method="average", pct=True) * 100
        for k, v in zip(sub[key_col], r):
            out.setdefault(k, {})[short] = int(round(v))
    return out


# ---------------------------------------------------------------- writing
def write_json(path: Path, obj) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    path.write_text(data, encoding="utf-8")
    return len(data.encode("utf-8"))


def mb(n: int) -> str:
    return f"{n / 1e6:.1f} MB"


# ---------------------------------------------------------------- spot check
def spot_check(kind: str, key_col: str, keys: list[str], shard_of, months: list[int]) -> None:
    li = len(months) - 1
    month = months[li]
    log(f"  spot check {kind} @ {month}:")
    wanted = set(keys)
    found: dict[str, dict[str, str]] = {}
    with open(resolve(kind), newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("month_date_yyyymm", "").strip() != str(month):
                continue
            k = (row.get(key_col) or "").strip()
            if kind in ("zip", "county"):
                k = k.zfill(5)
            if k in wanted:
                found[k] = row
    for k in keys:
        shard_path = shard_of(k)
        rec = json.loads(shard_path.read_text(encoding="utf-8")).get(k)
        row = found.get(k)
        if rec is None or row is None:
            problems.append(f"spot check {kind} {k}: missing in {'output' if rec is None else 'raw'}")
            log(f"    {k}: MISSING")
            continue
        line = []
        for short in ("p", "al", "pr"):
            col, sc = METRICS[short]
            raw_s = (row.get(col) or "").strip()
            raw_v = None if raw_s == "" else float(raw_s)
            out_v = decode_value(rec["d"], short, li)
            if raw_v is None or out_v is None:
                ok = raw_v is None and out_v is None
            else:
                ok = abs(out_v - raw_v) <= 0.5 / sc + 1e-9
            line.append(f"{short}={out_v} vs raw {raw_v} {'ok' if ok else 'MISMATCH'}")
            if not ok:
                problems.append(f"spot check {kind} {k} {col}: output {out_v} != raw {raw_v}")
        log(f"    {k} ({rec.get('n')}): " + "; ".join(line))


# ---------------------------------------------------------------- main
def main() -> int:
    quick = "--quick" in sys.argv
    t_start = time.time()
    log(f"Zip Market Explorer build - {datetime.now():%Y-%m-%d %H:%M}")
    if not RAW.exists():
        log("raw/ folder not found")
        return 1

    log("Reading raw files")
    st = read_history("state", "state_id", ["state"])
    me = read_history("metro", "cbsa_code", ["cbsa_title", "HouseholdRank"])
    co = read_history("county", "county_fips", ["county_name"])
    us = read_history("us", "country", [])
    zp = None if quick else read_history("zip", "postal_code", ["zip_name"])
    if us is None:
        warnings.append(f"{FILES['us']} not found in raw/ - US view and US benchmark will be missing")
    for name, df in [("state", st), ("metro", me), ("county", co)] + ([] if quick else [("zip", zp)]):
        if df is None:
            problems.append(f"{FILES[name]} could not be read")
    if problems:
        return report(None, t_start)

    frames = [d for d in (st, me, co, us, zp) if d is not None]
    months = sorted(set().union(*[set(d["month"].unique()) for d in frames]))
    months = [int(m) for m in months]
    latest = months[-1]
    expected, y, mo = [], months[0] // 100, months[0] % 100
    while y * 100 + mo <= latest:
        expected.append(y * 100 + mo)
        y, mo = (y + 1, 1) if mo == 12 else (y, mo + 1)
    gaps = [m for m in expected if m not in set(months)]
    if gaps:
        warnings.append(f"global month list has gaps: {gaps}")
    for d in frames:
        if d["month"].max() != latest:
            warnings.append(f"{d.attrs['file']} ends at {d['month'].max()}, others at {latest}")

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    idx: list[list] = []
    sizes: dict[str, int] = {}

    # ---- US
    if us is not None:
        us = us.assign(_k="us")
        enc = encode(us, "_k", months)
        sizes["us.json"] = write_json(OUT / "us.json", {"us": {"n": "United States", "d": enc["us"]}})
        idx.append(["us", "us", "United States", ""])

    # ---- states
    st_names = latest_names(st, "state_id", "state")
    enc = encode(st, "state_id", months)
    states = {}
    for k, d in enc.items():
        states[k] = {"n": st_names.get(k, k), "st": k, "d": d}
        idx.append(["state", k, st_names.get(k, k), k])
    sizes["states.json"] = write_json(OUT / "states.json", states)
    valid_states = set(states)

    # ---- metros
    me_names = latest_names(me, "cbsa_code", "cbsa_title")
    hr = (me.sort_values("month").dropna(subset=["HouseholdRank"]).groupby("cbsa_code")["HouseholdRank"].last()
          if "HouseholdRank" in me else pd.Series(dtype=str))
    enc = encode(me, "cbsa_code", months)
    shards: dict[str, dict] = {}
    for k, d in enc.items():
        n = me_names.get(k) or f"Metro {k}"
        stt = state_of(n)
        rec = {"n": n, "st": stt if stt in valid_states else None, "d": d}
        if k in hr.index:
            try:
                rec["hr"] = int(float(hr[k]))
            except ValueError:
                pass
        shards.setdefault(k[:2], {})[k] = rec
        idx.append(["metro", k, n, rec["st"] or ""])
    for p, obj in shards.items():
        sizes[f"metro/{p}.json"] = write_json(OUT / "metro" / f"{p}.json", obj)

    # ---- counties
    co_names = latest_names(co, "county_fips", "county_name")
    co["st"] = co["county_fips"].str[:2].map(STATE_FIPS)
    co_latest = co[co["month"] == latest]
    co_ranks = pct_ranks(co_latest, "county_fips", "st")
    co_n_state = co_latest.groupby("st")["county_fips"].nunique().to_dict()
    enc = encode(co, "county_fips", months)
    shards = {}
    for k, d in enc.items():
        n = title_place(co_names.get(k)) or f"County {k}"
        stt = STATE_FIPS.get(k[:2]) or state_of(n)
        rec = {"n": n, "st": stt, "d": d}
        if k in co_ranks:
            rec["rk"] = co_ranks[k]
        shards.setdefault(k[:2], {})[k] = rec
        idx.append(["county", k, n, stt or ""])
    for p, obj in shards.items():
        sizes[f"county/{p}.json"] = write_json(OUT / "county" / f"{p}.json", obj)

    zip_stats = {}
    if zp is not None:
        # ---- zips
        zp_names = latest_names(zp, "postal_code", "zip_name")
        keys = zp["postal_code"].unique()
        zst = pd.Series({k: state_of(zp_names.get(k)) for k in keys})
        zst = zst.where(zst.isin(valid_states))
        # Unnamed zips: borrow the most common state among named zips with the same 3-digit prefix.
        pref = pd.Series(zst.index.str[:3], index=zst.index)
        pref_state = zst.dropna().groupby(pref[zst.notna()]).agg(lambda s: s.mode().iat[0])
        inferred = zst.isna() & pref.map(pref_state).notna()
        zst = zst.fillna(pref.map(pref_state))
        zp["st"] = zp["postal_code"].map(zst)
        zp_latest = zp[zp["month"] == latest]
        z_ranks = pct_ranks(zp_latest, "postal_code", "st")
        log("  encoding zips...")
        enc = encode(zp, "postal_code", months)
        shards = {}
        unnamed = 0
        for k, d in enc.items():
            raw_n = zp_names.get(k)
            n = title_place(raw_n)
            if not n:
                unnamed += 1
            stt = zst.get(k)
            stt = stt if isinstance(stt, str) else None
            rec = {"n": n or f"Zip {k}", "st": stt, "d": d}
            if k in z_ranks:
                rec["rk"] = z_ranks[k]
            shards.setdefault(k[:2], {})[k] = rec
            idx.append(["zip", k, rec["n"], stt or ""])
        for p, obj in shards.items():
            sizes[f"zip/{p}.json"] = write_json(OUT / "zip" / f"{p}.json", obj)
        zip_stats = {"zips": len(enc), "unnamed": unnamed, "inferred_state": int(inferred.sum()),
                     "no_state": int(zst.isna().sum()), "in_latest": int(zp_latest["postal_code"].nunique())}

    # ---- meta
    type_order = {"us": 0, "state": 1, "metro": 2, "county": 3, "zip": 4}
    idx.sort(key=lambda r: (type_order[r[0]], r[1]))
    meta = {
        "built": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ"),
        "source": "realtor.com Inventory Core Metrics (History files)",
        "months": months,
        "scale": SCALE,
        "rankKeys": RANK_KEYS,
        "rankN": {"county": co_n_state,
                  "zip": (zp[zp["month"] == latest].groupby("st")["postal_code"].nunique().to_dict()
                          if zp is not None else {})},
        "hasUS": us is not None,
        "idx": idx,
    }
    sizes["meta.json"] = write_json(OUT / "meta.json", meta)

    # ---- validation
    log("Validation")
    if us is not None:
        # The country file's key is the name ("United States"); the output record is keyed "us".
        us_key = str(us["country"].iloc[0])
        us_rec = json.loads((OUT / "us.json").read_text(encoding="utf-8"))["us"]
        tmp = OUT / "_us_check.json"
        tmp.write_text(json.dumps({us_key: us_rec}), encoding="utf-8")
        spot_check("us", "country", [us_key], lambda k: tmp, months)
        tmp.unlink()
    spot_check("state", "state_id", ["GA", "CA", "TX"], lambda k: OUT / "states.json", months)
    spot_check("county", "county_fips", ["13089", "06037", "48201"],
               lambda k: OUT / "county" / f"{k[:2]}.json", months)
    if zp is not None:
        latest_zips = sorted(zp_latest.dropna(subset=["median_listing_price"])["postal_code"].unique())
        rnd = random.Random(latest)
        picks = ["30084"] + rnd.sample([z for z in latest_zips if z != "30084"], 2)
        spot_check("zip", "postal_code", picks, lambda k: OUT / "zip" / f"{k[:2]}.json", months)

    return report({"frames": frames, "months": months, "sizes": sizes, "zip": zip_stats,
                   "counts": {"states": len(states), "metros": me["cbsa_code"].nunique(),
                              "counties": co["county_fips"].nunique()}}, t_start)


def report(info, t_start) -> int:
    log("")
    log("=" * 64)
    log("BUILD REPORT")
    log("=" * 64)
    if info:
        m = info["months"]
        log(f"Months: {len(m)}  ({m[0]} -> {m[-1]})")
        log("Rows per file:")
        for d in info["frames"]:
            a = d.attrs
            log(f"  {a['file']:<52} {a['rows']:>10,} rows  {a['dropped']} dropped  "
                f"{d['month'].min()}-{d['month'].max()}")
        c = info["counts"]
        log(f"Geographies: {c['states']} states, {c['metros']} metros, {c['counties']} counties"
            + (f", {info['zip']['zips']:,} zips" if info["zip"] else ""))
        if info["zip"]:
            z = info["zip"]
            log(f"Zips: {z['in_latest']:,} in latest month; {z['unnamed']:,} with no name (shown as 'Zip #####'); "
                f"{z['inferred_state']:,} state inferred from 3-digit prefix; {z['no_state']} with no state")
        sizes = info["sizes"]
        total = sum(sizes.values())
        zsh = {k: v for k, v in sizes.items() if k.startswith("zip/")}
        log(f"Output: {len(sizes)} files, {mb(total)} total (limit {SITE_MB_LIMIT} MB)")
        log(f"  meta.json {mb(sizes['meta.json'])}")
        if zsh:
            big = max(zsh, key=zsh.get)
            log(f"  zip shards: {len(zsh)}, largest {big} {mb(zsh[big])}, median {mb(int(np.median(list(zsh.values()))))}")
            if zsh[big] > ZIP_SHARD_MB_WARN * 1e6:
                warnings.append(f"largest zip shard {big} is {mb(zsh[big])}")
        if total > SITE_MB_LIMIT * 1e6:
            problems.append(f"site data {mb(total)} exceeds {SITE_MB_LIMIT} MB")
    for w in warnings:
        log(f"WARNING: {w}")
    for p in problems:
        log(f"FAIL: {p}")
    log(f"Finished in {time.time() - t_start:.0f}s - {'FAILED' if problems else 'OK'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
