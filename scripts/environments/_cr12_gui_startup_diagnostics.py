"""Opt-in read-only observations around the real Windows GUI App constructor.

No simulator imports, Win32 calls or DPI changes occur on module import.
All values describe this process at sampling time, never a historical process.
"""
from __future__ import annotations

import ctypes as ct
from ctypes import wintypes as wt
import os
from pathlib import Path
import re
import sys
import time


class GuiStartupDiagnosticError(RuntimeError):
    category = "GUI_STARTUP_DIAGNOSTICS"

    def __init__(self, message, **details):
        super().__init__(message)
        self.details = details


class STARTUPINFOW(ct.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR), ("lpDesktop", wt.LPWSTR),
        ("lpTitle", wt.LPWSTR), ("dwX", wt.DWORD), ("dwY", wt.DWORD),
        ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
        ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
        ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
        ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
        ("lpReserved2", ct.POINTER(wt.BYTE)),
        ("hStdInput", wt.HANDLE), ("hStdOutput", wt.HANDLE), ("hStdError", wt.HANDLE)]


class USEROBJECTFLAGS(ct.Structure):
    _fields_ = [("fInherit", wt.BOOL), ("fReserved", wt.BOOL), ("dwFlags", wt.DWORD)]


class MONITORINFO(ct.Structure):
    _fields_ = [("cbSize", wt.DWORD), ("rcMonitor", wt.RECT),
                ("rcWork", wt.RECT), ("dwFlags", wt.DWORD)]


def observation(api, unit, callback):
    """Do not manufacture zeros or success when an observation fails."""
    try:
        return {"api": api, "unit": unit, "status": "OK", "value": callback(), "error": None}
    except Exception as exc:
        return {"api": api, "unit": unit, "status": "ERROR", "value": None,
                "error": {"type": type(exc).__name__, "message": str(exc),
                          "winerror": getattr(exc, "winerror", None)}}


class WindowsReader:
    def __init__(self):
        if sys.platform != "win32":
            raise RuntimeError("Windows process observation is unavailable on this platform")
        self.kernel = ct.WinDLL("kernel32", use_last_error=True)
        self.user = ct.WinDLL("user32", use_last_error=True)
        self._bind(self.kernel, "GetCurrentThreadId", [], wt.DWORD)
        self._bind(self.kernel, "GetStartupInfoW", [ct.POINTER(STARTUPINFOW)], None)
        self._bind(self.kernel, "ProcessIdToSessionId", [wt.DWORD, ct.POINTER(wt.DWORD)], wt.BOOL)
        self._bind(self.user, "GetProcessWindowStation", [], wt.HANDLE)
        self._bind(self.user, "GetThreadDesktop", [wt.DWORD], wt.HANDLE)
        self._bind(self.user, "GetUserObjectInformationW",
            [wt.HANDLE, ct.c_int, wt.LPVOID, wt.DWORD, ct.POINTER(wt.DWORD)], wt.BOOL)
        self.monitor_callback = ct.WINFUNCTYPE(wt.BOOL, wt.HMONITOR, wt.HDC, ct.POINTER(wt.RECT), wt.LPARAM)
        self._bind(self.user, "EnumDisplayMonitors", [wt.HDC, ct.POINTER(wt.RECT), self.monitor_callback, wt.LPARAM], wt.BOOL)
        self._bind(self.user, "GetMonitorInfoW", [wt.HMONITOR, ct.POINTER(MONITORINFO)], wt.BOOL)
        for name, arguments, result in (
            ("GetThreadDpiAwarenessContext", [], wt.HANDLE),
            ("GetAwarenessFromDpiAwarenessContext", [wt.HANDLE], ct.c_int),
            ("GetDpiForSystem", [], wt.UINT)):
            if hasattr(self.user, name):
                self._bind(self.user, name, arguments, result)

    @staticmethod
    def _bind(dll, name, arguments, result):
        function = getattr(dll, name)
        function.argtypes, function.restype = arguments, result

    @staticmethod
    def _require(value):
        if not value:
            raise ct.WinError(ct.get_last_error())
        return value

    def session(self):
        value = wt.DWORD()
        self._require(self.kernel.ProcessIdToSessionId(os.getpid(), ct.byref(value)))
        return int(value.value)

    def startup(self):
        info = STARTUPINFOW()
        info.cb = ct.sizeof(info)
        # VOID return: do not treat None as failure or inspect stale last-error.
        self.kernel.GetStartupInfoW(ct.byref(info))
        return decode_startup(info)

    def _object_info(self, handle, index, kind):
        value = kind()
        needed = wt.DWORD()
        self._require(self.user.GetUserObjectInformationW(handle, index, ct.byref(value),
                                                          ct.sizeof(value), ct.byref(needed)))
        return value

    def _object_name(self, handle):
        needed = wt.DWORD()
        ct.set_last_error(0)
        ok = self.user.GetUserObjectInformationW(handle, 2, None, 0, ct.byref(needed))
        code = ct.get_last_error()
        # The expected sizing call fails with ERROR_INSUFFICIENT_BUFFER (122).
        if not ok and code != 122:
            raise ct.WinError(code)
        if not 0 < needed.value <= 32768:
            raise ValueError("Invalid window-object name buffer size")
        buffer = ct.create_unicode_buffer((needed.value + ct.sizeof(ct.c_wchar)-1)//ct.sizeof(ct.c_wchar))
        self._require(self.user.GetUserObjectInformationW(handle, 2, buffer, ct.sizeof(buffer), ct.byref(needed)))
        return buffer.value

    def window_station(self):
        handle = self._require(self.user.GetProcessWindowStation())
        flags = self._object_info(handle, 1, USEROBJECTFLAGS)
        # This borrowed handle MUST NOT be closed; WSF_VISIBLE applies to stations.
        return {"name": self._object_name(handle), "flags": int(flags.dwFlags),
                "visible_display_surfaces": bool(flags.dwFlags & 1)}

    def desktop(self):
        thread = int(self.kernel.GetCurrentThreadId())
        handle = self._require(self.user.GetThreadDesktop(thread))
        # Borrowed handle; UOI_IO is a desktop bool, not WSF_VISIBLE.
        input_value = observation("GetUserObjectInformationW(UOI_IO)", "boolean",
                                  lambda: bool(self._object_info(handle, 6, wt.BOOL).value))
        return {"thread_id": thread, "name": self._object_name(handle), "receiving_input": input_value}

    def monitors(self):
        monitors, callback_errors = [], []
        def visit(handle, _dc, _rect, _data):
            try:
                info = MONITORINFO()
                info.cbSize = ct.sizeof(info)
                self._require(self.user.GetMonitorInfoW(handle, ct.byref(info)))
                def rectangle(value):
                    return [int(value.left), int(value.top), int(value.right), int(value.bottom)]
                monitors.append({"monitor_rect": rectangle(info.rcMonitor), "work_rect": rectangle(info.rcWork),
                                 "primary": bool(info.dwFlags & 1)})
                return 1
            except Exception as exc:
                callback_errors.append(exc)
                return 0
        callback = self.monitor_callback(visit)  # Strong reference for the complete synchronous call.
        result = self.user.EnumDisplayMonitors(None, None, callback, 0)
        if callback_errors:
            raise callback_errors[0]
        self._require(result)
        return monitors

    def awareness(self):
        context = self._require(self.user.GetThreadDpiAwarenessContext())
        awareness = int(self.user.GetAwarenessFromDpiAwarenessContext(context))
        if awareness not in (0, 1, 2):
            raise ValueError("Invalid DPI awareness context")
        return {"awareness": awareness,
                "name": ("unaware", "system_aware", "per_monitor_aware")[awareness],
                "context": hex(context)}

    def system_dpi(self):
        value = int(self.user.GetDpiForSystem())
        if value <= 0:
            raise ValueError("GetDpiForSystem returned a nonpositive DPI")
        return value


def decode_startup(info):
    flags = int(info.dwFlags)
    return {"flags": flags, "flags_hex": hex(flags), "desktop_requested": info.lpDesktop,
        "position": {"enabled": bool(flags & 4), "raw": [int(info.dwX), int(info.dwY)], "unit": "pixels"},
        "window_size": {"enabled": bool(flags & 2), "raw": [int(info.dwXSize), int(info.dwYSize)], "unit": "pixels"},
        "console_buffer": {"enabled": bool(flags & 8), "raw": [int(info.dwXCountChars), int(info.dwYCountChars)],
                           "unit": "character columns/rows"},
        "show_window": {"enabled": bool(flags & 1), "raw": int(info.wShowWindow), "unit": "SW_* enum"},
        "standard_handles_requested": bool(flags & 0x100),
        "standard_handles": [None if h is None else hex(h) for h in (info.hStdInput, info.hStdOutput, info.hStdError)],
        "limit": "Flags gate fields; GUI size/position only apply to the first eligible CW_USEDEFAULT window. No native-window size inferred."}


def sample_windows_context(reader=None):
    fields = (
        ("session_id", "ProcessIdToSessionId(current PID)", "session identifier", "session"),
        ("startup", "GetStartupInfoW", "structured field-specific units", "startup"),
        ("window_station", "GetProcessWindowStation + GetUserObjectInformationW", "name/flags", "window_station"),
        ("desktop", "GetThreadDesktop(current thread) + GetUserObjectInformationW", "name/boolean", "desktop"),
        ("monitors", "EnumDisplayMonitors + GetMonitorInfoW", "virtual-screen coordinates; caller DPI context; not renderer pixels", "monitors"),
        ("dpi_awareness", "GetThreadDpiAwarenessContext + GetAwarenessFromDpiAwarenessContext", "DPI_AWARENESS enum", "awareness"),
        ("system_dpi", "GetDpiForSystem", "DPI as observed by caller; not raw monitor DPI", "system_dpi"))
    result = {"pid": os.getpid(), "wall_time_s": time.time(), "monotonic_s": time.monotonic(),
              "scope": "actual target process, sample time only", "read_only": True}
    try:
        reader = WindowsReader() if reader is None else reader
    except Exception as exc:
        for key, api, unit, _method in fields:
            result[key] = {"api": api, "unit": unit, "status": "ERROR", "value": None,
                           "error": {"type": type(exc).__name__, "message": str(exc), "winerror": getattr(exc, "winerror", None)}}
        return result
    for key, api, unit, method in fields:
        result[key] = observation(api, unit, lambda method=method: getattr(reader, method)())
    return result


def validate_pre_context(record):
    station, monitors = record["window_station"], record["monitors"]
    reasons = []
    if station["status"] == "OK" and station["value"]["visible_display_surfaces"] is False:
        reasons.append("Current window station reports no visible display surfaces")
    if monitors["status"] == "OK" and not monitors["value"]:
        reasons.append("Successful monitor enumeration returned no monitors")
    # UOI_IO false, session zero/mismatch or an API error alone is NOT a proof of no GUI.
    if reasons:
        raise GuiStartupDiagnosticError("Known unsuitable GUI context", reasons=reasons)


SETTING_PATHS = (
    "/app/window/width", "/app/window/height", "/app/window/scaleToMonitor", "/app/window/dpiScaleOverride",
    "/persistent/app/window/width", "/persistent/app/window/height", "/persistent/app/window/maximized",
    "/app/renderer/resolution/width", "/app/renderer/resolution/height", "/app/vulkan", "/app/userConfigPath", "/log/file")


def read_graphics_api(log_path, *, not_before, log_root=None, max_bytes=8*1024*1024):
    """Read only the active /log/file; never discover a latest log or create an App."""
    record = {"api": "carb.settings /log/file + bounded same-file log read", "unit": "graphics API label",
              "status": "ERROR", "actual_graphics_api": "UNKNOWN", "path": log_path,
              "matched_lines": [], "error": None}
    try:
        if not isinstance(log_path, str) or not log_path or not isinstance(not_before, (int, float)):
            raise ValueError("Active log path and pre-App sample time are required")
        root = (Path(sys.prefix)/"Lib/site-packages/omni/logs/Kit/Isaac-Sim/4.5" if log_root is None else Path(log_root)).resolve()
        source = Path(log_path).resolve(strict=True)
        if not source.is_relative_to(root) or source.suffix.lower() != ".log":
            raise ValueError("Active log path lies outside this environment's Kit log directory")
        metadata = source.stat()
        if not not_before-2 <= metadata.st_mtime <= time.time()+2:
            raise ValueError("Active log timestamp is outside this attempt")
        if metadata.st_size > max_bytes:
            raise ValueError("Active log exceeds the bounded read budget")
        with source.open("rb") as stream:
            raw = stream.read(max_bytes+1)
        if len(raw) > max_bytes:
            raise ValueError("Active log grew beyond the bounded read budget")
        labels, count = set(), 0
        for number, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            match = re.search(r"(?:\[Graphics API\]\s*|Graphics API:\s*)([A-Za-z0-9_]+)", line)
            if match:
                label = match.group(1).upper()
                labels.add("D3D12" if label in ("DX12", "D3D12") else label)
                count += 1
                if len(record["matched_lines"]) < 8:
                    record["matched_lines"].append({"line": number, "text": line[:512]})
        actual = next(iter(labels)) if len(labels) == 1 else "UNKNOWN"
        record.update(status="OK" if actual != "UNKNOWN" else "UNKNOWN",
            actual_graphics_api=actual, path=str(source), bytes_read=len(raw),
            source_mtime_ns=metadata.st_mtime_ns, match_count=count)
    except (OSError, ValueError, TypeError) as exc:
        record["error"] = {"type": type(exc).__name__, "message": str(exc), "winerror": getattr(exc, "winerror", None)}
    return record


def sample_after_app(launcher, *, settings=None, window=None, context=None, graphics_api=None, not_before=None):
    if settings is None:
        import carb
        settings = carb.settings.get_settings()
    if window is None:
        import omni.appwindow
        window = omni.appwindow.get_default_app_window()
    def setting(path):
        value = settings.get(path)
        if value is None:
            raise LookupError("Setting is absent: " + path)
        return value
    result = {"context": sample_windows_context() if context is None else context,
        "settings_time": "after AppLauncher returned; does not reconstruct window-creation-time settings",
        "settings": {path: observation("carb.settings.get", "setting-specific", lambda p=path: setting(p))
                     for path in SETTING_PATHS},
        "launcher": {"experience": str(launcher._sim_experience_file), "headless": launcher._headless,
            "enable_cameras": launcher._enable_cameras, "livestream": launcher._livestream, "xr": launcher._xr},
        "window": {}}
    for field, method, unit in (
        ("width", "get_width", "IAppWindow reported window units; not claimed Win32 client/outer rect"),
        ("height", "get_height", "IAppWindow reported window units; not claimed Win32 client/outer rect"),
        ("dpi_scale", "get_dpi_scale", "scale factor"),
        ("dpi_scale_override", "get_dpi_scale_override", "scale factor"),
        ("maximized", "is_maximized", "boolean")):
        result["window"][field] = observation("omni.appwindow.IAppWindow."+method, unit,
                                               lambda method=method: getattr(window, method)())
    result["graphics_api"] = (read_graphics_api(result["settings"]["/log/file"]["value"], not_before=not_before)
                              if graphics_api is None else graphics_api)
    return result


def validate_post_context(record, private_path):
    def value(observed):
        return observed["value"] if observed["status"] == "OK" else None
    settings, window, launcher = record["settings"], record["window"], record["launcher"]
    expected_experience = Path(__file__).resolve().parents[2] / "apps/isaaclab.python.rendering.kit"
    def same_path(observed, expected):
        try:
            return isinstance(observed, str) and Path(observed).resolve() == Path(expected).resolve()
        except (OSError, ValueError, TypeError):
            return False
    def exact(observed, expected):
        return type(observed) is type(expected) and observed == expected
    checks = {
        "window_width_1440": exact(value(window["width"]), 1440),
        "window_height_900": exact(value(window["height"]), 900),
        "scale_to_monitor_false": value(settings["/app/window/scaleToMonitor"]) is False,
        "dpi_override_1": type(value(settings["/app/window/dpiScaleOverride"])) in (int, float)
            and value(settings["/app/window/dpiScaleOverride"]) == 1.0,
        "native_dpi_override_1": type(value(window["dpi_scale_override"])) in (int, float)
            and value(window["dpi_scale_override"]) == 1.0,
        "d3d12_requested_effective": value(settings["/app/vulkan"]) is False,
        "actual_d3d12_same_log": record["graphics_api"]["status"] == "OK"
            and record["graphics_api"]["actual_graphics_api"] == "D3D12",
        "rendering_experience": same_path(launcher["experience"], expected_experience),
        "private_config": same_path(value(settings["/app/userConfigPath"]), private_path),
        "gui_camera_mode": launcher["headless"] is False and launcher["enable_cameras"] is True
            and launcher["livestream"] == 0 and launcher["xr"] is False,
        "requested_window_1440x900": exact(value(settings["/app/window/width"]), 1440)
            and exact(value(settings["/app/window/height"]), 900),
        "renderer_1280x720": exact(value(settings["/app/renderer/resolution/width"]), 1280)
            and exact(value(settings["/app/renderer/resolution/height"]), 720),
    }
    record["frozen_startup_checks"] = checks
    record["frozen_startup_checks_passed"] = all(checks.values())
    if not all(checks.values()):
        raise GuiStartupDiagnosticError("Post-App startup facts differ from frozen diagnostic conditions", checks=checks)


def record_gui_startup_diagnostics(args, recorder, phase, *, launcher=None):
    if phase == "before_app":
        record = sample_windows_context()
        validator = lambda: validate_pre_context(record)
    elif phase == "after_app" and launcher is not None:
        before = recorder.result.get("gui_startup_diagnostics", {}).get("before_app", {})
        record = sample_after_app(launcher, not_before=before.get("wall_time_s"))
        validator = lambda: validate_post_context(record, args.private_user_config)
    else:
        raise ValueError("Unexpected GUI diagnostics phase")
    recorder.result.setdefault("gui_startup_diagnostics", {})[phase] = record
    def emit():
        recorder.emit("gui_startup_diagnostics", sampling_phase=phase,
                      target_pid=os.getpid(), post_pass=record.get("frozen_startup_checks_passed"),
                      validation_error=record.get("validation_error"),
                      details_field="gui_startup_diagnostics."+phase)
    try:
        validator()
    except Exception as exc:
        record["validation_error"] = {"type": type(exc).__name__, "message": str(exc),
                                      "details": getattr(exc, "details", {})}
        recorder.save()
        emit()
        raise
    recorder.save()
    emit()

