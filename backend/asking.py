"""Transparent comparable-sale screening; no sale-outcome probability model."""
import math


def assess(con, params):
    town, kind = params.get('town', ''), params.get('flat_type', '')
    if not con.execute('SELECT 1 FROM sales WHERE town=? LIMIT 1', (town,)).fetchone():
        raise ValueError('Select a valid estate.')
    if not con.execute('SELECT 1 FROM sales WHERE flat_type=? LIMIT 1', (kind,)).fetchone():
        raise ValueError('Select a valid flat type.')
    try:
        price, lease = float(params.get('asking', '')), float(params.get('lease', ''))
    except (TypeError, ValueError):
        raise ValueError('Enter a positive asking price and remaining lease between 0 and 99 years.') from None
    if not math.isfinite(price) or price <= 0 or not math.isfinite(lease) or not 0 < lease <= 99:
        raise ValueError('Enter a positive asking price and remaining lease between 0 and 99 years.')
    latest = con.execute('SELECT MAX(month) FROM sales').fetchone()[0]
    year, month = map(int, latest.split('-'))
    index = year * 12 + month - 1
    def month_string(i):
        return f'{i // 12:04d}-{i % 12 + 1:02d}'
    start, end = month_string(index - 12), month_string(index - 1)
    rows = [dict(r) for r in con.execute('''SELECT month, block, street_name, remaining_lease,
        resale_price, floor_area_sqm, storey_range FROM sales
        WHERE town=? AND flat_type=? AND month>=? AND month<=?
        AND remaining_lease BETWEEN ? AND ? AND resale_price>0
        ORDER BY month DESC, rowid DESC''', (town, kind, start, end, max(0, lease - 5), min(99, lease + 5)))]
    blocks = len({(r['block'], r['street_name']) for r in rows})
    result = dict(status='insufficient', count=len(rows), blocks=blocks, start=start, end=end,
                  town=town, flat_type=kind, asking=price, lease=lease,
                  lease_band=[max(0, lease-5), min(99, lease+5)], range=None, median=None,
                  examples=rows[:10])
    if len(rows) < 20 or blocks < 3:
        return result
    def quantile(values, p):
        values = sorted(values)
        pos = (len(values)-1)*p
        lo, hi = math.floor(pos), math.ceil(pos)
        return values[lo] + (values[hi]-values[lo])*(pos-lo)
    prices = [r['resale_price'] for r in rows]
    lower, median, upper = (quantile(prices, p) for p in (.25, .5, .75))
    result.update(range=[lower, upper], median=median, gap_pct=(price/median-1)*100,
                  status='above_range' if price>upper else 'below_range' if price<lower else 'within_range',
                  area_range=[min(r['floor_area_sqm'] for r in rows), max(r['floor_area_sqm'] for r in rows)])
    return result
