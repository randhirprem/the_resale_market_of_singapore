import csv
import tempfile
import unittest
from pathlib import Path
from backend.data import import_data, connect, dashboard, transactions, metadata

FIELDS = ['month','town','flat_type','block','street_name','storey_range','floor_area_sqm','flat_model','lease_commence_date','remaining_lease','resale_price']

class DataTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.csv = self.root/'sample.csv'
        rows = [
            ['2024-01','BEDOK','3 ROOM','1','TEST ROAD','01 TO 03','50','Improved','1980','55 years 04 months','100000'],
            ['2024-01','BEDOK','3 ROOM','1','TEST ROAD','01 TO 03','50','Improved','1980','55 years 04 months','100000'],
            ['2024-02','BEDOK','4 ROOM','2','OTHER ROAD','04 TO 06','100','MODEL A','1990','65','300000'],
            ['2024-02','TAMPINES','MULTI GENERATION','3','THIRD ROAD','07 TO 09','200','Model A','2000','','900000'],
            ['2023-12','BEDOK','3 ROOM','4','OLD ROAD','01 TO 03','60','Improved','1980','','80000'],
        ]
        with self.csv.open('w',newline='') as f:
            w=csv.writer(f); w.writerow(FIELDS); w.writerows(rows)
        self.db = self.root/'data.db'
        import_data([self.csv], self.db)
        self.con = connect(self.db)
    def tearDown(self):
        self.con.close(); self.tmp.cleanup()
    def test_import_preserves_duplicate_transactions(self):
        self.assertEqual(metadata(self.con)['count'],5)
        self.assertEqual(metadata(self.con)['max_month'],'2024-02')
    def test_exact_even_medians(self):
        result=dashboard(self.con,{'start':'2024-01','end':'2024-12'})
        self.assertEqual(result['summary']['count'],4)
        self.assertEqual(result['summary']['price'],200000)
        self.assertEqual(result['summary']['psm'],2500)
        self.assertEqual(result['summary']['area'],75)
    def test_intersecting_filters_and_odd_median(self):
        result=dashboard(self.con,{'start':'2024-01','end':'2024-12','town':'BEDOK','flat_type':'3 ROOM'})
        self.assertEqual(result['summary']['count'],2)
        self.assertEqual(result['summary']['price'],100000)
        self.assertEqual(len(result['towns']),1)
    def test_town_comparisons_ignore_selected_town(self):
        result=dashboard(self.con,{'start':'2024-01','end':'2024-12','town':'BEDOK'})
        self.assertEqual(result['summary']['price'],100000)
        self.assertEqual(len(result['towns']),2)
    def test_empty_results_have_null_price(self):
        result=dashboard(self.con,{'town':'NO SUCH TOWN'})
        self.assertEqual(result['summary']['count'],0)
        self.assertIsNone(result['summary']['price'])
    def test_normalization_and_lease(self):
        result=transactions(self.con,{'flat_type':'MULTI-GENERATION'})
        self.assertEqual(result['total'],1)
        result=transactions(self.con,{'search':'test road'})
        self.assertEqual(result['total'],2)
        self.assertAlmostEqual(result['rows'][0]['remaining_lease'],55+4/12)
    def test_address_search_treats_wildcards_literally(self):
        self.assertEqual(transactions(self.con,{'search':'%'})['total'],0)
        self.assertEqual(transactions(self.con,{'search':'_'})['total'],0)
    def test_trend_retains_months_without_sales(self):
        result=dashboard(self.con,{'start':'2023-12','end':'2024-02','flat_type':'4 ROOM'})
        self.assertEqual([r['month'] for r in result['trend']],['2023-12','2024-01','2024-02'])
        self.assertEqual(result['trend'][0]['count'],0)
        self.assertIsNone(result['trend'][0]['price'])
        self.assertEqual(result['trend'][2]['count'],1)
    def test_pagination(self):
        a=transactions(self.con,{'page':'1','page_size':'2'})
        b=transactions(self.con,{'page':'2','page_size':'2'})
        self.assertEqual(len(a['rows']),2)
        self.assertTrue(set(r['id'] for r in a['rows']).isdisjoint(r['id'] for r in b['rows']))
        self.assertEqual(a['total'],5)
    def test_invalid_filters_rejected(self):
        for filters in [{'start':'2024-99'},{'start':'2024-04','end':'2023-01'},{'page':'-1'},{'page_size':'100000'}]:
            with self.subTest(filters=filters), self.assertRaises(ValueError):
                transactions(self.con,filters)
    def test_invalid_rows_reported_without_replacing_existing_database(self):
        with self.csv.open('a') as f:
            f.write('2024-01,BEDOK,3 ROOM,5,BAD,01 TO 03,0,Improved,1980,,100000\n')
        with self.assertRaisesRegex(ValueError,'sample.csv.*7'):
            import_data([self.csv], self.db)
        self.assertEqual(metadata(self.con)['count'],5)

if __name__=='__main__': unittest.main()
