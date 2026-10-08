import sqlite3
import unittest
from backend import asking

class AskingTest(unittest.TestCase):
    def setUp(self):
        self.con = sqlite3.connect(':memory:')
        self.con.row_factory = sqlite3.Row
        self.con.execute('CREATE TABLE sales(month, town, flat_type, block, street_name, remaining_lease, resale_price, floor_area_sqm, storey_range)')
        self.con.executemany('INSERT INTO sales VALUES(?,?,?,?,?,?,?,?,?)', [('2026-09','BEDOK','4 ROOM',str(i%4),'ROAD',70,300000+i*10000,100,'04 TO 06') for i in range(20)])
        self.con.execute("INSERT INTO sales VALUES('2026-10','BEDOK','4 ROOM','9','ROAD',70,9000000,100,'04 TO 06')")
        self.params = dict(town='BEDOK',flat_type='4 ROOM',lease='70',asking='500000')
    def tearDown(self):
        self.con.close()
    def test_high_asking_and_exact_comparison_range(self):
        result=asking.assess(self.con,self.params)
        self.assertEqual(result['status'],'above_range')
        self.assertEqual(result['count'],20)
        self.assertEqual(result['median'],395000)
        self.assertEqual(result['range'],[347500,442500])
        self.assertEqual(result['end'],'2026-09')
    def test_at_and_below_range_are_not_called_overpriced(self):
        for price,status in [('400000','within_range'),('300000','below_range')]:
            self.assertEqual(asking.assess(self.con,{**self.params,'asking':price})['status'],status)
    def test_unrelated_and_old_sales_do_not_influence_result(self):
        for month,town,kind,lease in [('2025-09','BEDOK','4 ROOM',70),('2026-09','BEDOK','3 ROOM',70),('2026-09','TAMPINES','4 ROOM',70),('2026-09','BEDOK','4 ROOM',80)]:
            self.con.execute('INSERT INTO sales VALUES(?,?,?,?,?,?,?,?,?)',(month,town,kind,'9','ROAD',lease,9000000,100,'04 TO 06'))
        self.assertEqual(asking.assess(self.con,self.params)['median'],395000)
    def test_sparse_or_one_block_withholds_price_verdict(self):
        self.assertEqual(asking.assess(self.con,{**self.params,'lease':'40'})['status'],'insufficient')
        self.con.execute("UPDATE sales SET block='1'")
        self.assertEqual(asking.assess(self.con,self.params)['status'],'insufficient')
    def test_examples_follow_recent_records_not_cheapest_prices(self):
        result=asking.assess(self.con,self.params)
        self.assertEqual(result['examples'][0]['resale_price'],490000)
        self.assertEqual(result['examples'][-1]['resale_price'],400000)
    def test_bad_inputs_rejected(self):
        for key,value in [('asking','nan'),('asking','-1'),('lease','100'),('lease','inf'),('town','UNKNOWN'),('flat_type','')]:
            with self.assertRaises(ValueError): asking.assess(self.con,{**self.params,key:value})
