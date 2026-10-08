# Asking-price assessment

[Wiki home](Home.md) · [Dashboard guide](Dashboard-Guide.md) · [API reference](Architecture-and-API.md#asking-price-api)

## Use the form

Open **Asking price** in the navigation of the running app, or visit [the local form](http://127.0.0.1:8000/#asking).

1. Select an estate and housing type.
2. Enter the asking price in SGD, without currency symbols or commas.
3. Enter the remaining lease in years; decimals such as `70.5` are accepted.
4. Select **Assess asking price**.

Inputs belong to this form, independently of the dashboard filters. Changing any input clears the previous result. The form's inputs and result are not stored in shared URLs and are lost on reload. Select the HDB flat type, not the bedroom count: a five-room HDB flat can have three bedrooms.

![Jurong East asking-price form showing the comparison range and evidence](../screenshots/asking-price.jpg)

Captured 8 October 2026. Values reflect the imported snapshot.

## Read the result

| Result | Meaning |
| --- | --- |
| Asking price looks high | Asking exceeds the upper comparison endpoint; below asking is better supported by recorded prices. |
| Asking price is within the comparison range | At asking is supported by comparables, though negotiation below asking remains possible. |
| Asking price is below the comparison range | At asking is supported by comparables; investigate why the property is priced lower. This does not predict competing bids. |
| Not enough comparable sales | No price verdict or range is issued. The matching sample is too small or concentrated in too few blocks. |

The cards show the price-based assessment, indicative acceptable range, comparable median and percentage gap. Positive gap means asking is above the median: `(asking / median − 1) × 100`. Expand **Comparison method and supporting sales** to inspect up to ten recent matching transactions. These are comparisons, not identified outcomes for your listing.

## How comparisons are selected

- Same estate and flat type as the input.
- Supplied remaining lease within five years of the input, bounded to 0–99 years. Lease is measured as recorded at the transaction, not aged forward to today. Missing leases are excluded.
- The 12 months before the latest source month; that latest month is excluded as potentially incomplete. The current window is October 2025–September 2026.
- At least 20 sales across three distinct block/street pairs are required. The app does not silently broaden the criteria when this threshold is missed.

The range is the **25th–75th percentile**, the middle half of matching completed sale prices. Percentiles use linear interpolation between sorted observations, with position `(n − 1) × percentile`. The median is the 50th percentile. Prices equal to either range endpoint count as within the range. Supporting records are ordered by month descending, then import ID descending; order within a month does not imply a known day of sale.

## Worked examples

These results were checked against the current local snapshot on 8 October 2026. They will change after a data refresh.

| Estate / flat type / remaining lease | Asking price | Comparison range | Result |
| --- | ---: | ---: | --- |
| Woodlands / 4 Room / 70 years | $650,000 | $528,000–$575,000 | High; below asking better supported |
| Woodlands / 4 Room / 70 years | $550,000 | $528,000–$575,000 | Within range; at asking supported |
| Woodlands / 4 Room / 70 years | $500,000 | $528,000–$575,000 | Below range; investigate property differences |
| Jurong East / 5 Room / 54 years | $679,999 | $610,000–$685,000 | Within range; at asking supported |

The Woodlands sample contains 559 sales across 251 blocks, median $547,000. The Jurong East sample contains 57 sales across 34 blocks, median $648,000; its asking price is 4.9% above the median. These are estate-level comparisons, not a valuation of a particular block or unit.

## What this cannot determine

**Sale likelihood is not estimated.** Completed-sale records do not include the unsold listings and matched asking-price histories needed to validate a sale probability, time on market or above/below-asking forecast. “At asking supported” describes price evidence, not a promise that the home will sell. The app does not scrape, monitor or confirm the status of property advertisements.

All floor areas and storeys within the selected flat type are included. The sample's area span is shown, but exact size, storey, location, renovation, condition, views and accessibility are not controlled for. Such differences may justify prices outside the range. The middle 50% of past prices is neither a prediction interval nor a professional valuation.

This calculation is separate from the [national and estate regression equations](Price-Equations.md). It needs the imported resale database but no NumPy installation or generated model artifact.
