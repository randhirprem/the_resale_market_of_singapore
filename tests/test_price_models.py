import math
import tempfile
import unittest
from pathlib import Path
import numpy as np
from backend.price_models import fit_model, predict, model_window, load_models, database_signature, validation_rows, VERSION
import json


class PriceModelTest(unittest.TestCase):
    def rows(self):
        rng = np.random.default_rng(42)
        rows = []
        for i in range(500):
            area, lease, floor, t = rng.uniform(60, 140), rng.uniform(45, 95), rng.uniform(2, 35), rng.uniform(-2, 0)
            town = 'A' if i % 2 else 'B'
            flat_type = '4 ROOM' if i % 3 else '5 ROOM'
            y = 13 + .8 * math.log(area / 100) + .12 * ((lease - 70) / 10) + .03 * ((floor - 8) / 10) + .04 * t
            y += .08 if flat_type == '5 ROOM' else 0
            y += .2 if town == 'A' else -.2
            rows.append(dict(area=area, lease=lease, floor=floor, t=t, town=town, flat_type=flat_type,
                             log_price=y, price=math.exp(y), block_key=f'{town}:{i % 60}'))
        return rows

    def test_national_recovers_known_equation_and_centred_estate_effects(self):
        rows = self.rows()
        model = fit_model(rows, national=True)
        self.assertAlmostEqual(model['coefficients']['log_area'], .8, places=8)
        self.assertAlmostEqual(model['coefficients']['lease'], .12, places=8)
        self.assertAlmostEqual(model['coefficients']['floor'], .03, places=8)
        self.assertAlmostEqual(model['coefficients']['time'], .04, places=8)
        self.assertAlmostEqual(sum(model['town_effects'].values()), 0, places=8)
        np.testing.assert_allclose(predict(model, rows), [r['price'] for r in rows], rtol=1e-8)

    def test_local_recovers_slopes_and_omits_estate_terms(self):
        rows = [r for r in self.rows() if r['town'] == 'A']
        model = fit_model(rows)
        self.assertAlmostEqual(model['coefficients']['intercept'], 13.2, places=8)
        self.assertEqual(model['town_effects'], {})
        self.assertAlmostEqual(model['coefficients']['log_area'], .8, places=8)

    def test_degenerate_data_does_not_produce_a_misleading_equation(self):
        row = self.rows()[1]
        with self.assertRaisesRegex(ValueError, 'rank'):
            fit_model([row] * 30)

    def test_window_excludes_latest_month_and_separates_validation(self):
        self.assertEqual(model_window('2026-10'), {'start': '2023-10', 'train_end': '2026-03',
                         'test_start': '2026-04', 'end': '2026-09', 'reference_month': '2026-03'})

    def test_validation_threshold_applies_after_unseen_types_are_removed(self):
        rows = [{'flat_type': '4 ROOM'}] * 29 + [{'flat_type': '2 ROOM'}] * 40
        with self.assertRaisesRegex(ValueError, '30 comparable'):
            validation_rows(['4 ROOM'], rows)
        rows.append({'flat_type': '4 ROOM'})
        self.assertEqual(len(validation_rows(['4 ROOM'], rows)), 30)

    def test_missing_artifact_has_actionable_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, 'not available'):
                load_models(Path(folder) / 'models.json', Path(folder) / 'db')

    def test_reimport_invalidates_old_equations(self):
        with tempfile.TemporaryDirectory() as folder:
            database, artifact = Path(folder) / 'db', Path(folder) / 'models.json'
            database.write_bytes(b'first')
            artifact.write_text(json.dumps({'version': VERSION, 'database': database_signature(database)}))
            self.assertEqual(load_models(artifact, database)['version'], VERSION)
            database.write_bytes(b'replaced database')
            with self.assertRaisesRegex(ValueError, 'refreshing'):
                load_models(artifact, database)


if __name__ == '__main__': unittest.main()
