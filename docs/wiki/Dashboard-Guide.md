# Dashboard guide

[Wiki home](Home.md) · [Data and methodology](Data-and-Methodology.md)

## 1. Choose a comparison

Use From and To to set an inclusive month range. Pick a flat type for a more comparable group of homes, then optionally select a town. Reset restores January-December 2024, all towns and all flat types. Copy the browser URL to preserve these shared filters.

The four summary cards show median resale price, median price per square metre, transaction count and median floor area. Currency is SGD. Missing medians display as a dash, not a zero price.

## 2. Read the map

![Singapore town-level price map](../screenshots/map.jpg)

Click a town marker to update the summary cards, trend, flat profile and transaction table. Click its selected-town badge to clear the town filter. Map and ranking comparisons remain island-wide for the chosen dates and flat type.

- Colour represents median resale price or price per square metre, depending on the selected map mode. The legend rescales to the current comparison.
- Marker size represents transaction count. Hover for the town name, median and sample size.
- Use the zoom buttons, reset-view button or expanded map. Press Escape to close the expanded view.
- Markers represent towns using planning-area centroids, not individual blocks. The planning polygons are spatial context, not exact HDB town boundaries.

## 3. Explore time and flat profiles

![Monthly trends, flat-type mix and town rankings](../screenshots/analytics.jpg)

The trend offers Price, $/m² and Volume modes. Monthly medians are based on that month's transactions. Months without sales have zero volume and no price median, so gaps are not hidden. A completely empty selection shows an empty state.

The flat profile starts with each flat type's share of matching transactions. Compare prices changes it to median price by flat type. The town ranking uses the map's selected price measure; expand it to see all matching towns. A high town median can reflect larger or newer homes, not just location.

## 4. Inspect and export records

![Transaction table with address search and current-page export](../screenshots/transactions.jpg)

Search block or street names in the transaction explorer. This search affects the table only, while shared filters apply to both the table and dashboard. Results are sorted by month descending, then source import ID, with 12 rows per page. Order within a month does not imply a known day of sale.

Export page downloads only the current page as CSV. Its 13 columns include the original source filename. Page and search are not saved in the shared URL. Changing shared filters resets the table; changing search returns to page 1.

## Worked example

For January-December 2024, select **4 ROOM** and **BEDOK**. The local dataset contains **452 transactions**, a **$540,000** median resale price and **92 m²** median area. Selecting **TAMPINES** on the map changes that selection to **867 transactions** and a **$625,000** median resale price. These are historical observations, not current asking prices.
