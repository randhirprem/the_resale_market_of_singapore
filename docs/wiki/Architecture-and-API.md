# Architecture and API

[Wiki home](Home.md) · [Maintenance](Maintenance.md)

## Data flow

```text
Five selected resale CSVs -> validated atomic import -> data/hdb.sqlite3
                                             |
                              Python read-only HTTP API
                                             |
                            React dashboard / Leaflet / Recharts
                                             |
                Local URA geometry + online OpenStreetMap tiles
```

| Component | Responsibility |
| --- | --- |
| `backend/data.py` | Import, normalization, indexes, exact statistics and transaction queries |
| `backend/asking.py` | Comparable-sale selection, sample safeguards and price classification |
| `backend/price_models.py` | Offline regression fitting, validation and artifact loading |
| `backend/insights.py` | Balanced secondary-school ranking and matching safeguards |
| `src/AskingPrice.jsx` | Independent asking-price form, assessment and supporting records |
| `src/PriceEquations.jsx` | National/estate equations, factor comparisons and audit |
| `backend/context.py` | Explicit source registry, school joins, reference search and viewport map queries |
| `src/ContextLayers.jsx` | Lazy map overlay loading, popups and feature-limit feedback |
| `src/ReferenceExplorer.jsx` | Dataset selector, search, school/building cards and paginated reference tables |
| `backend/server.py` | GET API, up to 32 cached responses and production `dist/` assets |
| `src/App.jsx` | Shared filters, URL state, requests and dashboard composition |
| `src/MapView.jsx` | Leaflet basemap, local boundaries, representative town markers |
| `src/Charts.jsx` | Metrics, trends, flat profile, ranking and empty states |
| `src/Transactions.jsx` | Table search, pagination and current-page CSV download |
| `src/styles.css` | Cyberpunk theme and responsive layouts |
| `scripts/python.mjs` | Locate a working Python interpreter for npm commands |

React/Vite builds to `dist/`. Python serves the production frontend and API on the same origin. During frontend development Vite proxies API requests to port 8000. SQLite has indexes on month, town/month and flat-type/month; statistical medians are computed in Python from matching rows.

## Endpoints

All routes below are GET requests to `http://127.0.0.1:8000`. They do not modify data.

| Endpoint | Response |
| --- | --- |
| `/api/meta` | `count`, `min_month`, `max_month`, `towns`, `flat_types`, `sources` |
| `/api/dashboard` | `summary`, `trend`, `towns`, `mix` |
| `/api/transactions` | `total`, `page`, `page_size`, `rows` |
| `/api/asking` | Comparable-sale sample, percentile range and asking-price classification |
| `/api/models` | Generated national and estate equation artifact |

Summary objects contain `count`, `price`, `psm` and `area`. Trend entries add `month`; town entries add `town`; mix entries add `flat_type`. `price` and `psm` are medians, not individual prices.

### Dashboard and transaction query parameters

| Parameter | Meaning |
| --- | --- |
| `start`, `end` | Inclusive `YYYY-MM`; omitted or blank means unbounded |
| `town` | Exact normalized town label, for example `BEDOK` |
| `flat_type` | Exact normalized type, for example `4 ROOM` |
| `search` | Transactions only: case-insensitive literal substring in block plus street; up to 200 characters are used |
| `page` | Transactions only: positive integer; default 1 |
| `page_size` | Transactions only: integer 1-100; default 12 |

Use values from `/api/meta` for normalized labels. Unknown town/type values produce an empty selection. Dashboard `towns` intentionally ignores the selected town while respecting dates and flat type. Address search does not affect dashboard aggregates.

```sh
curl 'http://127.0.0.1:8000/api/dashboard?start=2024-01&end=2024-12&town=BEDOK&flat_type=4%20ROOM'
curl 'http://127.0.0.1:8000/api/transactions?town=BEDOK&page=1&page_size=12'
```

Invalid filters return HTTP 400 with an `error` message. Unknown API routes return 404. Unexpected query failures return 500 and log details in the server terminal. SQL values use bound parameters. The server binds to localhost and is not a production hosting stack.

## Reference API

- `GET /api/context/catalog`: available `datasets` and `layers` with IDs, labels and source filenames.
- `GET /api/context/records?dataset=schools&search=robotics&page=1&page_size=12`: `columns`, `rows`, `total`, `source_count`, pagination and source file. Search is a literal case-insensitive substring across all fields, including joined school programmes. Page size is 1–100. Use IDs from the catalog.
- `GET /api/context/map?layer=mrt-exits&bbox=103.7,1.2,104,1.5&limit=2000`: GeoJSON FeatureCollection with `matched`, `truncated` and `file`. Bounding box is west,south,east,north; limit is 1–3,000. Use layer IDs from the catalog. Invalid IDs and parameters return 400.

Reference routes bypass the resale-response cache. Parsed CSVs and up to three parsed geographic files are cached by path and modification time. No arbitrary file paths are accepted. Reference data is queried independently of resale filters and needs no external geocoder.

`/api/context/records?dataset=school-rankings` returns the derived balanced school ranking in the same paginated format, with `origins`, `methodology` and `excluded` audit details. Calculation lives in `backend/insights.py`; its dependencies are the directory, subjects, CCAs and travel CSVs. Ranking scores remain global to the eligible cohort when searching/paginating.

## Price equations

`GET /api/models` returns the versioned model artifact: window, exclusions, national coefficients and intervals, centred estate offsets, chronological validation, factor-removal comparisons, local model results and support warnings. It ignores dashboard filters because all models share one fixed comparison window. Missing/stale artifacts return HTTP 400; `npm run model` regenerates them. The server reads JSON without importing NumPy. See [Price equations](Price-Equations.md).


## Asking-price API

`GET /api/asking` takes four required parameters, independent of the dashboard filters:

| Parameter | Validation |
| --- | --- |
| `town` | Exact estate label from `/api/meta`; unknown labels return 400 |
| `flat_type` | Exact type from `/api/meta`; unknown labels return 400 |
| `asking` | Positive finite number, SGD |
| `lease` | Finite decimal years greater than 0 and at most 99 |

```sh
curl 'http://127.0.0.1:8000/api/asking?town=JURONG%20EAST&flat_type=5%20ROOM&asking=679999&lease=54'
```

All successful responses contain `status`, echoed inputs (`town`, `flat_type`, `asking`, `lease`), `count`, `blocks`, `start`, `end`, `lease_band`, `range`, `median` and `examples`. `status` is `above_range`, `within_range`, `below_range` or `insufficient`. Sufficient samples also include `gap_pct` and `area_range`. Insufficient samples have null `range` and `median` and omit those last two fields; they return HTTP 200, not a validation error.

Each example contains `month`, `block`, `street_name`, `remaining_lease`, `resale_price`, `floor_area_sqm` and `storey_range`. At most ten examples are returned. Invalid inputs return HTTP 400 with an `error` string. No probability or predicted transaction outcome is returned.

The endpoint shares the 32-entry resale response cache. Restart after importing data. It reads SQLite directly and does not depend on `/api/models` or NumPy. See [selection rules and classification](Asking-Price.md#how-comparisons-are-selected).
