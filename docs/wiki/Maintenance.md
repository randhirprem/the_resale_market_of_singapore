# Maintenance

[Wiki home](Home.md) · [Getting started](Getting-Started.md)

## Refresh transaction data

1. Stop the running server with Ctrl+C.
2. Replace the relevant root CSVs with non-overlapping source files. The specifically named newer 2017-onward snapshot automatically supersedes the original one. Avoid other overlapping resale files: the importer preserves every selected row. Unrelated CSVs are excluded by schema.
3. Run `npm run import`. Check source row counts and any reported file/row errors.
4. Run `npm run model` (NumPy required) to rebuild price equations, then `npm test` and restart with `npm start`.
5. Verify `/api/meta` coverage and compare a known period in the dashboard. Check the asking-price sample window and range after refresh; they depend on the latest imported month.

The server caches responses, so restart after importing. Equation artifacts are tied to the database file size and modification timestamp; old equations are rejected after an import until rebuilt. Import failure leaves the previous database intact. CSV changes do not require a frontend build, but frontend changes do: run `npm run build`. The default date range is the latest 12 available months in `src/App.jsx`. Reference files are allowlisted in `backend/context.py`; restart after replacing reference files.

## Verification

```sh
npm test
npm run build
```

The test suite covers source selection, school enrichment, reference pagination, map viewport limits, invalid coordinates, and row preservation, even/odd medians, filters, empty results, lease normalization, pagination, invalid input, atomic rollback, literal search and zero-sale months. Browser checks from the initial build covered map selection, chart modes, filters, search, pagination, export, invalid-date handling and a 390px mobile viewport. These are recorded checks, not an automated browser test suite.

### Asking-price regression checks

`tests/test_asking.py` covers price classification, interpolated ranges, exclusion of unrelated/old/latest-month sales, invalid inputs, sparse or single-block samples, and price-independent ordering of supporting records. Model tests additionally check chronological validation, coefficient recovery, degenerate designs and missing/stale artifacts.

On 8 October 2026, all **31 automated tests** and the production build passed. Browser checks confirmed:

- Woodlands four-room, 70-year lease: $650,000 high, $550,000 within range and $500,000 below range; comparison range $528,000–$575,000.
- Negative asking prices and leases over 99 years are blocked; editing fields clears stale results.
- No-match inputs withhold the verdict and range.
- Jurong East five-room, 54-year lease, $679,999: range $610,000–$685,000, 57 sales across 34 blocks.
- Supporting-sales table, transaction address search, school search and estate-equation selection work. Changing the dashboard estate leaves the independent asking assessment intact.
- No browser console errors were captured in that test session.

These are manual browser checks against the recorded snapshot, not a reusable automated end-to-end suite or proof that sale-outcome predictions are accurate. Recheck relevant flows after UI/API changes; sample counts and ranges can change after imports.

## Documentation and screenshots

- `README.md`: entry point, gallery, setup and data caveats.
- `docs/wiki/`: linked Markdown wiki pages.
- `docs/screenshots/`: actual browser captures; current browser captures and a [state inventory](../screenshots/README.md); dashboard views use November 2025–October 2026.
- `output/pdf/HDB-Atlas-Guide.pdf`: illustrated user and maintainer guide.
- `scripts/build_guide.py`: regenerate the PDF from current statistics, documentation content and existing screenshots.

To rebuild the PDF, use a Python environment containing `reportlab` and Pillow, then run `python3 scripts/build_guide.py`. These are documentation dependencies only, not application runtime requirements. After regeneration, render and visually inspect every PDF page before sharing. Screenshots must be refreshed manually from the running app when the UI changes; the builder does not recapture them.

The screenshots and nine-page PDF were refreshed on 8 October 2026, including schools, asking-price assessment and estate equations. Keep the README, wiki, screenshot inventory and guide captions aligned when replacing captures. The PDF builder checks for body text extending into the footer; rendering and visual inspection are still required.
