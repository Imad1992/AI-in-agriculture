import csv
import json
import tempfile
import unittest
from pathlib import Path

from build_dashboard import build_dashboard
from generate_data import generate_dataset
from generate_hyperspectral_images import generate_images
from monitoring_analysis import run_monitoring


class TraceDemoPipelineTest(unittest.TestCase):
    def test_pipeline_outputs_expected_shapes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            data_dir = root / "data"

            shipments_path, sensor_path = generate_dataset(data_dir, seed=42)
            hyperspectral_path = generate_images(shipments_path, data_dir / "hyperspectral_images.json", seed=42)
            monitoring_path = run_monitoring(shipments_path, sensor_path, data_dir / "monitoring_analysis.json")
            dashboard_data_path = data_dir / "dashboard_data.json"
            dashboard_html_path = root / "dashboard.html"
            build_dashboard(
                shipments_path=shipments_path,
                sensor_path=sensor_path,
                monitoring_path=monitoring_path,
                hyperspectral_path=hyperspectral_path,
                data_output=dashboard_data_path,
                html_output=dashboard_html_path,
            )

            with shipments_path.open(newline="", encoding="utf-8") as f:
                shipments = list(csv.DictReader(f))
            with sensor_path.open(newline="", encoding="utf-8") as f:
                sensors = list(csv.DictReader(f))
            with hyperspectral_path.open(encoding="utf-8") as f:
                hyperspectral = json.load(f)
            with dashboard_data_path.open(encoding="utf-8") as f:
                dashboard_data = json.load(f)

            self.assertEqual(len(shipments), 42)
            self.assertEqual(len(sensors), 8064)
            self.assertEqual(len(hyperspectral["shipments"]), 4)
            self.assertTrue(all(len(s["checkpoints"]) == 4 for s in hyperspectral["shipments"]))
            self.assertEqual(dashboard_data["kpis"]["total_shipments"], 42)
            self.assertEqual(dashboard_data["kpis"]["total_smes"], 6)
            self.assertTrue(dashboard_html_path.exists())


if __name__ == "__main__":
    unittest.main()
