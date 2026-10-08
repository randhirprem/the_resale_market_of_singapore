import csv
import tempfile
import unittest
from pathlib import Path
from backend.insights import school_rankings


class RankingTest(unittest.TestCase):
    def test_balance_complete_routes_and_postal_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = {
                'General information of schools.csv': (
                    ['school_name', 'postal_code', 'mainlevel_code', 'dgp_code'],
                    [['A Secondary School', '012345', 'SECONDARY (S1-S5)', 'A'],
                     ['B Secondary School', '123456', 'SECONDARY (S1-S5)', 'B'],
                     ['C Secondary School', '234567', 'SECONDARY (S1-S5)', 'C']]),
                'Subjects Offered.csv': (['School_Name', 'Subject_Desc'],
                    [['A Secondary School', 'Math'], ['B Secondary School', 'Math'],
                     ['B Secondary School', 'Art'], ['C Secondary School', 'Math']]),
                'Co-curricular activities (CCAs).csv': (['School_name', 'cca_grouping_desc'],
                    [['A Secondary School', 'Choir'], ['B Secondary School', 'Choir'],
                     ['B Secondary School', 'Dance'], ['C Secondary School', 'Choir']]),
                'TravellingDistancebetweenMRTLRTStationtoSecondarySchool.csv': (
                    ['From', 'To', 'To_PostalCode', 'TimeTaken_Mins'],
                    [['S1', 'A Secondary School', '012345', '10'], ['S2', 'A Secondary School', '012345', '20'],
                     ['S1', 'B Secondary School', '123456', '20'], ['S2', 'B Secondary School', '123456', '30'],
                     ['S1', 'C Secondary School', '999999', '1'], ['S2', 'C Secondary School', '999999', '1']]),
            }
            for filename, (fields, rows) in files.items():
                with (root / filename).open('w', newline='') as stream:
                    writer = csv.writer(stream); writer.writerow(fields); writer.writerows(rows)
            result = school_rankings(root)
            self.assertEqual(len(result['rows']), 2)
            # Better access and broader offerings balance equally; ties share a rank.
            self.assertEqual([r['balanced_score'] for r in result['rows']], [50, 50])
            self.assertEqual([r['rank'] for r in result['rows']], [1, 1])
            self.assertEqual(result['origins'], 2)
            self.assertIn('postcode', result['excluded'][0]['reason'])


if __name__ == '__main__': unittest.main()
