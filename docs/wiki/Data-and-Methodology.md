# Data and methodology

[Wiki home](Home.md) · [Architecture and API](Architecture-and-API.md)

## Source coverage

| Root CSV | Rows | Period | Date basis |
| --- | ---: | --- | --- |
| Resale Flat Prices (Based on Approval Date), 1990 - 1999.csv | 287,196 | Jan 1990-Dec 1999 | Approval |
| Resale Flat Prices (Based on Approval Date), 2000 - Feb 2012.csv | 369,651 | Jan 2000-Feb 2012 | Approval |
| Resale Flat Prices (Based on Registration Date), From Mar 2012 to Dec 2014.csv | 52,203 | Mar 2012-Dec 2014 | Registration |
| Resale Flat Prices (Based on Registration Date), From Jan 2015 to Dec 2016.csv | 37,153 | Jan 2015-Dec 2016 | Registration |
| ResaleflatpricesbasedonregistrationdatefromJan2017onwards.csv | 241,920 | Jan 2017-Oct 2026 | Registration |
| **Total** | **988,123** | **Jan 1990-Oct 2026** | Mixed historical basis |

There are 27 distinct town labels across the complete history. The default view uses the latest 12 available months, currently November 2025–October 2026. October 2026 may be incomplete. There is no automatic data update.

## Calculations

- Resale price: median of individual matching sale prices.
- Price per m²: compute `resale_price / floor_area_sqm` for every matching transaction, then take the median. It is not median price divided by median area.
- Floor area: median of individual matching areas, in square metres.
- Volume: count of matching source rows, including duplicate-looking rows.
- Flat mix: count for each flat type divided by total matching count.
- Empty group: count 0 and null price/area metrics. The UI displays a dash for unavailable values.

For an even number of values the median is the average of the two central sorted values. Statistics are calculated from transactions, never by averaging subgroup medians. Prices are nominal SGD, without inflation adjustment.

### Archived 2024 example (v1.0 snapshot)

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

Approval dates change to registration dates in March 2012. Comparing across this transition needs care. The mix of flat sizes, types, age and location changes over time; median changes are not a quality-adjusted price index or an individual property's appreciation. Small samples can have unstable medians. The app includes descriptive price regressions and a comparable-sales asking-price screen, but no live listings or validated individual-home valuation forecast.

## Geography and attribution

The local file `public/data/planning-areas.geojson` contains 55 official [URA Master Plan 2019 Planning Area Boundary (No Sea)](https://data.gov.sg/datasets/d_4765db0e87b9c86336792efe8a1f7a66/view) features, downloaded on 1 October 2026 under the [Singapore Open Data Licence](https://data.gov.sg/open-data-licence).

Markers use area-weighted centroids of polygon outer rings. Kallang represents Kallang/Whampoa and Downtown Core represents Central Area. Planning-area outlines are not exact historical HDB town boundaries. The original CSVs do not contain block coordinates.

Basemap attribution: [OpenStreetMap contributors](https://www.openstreetmap.org/copyright). Tiles are darkened with CSS. Review the [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) before any public deployment. Screenshots retain map attribution.

## Neighbourhood reference snapshots

The 11 reference CSVs and 17 GeoJSON overlays are separate from resale statistics. They do not inherit transaction date, town or flat-type filters. The newer 2017-onward resale snapshot replaces the old snapshot rather than appending to it; raw files are preserved.

Schools are joined to subjects, CCAs, MOE and distinctive programmes by normalized school name, with unique aliases for School/ST/Saint and punctuation variants. Primary and secondary distinctions are retained; ambiguous aliases are not joined. Missing matches stay empty; postal codes remain text. HDB building details are browsable by block/street and are not inferred property valuations. Station-to-school travel times are supplied historical values, not live routing or distances from flats. Annual car, rail and community statistics are national aggregates.

GeoJSON layers retain their supplied coordinates and attributes. Legacy HTML property tables are parsed into plain text. Road school zones are not school admission-distance boundaries. The 2014/2019 plan annotation layers are text-placement geometry, not park or reserve boundaries. Overlapping community and after-death sources are offered separately, not counted as unique facilities.

Map queries use feature bounding boxes against the visible viewport. At most 2,000 features are displayed by the UI (API maximum 3,000); a visible notice asks users to zoom in when this limit is reached. A bounding-box intersection is an approximate viewport filter, not an exact spatial intersection or proximity calculation.

## Balanced school comparison

The derived `school-rankings` reference view compares 115 eligible SECONDARY (S1-S5) schools across the same 189 recorded station origins. The score is 50% midrank percentile of negative median recorded travel time, 25% unique subject-listing percentile and 25% unique CCA-grouping percentile. Percentiles use `(average zero-based rank)/(N-1)*100`. Scores round to one decimal, and tied displayed scores share a competition rank. Raw subject labels can include language and curriculum variants; breadth is not academic quality. ALP/LLP and MOE programmes remain profile information rather than automatic quality bonuses.

Exact school names take priority, followed by unique normalized aliases, then unique school postcodes. Directory and route postcodes must agree. CHIJ St. Theresa’s Convent and Outram Secondary are excluded because these sources have conflicting postcodes. Incomplete station coverage, conflicting route times and missing subject/CCA data are excluded instead of receiving zero scores. Primary schools lack equivalent travel data and are not assigned this balanced score.

Every recorded station has equal weight, so the access component favours network-central schools. It is not a commute estimate from a particular flat. The travel file does not specify mode, departure time or observation date; minutes are labelled source-recorded, never walking minutes. Records may refer to different snapshot dates, and eligibility or gender restrictions still need to be considered separately.


## Asking-price comparisons and estate equations

The [asking-price form](Asking-Price.md) selects recent transactions by estate, flat type and a five-year lease tolerance. Its middle-50% comparison range and high/within/below labels are descriptive rules. They do not control for floor area, storey or property condition and do not estimate sale probability. No live advertisement or unsold-listing dataset is imported.

The [price equations](Price-Equations.md) separately model log sale price using area, flat type, remaining lease, storey, timing and, nationally, estate effects. They use a fixed chronological train/test window, with pooled estimates for estates that lack enough data. Their coefficient intervals are not individual price prediction intervals. Neither analysis quantifies a causal school or transport premium.

## Licensing

Original project code and documentation use the [MIT License](../../LICENSE), copyright © 2026 Randhir Prem (randhirprem). Third-party datasets, map geometry, tiles, fonts and dependencies retain their own licences. The source registry identifies files and coverage; it does not grant redistribution rights. See the source attributions above and each provider's terms.
