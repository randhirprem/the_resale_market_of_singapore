# Maintenance

[Wiki home](Home.md) · [Getting started](Getting-Started.md)

## Refresh transaction data

1. Stop the running server with Ctrl+C.
2. Replace the relevant root CSVs with non-overlapping source files. Do not keep old and new versions covering the same dates: the importer deliberately preserves every row.
3. Run `npm run import`. Check source row counts and any reported file/row errors.
4. Run `npm test` and restart with `npm start`.
5. Verify `/api/meta` coverage and compare a known period in the dashboard.

The server caches responses, so restart after importing. Import failure leaves the previous database intact. CSV changes do not require a frontend build, but frontend changes do: run `npm run build`. The default date range is currently fixed to 2024 in `src/App.jsx`.

## Verification

```sh
npm test
npm run build
```

The 11 data tests cover row preservation, even/odd medians, filters, empty results, lease normalization, pagination, invalid input, atomic rollback, literal search and zero-sale months. Browser checks from the initial build covered map selection, chart modes, filters, search, pagination, export, invalid-date handling and a 390px mobile viewport. These are recorded checks, not an automated browser test suite.

## Documentation and screenshots

- `README.md`: entry point, gallery, setup and data caveats.
- `docs/wiki/`: linked Markdown wiki pages.
- `docs/screenshots/`: actual browser captures; the four desktop views use January-December 2024, all towns and flat types.
- `output/pdf/HDB-Atlas-Guide.pdf`: illustrated user and maintainer guide.
- `scripts/build_guide.py`: regenerate the PDF from current statistics, documentation content and existing screenshots.

To rebuild the PDF, use a Python environment containing `reportlab` and Pillow, then run `python3 scripts/build_guide.py`. These are documentation dependencies only, not application runtime requirements. After regeneration, render and visually inspect every PDF page before sharing. Screenshots must be refreshed manually from the running app when the UI changes; the builder does not recapture them.

The bundled screenshot dates and numeric examples describe the supplied historical data. If data is refreshed, update example figures, source row counts, screenshots and the PDF together.
