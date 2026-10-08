"""Offline log-price regressions and lightweight serving of versioned results.

NumPy is needed only to generate the artifact, not to serve the dashboard.
Equations are trained on 30 months; the following six months are held out.
"""
import argparse
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from backend.data import DEFAULT_DB, ROOT, connect

ARTIFACT = ROOT / 'data' / 'price-models.json'
VERSION = 1
TYPES = {'2 ROOM', '3 ROOM', '4 ROOM', '5 ROOM', 'EXECUTIVE'}
GROUPS = {'size_layout': 'Floor area & flat type', 'lease': 'Remaining lease',
          'floor': 'Storey', 'time': 'Sale timing', 'town': 'Estate location'}


def month_index(month):
    year, number = map(int, month.split('-'))
    return year * 12 + number - 1


def month_text(index):
    return f'{index // 12:04d}-{index % 12 + 1:02d}'


def model_window(latest):
    end = month_index(latest) - 1  # Always exclude the potentially partial latest month.
    return dict(start=month_text(end - 35), train_end=month_text(end - 6),
                test_start=month_text(end - 5), end=month_text(end), reference_month=month_text(end - 6))


def _design(rows, schema):
    import numpy as np
    columns = schema['columns']
    matrix = np.zeros((len(rows), len(columns)))
    for i, row in enumerate(rows):
        values = {'intercept': 1, 'log_area': math.log(row['area'] / 100),
                  'lease': (row['lease'] - 70) / 10, 'floor': (row['floor'] - 8) / 10, 'time': row['t']}
        for j, column in enumerate(columns):
            if column.startswith('type:'):
                matrix[i, j] = float(row['flat_type'] == column[5:])
            elif column.startswith('town:'):
                town = column[5:]
                matrix[i, j] = float(row['town'] == town) - schema['town_weights'][town]
            else:
                matrix[i, j] = values[column]
    return matrix


def fit_model(rows, national=False, omit=None, uncertainty=True):
    import numpy as np
    if not rows:
        raise ValueError('No rows to fit')
    types = sorted({row['flat_type'] for row in rows})
    if '4 ROOM' not in types:
        raise ValueError('No 4 ROOM reference category')
    town_counts = Counter(row['town'] for row in rows) if national else {}
    weights = {town: count / len(rows) for town, count in town_counts.items()}
    towns = sorted(weights)
    columns = ['intercept']
    if omit != 'size_layout':
        columns += ['log_area'] + ['type:' + kind for kind in types if kind != '4 ROOM']
    columns += [field for field in ('lease', 'floor', 'time') if field != omit]
    if national and omit != 'town':
        columns += ['town:' + town for town in towns[1:]]
    schema = {'columns': columns, 'town_weights': weights}
    x = _design(rows, schema)
    y = np.array([row['log_price'] for row in rows])
    beta, _, rank, singular = np.linalg.lstsq(x, y, rcond=None)
    if rank < len(columns):
        raise ValueError('Design matrix is rank deficient; independent effects cannot be separated')
    if singular[0] / singular[-1] > 1e8:
        raise ValueError('Design matrix is ill-conditioned')
    residual = y - x @ beta
    coefficients = dict(zip(columns, map(float, beta)))
    covariance = None
    blocks = sorted({row['block_key'] for row in rows})
    if uncertainty and len(blocks) > 1 and len(rows) > len(columns):
        block_index = {block: i for i, block in enumerate(blocks)}
        scores = np.zeros((len(blocks), len(columns)))
        np.add.at(scores, [block_index[row['block_key']] for row in rows], x * residual[:, None])
        inverse = np.linalg.inv(x.T @ x)
        correction = len(blocks) / (len(blocks) - 1) * (len(rows) - 1) / (len(rows) - len(columns))
        covariance = inverse @ (scores.T @ scores) @ inverse * correction
    intervals = {}
    if covariance is not None:
        for i, column in enumerate(columns):
            se = math.sqrt(max(0, float(covariance[i, i])))
            intervals[column] = [float(beta[i] - 1.96 * se), float(beta[i] + 1.96 * se)]
    shift = sum(coefficients.get('town:' + town, 0) * weight for town, weight in weights.items())
    effects = {town: coefficients.get('town:' + town, 0) - shift for town in towns} if national else {}
    support = {field: {'min': min(r[field] for r in rows), 'max': max(r[field] for r in rows),
                       'p25': float(np.percentile([r[field] for r in rows], 25)),
                       'p75': float(np.percentile([r[field] for r in rows], 75))}
               for field in ('area', 'lease', 'floor')}
    return {**schema, 'coefficients': coefficients, 'intervals': intervals,
            'town_effects': effects, 'flat_types': types, 'n': len(rows), 'blocks': len(blocks),
            'support': support, 'type_counts': dict(Counter(row['flat_type'] for row in rows)),
            'fit_r2_log': float(1 - (residual @ residual) / max(float(((y - y.mean()) ** 2).sum()), 1e-12))}


def predict(model, rows):
    import numpy as np
    beta = np.array([model['coefficients'][column] for column in model['columns']])
    return np.exp(_design(rows, model) @ beta)


def errors(model, rows):
    if not rows:
        return None
    predictions = predict(model, rows)
    ape = [abs(float(predicted) / row['price'] - 1) * 100 for predicted, row in zip(predictions, rows)]
    return {'n': len(rows), 'median_ape': statistics.median(ape), 'mean_ape': statistics.mean(ape)}


def validation_rows(flat_types, rows):
    comparable = [row for row in rows if row['flat_type'] in flat_types]
    if len(comparable) < 30:
        raise ValueError('Fewer than 30 comparable later sales after excluding flat types absent from training; use the pooled equation.')
    return comparable


def ablations(model, train, test, national=False):
    baseline = errors(model, test)
    if not baseline:
        return []
    results = []
    for group, label in GROUPS.items():
        if group == 'town' and not national:
            continue
        try:
            reduced = fit_model(train, national=national, omit=group, uncertainty=False)
            reduced_error = errors(reduced, test)['mean_ape']
            results.append({'group': group, 'label': label,
                            'error_increase_pp': reduced_error - baseline['mean_ape']})
        except ValueError:
            results.append({'group': group, 'label': label, 'error_increase_pp': None})
    return sorted(results, key=lambda item: item['error_increase_pp'] if item['error_increase_pp'] is not None else -math.inf, reverse=True)


def database_signature(path=DEFAULT_DB):
    stat = Path(path).stat()
    return {'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns}


def build_models(database=DEFAULT_DB, destination=ARTIFACT):
    source_signature = database_signature(database)
    with connect(database) as con:
        latest = con.execute('SELECT MAX(month) FROM sales').fetchone()[0]
        if not latest:
            raise ValueError('The transaction database is empty')
        window = model_window(latest)
        raw = con.execute('SELECT month,town,flat_type,block,street_name,storey_range,floor_area_sqm,remaining_lease,resale_price '
                          'FROM sales WHERE month BETWEEN ? AND ?', (window['start'], window['end'])).fetchall()
    rows, excluded = [], Counter()
    for row in raw:
        if row['flat_type'] not in TYPES:
            excluded['rare_flat_types'] += 1
            continue
        try:
            low, high = map(int, row['storey_range'].split(' TO '))
            area, lease, price = float(row['floor_area_sqm']), float(row['remaining_lease']), float(row['resale_price'])
            if not all(math.isfinite(v) for v in (area, lease, price)) or min(area, lease, price) <= 0 or not 0 < low <= high:
                raise ValueError()
        except (ValueError, TypeError):
            excluded['invalid_or_missing_fields'] += 1
            continue
        rows.append({'month': row['month'], 'town': row['town'], 'flat_type': row['flat_type'],
                     'area': area, 'lease': lease, 'floor': (low + high) / 2,
                     't': (month_index(row['month']) - month_index(window['reference_month'])) / 12,
                     'price': price, 'log_price': math.log(price),
                     'block_key': '|'.join((row['town'], row['block'], row['street_name']))})
    train = [row for row in rows if row['month'] <= window['train_end']]
    test = [row for row in rows if row['month'] >= window['test_start']]
    if len({row['month'] for row in train}) != 30 or len({row['month'] for row in test}) != 6:
        raise ValueError('Models require 30 training months followed by six observed validation months')
    national = fit_model(train, national=True)
    national['validation'] = errors(national, test)
    national['importance'] = ablations(national, train, test, national=True)
    towns = []
    for town in sorted({row['town'] for row in rows}):
        training = [row for row in train if row['town'] == town]
        testing = [row for row in test if row['town'] == town]
        result = {'town': town, 'training_n': len(training), 'test_n': len(testing),
                  'national_offset': national['town_effects'].get(town), 'warnings': []}
        if len(training) < 200 or len({row['block_key'] for row in training}) < 20 or len(testing) < 30:
            result.update(model=None, reason='Insufficient support: requires 200 training sales, 20 blocks and 30 later sales. Use the island equation with this estate’s offset.')
        else:
            try:
                local = fit_model(training)
                comparable = validation_rows(local['flat_types'], testing)
                result['test_unseen_type_n'] = len(testing) - len(comparable)
                local['validation'] = errors(local, comparable)
                local['importance'] = ablations(local, training, comparable)
                result.update(model=local, national_validation=errors(national, comparable))
                if local['support']['lease']['max'] - local['support']['lease']['min'] < 10:
                    result['warnings'].append('Less than ten years of lease variation: a ten-year lease comparison extrapolates beyond this estate’s observed range.')
                if any(count < 20 for count in local['type_counts'].values()):
                    result['warnings'].append('Some flat types have fewer than 20 training sales; their separate effects are weakly supported.')
                if local['support']['lease']['min'] > 70 or local['support']['lease']['max'] < 70:
                    result['warnings'].append('The equation’s 70-year reference lease lies outside the local sample. Its intercept is algebraic, not a typical-flat valuation.')
                if local['validation'] and local['validation']['mean_ape'] >= result['national_validation']['mean_ape']:
                    result['warnings'].append('The local equation does not improve average percentage error over the island model on the same later sales.')
            except ValueError as error:
                result.update(model=None, reason=str(error))
        if result['model'] is None:
            result['national_validation'] = errors(national, testing)
        towns.append(result)
    if database_signature(database) != source_signature:
        raise ValueError('Transaction data changed while fitting; rerun the model build.')
    output = {'version': VERSION, 'database': source_signature,
              'generated_at': datetime.now(timezone.utc).isoformat(), 'window': window,
              'excluded': dict(excluded), 'national': national, 'towns': towns,
              'notes': ['Log-price ordinary least squares; equation predicts the geometric price centre, not an unbiased arithmetic mean.',
                        'Training: first 30 months; validation: next six months. Latest source month is excluded. No random split or refit on validation sales.',
                        'National model includes transaction-weight-centred estate intercepts; local models estimate their own slopes.',
                        'Approximate 95% coefficient intervals use standard errors clustered by block. Intervals are not prediction intervals.',
                        'Factor importance is the increase in held-out mean absolute percentage error when that group is removed and the model refitted. Negative values mean removal improved this validation sample.',
                        'Importance measures dependence of this model, not a causal contribution or a share of the sale price. Correlated factors can substitute for one another.',
                        'Schools, MRT distance, parks, renovations, views and exact block location are not measured predictors. Estate offsets also capture omitted differences.',
                        'Rare 1 ROOM and MULTI-GENERATION sales are excluded. Equations apply only to the listed flat types and observed ranges.']}
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix('.building.json')
    staging.write_text(json.dumps(output, allow_nan=False, indent=2))
    staging.replace(destination)
    return output


@lru_cache(maxsize=1)
def _read_artifact(path, modified):
    return json.loads(Path(path).read_text())


def load_models(path=ARTIFACT, database=DEFAULT_DB):
    path = Path(path)
    if not path.is_file():
        raise ValueError('Price equations are not available for this dataset yet.')
    result = _read_artifact(str(path), path.stat().st_mtime_ns)
    if result.get('version') != VERSION or result.get('database') != database_signature(database):
        raise ValueError('Price equations need refreshing after the transaction data changed.')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Fit national and estate equations with a chronological holdout')
    parser.add_argument('--database', type=Path, default=DEFAULT_DB)
    parser.add_argument('--output', type=Path, default=ARTIFACT)
    args = parser.parse_args()
    report = build_models(args.database, args.output)
    print(f"Fitted {report['national']['n']:,} national training sales; {sum(t['model'] is not None for t in report['towns'])} independent estate equations.")
    print(f"Held-out mean absolute percentage error: {report['national']['validation']['mean_ape']:.2f}%")
    print(f'Wrote {args.output}')
