import csv
import json
import tempfile
import unittest
from pathlib import Path

from backend.data import resale_sources
from backend.context import catalog, records, map_features


class ContextTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write_csv(self, name, fields, rows):
        with (self.root / name).open('w', newline='') as stream:
            writer = csv.writer(stream)
            writer.writerow(fields)
            writer.writerows(rows)

    def test_resale_source_selection_excludes_context_and_old_snapshot(self):
        fields = ['month', 'town', 'flat_type', 'block', 'street_name', 'storey_range',
                  'floor_area_sqm', 'flat_model', 'lease_commence_date', 'resale_price']
        old = 'Resale flat prices based on registration date from Jan-2017 onwards.csv'
        new = 'ResaleflatpricesbasedonregistrationdatefromJan2017onwards.csv'
        for name in [old, new, 'historical.csv']:
            self.write_csv(name, fields, [])
        self.write_csv('schools.csv', ['school_name'], [['A']])
        self.assertEqual({p.name for p in resale_sources(self.root)}, {new, 'historical.csv'})
        (self.root / new).unlink()
        self.assertIn(old, {p.name for p in resale_sources(self.root)})

    def test_school_details_join_by_normalized_name_and_keep_postcodes(self):
        self.write_csv('General information of schools.csv', ['school_name', 'postal_code'], [['Test School', '012345']])
        self.write_csv('Subjects Offered.csv', ['School_Name', 'Subject_Desc'], [[' TEST SCHOOL ', 'MATHEMATICS']])
        result = records({'dataset': 'schools', 'search': 'mathematics'}, self.root)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['rows'][0]['postal_code'], '012345')
        self.assertIn('MATHEMATICS', result['rows'][0]['subjects'])

    def test_invalid_replacement_snapshot_fails_instead_of_losing_recent_sales(self):
        self.write_csv('ResaleflatpricesbasedonregistrationdatefromJan2017onwards.csv', ['wrong_header'], [])
        with self.assertRaisesRegex(ValueError, 'resale columns'):
            resale_sources(self.root)

    def test_school_short_names_join_and_cca_choices_remain_distinct(self):
        self.write_csv('General information of schools.csv', ['school_name', 'postal_code'],
                       [['Admiralty Secondary School', '123456'], ['Admiralty Primary School', '234567']])
        self.write_csv('School Distinctive Programmes.csv', ['school_name', 'alp_title'],
                       [['Admiralty Secondary', 'Design Thinking']])
        self.write_csv('Co-curricular activities (CCAs).csv',
                       ['School_name', 'cca_grouping_desc', 'cca_generic_name', 'cca_customized_name'],
                       [['Admiralty Secondary School', 'CHOIR', 'VISUAL AND PERFORMING ARTS', ''],
                        ['Admiralty Secondary School', 'MODERN DANCE', 'VISUAL AND PERFORMING ARTS', '']])
        rows = records({'dataset': 'schools'}, self.root)['rows']
        self.assertIn('Design Thinking', rows[0]['distinctive_programmes'])
        self.assertEqual(rows[1]['distinctive_programmes'], '')
        self.assertIn('CHOIR', rows[0]['ccas'])
        self.assertIn('MODERN DANCE', rows[0]['ccas'])

    def test_pagination_search_and_allowlist(self):
        self.write_csv('HDBPropertyInformation.csv', ['blk_no', 'street'], [['1', 'A ROAD'], ['2', 'A ROAD'], ['3', 'B ROAD']])
        result = records({'dataset': 'buildings', 'search': 'a road', 'page_size': '1', 'page': '2'}, self.root)
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['rows'][0]['blk_no'], '2')
        self.assertEqual(records({'dataset': 'buildings', 'search': '%'}, self.root)['total'], 0)
        with self.assertRaises(ValueError):
            records({'dataset': '../secret'}, self.root)
        with self.assertRaises(ValueError):
            records({'dataset': 'buildings', 'page': '0'}, self.root)

    def test_geo_viewport_limit_and_html_properties(self):
        features = [{'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [103.8 + i / 100, 1.3]},
                     'properties': {'Description': '<table><tr><th>NAME</th><td>Club &amp; Hall</td></tr></table>'}}
                    for i in range(3)]
        (self.root / 'CommunityClubs.geojson').write_text(json.dumps({'type': 'FeatureCollection', 'features': features}))
        result = map_features({'layer': 'community-clubs', 'bbox': '103.795,1.29,103.815,1.31', 'limit': '1'}, self.root)
        self.assertEqual(result['matched'], 2)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['features'][0]['properties']['NAME'], 'Club & Hall')
        for bbox in ['nan,1,104,2', '104,1,103,2', 'garbage']:
            with self.assertRaises(ValueError):
                map_features({'layer': 'community-clubs', 'bbox': bbox}, self.root)
        self.assertEqual(len(catalog(self.root)['layers']), 1)


if __name__ == '__main__':
    unittest.main()
