# HDB / ATLAS

A cyberpunk Singapore HDB resale dashboard built from all five CSVs in this folder. Includes **947,370 transactions from January 1990 through February 2025**. The original CSVs are unchanged.

## Documentation

- **[Illustrated PDF guide](output/pdf/HDB-Atlas-Guide.pdf)** - dashboard walkthrough, data methodology, setup and maintenance.
- **[Project wiki](docs/wiki/Home.md)** - linked guides for users and maintainers, including the API reference.
- [Full dashboard screenshot](docs/screenshots/full-dashboard.jpg).

## Screenshots

Actual captures of the running app, using **January-December 2024, all towns and all flat types**. The underlying dataset ends in February 2025.

### Dashboard overview

![Cyberpunk HDB Atlas overview showing filters and four market summary cards](docs/screenshots/overview.jpg)

### Interactive town map

![Expanded Singapore map showing town-level median prices and transaction volumes](docs/screenshots/map.jpg)

### Trends and comparisons

![Monthly price trends, flat-type transaction mix and town rankings](docs/screenshots/analytics.jpg)

### Transaction explorer

![Paginated transaction table with street search and current-page CSV export](docs/screenshots/transactions.jpg)

## Run

Requires Node.js 20.19+ (or 22.12+) and Python 3.9+. No Python packages, accounts, API keys, or hosted database are required.

```sh
npm install
npm run build
npm start
```

Open **http://127.0.0.1:8000**. The first start imports the CSVs if the local database is absent. Subsequent starts reuse it. Stop with Ctrl+C.

If Python is not found, set `HDB_PYTHON` to its executable path. To use another port: `npm start -- --port 8001`.

For frontend development, keep `npm start` running in one terminal and run `npm run dev` in another; use the Vite URL printed in the terminal. API requests are proxied to port 8000.

## Explore

- Change the date range, flat type, or town. The initial view uses the complete calendar year 2024.
- Click a map marker or town ranking to filter the summary, trends, flat profile, and table. Map/rank comparisons keep all towns for the selected dates and flat type.
- Switch the map between median resale price and median price per square metre. Marker size represents transaction volume. Expand/reset the map or use its zoom controls.
- Switch the trend between price, price per m², and transaction volume. Zero-sale months remain on the timeline; their price medians are absent.
- Search transactions by block/street, page through matching rows, and export the current page as CSV.
- Copy the URL to preserve date, town, and flat-type filters. Table search and page are local to the current view.
- Expand “Know your data” for methodology and exact source row counts.

## Data refresh and checks

Replace the local source CSVs with the desired non-overlapping source files, stop the server, and run:

```sh
npm run import
npm test
npm start
```

The import validates each row and atomically replaces `data/hdb.sqlite3` only when all files succeed. Errors identify the source file and row; the existing database remains intact. Duplicate-looking source rows are intentionally preserved, so do not retain overlapping versions of input files. Restart the server after every import to clear its in-memory response cache. The current app defaults to 2024; change the date filters to explore any newly imported records.

Exact medians are calculated from individual transactions. Price per m² is computed per transaction before taking its median. The test suite covers import preservation and rollback, normalization, leases, even/odd medians, combined filters, empty results, monthly gaps, invalid dates, pagination, and literal address search.

## Map sources and limitations

Local map geometry is [URA Master Plan 2019 Planning Area Boundary (No Sea)](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view), retrieved from data.gov.sg on 1 October 2026 and reused under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence). `public/data/planning-areas.geojson` is the official downloaded file. Geometry remains available offline.

The basemap uses [OpenStreetMap](https://www.openstreetmap.org/copyright) tiles with a dark visual filter; internet is required for those tiles and optional Google Fonts. Local data and planning-area geometry need no network after setup. The public OSM tile service is suitable for this local viewer; consult its [tile usage policy](https://operations.osmfoundation.org/policies/tiles/) before public deployment or substantial traffic.

Markers are area-weighted polygon centroids, not geocoded HDB blocks. Planning areas provide spatial context, not exact HDB town boundaries. Kallang represents the Kallang/Whampoa town aggregate; Downtown Core represents Central Area. Coordinates are not present in the original transaction CSVs.

Prices are nominal SGD, not inflation-adjusted or a valuation estimate. Changes can reflect the mix of homes sold. Approval dates are used through February 2012 and registration dates from March 2012. Remaining lease is shown only when supplied. February 2025 may be incomplete. There is no automatic live-data refresh.

## Project layout

- `backend/data.py`: CSV validation/import and exact aggregate queries.
- `backend/server.py`: read-only API and production asset server, bound to localhost.
- `src/`: React dashboard, Leaflet map, Recharts charts, transaction explorer, responsive styles.
- `public/data/`: locally bundled official map geometry.
- `tests/`: deterministic data tests using temporary fixtures.
- `docs/wiki/`: user guide, methodology, architecture/API and maintenance wiki.
- `docs/screenshots/`: browser screenshots embedded above.
- `output/pdf/HDB-Atlas-Guide.pdf`: illustrated project guide.
- `scripts/build_guide.py`: reproducible PDF builder (documentation-only dependencies: reportlab and Pillow).
- `scripts/python.mjs`: finds a working Python 3 interpreter across local environments.

The Python standard-library server is intended for local use. Hosting, authentication, and block-level geocoding are outside this version.

## License

Original project code and documentation are licensed under the [MIT License](LICENSE).
Third-party datasets, map geometry, map tiles, and dependencies retain their respective licenses; see the map source attributions above.
