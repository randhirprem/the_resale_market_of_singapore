"""Local reference datasets, school joins, and bounded map viewport queries.

All file access uses this explicit registry. Reference snapshots are independent
of resale date/town filters; no proximity or price causation is inferred.
"""
import csv
import json
import math
import re
from collections import defaultdict
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path

from backend.data import ROOT

TABLES = {
    'schools': ('Schools & programmes', 'General information of schools.csv'),
    'buildings': ('HDB buildings', 'HDBPropertyInformation.csv'),
    'hawkers': ('Markets & hawker stalls', 'ListofGovernmentMarketsHawkerCentres.csv'),
    'school-travel': ('MRT / LRT → secondary schools', 'TravellingDistancebetweenMRTLRTStationtoSecondarySchool.csv'),
    'cars': ('Annual car population by make', 'AnnualCarPopulationbyMake.csv'),
    'rail': ('MRT & LRT station counts', 'NumberofMRTandLRTStations.csv'),
    'courses': ('Community courses by year', 'SportsAndPerformingArtsCoursesConductedByCommunityClubsResidentsCommitteesResidentsNetworksNeighbourhoodCommitteesAndPassionWaveAnnual.csv'),
    'ccas': ('School CCAs', 'Co-curricular activities (CCAs).csv'),
    'subjects': ('School subjects', 'Subjects Offered.csv'),
    'moe': ('MOE programmes', 'MOE Programmes.csv'),
    'distinctive': ('School distinctive programmes', 'School Distinctive Programmes.csv'),
}
LAYERS = {
    'mrt-exits': ('MRT station exits', 'LTAMRTStationExitGEOJSON.geojson', '#3ee7d4'),
    'hawkers': ('Hawker centres', 'HawkerCentresGEOJSON.geojson', '#eacc67'),
    'community-wave': ('Community clubs & PAssion WaVe', 'CommunityClubPAssionWaVeOutlet.geojson', '#f05eb9'),
    'community-clubs': ('Community clubs (alternate source)', 'CommunityClubs.geojson', '#e7a1cd'),
    'parks': ('Parks & nature reserves', 'NParksParksandNatureReserves.geojson', '#70db8d'),
    'facilities': ('Park facilities', 'ParkFacilities.geojson', '#c5de75'),
    'cycling': ('Cycling paths', 'CyclingPathNetworkGEOJSON.geojson', '#6da9ff'),
    'tracks': ('Park tracks', 'NParksTracks.geojson', '#9bcd85'),
    'connectors': ('Park connector loops', 'ParkConnectorLoop.geojson', '#42cfaf'),
    'school-zones': ('Road school zones', 'LTASchoolZone.geojson', '#ffbc7a'),
    'carparks': ('HDB car park outlines', 'HDBCarParksOutlines.geojson', '#9caaf9'),
    'subzones': ('URA 2019 subzones', 'MasterPlan2019SubzoneBoundaryNoSeaGEOJSON.geojson', '#a88aff'),
    'cemeteries': ('Active cemeteries', 'ActiveCemeteriesGEOJSON.geojson', '#c8b6a6'),
    'after-death': ('After-death facilities', 'AfterDeathFacilities.geojson', '#ccaacc'),
    'columbaria': ('Dedicated columbaria', 'DedicatedColumbariaGEOJSON.geojson', '#baa0db'),
    'park-labels': ('2014 park plan annotations', 'MP14SDCPPWPLANParksandOpenSpaceName.geojson', '#a8c38e'),
    'nature-labels': ('2019 nature plan annotations', 'MasterPlan2019SDCPNatureBoundaryTextlayerGEOJSON.geojson', '#84b9a0'),
}


def catalog(root=ROOT):
    result = {
        'datasets': [{'id': key, 'label': value[0], 'file': value[1]}
                     for key, value in TABLES.items() if (Path(root) / value[1]).is_file()],
        'layers': [{'id': key, 'label': value[0], 'file': value[1], 'color': value[2]}
                   for key, value in LAYERS.items() if (Path(root) / value[1]).is_file()],
    }
    if all((Path(root) / TABLES[key][1]).is_file() for key in ('schools', 'subjects', 'ccas', 'school-travel')):
        result['datasets'].insert(0, {'id': 'school-rankings', 'label': 'School ranking · programmes & access (S1–S5)',
                                     'file': 'Derived from school directory, subject, CCA and station-to-school travel files'})
    return result


@lru_cache(maxsize=24)
def _read_csv(path, modified):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames or []
        return columns, [{key: (value or '').strip() for key, value in row.items() if key}
                         for row in reader]


def table(key, root):
    path = Path(root) / TABLES[key][1]
    return _read_csv(str(path), path.stat().st_mtime_ns)


def _school_key(name):
    return ' '.join(name.upper().split())


def school_alias(name):
    """Conservative spelling variants; retain primary/secondary distinctions."""
    name = re.sub(r'\bST\.?(?=\s)', 'SAINT', _school_key(name))
    name = re.sub(r'\bSCHOOL\b', '', name)
    return re.sub(r'[^A-Z0-9]', '', name)


def school_rows(root):
    columns, base = table('schools', root)
    rows = [dict(row) for row in base]
    indexed = {_school_key(row['school_name']): row for row in rows}
    aliases = defaultdict(list)
    for key in indexed:
        aliases[school_alias(key)].append(key)
    extras = [('subjects', 'subjects', ['Subject_Desc']),
              ('ccas', 'ccas', ['cca_grouping_desc', 'cca_generic_name', 'cca_customized_name']),
              ('moe', 'moe_programmes', ['moe_programme_desc']),
              ('distinctive', 'distinctive_programmes', ['alp_domain', 'alp_title', 'llp_domain1', 'llp_title'])]
    for source, field, values in extras:
        groups = {}
        if (Path(root) / TABLES[source][1]).is_file():
            for row in table(source, root)[1]:
                name = next((v for k, v in row.items() if k.lower() == 'school_name'), '')
                value = ' · '.join(dict.fromkeys(row.get(k, '') for k in values
                                                if row.get(k, '').lower() not in ('', 'na', 'null')))
                if value:
                    key = _school_key(name)
                    candidates = aliases[school_alias(name)]
                    if key not in indexed and len(candidates) == 1:
                        key = candidates[0]
                    groups.setdefault(key, set()).add(value)
        for key, row in indexed.items():
            row[field] = '; '.join(sorted(groups.get(key, [])))
    return columns + [item[1] for item in extras], rows


def positive_int(value, name, maximum=None):
    try:
        result = int(value)
    except (ValueError, TypeError) as error:
        raise ValueError(f'{name} must be an integer') from error
    if result < 1 or (maximum and result > maximum):
        raise ValueError(f'{name} must be between 1 and {maximum}' if maximum else f'{name} must be positive')
    return result


def records(params, root=ROOT):
    key = params.get('dataset', 'schools')
    if key == 'school-rankings':
        from backend.insights import school_rankings
        result = school_rankings(root)
        page = positive_int(params.get('page', 1), 'Page')
        size = positive_int(params.get('page_size', 12), 'Page size', 100)
        rows = result.pop('rows')
        count = len(rows)
        search = params.get('search', '').strip().casefold()[:200]
        rows = [row for row in rows if search in ' '.join(str(v) for v in row.values()).casefold()]
        return {**result, 'dataset': key, 'file': 'Derived school ranking', 'source_count': count,
                'total': len(rows), 'page': page, 'page_size': size, 'rows': rows[(page - 1) * size:page * size]}
    if key not in TABLES:
        raise ValueError('Unknown reference dataset')
    if not (Path(root) / TABLES[key][1]).is_file():
        raise ValueError('Reference source is not available')
    page = positive_int(params.get('page', 1), 'Page')
    size = positive_int(params.get('page_size', 12), 'Page size', 100)
    columns, rows = school_rows(root) if key == 'schools' else table(key, root)
    count = len(rows)
    search = params.get('search', '').strip().casefold()[:200]
    if search:
        rows = [row for row in rows if search in ' '.join(row.values()).casefold()]
    return {'dataset': key, 'file': TABLES[key][1], 'columns': columns,
            'source_count': count, 'total': len(rows), 'page': page, 'page_size': size,
            'rows': rows[(page - 1) * size:page * size]}


class AttributeTable(HTMLParser):
    """Extract the legacy GeoJSON HTML table as plain text, never as markup."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cells, self.properties, self.text, self.in_cell = [], {}, [], False

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cells = []
        if tag in ('td', 'th'):
            self.text, self.in_cell = [], True

    def handle_data(self, data):
        if self.in_cell:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag in ('td', 'th'):
            self.cells.append(''.join(self.text).strip())
            self.in_cell = False
        if tag == 'tr' and len(self.cells) == 2:
            self.properties[self.cells[0]] = self.cells[1]


def points(coords):
    if coords and isinstance(coords[0], (int, float)):
        yield coords
    else:
        for child in coords:
            yield from points(child)


@lru_cache(maxsize=3)
def _geometry(path, modified):
    with Path(path).open() as stream:
        data = json.load(stream)
    items = []
    for feature in data['features']:
        geometry = feature.get('geometry')
        if not geometry:
            continue
        positions = list(points(geometry['coordinates']))
        if not positions:
            continue
        bounds = (min(p[0] for p in positions), min(p[1] for p in positions),
                  max(p[0] for p in positions), max(p[1] for p in positions))
        props = dict(feature.get('properties') or {})
        if '<' in str(props.get('Description', '')):
            parser = AttributeTable()
            parser.feed(props.pop('Description'))
            props.update(parser.properties)
        # Photo and external links are reference strings, never rendered as HTML.
        props = {k: v for k, v in props.items() if v is not None and v != ''}
        items.append((bounds, {'type': 'Feature', 'geometry': geometry, 'properties': props}))
    return items


def map_features(params, root=ROOT):
    key = params.get('layer', '')
    if key not in LAYERS:
        raise ValueError('Unknown map layer')
    path = Path(root) / LAYERS[key][1]
    if not path.is_file():
        raise ValueError('Map source is not available')
    limit = positive_int(params.get('limit', 2000), 'Feature limit', 3000)
    try:
        bbox = [float(value) for value in params.get('bbox', '-180,-90,180,90').split(',')]
        if (len(bbox) != 4 or not all(math.isfinite(v) for v in bbox)
                or not -180 <= bbox[0] <= bbox[2] <= 180 or not -90 <= bbox[1] <= bbox[3] <= 90):
            raise ValueError()
    except (ValueError, TypeError) as error:
        raise ValueError('bbox must be west,south,east,north in valid longitude/latitude') from error
    matched, features = 0, []
    for bounds, feature in _geometry(str(path), path.stat().st_mtime_ns):
        if bounds[0] <= bbox[2] and bounds[2] >= bbox[0] and bounds[1] <= bbox[3] and bounds[3] >= bbox[1]:
            matched += 1
            if len(features) < limit:
                features.append(feature)
    return {'type': 'FeatureCollection', 'features': features, 'matched': matched,
            'truncated': matched > limit, 'file': path.name}
