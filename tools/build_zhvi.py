"""
Zillow Home Value Index (ZHVI) by ZIP, trimmed for EstatePro.

Source: Zillow Research public data, "ZHVI All Homes (SFR, Condo/Co-op), smoothed, seasonally adjusted, ZIP Code".
https://www.zillow.com/research/data/   (data is Zillow's; shown in the app with attribution)

    python3 -I tools/build_zhvi.py <Zip_zhvi_..._month.csv> <out dir>

Writes <out>/<first 2 digits>.json = { "<zip>": {"e": global month index of last value (0 = Jul 2016), "v": "24 comma separated dollars"} }.
"""
import csv, json, sys
from pathlib import Path

KEEP = 24


def month_index(date):                       # '2026-09-30' -> months since Jul 2016
    y, m = int(date[:4]), int(date[5:7])
    return (y - 2016) * 12 + m - 7


def main(src, out):
    out = Path(out)
    shards, last_idx, n = {}, None, 0
    with open(src, newline='', encoding='utf-8-sig') as f:
        rd = csv.reader(f)
        head = next(rd)
        cols = {c: i for i, c in enumerate(head)}
        if 'RegionName' not in cols or 'RegionType' not in cols:
            sys.exit('Unexpected columns: %s' % head[:12])
        dates = [c for c in head if len(c) == 10 and c[4] == '-' and c[7] == '-']
        if len(dates) < KEEP:
            sys.exit('Too few month columns: %d' % len(dates))
        use = dates[-KEEP:]
        last_idx = month_index(use[-1])
        ci = [cols[d] for d in use]
        for row in rd:
            if len(row) <= max(ci) or row[cols['RegionType']] != 'zip':
                continue
            z = row[cols['RegionName']].zfill(5)
            vals = [row[i] for i in ci]
            if all(v == '' for v in vals):
                continue
            shards.setdefault(z[:2], {})[z] = {'e': last_idx, 'v': ','.join('' if v == '' else str(int(round(float(v)))) for v in vals)}
            n += 1
    if n < 20000:
        sys.exit('Sanity check failed: only %d ZIPs' % n)
    out.mkdir(parents=True, exist_ok=True)
    for k, d in shards.items():
        (out / (k + '.json')).write_text(json.dumps(d, separators=(',', ':')), encoding='utf-8')
    print('zhvi: %d zips, %d shards, last month index %d' % (n, len(shards), last_idx))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
