# Screenshot inventory

Refreshed **8 October 2026** from the running HDB Atlas app at `http://127.0.0.1:8000`. These are actual browser screenshots, not mockups. The imported resale snapshot contains 988,123 records through October 2026. The latest month may be incomplete.

| File | Captured state |
| --- | --- |
| `overview.jpg` | Header, latest 12-month filters and summary cards; November 2025–October 2026, all towns/types |
| `map.jpg` | Same filters; town median resale prices, overlay selector, legend and map attribution |
| `analytics.jpg` | Same filters; monthly price trend, flat-type mix and town comparison |
| `transactions.jpg` | Same filters; first page, no address search, 12 source records |
| `schools.jpg` | Balanced secondary-school ranking, first page, no search; independent of resale filters |
| `asking-price.jpg` | Jurong East, 5 Room, 54 remaining lease years, $679,999 asking; range $610,000–$685,000 from 57 sales |
| `price-equations.jpg` | Singapore and Jurong East formulas, sample sizes, test errors and paired comparison; upper portion of equation panel |
| `full-dashboard.jpg` | Complete latest-window island-wide dashboard, with unfilled asking-price form and national equation |
| `capture-layout.json` | Browser-measured section coordinates for reproducible crops from the full dashboard |

Focused sections are cropped from real browser captures without changing their contents. Map attribution is retained. The asking-price range uses October 2025–September 2026 comparisons; the equation fit/test windows are separate and displayed in the image.

The README, wiki and nine-page PDF guide use these current captures. To refresh, capture the running app after data has finished loading, verify inputs and visible results, save the same filenames, update captions, then run `python3 scripts/build_guide.py`. Inspect the rebuilt PDF before sharing it.

`../dashboard-preview.jpg` is refreshed to match `overview.jpg`; historical implementation notes may refer to its original capture.
