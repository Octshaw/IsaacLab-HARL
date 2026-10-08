"""Bounded CPU tests for visual source identity and transform comparison."""

from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts/environments"))
from _cr12_visual_source import compare_mesh, load_visual_sources, read_obj, source_summary


class VisualSourceTests(unittest.TestCase):
    def setUp(self):
        self.points = np.array([[0., 0, 0], [1., 0, 0], [0., 1, 0], [0., 0, 1]])
        self.triangles = np.array([[0, 1, 2], [0, 3, 1], [0, 2, 3], [1, 3, 2]], dtype=np.int64)
        self.expected = {"points_body": self.points, "triangles": self.triangles}

    def compare(self, points, triangles):
        return compare_mesh(self.expected, points, np.full(len(triangles), 3, dtype=np.int64), triangles.reshape(-1))

    def test_vertex_reorder_and_triangle_reorder(self):
        order = np.array([2, 0, 3, 1]); inverse = np.argsort(order)
        result = self.compare(self.points[order], inverse[self.triangles[::-1]])
        self.assertTrue(result["points_match"])
        self.assertTrue(result["triangle_geometry_match"])
        self.assertTrue(result["winding_match"])

    def test_normal_splits_and_cyclic_order(self):
        points = self.points[self.triangles].reshape(-1, 3)
        triangles = np.arange(12).reshape(-1, 3)[:, [1, 2, 0]]
        result = self.compare(points, triangles)
        self.assertTrue(result["triangle_geometry_match"])
        self.assertTrue(result["winding_match"])
        self.assertEqual(result["observed_vertex_count"], 12)

    def test_reverse_winding_separately_reported(self):
        result = self.compare(self.points, self.triangles[:, ::-1])
        self.assertTrue(result["triangle_geometry_match"])
        self.assertFalse(result["winding_match"])

    def test_same_bounds_missing_surface_is_not_match(self):
        result = self.compare(self.points, self.triangles[:-1])
        self.assertEqual(result["bounds_max_error_m"], 0)
        self.assertFalse(result["triangle_geometry_match"])

    def test_near_float32_points_cross_grid_boundary(self):
        points = self.points.copy(); points[:, 0] += .3e-6
        self.assertTrue(self.compare(points, self.triangles)["triangle_geometry_match"])
        points[0, 0] += 2e-6
        self.assertFalse(self.compare(points, self.triangles)["points_match"])

    def test_invalid_points_indices_counts_fail(self):
        points = self.points.copy(); points[0, 0] = np.nan
        with self.assertRaises(ValueError):
            self.compare(points, self.triangles)
        for counts, indices in (([3], [0, 1, 5]), ([3], [0, 1]), ([2], [0, 1]), ([3], [0., 1., 2.])):
            with self.assertRaises(ValueError):
                compare_mesh(self.expected, self.points, counts, indices)

    def test_obj_negative_indices_and_explicit_fan(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"input.obj"
            path.write_text("v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\nf -4 -3 -2 -1\n", encoding="utf-8")
            source = read_obj(path)
            np.testing.assert_array_equal(source["triangles"], [[0, 1, 2], [0, 2, 3]])
            self.assertEqual(source["face_count"], 1)
            self.assertEqual(source["triangle_count"], 2)

    def test_actual_sources_preserve_single_scale_and_scanner_origin(self):
        path = REPO / "source/isaaclab_tasks/isaaclab_tasks/direct/scan_mobile_manipulator/assets/rokeaCR12/derived/fixed_lift0_v1/cr12_fixed_lift0.urdf"
        records = load_visual_sources(path)
        self.assertEqual(len(records), 20)
        self.assertEqual(sum(x["kind"] == "visual" for x in records), 10)
        self.assertEqual(sum(x["kind"] == "collision" for x in records), 10)
        scanner = next(x for x in records if x["name"] == "scanner_visual")
        raw = read_obj(scanner["filename"])["points"]
        c = np.sqrt(.5)
        expected = raw*.001 @ np.array([[-c, c, 0], [-c, -c, 0], [0, 0, 1]])
        np.testing.assert_allclose(scanner["points_body"], expected, atol=2e-16, rtol=0)
        summary = source_summary(scanner)
        self.assertNotIn("points_body", summary)
        self.assertNotIn("triangles", summary)
        self.assertEqual(scanner["body"], "link_6")
        elevate = next(x for x in records if x["name"] == "elevate_visual")
        raw = read_obj(elevate["filename"])["points"]
        np.testing.assert_allclose(elevate["points_body"], raw*.001+[0, 0, .314], atol=1e-15)


if __name__ == "__main__":
    unittest.main()
