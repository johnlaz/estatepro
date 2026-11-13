#!/usr/bin/env python3
"""
Build EstatePro's own copy of the market data from a Zip Market Explorer build.

Zip Market Explorer is a GeniusPete Project (https://petelazzaro.github.io/zip-market-explorer/).
Its data is realtor.com Inventory Core Metrics (listing metrics, not closed sales). EstatePro
keeps a trimmed copy in app/d/ so valuations keep working even if the original host moves.

Normally the monthly GitHub Action (.github/workflows/refresh-data.yml) runs tools/build.py on the
free realtor.com files and then this script. To run it by hand against any explorer-format data:

    python3 -I tools/trim-market-data.py <explorer d/ folder> <out> [folder holding the current zip_to_county.json]

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


def main(src_dir, out_dir, keep_dir=None):
    src, out = Path(src_dir), Path(out_dir)
    keep = Path(keep_dir) if keep_dir else out        # where an existing zip_to_county.json can be taken from
    if not (src / 'states.json').exists():
        sys.exit('No states.json in %s: point this at the explorer\'s d/ folder' % src)
    z2c_keep = None
    if not (src / 'zip_to_county.json').exists():          # build.py does not make it; it only changes once a decade (Census ZCTA file)
        old = keep / 'zip_to_county.json'
        if not old.exists():
            sys.exit('No zip_to_county.json in the source or in %s' % keep)
        z2c_keep = old.read_bytes()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    counts = {'zip': 0, 'county': 0}
    for kind in ('zip', 'county'):
        for f in sorted((src / kind).glob('*.json')):
            counts[kind] += trim_file(f, out / kind / f.name)
    trim_file(src / 'states.json', out / 'states.json')
    if z2c_keep is not None:
        (out / 'zip_to_county.json').write_bytes(z2c_keep)
    else:
        shutil.copyfile(src / 'zip_to_county.json', out / 'zip_to_county.json')
    trim_file(src / 'us.json', out / 'us.json')
    for m in sorted((src / 'metro').glob('*.json')):
        trim_file(m, out / 'metro' / m.name)
    meta = json.loads((src / 'meta.json').read_text(encoding='utf-8'))
    (out / 'meta.json').write_text(json.dumps({'idx': meta.get('idx', [])}, separators=(',', ':')), encoding='utf-8')   # place search list
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
    if counts['zip'] < 30000 or counts['county'] < 3000:
        sys.exit('Sanity check failed: only %d zips and %d counties, refusing to publish' % (counts['zip'], counts['county']))
    print('zips: %d, counties: %d, last month: %s, size: %.1f MB' % (counts['zip'], counts['county'], info['lastYM'], total / 1e6))


if __name__ == '__main__':
    if len(sys.argv) not in (3, 4):
        sys.exit(__doc__)
    main(*sys.argv[1:])
