# HDB Atlas design

## Purpose
Build a local web application to explore the five supplied HDB resale CSVs using a Singapore map, historical price charts, and transaction details. Assume a general exploration audience. Success means a user can select a period and flat type, identify differences between towns, and inspect the underlying transactions.

## Recommended approach
Use a React frontend, Leaflet map, and a small Python API backed by SQLite. Import CSVs once into an indexed local database; query filtered records on the server rather than sending almost one million records to the browser. This provides exact medians and flexible transaction filters without a hosted database or account.

Alternatives: precomputed static summaries simplify deployment but limit combinations of filters and transaction browsing; a hosted database adds operations and credentials unnecessary for this local version.

## Interface
A responsive cyberpunk dashboard named HDB Atlas with a wide interactive map, dark panels, neon cyan/magenta/purple accents, monospace data labels, and readable charts. User explicitly requested this styling and implementation on 1 October 2026. Show the actual dataset end date prominently.

Shared controls: start and end month, flat type, and town, plus a reset button. Default to the last complete calendar year available, 2024, and all flat types. Clicking a town marker selects that town and updates the charts, summary cards, and table. Clear selection returns to all towns.

Summary cards: transaction count, median resale price, median price per square metre, and median floor area. A monthly trend chart shows median resale price with transaction counts in tooltips. A town comparison chart shows median resale prices with sample counts. A paginated transaction table lists month, town, block/street, flat type, storey range, area, lease commencement year, resale price, and price per square metre.

## Map
Use a tile basemap with attribution and verified representative town coordinates. Each marker represents a town aggregate, never an individual block location. Marker colour represents median price and size represents transaction volume. Include a legend, selected-town state, reset view, and a clear town-level location label. Town comparisons stay visible when a town is selected, using the same dates and flat type. Show a useful fallback if tiles cannot load.

Block geocoding is outside the initial version because the files have no coordinates. Adding it later requires a verified geocoding source, cached results, and explicit reporting of unmatched addresses.

## Data integrity
Input coverage: 947,370 rows, January 1990 through February 2025. Preserve source filenames and all source rows; identical-looking rows may be separate transactions. Standardize text case and equivalent flat-type spellings. Parse numeric fields and remaining lease formats. Validate required fields and report rejected rows and reasons during import. Never silently omit files or records.

Compute medians from underlying matching transactions, not averages of subgroup medians. Calculate price per square metre per transaction before aggregation. Prices are nominal SGD. Describe trend changes as changes in observed transactions, not valuation estimates or a quality-adjusted index. Mark the transition from approval date to registration date in March 2012. Explain that remaining lease is not supplied in older sources and that February 2025 may be incomplete.

## Architecture and operation
Keep CSV inputs unchanged. Store the generated database in an ignored local data directory. Provide an explicit import command, backend and frontend development commands, and a README with prerequisites. Keep data loading, query logic, API routes, and frontend components separate. Validate API filters and use parameterized SQL. Bind the local API to localhost by default.

Return metadata, summary metrics, monthly trends, town comparisons, and paginated transactions through a small read-only API. Include loading, empty-result, invalid-filter, and request-failure states. Make controls keyboard accessible and provide textual values alongside map colours.

## Verification
Verify imported row counts and date coverage against all five CSVs. Test exact medians with even and odd sample sizes, filter intersections, normalization, invalid inputs, and table pagination. Verify frontend production build and exercise the app in a browser: map selection, filters, reset, empty states, chart updates, table navigation, and mobile layout. Check representative API totals against independent CSV calculations.

## Delivery scope
A working local dashboard, reproducible import, tests for data/query correctness, and startup documentation. No login, live refresh, prediction model, hosting, or paid services in this first version.
