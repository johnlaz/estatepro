#!/usr/bin/env python3
"""
Build EstatePro's own copy of the market data from a Zip Market Explorer build.

Zip Market Explorer is a GeniusPete Project (https://petelazzaro.github.io/zip-market-explorer/).
Its data is realtor.com Inventory Core Metrics (listing metrics, not closed sales). EstatePro
keeps a trimmed copy in app/d/ so valuations keep working even if the original host moves.

The explorer publishes its data to the gh-pages branch of petelazzaro/zip-market-explorer.

    git clone --depth 1 --branch gh-pages https://github.com/petelazzaro/zip-market-explorer /tmp/zme
    python3 -I docs/refresh-market-data.py /tmp/zme/d app/d

What it keeps: the ZIP and county shards and the state file, last 24 months, only the series the
app uses. Records keep the explorer's format, plus "e": the global month index of the last value
(0 = Jul 2016), which the app needs because the arrays are trimmed. Refresh monthly.
"""
import json, sys, os, shutil
from pathlib import Path

KEEP = 24
SERIES = ['p', 'f', 's', 'al', 'dom', 'prs', 'pr', 'q']   # median price, $/sq ft, sq ft, active, DOM, price cuts, pending ratio, quality flag


def trim_record(rec):
    d = rec.get('d') or {}
    out_d, last = {}, None
    for k in SERIES:
        s = d.get(k)
        if s is None:
            continue
        vals = s.split(',')
        last = len(vals) - 1 if last is None else max(last, len(vals) - 1)
        out_d[k] = ','.join(vals[-KEEP:])
    if last is None:
        return None
    out = {'n': rec.get('n', ''), 'st': rec.get('st', ''), 'e': last, 'd': out_d}
    if rec.get('rk'):
        out['rk'] = rec['rk']
    return out


def trim_file(src, dst):
    data = json.loads(Path(src).read_text(encoding='utf-8'))
    out = {}
    for key, rec in data.items():
        t = trim_record(rec)
        if t:
            out[key] = t
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_text(json.dumps(out, separators=(',', ':')), encoding='utf-8')
    return len(out)


def main(src_dir, out_dir):
    src, out = Path(src_dir), Path(out_dir)
    if not (src / 'states.json').exists():
        sys.exit('No states.json in %s: point this at the explorer\'s d/ folder' % src)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    counts = {'zip': 0, 'county': 0}
    for kind in ('zip', 'county'):
        for f in sorted((src / kind).glob('*.json')):
            counts[kind] += trim_file(f, out / kind / f.name)
    trim_file(src / 'states.json', out / 'states.json')
    shutil.copyfile(src / 'zip_to_county.json', out / 'zip_to_county.json')
    meta = json.loads((src / 'meta.json').read_text(encoding='utf-8'))
    months = meta.get('months') or []
    info = {
        'built': meta.get('built'),
        'lastYM': months[-1] if months else None,
        'lastIdx': len(months) - 1 if months else None,
        'monthsKept': KEEP,
        'source': 'Zip Market Explorer (GeniusPete Project), realtor.com Inventory Core Metrics',
        'url': 'https://petelazzaro.github.io/zip-market-explorer/',
    }
    (out / 'info.json').write_text(json.dumps(info, indent=1), encoding='utf-8')
    total = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
    print('zips: %d, counties: %d, last month: %s, size: %.1f MB' % (counts['zip'], counts['county'], info['lastYM'], total / 1e6))


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
