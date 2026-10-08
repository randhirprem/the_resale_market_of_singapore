"""Lossless CSV ingestion and exact, filtered HDB resale statistics."""
import argparse
import csv
import json
import math
import re
import sqlite3
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = ROOT / 'data' / 'hdb.sqlite3'
MONTH = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')


def resale_sources(root=ROOT):
    """Discover sales by schema; the newer full snapshot supersedes the old one."""
    old = 'Resale flat prices based on registration date from Jan-2017 onwards.csv'
    new = 'ResaleflatpricesbasedonregistrationdatefromJan2017onwards.csv'
    required = {'month', 'town', 'flat_type', 'block', 'street_name', 'storey_range',
                'floor_area_sqm', 'flat_model', 'lease_commence_date', 'resale_price'}
    paths = []
    for path in sorted(Path(root).glob('*.csv')):
        if path.name == old and (Path(root) / new).is_file():
            continue
        with path.open(encoding='utf-8-sig', newline='') as stream:
            valid = required.issubset(next(csv.reader(stream), []))
            if path.name in (old, new) and not valid:
                raise ValueError(f'{path.name}: missing required resale columns')
            if valid:
                paths.append(path)
    return paths


def connect(path=DEFAULT_DB):
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def normalized(row, source):
    month = row['month'].strip()
    if not MONTH.fullmatch(month):
        raise ValueError('invalid month')
    area, price = float(row['floor_area_sqm']), float(row['resale_price'])
    if not all(math.isfinite(x) and x > 0 for x in (area, price)):
        raise ValueError('price and area must be positive finite numbers')
    lease = row.get('remaining_lease', '').strip()
    if lease:
        if re.fullmatch(r'\d+(\.\d+)?', lease):
            lease = float(lease)
        else:
            match = re.fullmatch(r'(\d+) years?(?: (\d+) months?)?', lease)
            if not match:
                raise ValueError('invalid remaining lease')
            lease = int(match[1]) + int(match[2] or 0) / 12
    else:
        lease = None
    flat_type = row['flat_type'].strip().upper().replace('MULTI GENERATION', 'MULTI-GENERATION')
    town = row['town'].strip().upper()
    if not town or not flat_type:
        raise ValueError('missing town or flat type')
    return (month, town, flat_type, row['block'].strip(), row['street_name'].strip().upper(),
            row['storey_range'].strip(), area, row['flat_model'].strip().upper(),
            int(row['lease_commence_date']), lease, price, price / area, source)


def import_data(csv_paths, database_path=DEFAULT_DB):
    paths = sorted(Path(p) for p in csv_paths)
    if not paths:
        raise ValueError('No source CSV files found')
    db = Path(database_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    staging = db.with_suffix('.building.sqlite3')
    staging.unlink(missing_ok=True)
    con = connect(staging)
    sources = []
    try:
        con.executescript('''
            CREATE TABLE sales (
                id INTEGER PRIMARY KEY, month TEXT NOT NULL, town TEXT NOT NULL,
                flat_type TEXT NOT NULL, block TEXT, street_name TEXT, storey_range TEXT,
                floor_area_sqm REAL, flat_model TEXT, lease_commence_date INTEGER,
                remaining_lease REAL, resale_price REAL, price_per_sqm REAL, source TEXT
            );
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
        ''')
        for path in paths:
            count = 0
            with path.open(encoding='utf-8-sig', newline='') as stream:
                batch = []
                for line, row in enumerate(csv.DictReader(stream), 2):
                    try:
                        batch.append(normalized(row, path.name))
                    except (ValueError, KeyError, TypeError) as error:
                        raise ValueError(f'{path.name}: row {line}: {error}') from error
                    count += 1
                    if len(batch) >= 10000:
                        con.executemany('INSERT INTO sales VALUES (NULL,' + ','.join(['?']*13) + ')', batch)
                        batch.clear()
                if batch:
                    con.executemany('INSERT INTO sales VALUES (NULL,' + ','.join(['?']*13) + ')', batch)
            sources.append({'file': path.name, 'rows': count})
        con.executescript('''
            CREATE INDEX sales_month ON sales(month);
            CREATE INDEX sales_town_month ON sales(town,month);
            CREATE INDEX sales_type_month ON sales(flat_type,month);
        ''')
        con.execute('INSERT INTO metadata VALUES (?,?)', ('sources', json.dumps(sources)))
        con.commit()
        con.close()
        staging.replace(db)
        return sources
    except Exception:
        con.close()
        staging.unlink(missing_ok=True)
        raise


def metadata(con):
    row = dict(con.execute('SELECT COUNT(*) AS count, MIN(month) AS min_month, MAX(month) AS max_month FROM sales').fetchone())
    row['towns'] = [r[0] for r in con.execute('SELECT DISTINCT town FROM sales ORDER BY town')]
    row['flat_types'] = [r[0] for r in con.execute('SELECT DISTINCT flat_type FROM sales ORDER BY flat_type')]
    row['sources'] = json.loads(con.execute("SELECT value FROM metadata WHERE key='sources'").fetchone()[0])
    return row


def where(filters, ignore_town=False, include_search=False):
    clauses, values = [], []
    for key, operator in [('start', '>='), ('end', '<=')]:
        value = filters.get(key, '')
        if value:
            if not MONTH.fullmatch(value):
                raise ValueError(f'{key} must be a valid YYYY-MM month')
            clauses.append(f'month {operator} ?')
            values.append(value)
    if filters.get('start') and filters.get('end') and filters['start'] > filters['end']:
        raise ValueError('Start month must be before or equal to end month')
    for key in ('town', 'flat_type'):
        if filters.get(key) and not (key == 'town' and ignore_town):
            clauses.append(f'{key} = ?')
            values.append(filters[key])
    if include_search and filters.get('search', '').strip():
        # instr treats percent and underscore literally and uses bound values.
        clauses.append("instr(upper(block || ' ' || street_name), upper(?)) > 0")
        values.append(filters['search'].strip()[:200])
    return (' WHERE ' + ' AND '.join(clauses) if clauses else ''), values


def summarize(rows):
    return {
        'count': len(rows),
        'price': statistics.median(r['resale_price'] for r in rows) if rows else None,
        'psm': statistics.median(r['price_per_sqm'] for r in rows) if rows else None,
        'area': statistics.median(r['floor_area_sqm'] for r in rows) if rows else None,
    }


def group_summary(rows, key):
    groups = defaultdict(list)
    for row in rows:
        groups[row[key]].append(row)
    return [{key: name, **summarize(group)} for name, group in sorted(groups.items())]


def dashboard(con, filters):
    clause, values = where(filters, ignore_town=True)
    rows = con.execute('SELECT month,town,flat_type,resale_price,price_per_sqm,floor_area_sqm FROM sales' + clause, values).fetchall()
    selected = [r for r in rows if not filters.get('town') or r['town'] == filters['town']]
    trend = []
    if selected:
        coverage = con.execute('SELECT MIN(month), MAX(month) FROM sales').fetchone()
        start = max(filters.get('start') or coverage[0], coverage[0])
        end = min(filters.get('end') or coverage[1], coverage[1])
        monthly = {row['month']: row for row in group_summary(selected, 'month')}
        year, month = map(int, start.split('-'))
        current = start
        while current <= end:
            trend.append(monthly.get(current, {'month': current, 'count': 0, 'price': None, 'psm': None, 'area': None}))
            month += 1
            if month == 13:
                month, year = 1, year + 1
            current = f'{year:04d}-{month:02d}'
    return {'summary': summarize(selected), 'trend': trend,
            'towns': sorted(group_summary(rows, 'town'), key=lambda r: r['price'], reverse=True),
            'mix': group_summary(selected, 'flat_type')}


def transactions(con, filters):
    clause, values = where(filters, include_search=True)
    try:
        page, size = int(filters.get('page', 1)), int(filters.get('page_size', 12))
    except (TypeError, ValueError) as error:
        raise ValueError('Page and page size must be integers') from error
    if page < 1 or not 1 <= size <= 100:
        raise ValueError('Page must be positive and page size between 1 and 100')
    count = con.execute('SELECT COUNT(*) FROM sales' + clause, values).fetchone()[0]
    rows = con.execute('SELECT * FROM sales' + clause + ' ORDER BY month DESC, id DESC LIMIT ? OFFSET ?', values + [size, (page-1)*size]).fetchall()
    return {'total': count, 'page': page, 'page_size': size, 'rows': [dict(row) for row in rows]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Import resale CSVs, preferring the latest 2017-onward snapshot')
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    args = parser.parse_args()
    result = import_data(resale_sources(), args.database)
    print(json.dumps(result, indent=2))
    print(f'Imported {sum(source["rows"] for source in result):,} transactions into {args.database}')
