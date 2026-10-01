# Data and methodology

[Wiki home](Home.md) · [Architecture and API](Architecture-and-API.md)

## Source coverage

| Root CSV | Rows | Period | Date basis |
| --- | ---: | --- | --- |
| Resale Flat Prices (Based on Approval Date), 1990 - 1999.csv | 287,196 | Jan 1990-Dec 1999 | Approval |
| Resale Flat Prices (Based on Approval Date), 2000 - Feb 2012.csv | 369,651 | Jan 2000-Feb 2012 | Approval |
| Resale Flat Prices (Based on Registration Date), From Mar 2012 to Dec 2014.csv | 52,203 | Mar 2012-Dec 2014 | Registration |
| Resale Flat Prices (Based on Registration Date), From Jan 2015 to Dec 2016.csv | 37,153 | Jan 2015-Dec 2016 | Registration |
| Resale flat prices based on registration date from Jan-2017 onwards.csv | 201,167 | Jan 2017-Feb 2025 | Registration |
| **Total** | **947,370** | **Jan 1990-Feb 2025** | Mixed historical basis |

There are 27 distinct town labels across the complete history and 26 with sales in the default 2024 view. February 2025 may be incomplete. There is no automatic data update.

## Calculations

- Resale price: median of individual matching sale prices.
- Price per m²: compute `resale_price / floor_area_sqm` for every matching transaction, then take the median. It is not median price divided by median area.
- Floor area: median of individual matching areas, in square metres.
- Volume: count of matching source rows, including duplicate-looking rows.
- Flat mix: count for each flat type divided by total matching count.
- Empty group: count 0 and null price/area metrics. The UI displays a dash for unavailable values.

For an even number of values the median is the average of the two central sorted values. Statistics are calculated from transactions, never by averaging subgroup medians. Prices are nominal SGD, without inflation adjustment.

### Independently checked default view

| Metric | Jan-Dec 2024, all towns and types |
| --- | ---: |
| Transaction count | 27,836 |
| Median resale price | $590,000 |
| Median price per m² | $6,097.826086956522 (displayed as $6,098) |
| Median area | 93 m² |

## Import and normalization

Root CSVs are read with Python's CSV reader. Town, flat model and street names are standardized to uppercase. MULTI GENERATION is normalized to MULTI-GENERATION. Remaining lease can be numeric years or years/months; both are represented as decimal years. Missing remaining lease stays null and is not estimated.

The importer preserves each row and its source filename. It validates month format, numeric fields, positive finite price/area, town/flat type and supported lease formats. An invalid row aborts the import with a filename and row number. The previous database remains intact because replacement happens only after the staging import succeeds.

## Interpretation limits

Approval dates change to registration dates in March 2012. Comparing across this transition needs care. The mix of flat sizes, types, age and location changes over time; median changes are not a quality-adjusted price index or an individual property's appreciation. Small samples can have unstable medians. The app contains no predictive valuation model or live listings.

## Geography and attribution

The local file `public/data/planning-areas.geojson` contains 55 official [URA Master Plan 2019 Planning Area Boundary (No Sea)](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) features, downloaded on 1 October 2026 under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence).

Markers use area-weighted centroids of polygon outer rings. Kallang represents Kallang/Whampoa and Downtown Core represents Central Area. Planning-area outlines are not exact historical HDB town boundaries. The original CSVs do not contain block coordinates.

Basemap attribution: [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). Tiles are darkened with CSS. Review the [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) before any public deployment. Screenshots retain map attribution.
