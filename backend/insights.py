"""Explicit, descriptive school comparisons; not academic or valuation scores."""
import math
import statistics
from collections import defaultdict
from backend.data import ROOT


def percentile_scores(values):
    """Midrank percentiles, with ties equal and a singleton neutral."""
    ordered = sorted(values)
    n = len(values)
    if n < 2:
        return [50.0] * n
    scores = {}
    for i, value in enumerate(ordered):
        scores.setdefault(value, []).append(i)
    return [statistics.mean(scores[value]) / (n - 1) * 100 for value in values]


def school_rankings(root=ROOT):
    from backend.context import table, school_alias, _school_key

    schools = table('schools', root)[1]
    indexed = {_school_key(row['school_name']): row for row in schools}
    aliases = defaultdict(list)
    postcodes = defaultdict(list)
    for key, row in indexed.items():
        aliases[school_alias(key)].append(key)
        postcodes[row['postal_code']].append(key)
    subjects, ccas = defaultdict(set), defaultdict(set)
    for row in table('subjects', root)[1]:
        if row.get('Subject_Desc'):
            subjects[_school_key(row['School_Name'])].add(row['Subject_Desc'].casefold())
    for row in table('ccas', root)[1]:
        if row.get('cca_grouping_desc'):
            ccas[_school_key(row['School_name'])].add(row['cca_grouping_desc'].casefold())
    travel = table('school-travel', root)[1]
    origins = {row['From'] for row in travel}
    times, conflicts = defaultdict(dict), {}
    for row in travel:
        key = _school_key(row['To'])
        if key not in indexed:
            candidates = aliases[school_alias(key)]
            # A unique supplied school postcode is also a join key. No fuzzy match.
            if len(candidates) != 1:
                candidates = postcodes[row['To_PostalCode']]
            if len(candidates) != 1:
                continue
            key = candidates[0]
        if indexed[key]['postal_code'] != row['To_PostalCode']:
            conflicts[key] = 'Conflicting school postcode between directory and travel source'
            continue
        try:
            value = float(row['TimeTaken_Mins'])
            if not math.isfinite(value) or value < 0:
                raise ValueError()
        except (ValueError, TypeError):
            conflicts[key] = 'Invalid recorded travel time'
            continue
        origin = row['From']
        if origin in times[key] and times[key][origin] != value:
            conflicts[key] = 'Conflicting times for the same station origin'
        times[key][origin] = value
    rows, excluded = [], []
    for key, school in indexed.items():
        # Do not compare differing school stages or specialist curricula together.
        if school['mainlevel_code'] != 'SECONDARY (S1-S5)':
            continue
        reason = conflicts.get(key)
        if not reason and (not origins or set(times[key]) != origins):
            reason = 'Incomplete station-origin coverage in travel source'
        if not reason and (not subjects[key] or not ccas[key]):
            reason = 'Missing subject or CCA records; absence is not scored as zero'
        if reason:
            excluded.append({'school': school['school_name'], 'reason': reason})
            continue
        values = list(times[key].values())
        rows.append({'school': school['school_name'], 'planning_area': school.get('dgp_code', ''),
                     'median_recorded_minutes': statistics.median(values),
                     'origins_within_30_minutes': sum(value <= 30 for value in values),
                     'subject_listings': len(subjects[key]), 'cca_choices': len(ccas[key])})
    for field, weight, sign in [('median_recorded_minutes', .5, -1),
                                ('subject_listings', .25, 1), ('cca_choices', .25, 1)]:
        percentiles = percentile_scores([sign * row[field] for row in rows])
        for row, score in zip(rows, percentiles):
            row['balanced_score'] = row.get('balanced_score', 0) + weight * score
    for row in rows:
        row['balanced_score'] = round(row['balanced_score'], 1)
    rows.sort(key=lambda row: (-row['balanced_score'], row['school']))
    for i, row in enumerate(rows):
        row['rank'] = rows[i - 1]['rank'] if i and row['balanced_score'] == rows[i - 1]['balanced_score'] else i + 1
    return {'rows': rows, 'origins': len(origins), 'excluded': excluded,
            'columns': ['rank', 'school', 'planning_area', 'balanced_score',
                        'median_recorded_minutes', 'origins_within_30_minutes',
                        'subject_listings', 'cca_choices'],
            'methodology': 'S1–S5 secondary schools only. Score: 50% lower median recorded station-to-school time, '
                           '25% unique subject listings and 25% unique CCA choices, using midrank percentiles within '
                           'eligible schools. Every station origin has equal weight. This is a preference-based '
                           'comparison, not an academic ranking, an admissions prediction or a home commute estimate. '
                           'Travel mode and departure time are unspecified. Subject listings include curriculum and '
                           'language variants; more listings do not establish better teaching. Primary schools lack '
                           'equivalent travel data and are not assigned a balanced score.'}
