# EstatePro 4.2.0 — change log

| File | Change |
|---|---|
| app/index.html | New Explorer tab (search, market read, charts, rankings, CSV copy); Notes panel gets an email link |
| app/d/ | Trimmed snapshot of the market data (GeniusPete Project), 24 months; served first; the explorer's live site is only a backup |
| tools/, .github/workflows/refresh-data.yml | Monthly Action: downloads realtor.com files, builds (from the explorer's build.py), trims into app/d/ |
| app/sw.js | VERSION 4.2.0; /app/d/ excluded from the service-worker cache |

# EstatePro 4.1.0 — change log

| File | What changed | Why |
|---|---|---|
| app/index.html | Valuation engine: ZIP data → median listing $/sq ft × size × asking-to-sale gap × condition × your adjustment | The old valuation was an AI recalling comps it could not see |
| app/index.html | Data loader for Zip Market Explorer files (zip, county, state), 3-day local cache, county blend for thin ZIPs | Real inputs, works offline from cache |
| app/index.html | Result shows each step tagged data / assumption / estimate / you, market evidence table, 36-month chart | Every number can be checked or argued with |
| app/index.html | Verdict, deal grade, confidence, trend and range computed, not generated | AI no longer produces numbers |
| app/index.html | AI reduced to one optional call that interprets the numbers; pasted listing is a cross-check only | Was five calls, three of them invented market stats |
| app/index.html | Removed Parse URL, Floor/Unit, Utilities, Property Segment, mortgage-rate tile, fake comps, comp alert | Dead or meaningless (parseListingUrl was never defined) |
| app/index.html | Added ZIP field; beds, baths, year, lot, features moved under optional detail | Only ZIP, size, condition and ask change the answer |
| app/index.html | Market tab rebuilt on real data; invented walkability, school and investment scores removed | Those were made up |
| app/index.html | Lookup stops writing an AI price into Asking; recalled sq ft is flagged | It poisoned the verdict |
| app/index.html | Slider recalculates via the engine; resets per property; no history spam | Verdict was stale and history gained an entry per tick |
| app/sw.js | VERSION 4.1.0 | Matches APP_VERSION |
| README.md, index.html, docs/*.svg | Copy updated | No more "AI comps" |

Reinstall: no. Saved data is unchanged and old history and portfolio entries still open.

---

# EstatePro 4.0.0 — change log

| File | What changed | Why |
|---|---|---|
| app/index.html | Rejoined two JS strings broken by the © comment | Whole script failed to parse; every tab and button was dead |
| app/index.html | Renamed LazEstate → EstatePro; new navy/gold palette; Inter font; top-bar logo | New name, icon and look |
| app/index.html | Bottom tab bar (Value, Portfolio, Deals, Tools, More) with sheets; top tabs desktop-only | Mobile nav was clipped |
| app/index.html | County/listing link and extra detail folded; sticky Get Valuation button; scroll to result | Less to look at on a phone |
| app/index.html | Groq model list: fetch on key save + Refresh button; flags missing models; never swaps | Mixtral is retired; list was hardcoded |
| app/index.html | Version stamp (v4.0.0) tied to SW cache; update bar; hash deep links; aria labels, 44px targets | Audit items 4, 12 |
| app/index.html | Local-server tools tucked under Advanced; no localhost ping unless used | Console errors on every load |
| app/index.html | "Estimate only" notice under the valuation button | Honesty about data |
| app/sw.js | Rewritten: network-first pages, cache-first assets, update prompt, versioned cache | Stale HTML bug |
| app/manifest.json | id, 192/512 icons (any + maskable), screenshots, shortcuts, relative paths | Audit item 3 |
| app/icon-192.png, icon-512.png | New, from supplied logo | New icon |
| app/shot-*.png | Simulated screenshots from demo data | Manifest screenshots |
| index.html | New landing page; mobile overflow fixed; email in footer | Audit items 7, 11 |
| README.md, docs/*.svg | Full README + banner, how-it-works, architecture | Audit item 10 |
| Removed | root sw.js, root manifest.json, 404.html, both icons/ folders, app/README.md, app/_config.yml, app/download, .keep files | Flatten to target layout |

Reinstall: yes. The repo name and path change (/lazestate/ → /estatepro/), so existing installs must be removed and the app installed again from the new URL. Saved data lives in the browser under key `lazestate_v1` on johnlaz.github.io and carries over automatically; use Settings → Export first if you want a backup.
