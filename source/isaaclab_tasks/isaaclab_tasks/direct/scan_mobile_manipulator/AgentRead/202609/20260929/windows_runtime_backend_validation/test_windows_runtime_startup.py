"""Bounded standard-library tests: no viewer, training, or simulator imports."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock


REPO_ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "isaaclab.bat").is_file())
HELPER_PATH = REPO_ROOT / "scripts/environments/_windows_runtime_startup.py"


def load_helper():
    spec = importlib.util.spec_from_file_location("_windows_runtime_startup_under_test", HELPER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HELPER = load_helper()


class WindowsRuntimeArgumentsTest(unittest.TestCase):
    def prepare(self, args, argv=None, *, platform="win32", utf8=1):
        with mock.patch.object(HELPER.sys, "platform", platform), mock.patch.object(
            HELPER.sys, "flags", SimpleNamespace(utf8_mode=utf8)
        ):
            return HELPER.prepare_windows_runtime_args(args, original_argv=["entry.py"] if argv is None else argv)

    def test_empty_windows_request(self):
        args = SimpleNamespace(kit_args="", device="cuda:0", experience="custom.kit", headless=False)
        record = self.prepare(args)
        self.assertEqual(args.kit_args, "--/app/vulkan=false")
        self.assertEqual(record["source"], "windows_default")
        self.assertEqual(record["requested_backend"], "D3D12")
        self.assertEqual(record["original_kit_args"], "")
        self.assertEqual(vars(args), dict(kit_args="--/app/vulkan=false", device="cuda:0", experience="custom.kit", headless=False))
        json.dumps(record)

    def test_explicit_backend_requests_are_preserved(self):
        for value, backend in (("--vulkan", "Vulkan"), ("--/app/vulkan=true", "Vulkan"), ("--/app/vulkan=false", "D3D12")):
            with self.subTest(value=value):
                args = SimpleNamespace(kit_args=value)
                record = self.prepare(args, ["entry.py", "--kit_args=" + value])
                self.assertEqual(args.kit_args, value)
                self.assertEqual(record["source"], "explicit")
                self.assertEqual(record["requested_backend"], backend)

    def test_conflicts_fail_before_namespace_mutation(self):
        for value in ("--vulkan --/app/vulkan=false", "--/app/vulkan=false --/app/vulkan=true"):
            with self.subTest(value=value):
                args = SimpleNamespace(kit_args=value)
                with self.assertRaisesRegex(ValueError, "Conflicting"):
                    self.prepare(args)
                self.assertEqual(args.kit_args, value)

    def test_same_value_duplicates_and_repeated_helper_calls(self):
        for value in ("--vulkan --/app/vulkan=true --vulkan", "--/app/vulkan=false --/app/vulkan=false", ""):
            with self.subTest(value=value):
                args = SimpleNamespace(kit_args=value)
                first = self.prepare(args)
                second = self.prepare(args)
                self.assertEqual(first["final_kit_args"], second["final_kit_args"])
                self.assertEqual(args.kit_args, value or "--/app/vulkan=false")

    def test_unrelated_content_is_not_reformatted(self):
        for value in ('  --/custom/text="two words"\t--/rtx/foo=7  ', '--unknown=1', '\t'):
            with self.subTest(value=value):
                args = SimpleNamespace(kit_args=value)
                self.prepare(args)
                self.assertTrue(args.kit_args.startswith(value))
                self.assertEqual(args.kit_args[:len(value)], value)
                self.assertEqual(args.kit_args.split()[-1], "--/app/vulkan=false")
        value = ' --/custom/text="two words"\t--/app/vulkan=false  '
        args = SimpleNamespace(kit_args=value)
        self.prepare(args)
        self.assertEqual(args.kit_args, value)

    def test_ambiguous_backend_spellings_fail(self):
        for value in ('--/app/vulkan=False', '--/app/vulkan=0', '--/app/vulkan false', '--vulkan=false',
                      '--d3d12', '--no-vulkan', '"--/app/vulkan=false"', '--graphics-api=D3D12'):
            with self.subTest(value=value):
                args = SimpleNamespace(kit_args=value)
                with self.assertRaisesRegex(ValueError, "--kit_args"):
                    self.prepare(args)
                self.assertEqual(args.kit_args, value)

    def test_bare_backend_cannot_leak_into_hydra(self):
        for token in ('--vulkan', '--/app/vulkan=false', '--d3d12'):
            with self.subTest(token=token):
                args = SimpleNamespace(kit_args="")
                with self.assertRaisesRegex(ValueError, "Bare backend"):
                    self.prepare(args, ["entry.py", token])
                self.assertEqual(args.kit_args, "")

    def test_repeated_cli_kit_args_are_not_hidden_by_argparse(self):
        for argv in (["entry.py", "--kit_args=--vulkan", "--kit_args=--/app/vulkan=false"],
                     ["entry.py", "--kit_args", "--/app/vulkan=false", "--kit_args=--/app/vulkan=false"]):
            with self.subTest(argv=argv):
                args = SimpleNamespace(kit_args="--/app/vulkan=false")
                with self.assertRaisesRegex(ValueError, "Repeated --kit_args"):
                    self.prepare(args, argv)
                self.assertEqual(args.kit_args, "--/app/vulkan=false")

    def test_separate_kit_payload_is_not_a_bare_backend(self):
        args = SimpleNamespace(kit_args="--/app/vulkan=false --unrelated=x")
        argv = ["entry.py", "--kit_args", args.kit_args, "agent.seed=7"]
        record = self.prepare(args, argv)
        self.assertEqual(record["original_argv"], argv)
        self.assertEqual(record["source"], "explicit")

    def test_windows_requires_interpreter_utf8(self):
        args = SimpleNamespace(kit_args="")
        with self.assertRaisesRegex(RuntimeError, "conda.exe run.*-X utf8"):
            self.prepare(args, utf8=0)
        self.assertEqual(args.kit_args, "")

    def test_nonwindows_preserves_even_conflicting_requests(self):
        args = SimpleNamespace(kit_args="--vulkan --/app/vulkan=false --d3d12", device="cpu")
        before = vars(args).copy()
        record = self.prepare(args, ["entry.py", "--vulkan", "--kit_args=a", "--kit_args=b"], platform="linux", utf8=0)
        self.assertEqual(vars(args), before)
        self.assertEqual(record["source"], "non_windows_unchanged")
        self.assertIsNone(record["requested_backend"])

    def test_import_has_no_runtime_import_or_global_state_mutation(self):
        before_modules = set(sys.modules)
        before_path = list(sys.path)
        before_argv = list(sys.argv)
        original_import = __import__
        def guarded_import(name, *args, **kwargs):
            self.assertFalse(name.split(".")[0] in {"torch", "isaaclab", "isaaclab_tasks", "isaacsim", "omni", "carb", "pxr"}, name)
            return original_import(name, *args, **kwargs)
        with mock.patch("builtins.__import__", side_effect=guarded_import):
            load_helper()
        self.assertEqual(sys.path, before_path)
        self.assertEqual(sys.argv, before_argv)
        runtime_modules = {name for name in set(sys.modules) - before_modules if name.split(".")[0] in {"torch", "isaaclab", "isaacsim", "omni", "carb", "pxr"}}
        self.assertFalse(runtime_modules)


if __name__ == "__main__":
    unittest.main(verbosity=2)
