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
