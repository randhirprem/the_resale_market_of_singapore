# HDB Atlas wiki

HDB Atlas is a local, cyberpunk-styled explorer for Singapore HDB resale transactions. It combines an interactive town map, exact median statistics, monthly trends, flat profiles and transaction records, plus neighbourhood data, balanced school rankings, estate equations and an asking-price comparison form.

## Contents

| Page | What it covers |
| --- | --- |
| [Getting started](Getting-Started.md) | Requirements, startup, development and troubleshooting |
| [Dashboard guide](Dashboard-Guide.md) | Filters, map, charts, comparisons, search and export |
| [Data and methodology](Data-and-Methodology.md) | Source coverage, calculations, missing values and map limitations |
| [Architecture and API](Architecture-and-API.md) | Components, endpoint contracts and query parameters |
| [Asking-price assessment](Asking-Price.md) | Four-input form, comparison ranges, worked examples and limitations |
| [Price equations](Price-Equations.md) | National/estate formulas, validation, interpretation and limitations |
| [Maintenance](Maintenance.md) | Refreshing CSVs, verification and documentation upkeep |

[Project README](../../README.md) · [Download the PDF guide](../../output/pdf/HDB-Atlas-Guide.pdf) · [Full dashboard screenshot](../screenshots/full-dashboard.jpg)

The screenshots and nine-page PDF guide were refreshed on 8 October 2026 and cover the current app. See the [capture inventory](../screenshots/README.md).

![HDB Atlas overview, all flat types and towns, November 2025 to October 2026](../screenshots/overview.jpg)

## Dataset snapshot

- **988,123 transactions**, January 1990 through October 2026.
- Five selected resale CSVs, preserved unchanged by the application.
- 11 reference CSV datasets, a derived school ranking and 17 map overlays.
- National equation and 25 independent estate equations; Bukit Timah uses a pooled estimate in the current snapshot.
- Default view: the latest 12 available months, all towns and flat types.
- Historical records, not live listings or a property valuation service.

The wiki documents the local app; it is not published to a hosted wiki service.

## Licence

Original code and documentation: [MIT License](../../LICENSE), copyright © 2026 Randhir Prem (randhirprem). Third-party data, maps, fonts and dependencies retain their respective terms; see [source attribution](Data-and-Methodology.md#geography-and-attribution) and the [README](../../README.md#license).
