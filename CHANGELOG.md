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

## 4.3.6
- Typing a ZIP always fills City and State from the market data.
- Removed the address Lookup button and status dot (it only asked the AI to recall facts from the address text). A ZIP in the address still fills the ZIP field.

## 4.3.7
- Removed the Site Analysis "AI Analysis" button. It asked the AI about flood risk and schools from the address text alone, with no data behind it. The map, nearby places and FEMA flood link remain.

## 4.3.8
- Removed the optional local server (header dot, Settings downloads, localhost calls). Map It and nearby places already used OpenStreetMap directly.

## 4.3.9
- Nearby places: added fire, police, gas stations; added a wider search (about 25 miles) for airport, hospital, interstate, mall and university, keeping the nearest few; popups show distance; map zooms to fit.

## 4.3.10
- Nearby places: results are filtered by type (no more street names as hospitals), police and mall searches fixed, and nearest major highways (I-4, I-95, I-75, I-10, Florida Turnpike) added.

## 4.3.11
- Map It only accepts US results and uses the ZIP, city and state from the Value form, so a street name alone no longer lands overseas.
- History: each entry now has Reopen (refills the form), Map, + Portfolio, Compare, Note and delete buttons. New entries also store ZIP, lot, condition and features.

## 4.3.12
- Valuation result: "Check this address on" buttons for Zillow, Realtor.com, Redfin and a web search.

## 4.3.13 / 4.3.14
- Market and Explorer merged into one Market tab (the Explorer). The old Market tab is gone; its AI briefing is now a button on any ZIP in the Market tab.
- Compare is now a plain side-by-side of real numbers (price, $/sq ft, saved EstatePro value, value vs list). The AI scores and "AI fair value" it used to make up are gone.
- Deal Tools: removed Cash-on-Cash Interpreter (the Analyze tab covers it) and Rent Roll Summary; Negotiation Coach now prefills the ask price and valuation; added a review-before-sending note.

## 4.3.15
- Realtor.com and Redfin buttons jump to the top search result (I am feeling lucky) instead of a results page. "Open in a new tab" checkbox under the listing buttons (default on).

## 4.3.16
- New-tab toggle is now a labelled button (the checkbox rendered as a wide empty box).

## 4.3.17
- Realtor.com and Redfin buttons back to a site-restricted Google search (the lucky redirect still showed a Google click-through page). New-tab choice is saved with the app data.

## 4.4.0
- Map It now looks addresses up with the US Census Geocoder first (fast, free, no strict rate limit) and falls back to OpenStreetMap. This fixes "failed to fetch" when the OpenStreetMap geocoder was refusing requests. Marker popup and message show the address the Census matched.
- Nearby places now appear in a list below the map, grouped by type with distance and compass direction. Tap one to find it on the map. Results are cached on the device for 30 days, and the search stops early if the map server is refusing requests.
- PDF report rebuilt: how the value was calculated, market evidence table and chart, Zillow cross-check, deal metrics, mortgage, nearby places with distances, and a sources and limits block. Removed the empty Comparable Sales section.
