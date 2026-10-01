# Architecture and API

[Wiki home](Home.md) · [Maintenance](Maintenance.md)

## Data flow

```text
Five root CSVs -> validated atomic import -> data/hdb.sqlite3
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

Summary objects contain `count`, `price`, `psm` and `area`. Trend entries add `month`; town entries add `town`; mix entries add `flat_type`. `price` and `psm` are medians, not individual prices.

### Query parameters

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
