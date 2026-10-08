# Implementation progress

## Current snapshot — 8 October 2026

- 988,123 resale records, January 1990–October 2026; 11 reference datasets and 17 map overlays.
- Balanced secondary-school rankings, national/estate equations and the four-input asking-price assessment are implemented.
- Most recent app validation: 31 automated tests and production build passed; browser checks covered asking-price classifications, invalid inputs, sparse samples, supporting sales, searches and estate equations.
- Documentation refresh: current screenshots, README and wiki, plus a rebuilt nine-page illustrated PDF guide. Capture states are recorded in `docs/screenshots/README.md`.

## Historical implementation log — initial release

The figures and checks below describe the initial 1 October 2026 build, not the current dataset.

Plan: docs/superpowers/plans/2026-10-01-hdb-atlas.md
Ruling: Proceed inline after user explicitly requested building now; avoid another design approval round.
Ruling: Use this requested folder directly; its enclosing Git repository includes unrelated home-directory content, so no parent repository operations or commits.
Pre-flight: Backend response contract supplies metadata, summary, monthly trend, town ranking and flat mix to frontend. Transactions endpoint independently paginated with shared filters.

Task 1: complete — all 947,370 source rows imported without rejects. Fixture tests verify medians, duplicates, normalization, filters, rollback and pagination.
Task 2: complete — cyberpunk responsive UI with town map, shared filters, KPIs, price/volume trends, flat mix, ranking, searchable transactions, current-page CSV export and methodology.
Review: independent code reviewer found stale dashboard on request errors and missing zero-sale months. Fixed both; added a regression test for monthly gaps and verified invalid filter behavior in browser.
Ruling: CARTO responded with API-key-required image tiles in browser. Replaced with standard OpenStreetMap tiles, darkened visually; local URA geometry remains independently available.
Validation: independent CSV scan matched 2024 count 27,836, median SGD 590,000, median price/m² 6,097.826086956522 and area 93 m². Full-history query returned 422 months in 2.98 seconds.
Browser checks: combined Bedok + 4 ROOM filters returned 452 sales, median SGD 540,000. Clicking Tampines marker returned 867 4 ROOM sales and median SGD 625,000. Map price/m² mode, trend volume mode, pagination, street search, empty search, reset, expanded map, and invalid date error were exercised. Mobile 390px viewport had pageWidth=390 (no page horizontal overflow); desktop and mobile screenshots inspected. Browser console had no errors/warnings after corrected build.
Final automated checks: npm test — 11 passing; npm run build — successful, vendor chunks separated.

CSV export verified from the browser download: 12 records, 13 columns, matching December 2024 page, source filename included. Browser download-event listener timed out, but exported file existed and contents passed independent checks. Screenshot saved to docs/dashboard-preview.jpg.
