"""Bounded CPU tests; no Win32 live sampling, App, torch, or simulator imports."""
import ast
import copy
import ctypes as ct
from ctypes import wintypes as wt
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts/environments/run_cr12_single_view_capture.py"
DIAG = ROOT / "scripts/environments/_cr12_gui_startup_diagnostics.py"
spec = importlib.util.spec_from_file_location("tested_gui_diagnostics", DIAG)
diag = importlib.util.module_from_spec(spec)
spec.loader.exec_module(diag)


class FakeReader:
    def session(self): return 7
    def startup(self): return {"flags": 0}
    def window_station(self): return {"name": "WinSta0", "visible_display_surfaces": True}
    def desktop(self): return {"name": "Default", "receiving_input": False}
    def monitors(self): return [{"monitor_rect": [-1920,0,0,1080], "work_rect": [-1920,0,0,1040], "primary": False}]
    def awareness(self): return {"awareness": 1, "name": "system_aware"}
    def system_dpi(self): return 144


PRIVATE = ROOT / "test-private/user.config.json"


def after_record():
    settings = {path: 0 for path in diag.SETTING_PATHS}
    settings.update({"/app/window/width": 1440, "/app/window/height": 900,
        "/app/window/scaleToMonitor": False, "/app/window/dpiScaleOverride": 1.,
        "/app/renderer/resolution/width": 1280, "/app/renderer/resolution/height": 720,
        "/app/vulkan": False, "/app/userConfigPath": str(PRIVATE)})
    window = SimpleNamespace(get_width=lambda:1440, get_height=lambda:900,
        get_dpi_scale=lambda:1., get_dpi_scale_override=lambda:1., is_maximized=lambda:False)
    launcher = SimpleNamespace(_sim_experience_file=ROOT/"apps/isaaclab.python.rendering.kit",
        _headless=False, _enable_cameras=True, _livestream=0, _xr=False)
    return diag.sample_after_app(launcher, settings=settings, window=window,
                                 context=diag.sample_windows_context(FakeReader()),
                                 graphics_api={"status":"OK", "actual_graphics_api":"D3D12"})


class ContextTests(unittest.TestCase):
    def test_startup_unused_zeros_and_120_columns_are_not_window_dimensions(self):
        info = diag.STARTUPINFOW()
        info.dwXCountChars = 120
        result = diag.decode_startup(info)
        self.assertEqual(result["console_buffer"]["raw"], [120,0])
        self.assertFalse(result["console_buffer"]["enabled"])
        self.assertFalse(result["window_size"]["enabled"])
        self.assertEqual(result["window_size"]["unit"], "pixels")

    def test_startup_flags_separate_size_character_and_show_units(self):
        info = diag.STARTUPINFOW()
        info.dwFlags = 0x100 | 1 | 2 | 8
        info.dwXSize, info.dwYSize = 1440, 900
        info.dwXCountChars, info.dwYCountChars, info.wShowWindow = 120,30,5
        result = diag.decode_startup(info)
        self.assertTrue(result["window_size"]["enabled"])
        self.assertFalse(result["position"]["enabled"])
        self.assertEqual(result["window_size"]["raw"], [1440,900])
        self.assertEqual(result["console_buffer"]["unit"], "character columns/rows")
        self.assertTrue(result["show_window"]["enabled"])
        self.assertTrue(result["standard_handles_requested"])

    def test_windows_abi_structs_preserve_64_bit_handles_and_signed_rectangles(self):
        self.assertEqual(ct.sizeof(diag.STARTUPINFOW), 104 if ct.sizeof(ct.c_void_p)==8 else 68)
        self.assertEqual(ct.sizeof(diag.MONITORINFO), 40)
        self.assertEqual(ct.sizeof(diag.USEROBJECTFLAGS), 12)
        self.assertEqual(wt.RECT(-1920,0,0,1080).left, -1920)

    def test_failed_field_has_error_none_value_and_other_fields_survive(self):
        reader = FakeReader()
        reader.session = mock.Mock(side_effect=OSError("query failed"))
        result = diag.sample_windows_context(reader)
        self.assertEqual(result["session_id"]["status"], "ERROR")
        self.assertIsNone(result["session_id"]["value"])
        self.assertEqual(result["system_dpi"]["value"], 144)

    def test_reader_construction_failure_does_not_fabricate_desktop_or_zero(self):
        with mock.patch.object(diag, "WindowsReader", side_effect=OSError("unavailable")):
            result = diag.sample_windows_context()
        self.assertEqual(result["monitors"]["status"], "ERROR")
        self.assertIsNone(result["monitors"]["value"])
        diag.validate_pre_context(result)

    def test_known_nonvisible_station_rejected(self):
        reader = FakeReader()
        reader.window_station = lambda: {"name":"service", "visible_display_surfaces":False}
        with self.assertRaises(diag.GuiStartupDiagnosticError):
            diag.validate_pre_context(diag.sample_windows_context(reader))

    def test_successful_empty_monitor_enumeration_rejected(self):
        reader=FakeReader()
        reader.monitors=lambda:[]
        with self.assertRaises(diag.GuiStartupDiagnosticError):
            diag.validate_pre_context(diag.sample_windows_context(reader))

    def test_session_zero_or_noninput_desktop_is_not_automatic_no_gui(self):
        reader=FakeReader()
        reader.session=lambda:0
        result=diag.sample_windows_context(reader)
        diag.validate_pre_context(result)
        self.assertEqual(result["session_id"]["value"], 0)

    def test_negative_monitor_coordinates_and_dpi_units_are_preserved(self):
        result=diag.sample_windows_context(FakeReader())
        self.assertEqual(result["monitors"]["value"][0]["work_rect"], [-1920,0,0,1040])
        self.assertIn("caller", result["system_dpi"]["unit"])
        self.assertIn("not renderer", result["monitors"]["unit"])


class PostTests(unittest.TestCase):
    def test_fixed_candidate_pass(self):
        record=after_record()
        diag.validate_post_context(record, PRIVATE)
        self.assertTrue(record["frozen_startup_checks_passed"])
        self.assertTrue(all(record["frozen_startup_checks"].values()))

    def test_120_by_zero_cannot_pass(self):
        record=after_record()
        record["window"]["width"]["value"]=120
        record["window"]["height"]["value"]=0
        with self.assertRaises(diag.GuiStartupDiagnosticError):
            diag.validate_post_context(record, PRIVATE)
        self.assertFalse(record["frozen_startup_checks_passed"])

    def test_dpi_settings_and_native_override_are_all_required(self):
        for field, value in (("scaleToMonitor",True), ("dpiScaleOverride",-1.), ("dpiScaleOverride",True)):
            record=after_record()
            record["settings"]["/app/window/"+field]["value"]=value
            with self.assertRaises(diag.GuiStartupDiagnosticError):
                diag.validate_post_context(record, PRIVATE)
        record=after_record()
        record["window"]["dpi_scale_override"]["value"]=-1.
        with self.assertRaises(diag.GuiStartupDiagnosticError):
            diag.validate_post_context(record, PRIVATE)

    def test_backend_experience_private_renderer_and_gui_conditions_rejected(self):
        cases=(
            lambda r:r["settings"]["/app/vulkan"].update(value=True),
            lambda r:r["launcher"].update(experience="wrong.kit"),
            lambda r:r["settings"]["/app/userConfigPath"].update(value="wrong.json"),
            lambda r:r["settings"]["/app/renderer/resolution/width"].update(value=640),
            lambda r:r["launcher"].update(headless=True))
        for mutation in cases:
            record=after_record()
            mutation(record)
            with self.assertRaises(diag.GuiStartupDiagnosticError):
                diag.validate_post_context(record, PRIVATE)

    def test_missing_native_readback_is_error_not_zero(self):
        record=after_record()
        record["window"]["height"]=diag.observation("get_height","window units",
                                                    mock.Mock(side_effect=RuntimeError("not available")))
        with self.assertRaises(diag.GuiStartupDiagnosticError):
            diag.validate_post_context(record, PRIVATE)
        self.assertIsNone(record["window"]["height"]["value"])

    def test_backend_setting_alone_cannot_replace_actual_log_api(self):
        for status, api in (("UNKNOWN","UNKNOWN"),("ERROR","UNKNOWN"),("OK","VULKAN")):
            record=after_record()
            record["graphics_api"]={"status":status,"actual_graphics_api":api}
            with self.assertRaises(diag.GuiStartupDiagnosticError):
                diag.validate_post_context(record, PRIVATE)

    def test_validation_failure_is_saved_before_propagation(self):
        record=after_record()
        record["window"]["height"]["value"]=0
        events=[]
        recorder=SimpleNamespace(result={}, save=lambda:events.append("save"),
                                  emit=lambda *a,**kw:events.append(("event",kw)))
        with mock.patch.object(diag,"sample_after_app",return_value=record):
            with self.assertRaises(diag.GuiStartupDiagnosticError):
                diag.record_gui_startup_diagnostics(SimpleNamespace(private_user_config=PRIVATE),
                                                     recorder,"after_app",launcher=object())
        self.assertFalse(recorder.result["gui_startup_diagnostics"]["after_app"]["frozen_startup_checks_passed"])
        self.assertEqual(events[0],"save")
        self.assertNotIn("observation",events[1][1])

    def test_window_and_settings_calls_are_readonly(self):
        tree=ast.parse(DIAG.read_text(encoding="utf-8"))
        calls=[ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n,ast.Call)]
        forbidden=("SetProcessDPIAware","SetProcessDpiAwareness","SetThreadDpiAwarenessContext",
                   "SetProcessWindowStation","SetThreadDesktop","SwitchDesktop","GetWindowText")
        self.assertFalse(any(any(x in call for x in forbidden) for call in calls))
        self.assertFalse(any(call != "record.update" and call.endswith((".update",".render",".resize",".focus",".move",".set_dpi_scale_override"))
                             for call in calls))
        # No installed package or Win32 initialization runs on importing the helper.
        self.assertFalse(any(isinstance(n,(ast.Import,ast.ImportFrom)) and
            any(a.name.startswith(("omni","carb","isaac")) for a in n.names) for n in tree.body))


class LogTests(unittest.TestCase):
    def test_same_log_dx12_and_d3d12_labels_match(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/"same.log"
            path.write_text("[Info] [Graphics API] DX12\n| Driver Version: x | Graphics API: D3D12\n",encoding="utf-8")
            record=diag.read_graphics_api(str(path),not_before=time.time(),log_root=name)
        self.assertEqual(record["status"],"OK")
        self.assertEqual(record["actual_graphics_api"],"D3D12")
        self.assertEqual(record["match_count"],2)

    def test_conflicting_or_missing_labels_are_unknown(self):
        for text in ("no API label", "[Graphics API] DX12\nGraphics API: Vulkan"):
            with tempfile.TemporaryDirectory() as name:
                path=Path(name)/"same.log"
                path.write_text(text,encoding="utf-8")
                record=diag.read_graphics_api(str(path),not_before=time.time(),log_root=name)
            self.assertEqual(record["status"],"UNKNOWN")
            self.assertEqual(record["actual_graphics_api"],"UNKNOWN")

    def test_outside_path_stale_missing_and_oversize_fail_without_fallback(self):
        with tempfile.TemporaryDirectory() as name:
            path=Path(name)/"same.log"
            path.write_text("[Graphics API] DX12",encoding="utf-8")
            cases=((str(path),time.time(),Path(name)/"other",100),
                   (str(path),time.time()+10,name,100),
                   (str(Path(name)/"missing.log"),time.time(),name,100),
                   (str(path),time.time(),name,2))
            for supplied, start, root, limit in cases:
                record=diag.read_graphics_api(supplied,not_before=start,log_root=root,max_bytes=limit)
                self.assertEqual(record["status"],"ERROR")
                self.assertEqual(record["actual_graphics_api"],"UNKNOWN")


class EntryBoundaryTests(unittest.TestCase):
    def test_default_control_flow_ast_equals_exact_pre_edit_baseline(self):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
        expected={"parse_args":"085c79fb845fd32fd2c10585c05c14e22ab1e3c13e7c9af6746794b2c31aabf3","main":"03b45fcb373310ce0a0588584f5a73cd08fac7256770a8372e08b1b164bc80b9"}
        class RemoveOptIn(ast.NodeTransformer):
            def visit_If(self,node):
                if ast.unparse(node.test)=="args.gui_startup_diagnostics":
                    return None
                return self.generic_visit(node)
            def visit_Expr(self,node):
                if isinstance(node.value,ast.Call) and node.value.args and isinstance(node.value.args[0],ast.Constant):
                    if node.value.args[0].value=="--gui-startup-diagnostics":
                        return None
                return self.generic_visit(node)
        for name in ("parse_args","main"):
            fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            fn=RemoveOptIn().visit(fn)
            digest=hashlib.sha256(ast.dump(fn,include_attributes=False).encode()).hexdigest()
            self.assertEqual(digest,expected[name],name)

    def test_opt_in_flag_is_store_true_and_false_by_default(self):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and n.args
               and isinstance(n.args[0],ast.Constant) and n.args[0].value=="--gui-startup-diagnostics"]
        self.assertEqual(len(calls),1)
        keywords={k.arg:ast.literal_eval(k.value) for k in calls[0].keywords}
        self.assertEqual(keywords["action"],"store_true")
        self.assertNotIn("default",keywords)

    def run_prefix(self,enabled,fail_post=False):
        tree=ast.parse(SOURCE.read_text(encoding="utf-8"))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="main")
        body=next(n for n in fn.body if isinstance(n,ast.Try)).body
        start=next(i for i,n in enumerate(body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and ast.unparse(n.value.func)=="recorder.emit" and n.value.args[0].value=="pre_app_cuda_begin")
        end=next(i for i,n in enumerate(body) if isinstance(n,ast.Import) and any(a.name=="carb" for a in n.names))
        events=[]
        def diagnostic(args,recorder,phase,**kwargs):
            events.append(phase)
            if fail_post and phase=="after_app": raise RuntimeError("post mismatch")
        namespace={"args":SimpleNamespace(gui_startup_diagnostics=enabled,device="cuda:0"),
            "recorder":SimpleNamespace(result={},emit=lambda name,**kw:events.append(name)),
            "_prepare_cuda_before_app":lambda unused:events.append("CUDA") or {},
            "phase_saved":lambda rec,phase:events.append(phase),
            "AppLauncher":lambda args:events.append("AppLauncher") or SimpleNamespace(app=object())}
        code=compile(ast.fix_missing_locations(ast.Module(body=copy.deepcopy(body[start:end]),type_ignores=[])),"actual-main-prefix","exec")
        with mock.patch.dict(sys.modules,{"_cr12_gui_startup_diagnostics":
                                         SimpleNamespace(record_gui_startup_diagnostics=diagnostic)}):
            try: exec(code,namespace)
            except RuntimeError:
                events.append("post_failure")
        return events

    def test_real_main_prefix_preserves_cuda_pre_post_order(self):
        events=self.run_prefix(True)
        self.assertEqual(events,["pre_app_cuda_begin","CUDA","pre_app_cuda_ready",
                                 "before_app","app_constructor_begin","AppLauncher","after_app"])

    def test_default_prefix_skips_diagnostics_and_post_failure_propagates(self):
        self.assertEqual(self.run_prefix(False),["pre_app_cuda_begin","CUDA","pre_app_cuda_ready",
                                                 "app_constructor_begin","AppLauncher"])
        self.assertEqual(self.run_prefix(True,True)[-2:],["after_app","post_failure"])


if __name__=="__main__":
    unittest.main(verbosity=2)

