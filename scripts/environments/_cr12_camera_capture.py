"""One owned camera product; no stepping, timeline control or runtime imports at import.

The installed Camera updates its buffer first. A narrow subclass then copies the
same frame, checking the product NEW_FRAME payload against ReferenceTime. An
independent subscription remains alive while Camera.pause() drains acquisition.
CPU tests use injected interfaces; only the real application proves rendering.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import hashlib
import math
from pathlib import Path
import re
import struct
import time
import zlib


class CameraCaptureError(RuntimeError):
    def __init__(self, category, message, **details):
        super().__init__(message)
        self.category, self.details = category, details


def event_evidence(event, parser, product_path=None):
    """Local syntheticdata sensors.py documents parsed product + rational time.

    Its NEW_FRAME listener also exposes payload.swh_frame_number. Do not replace
    a missing source identity with our own event counter.
    """
    parsed = parser(event.payload["product_path_handle"], event.payload["results"])
    if product_path is not None and str(parsed[0]) != product_path:
        return None
    numerator, denominator = int(parsed[1]), int(parsed[2])
    if denominator <= 0 or numerator < 0:
        raise CameraCaptureError("camera_event_identity", "Invalid rendered simulation rational time")
    source_frame = event.payload["swh_frame_number"]
    if isinstance(source_frame, bool) or int(source_frame) != source_frame or source_frame <= 0:
        raise CameraCaptureError("camera_event_identity", "Missing/invalid event SWH frame identity")
    return {"render_product_path": str(parsed[0]), "source_frame": int(source_frame),
            "source_time_numerator": numerator, "source_time_denominator": denominator,
            "source_time": float(Fraction(numerator, denominator))}


def _source_fraction(evidence):
    return Fraction(evidence["source_time_numerator"], evidence["source_time_denominator"])


def validate_frame(frame, event, resolution, *, baseline_frame, on_source_time, on_copy=None):
    """Return an independent RGBA copy after actual event/buffer identity checks."""
    import numpy as np
    number, rendered_time = frame.get("rendering_frame"), frame.get("rendering_time")
    if number == 0:
        return None  # Reject before touching initialize's possibly CUDA zero buffer.
    rgba_value = frame.get("rgba")
    if rgba_value is None:
        return None
    if hasattr(rgba_value, "detach"):
        rgba_value = rgba_value.detach().clone().cpu().numpy()
    rgba = np.asarray(rgba_value)
    if rgba.size == 0:
        return None
    width, height = resolution
    if rgba.shape != (height, width, 4) or rgba.dtype != np.uint8:
        raise CameraCaptureError("camera_frame_invalid", "Expected a real HxWx4 uint8 RGBA buffer",
                                 actual_shape=list(rgba.shape), actual_dtype=str(rgba.dtype))
    rgba = np.array(rgba, dtype=np.uint8, order="C", copy=True)
    if on_copy is not None:
        on_copy(rgba)
    if number != event["source_frame"]:
        raise CameraCaptureError("camera_frame_mismatch", "Camera buffer and product event have different source frames")
    if number <= baseline_frame or _source_fraction(event) < on_source_time:
        return None  # An identifiable old/in-flight frame is not this request.
    if rendered_time is None or not math.isfinite(float(rendered_time)):
        raise CameraCaptureError("camera_frame_invalid", "Camera rendering time is missing or non-finite")
    return rgba


def _camera_subclass(base_class):
    class PostUpdateCamera(base_class):
        def _data_acquisition_callback(self, event):
            owner = self._cr12_capture_owner
            try:
                evidence = event_evidence(event, self._sdg_interface.parse_rendered_simulation_event,
                                          self.get_render_product_path())
                # Do not read another product's buffer or relabel its event.
                if evidence is None:
                    return
                if not owner._claim_camera_event(evidence):
                    return
                super()._data_acquisition_callback(event)
                owner._after_camera_update(evidence, self)
            except Exception as exc:
                owner._record_error("camera_callback", exc)
    return PostUpdateCamera


class OwnedCameraCapture:
    """One device; legacy one/two requests or explicit bounded integration reuse."""

    @classmethod
    def prepare(cls, camera_prim_path, resolution=(640, 480), context_provider=None, *, runtime=None,
                max_requests=1, integration_mode=False, product_name='CR12SingleViewCapture',
                camera_name='cr12_single_view_camera', observer_name='cr12.camera.independent_completion'):
        """Create force_new product and immediately OFF, before any caller update.

        runtime is a small CPU-test injection seam. Production uses only local
        installed Camera/Replicator/USD APIs; no second render product is made.
        """
        if type(integration_mode) is not bool:
            raise ValueError("integration_mode must be an explicit bool")
        if type(max_requests) is not int or max_requests not in ((2, 3) if integration_mode else (1, 2)):
            raise ValueError("Legacy supports one/two requests; explicit integration supports two/three")
        if any(not isinstance(name, str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_.]*', name)
               for name in (product_name, camera_name, observer_name)):
            raise ValueError('Camera resource names must be nonempty unambiguous identifiers')
        named_resources = (product_name, camera_name, observer_name) != (
            'CR12SingleViewCapture', 'cr12_single_view_camera', 'cr12.camera.independent_completion')
        if runtime is None:
            from types import SimpleNamespace
            import omni.replicator.core as rep
            import omni.usd
            from isaacsim.sensors.camera import Camera
            runtime = SimpleNamespace(Camera=Camera, create_product=rep.create.render_product,
                context=omni.usd.get_context(), new_frame_type=int(omni.usd.StageRenderingEventType.NEW_FRAME))
            if named_resources:
                import carb
                from omni.replicator.core.scripts.utils import viewport_manager
                prefix = (carb.settings.get_settings().get_as_string(viewport_manager.RP_PREFIX_SETTING)
                          or viewport_manager.LEGACY_RP_PREFIX)
                stage = runtime.context.get_stage()
                runtime.product_path_for_name = lambda name: f'/Render/{prefix}{name}'
                runtime.prim_exists = lambda path: stage.GetPrimAtPath(path).IsValid()
                runtime.product_camera_targets = lambda path: [str(value) for value in
                    stage.GetPrimAtPath(path).GetRelationship('camera').GetTargets()]
        expected_product_path = None
        if named_resources:
            # Replicator otherwise silently appends a suffix for an occupied name.
            expected_product_path = str(runtime.product_path_for_name(product_name))
            if runtime.prim_exists(expected_product_path):
                raise CameraCaptureError('camera_resource_collision', 'Requested render product already exists',
                                         render_product_path=expected_product_path)
        self = cls()
        self.camera_prim_path, self.resolution = str(camera_prim_path), tuple(resolution)
        self._resource_names = dict(product_name=product_name, camera_name=camera_name, observer_name=observer_name)
        self._expected_product_path = expected_product_path
        self._context_provider = context_provider or (lambda: {})
        self._runtime, self._product, self._camera, self._observer = runtime, None, None, None
        self.product_path = None
        self._initialized = False
        self._request = self._snapshot = self._off = None
        self._raw_snapshot = None
        self._fresh_identity_validated = self._fsm_acquired_accepted = False
        self._integration_mode, self._request_retired = integration_mode, False
        self._retired_snapshots, self._retirements = [], []
        self._retirement_receipt = None
        self._on_source_time = None
        self._baseline_frame = 0
        self._accepting, self._released = False, False
        self._errors, self._switches = [], []
        self._close_errors = []
        self._product_events, self._global_events, self._camera_updates = 0, 0, 0
        self._last_event = None
        self._initialization_events = 0
        self._discarded_old = 0
        self._rejections = {}
        self._last_rejection = None
        self._release_result = None
        self._max_requests = max_requests
        self._requests, self._request_history, self._accepted_frames = [], [], set()
        self._event_history = {}
        self._camera_event_history = {}
        self._unique_product_events = self._duplicate_events = self._late_events = 0
        self._after_confirmed_off_events = 0
        self._highest_source_frame = 0
        self._last_unique_event = self._last_classification = None
        self._device_ids = self._annotator_ids = None
        self._lifecycle = dict(prepare_calls=1, product_create_calls=0, camera_create_calls=0,
            observer_create_calls=0, initialize_calls=0, begin_calls=0, off_requests=0,
            request_resume_calls=0, request_pause_calls=0, off_confirmed_count=0,
            release_calls=0, release_effective_count=0)
        self._lifecycle.update(retire_calls=0, retire_effective_count=0)
        try:
            self._lifecycle["product_create_calls"] += 1
            self._product = runtime.create_product(self.camera_prim_path, resolution=self.resolution,
                force_new=True, name=product_name)
            self.product_path = str(self._product.path)
            self._set_updates(False, "created_immediate_off")
            self._verify_product_binding()
            camera_class = _camera_subclass(runtime.Camera)
            self._lifecycle["camera_create_calls"] += 1
            self._camera = camera_class(prim_path=self.camera_prim_path, name=camera_name,
                frequency=-1, resolution=self.resolution, render_product_path=self.product_path)
            self._camera._cr12_capture_owner = self
            if (self._camera.get_render_product_path() != self.product_path
                    or self._camera._render_product is not None or self._camera.get_frequency() != -1):
                raise CameraCaptureError("camera_product_ownership", "Camera did not bind our sole product in every-frame mode")
            self._observer = runtime.context.get_rendering_event_stream().create_subscription_to_pop_by_type(
                runtime.new_frame_type, self._observe_event, name=observer_name, order=2000)
            self._lifecycle["observer_create_calls"] += 1
            self._device_ids = self._current_device_ids()
            self._set_updates(False, "prepared_off")
            return self
        except Exception:
            # No scene stepping has occurred here; preserve the original error.
            try:
                self.release()
            except Exception:
                pass
            raise

    @property
    def camera(self):
        return self._camera

    def _current_device_ids(self):
        return {"camera_id": id(self._camera), "product_id": id(self._product),
            "hydra_texture_id": id(self._product.hydra_texture),
            "observer_id": id(self._observer), "render_product_path": self.product_path,
            "camera_prim_path": self.camera_prim_path,
            "semantics": "process-local Python object identities; not persistent/native handle addresses"}

    def _verify_product_binding(self):
        if self._expected_product_path is not None:
            targets = self._runtime.product_camera_targets(self.product_path)
            if self.product_path != self._expected_product_path or targets != [self.camera_prim_path]:
                raise CameraCaptureError('camera_product_ownership', 'Named product path/camera relationship differs',
                    expected_product=self._expected_product_path, actual_product=self.product_path,
                    expected_camera=self.camera_prim_path, actual_camera_targets=targets)

    def render_evidence(self):
        """Small owned-product readback; no render, update, clock advance or RGBA copy."""
        self.device_identity()
        return {'product_path': self.product_path, 'updates_enabled': self.read_updates_enabled(),
            'own_unique_completions': self._unique_product_events, 'camera_updates': self._camera_updates,
            'request_ids': None if self._request is None else self._request_ids(),
            'snapshot_source': None if self._snapshot is None else copy.deepcopy(self._snapshot['metadata']),
            'observer_active': self._observer is not None}

    def _request_ids(self):
        keys = ('goal_id', 'attempt_id', 'capture_id', 'env_id', 'robot_id', 'agent_id', 'task_id',
                'claim_id', 'claim_token', 'episode_generation', 'run_instance_id')
        return {key: copy.deepcopy(self._request[key]) for key in keys if key in self._request}

    def device_identity(self):
        """Validate live ownership; after release return the recorded owned identities."""
        if not self._released:
            if self._current_device_ids() != self._device_ids:
                error = CameraCaptureError("camera_device_identity", "Owned device/product/observer was replaced")
                self._record_error("camera_device_identity", error, close_invalid=True)
                raise error
            if self._annotator_ids is not None:
                current = [id(self._camera._rgb_annotator), id(self._camera._fabric_time_annotator)]
                if current != self._annotator_ids:
                    error = CameraCaptureError("camera_device_identity", "Owned annotators were replaced")
                    self._record_error("camera_device_identity", error, close_invalid=True)
                    raise error
        return {**copy.deepcopy(self._device_ids),
            "rgb_annotator_id": None if self._annotator_ids is None else self._annotator_ids[0],
            "reference_time_annotator_id": None if self._annotator_ids is None else self._annotator_ids[1]}

    def _record_error(self, category, exc, *, close_invalid=False):
        item = {"category": getattr(exc, "category", category), "type": type(exc).__name__, "message": str(exc)}
        if not self._errors:
            self._errors.append(item)
        if close_invalid and not self._close_errors:
            self._close_errors.append(item)
        if close_invalid and self._off is not None:
            self._off["confirmed"] = False

    def _check_error(self):
        if self._errors:
            raise CameraCaptureError("camera_capture_backend", "Camera backend recorded a failure", errors=copy.deepcopy(self._errors))

    def _updates_enabled(self):
        return bool(self._product.hydra_texture.updates_enabled)

    def read_updates_enabled(self):
        """Actual switch readback remains available after acquisition failures."""
        return self._updates_enabled()

    def _set_updates(self, enabled, phase):
        self._product.hydra_texture.updates_enabled = bool(enabled)
        actual = self._updates_enabled()
        item = {"phase": phase, "requested": bool(enabled), "actual": actual,
                "updates_enabled": actual, "render_product_path": self.product_path,
                "wall_time": time.time(), "product": self.product_path}
        self._switches.append(item)
        if actual != bool(enabled):
            raise CameraCaptureError("camera_render_switch", "Hydra updates_enabled readback differs", **item)
        return item

    def _rational_now(self):
        values = self._camera._sdg_interface.get_rational_time_of_simulation(self._runtime.context.get_stage_id(), 0)
        if int(values[1]) <= 0:
            raise CameraCaptureError("camera_event_identity", "Invalid simulation source-time boundary")
        return Fraction(int(values[0]), int(values[1]))

    def initialize_off(self, physics_sim_view=None):
        if self._initialized or self._released or self._lifecycle["initialize_calls"]:
            raise CameraCaptureError("camera_initialization", "Camera may initialize only once")
        self.assert_off("before_camera_initialize")
        self._lifecycle["initialize_calls"] += 1
        self._camera.initialize(physics_sim_view=physics_sim_view)
        self._camera.pause()
        self._set_updates(False, "initialized_off")
        self._verify_product_binding()
        if self._camera.get_render_product_path() != self.product_path or self._camera._render_product is not None:
            raise CameraCaptureError("camera_product_ownership", "Camera.initialize created/rebound a second product")
        self._initialized = True
        self._annotator_ids = [id(self._camera._rgb_annotator), id(self._camera._fabric_time_annotator)]
        self._initialization_events = self._product_events
        return self.assert_off("ready_off")

    def assert_off(self, phase):
        self._check_error()
        self.device_identity()
        enabled = self._updates_enabled()
        if enabled:
            raise CameraCaptureError("camera_render_switch", "Product must remain OFF", phase=phase)
        return {"phase": str(phase), "updates_enabled": False, "render_product_path": self.product_path,
                "product_event_count": self._product_events, "camera_initialized": self._initialized}

    def begin_capture(self, ids, boundary):
        self._check_error()
        if not self._initialized or self._released or len(self._requests) >= self._max_requests:
            raise CameraCaptureError("camera_capture_state", "Request limit, initialization or released state forbids capture")
        if self._off is not None and self._request is None:
            raise CameraCaptureError("camera_capture_state", "A closed unstarted backend cannot begin a request")
        if self._request is not None:
            if self._integration_mode and not self._request_retired:
                raise CameraCaptureError("camera_capture_state", "Integration requires receipt-acknowledged retirement")
            if self._off is None or not self._off["confirmed"] or (not self._integration_mode and self._snapshot is None):
                raise CameraCaptureError("camera_capture_state", "Previous data and independent OFF confirmation are required")
        if not all(isinstance(ids.get(key), str) and ids[key] for key in ("goal_id", "attempt_id", "capture_id")):
            raise CameraCaptureError("camera_capture_identity", "All request identities are required")
        if self._requests and (ids["attempt_id"] != self._requests[0]["attempt_id"]
                or any(ids["goal_id"] == old["goal_id"] or ids["capture_id"] == old["capture_id"] for old in self._requests)):
            raise CameraCaptureError("camera_capture_identity", "Sequential requests need new goal/capture IDs in the same attempt")
        self.assert_off("arrived_hold_off")
        if not self._camera.is_paused():
            raise CameraCaptureError("camera_receiver", "Receiver must be paused before beginning a request")
        # Only request-local slots change. Prior snapshots and global identities
        # remain independent; no reset/reinitialize/detach occurs here.
        baseline = max(int(self._camera.get_current_frame(clone=True).get("rendering_frame", 0)),
                       self._highest_source_frame)
        on_source_time = self._rational_now()
        self._snapshot, self._off = None, None
        self._raw_snapshot = None
        self._fresh_identity_validated = self._fsm_acquired_accepted = False
        self._request_retired, self._retirement_receipt = False, None
        self._request = copy.deepcopy(ids)
        self._baseline_frame, self._on_source_time = baseline, on_source_time
        self._requests.append({key: ids[key] for key in ("goal_id", "attempt_id", "capture_id")})
        self._lifecycle["begin_calls"] += 1
        self._request.update({"boundary": copy.deepcopy(boundary), "product_event_baseline": self._product_events,
            "unique_product_event_baseline": self._unique_product_events,
            "source_frame_baseline": self._baseline_frame,
            "on_source_time_numerator": self._on_source_time.numerator,
            "on_source_time_denominator": self._on_source_time.denominator})
        self._accepting = True
        try:
            self._lifecycle["request_resume_calls"] += 1
            self._camera.resume()
            if self._camera.is_paused() or self._camera.get_frequency() != -1:
                raise CameraCaptureError("camera_receiver", "Every-frame receiver is not ready")
            self._request["receiver_subscription_id"] = id(self._camera._acquisition_callback)
            return self._set_updates(True, "capture_on")
        except Exception as exc:
            self._record_error("camera_begin", exc)
            raise

    def _after_camera_update(self, evidence, camera):
        self._camera_updates += 1
        if not self._accepting or self._snapshot is not None or self._errors:
            return
        if not self._updates_enabled():
            raise CameraCaptureError("camera_render_switch", "Receiver accepted work outside the ON window")
        reason = None
        if evidence["source_frame"] in self._accepted_frames:
            reason = "previously_accepted_source_frame"
        elif _source_fraction(evidence) < self._on_source_time:
            reason = "source_time_before_on"
        elif self._max_requests > 1 and _source_fraction(evidence) == self._on_source_time:
            reason = "source_time_not_after_on"
        elif evidence["source_frame"] <= self._baseline_frame:
            reason = "source_frame_not_new"
        if reason is not None:
            self._discarded_old += 1
            self._reject_frame(reason, evidence)
            return
        # Called immediately after Camera's own update, within this exact callback.
        frame = camera.get_current_frame(clone=True)
        def retain_copy(rgba):
            rgba.setflags(write=False)
            self._raw_snapshot = {"rgba": rgba, "metadata": {
                **self._request_ids(),
                **evidence, "rendering_frame": frame.get("rendering_frame"), "fresh": False}}
        rgba = validate_frame(frame, evidence, self.resolution, baseline_frame=self._baseline_frame,
                              on_source_time=self._on_source_time, on_copy=retain_copy)
        if rgba is None:
            self._reject_frame("buffer_not_ready_or_initial_zero", evidence)
            return
        rgba.setflags(write=False)
        metadata = self._request_ids()
        metadata.update({**evidence, "camera_prim_path": self.camera_prim_path,
            "rendering_frame": int(frame["rendering_frame"]), "rendering_time": float(frame["rendering_time"]),
            "received_wall_time": time.time(), "received_context": copy.deepcopy(self._context_provider()),
            "pose_time_semantics": "receive-time cached state; not an exact exposure pose",
            "resolution": list(self.resolution), "channels": "RGBA", "dtype": "uint8", "fresh": True,
            "freshness_basis": ("owned product NEW_FRAME after ON; event SWH equals Camera ReferenceTime frame; "
                + ("source time strictly after ON" if self._max_requests > 1 else "source time at/after ON")
                + "; post-super clone"),
            "data_received_count": 1})
        self._snapshot = {"rgba": rgba, "metadata": metadata}
        self._fresh_identity_validated = True
        self._accepted_frames.add(evidence["source_frame"])

    def _claim_camera_event(self, evidence):
        """Receiver duplicate check is independent of observer callback order."""
        frame, source = evidence["source_frame"], _source_fraction(evidence)
        if frame in self._camera_event_history:
            if self._camera_event_history[frame] != source:
                raise CameraCaptureError("camera_event_identity", "Repeated receiver frame changed its rational time")
            self._reject_frame("duplicate_receiver_notification", evidence)
            return False
        self._camera_event_history[frame] = source
        return True

    def _reject_frame(self, reason, evidence):
        self._rejections[reason] = self._rejections.get(reason, 0) + 1
        self._last_rejection = {"reason": reason, **evidence}

    def _observe_event(self, event):
        try:
            self._global_events += 1
            evidence = event_evidence(event, self._camera._sdg_interface.parse_rendered_simulation_event, self.product_path)
            if evidence is None:
                return
            self._product_events += 1
            self._last_event = {**evidence, "received_wall_time": time.time()}
            frame, source = evidence["source_frame"], _source_fraction(evidence)
            if frame in self._event_history:
                if source != self._event_history[frame]:
                    raise CameraCaptureError("camera_event_identity", "Repeated source frame changed its rational time")
                self._duplicate_events += 1
                self._last_classification = {"kind": "duplicate_notification", **self._last_event}
                return
            self._event_history[frame] = source
            self._unique_product_events += 1
            late = frame < self._highest_source_frame or (self._on_source_time is not None and source < self._on_source_time)
            self._late_events += int(late)
            self._highest_source_frame = max(self._highest_source_frame, frame)
            self._last_unique_event = copy.deepcopy(self._last_event)
            self._last_classification = {"kind": "late_source_notification" if late else "new_source_completion", **self._last_event}
            if self._off is not None:
                self._off["in_flight_event_count"] += 1
                self._off["last_in_flight_event"] = copy.deepcopy(self._last_event)
                if self._off["confirmed"]:
                    self._after_confirmed_off_events += 1
                    raise CameraCaptureError("camera_output_after_confirmed_off", "New product completion after confirmed OFF", **evidence)
                if _source_fraction(evidence) > self._off_source_time:
                    raise CameraCaptureError("camera_output_after_off", "Product completed a source frame newer than the OFF boundary", **evidence)
        except Exception as exc:
            self._record_error("camera_completion_observer", exc, close_invalid=True)

    def poll_snapshot(self):
        self._check_error()
        # The result owns a copy independent of the Camera. It is never overwritten.
        return self._snapshot

    def peek_retained_snapshot(self):
        """Inspect existing Python copies even after errors; no native/API reads.

        A copied buffer may precede failed source validation. Only the explicit
        fresh flag permits acquisition; FSM acceptance is a separate fact.
        """
        snapshot = self._snapshot if self._snapshot is not None else self._raw_snapshot
        return {"snapshot": None if snapshot is None else {
                    "rgba": snapshot["rgba"], "metadata": copy.deepcopy(snapshot["metadata"])},
                "raw_copy_present": snapshot is not None,
                "fresh_identity_validated": self._fresh_identity_validated,
                "fsm_acquired_accepted": self._fsm_acquired_accepted,
                "errors": copy.deepcopy(self._errors)}

    def _require_request_ids(self, ids):
        if not isinstance(ids, dict) or self._request is None or any(
                ids.get(key) != self._request[key] for key in ("goal_id", "attempt_id", "capture_id")):
            raise CameraCaptureError("camera_capture_identity", "Operation must refer to the retained request")

    def mark_snapshot_accepted(self, ids):
        """Caller records a successful FSM accept; this does not create data."""
        self._require_request_ids(ids)
        self._check_error()
        if self._snapshot is None or not self._fresh_identity_validated or self._request_retired:
            raise CameraCaptureError("camera_capture_state", "No validated active snapshot exists to accept")
        self._fsm_acquired_accepted = True

    def eligible_to_retire(self, ids, *, hold_verified):
        """Recheck live OFF/device health; never clear slots or advance clocks.

        The caller supplies the latest actual hold check. A fresh product event
        without an independently retained/accepted buffer is not a no-data proof.
        """
        self._require_request_ids(ids)
        if not self._integration_mode or self._released:
            raise CameraCaptureError("camera_retirement", "Retirement requires a live integration backend")
        self._check_error()
        try:
            self.device_identity()
            close = None if self._off is None else self.observe_close(render_opportunity=False)
        except Exception as exc:
            self._record_error("camera_handoff_health", exc, close_invalid=True)
            raise
        fresh_events = sum(frame > self._baseline_frame and source > self._on_source_time
                           for frame, source in self._event_history.items())
        retained = self.peek_retained_snapshot()
        reasons = []
        if hold_verified is not True:
            reasons.append("latest_actual_hold_not_verified")
        if close is None or close.get("confirmed") is not True:
            reasons.append("independent_off_not_confirmed")
        if retained["raw_copy_present"] and not (retained["fresh_identity_validated"] and retained["fsm_acquired_accepted"]):
            reasons.append("retained_data_not_validated_and_accepted")
        if not retained["raw_copy_present"] and fresh_events:
            reasons.append("fresh_product_output_without_retained_data")
        return {"eligible": not reasons, "reasons": reasons,
                "request": {key: self._request[key] for key in ("goal_id", "attempt_id", "capture_id")},
                "has_data": retained["raw_copy_present"], "fresh_product_event_count": fresh_events,
                "hold_verified": hold_verified is True, "resource_healthy": True,
                "off": close, "already_retired": self._request_retired}

    def retire_request(self, ids, *, authority_receipt, receipt_validator, hold_verified):
        """Retire local reuse eligibility only after the caller validates a receipt.

        The task adapter owns authority semantics. Its validator must verify the
        exact receipt/request association and return True. This backend neither
        manufactures receipts nor forgets prior data, OFF evidence or errors.
        """
        self._lifecycle["retire_calls"] += 1
        eligibility = self.eligible_to_retire(ids, hold_verified=hold_verified)
        if not eligibility["eligible"]:
            raise CameraCaptureError("camera_retirement", "Request is not eligible to retire", evidence=eligibility)
        if authority_receipt is None or not callable(receipt_validator):
            raise CameraCaptureError("camera_retirement_receipt", "A verified authority receipt is required")
        if receipt_validator(authority_receipt, dict(eligibility["request"])) is not True:
            raise CameraCaptureError("camera_retirement_receipt", "Authority receipt/request association was rejected")
        eligibility = self.eligible_to_retire(ids, hold_verified=hold_verified)
        if not eligibility["eligible"]:
            raise CameraCaptureError("camera_retirement", "Handoff conditions changed during receipt validation")
        if self._request_retired:
            if authority_receipt is not self._retirement_receipt:
                raise CameraCaptureError("camera_retirement_receipt", "Retirement cannot change its acknowledged receipt")
            return copy.deepcopy(self._retirements[-1])
        record = {"request": dict(eligibility["request"]), "has_data": eligibility["has_data"],
                  "receipt_type": type(authority_receipt).__name__, "receipt_object_id": id(authority_receipt),
                  "authority_receipt_validated": True, "eligibility": eligibility}
        self._retired_snapshots.append(self._snapshot if self._snapshot is not None else self._raw_snapshot)
        self._retirements.append(copy.deepcopy(record))
        self._retirement_receipt, self._request_retired = authority_receipt, True
        self._lifecycle["retire_effective_count"] += 1
        return copy.deepcopy(record)

    def request_off(self, boundary=None):
        if self._off is not None:
            return copy.deepcopy(self._off)
        if self._released:
            raise CameraCaptureError("camera_close_state", "Cannot request OFF after final resource release")
        self._accepting = False
        self._lifecycle["off_requests"] += 1
        switch = self._set_updates(False, "capture_off")
        self._lifecycle["request_pause_calls"] += 1
        self._camera.pause()
        self._off_source_time = self._rational_now()
        self._off = {"requested": True, "confirmed": False, "updates_enabled": switch["actual"],
            "boundary": copy.deepcopy(boundary), "requested_wall_time": switch["wall_time"],
            "off_source_time_numerator": self._off_source_time.numerator,
            "off_source_time_denominator": self._off_source_time.denominator,
            "opportunity_count": 0, "quiet_opportunities": 0,
            "product_event_count": self._product_events, "in_flight_event_count": 0,
            "last_in_flight_event": None, "independent_observer_active": self._observer is not None}
        self._close_event_baseline = self._unique_product_events
        return copy.deepcopy(self._off)

    def observe_close(self, render_opportunity=True):
        if self._off is None:
            raise CameraCaptureError("camera_close_state", "OFF must be requested before observing drain")
        enabled = self._updates_enabled()
        self._off["updates_enabled"] = enabled
        if enabled or self._observer is None:
            raise CameraCaptureError("camera_close_state", "OFF readback or independent observer was lost")
        if render_opportunity:
            self._off["opportunity_count"] += 1
            self._off["quiet_opportunities"] = (self._off["quiet_opportunities"] + 1
                if self._unique_product_events == self._close_event_baseline else 0)
            self._close_event_baseline = self._unique_product_events
        self._off["product_event_count"] = self._product_events
        self._off["global_event_count"] = self._global_events
        self._off["confirmed"] = bool(not self._close_errors and self._off["opportunity_count"] >= 30
                                     and self._off["quiet_opportunities"] >= 6)
        if self._off["confirmed"]:
            self._off.setdefault("confirmed_wall_time", time.time())
            if self._request is not None and not any(row["request"]["capture_id"] == self._request["capture_id"] for row in self._request_history):
                self._lifecycle["off_confirmed_count"] += 1
                self._request_history.append({"request": copy.deepcopy(self._request),
                    "acquired": self._snapshot is not None,
                    "snapshot_metadata": None if self._snapshot is None else copy.deepcopy(self._snapshot["metadata"]),
                    "off": copy.deepcopy(self._off), "device_identity": self.device_identity()})
        return copy.deepcopy(self._off)

    def summary(self):
        # Diagnostics must survive an identity failure instead of hiding the
        # already recorded primary exception with another readback exception.
        try:
            identity = self.device_identity()
            identity_valid = True
        except CameraCaptureError:
            identity, identity_valid = copy.deepcopy(self._device_ids), False
        return {"camera_prim_path": self.camera_prim_path, "render_product_path": self.product_path,
            "resource_names": dict(self._resource_names), "expected_product_path": self._expected_product_path,
            "resolution": list(self.resolution), "initialized": self._initialized,
            "acquired": self._snapshot is not None, "request": copy.deepcopy(self._request),
            "switches": copy.deepcopy(self._switches), "errors": copy.deepcopy(self._errors),
            "close_evidence_errors": copy.deepcopy(self._close_errors),
            "initialization_product_events": self._initialization_events,
            "product_event_count": self._product_events, "global_event_count": self._global_events,
            "camera_update_count": self._camera_updates, "discarded_old_frames": self._discarded_old,
            "max_requests": self._max_requests, "request_count": len(self._requests), "released": self._released,
            "integration_mode": self._integration_mode, "request_retired": self._request_retired,
            "retirements": copy.deepcopy(self._retirements),
            "retained_snapshot_state": {key: value for key, value in self.peek_retained_snapshot().items()
                                        if key not in ("snapshot", "errors")},
            "request_history": copy.deepcopy(self._request_history), "lifecycle": dict(self._lifecycle),
            "device_identity": identity, "device_identity_valid": identity_valid,
            "annotator_object_ids": copy.deepcopy(self._annotator_ids),
            "unique_product_event_count": self._unique_product_events,
            "event_classification": {"notification_count": self._product_events,
                "unique_completions": self._unique_product_events, "duplicate_notifications": self._duplicate_events,
                "late_source_notifications": self._late_events, "new_completions_after_confirmed_off": self._after_confirmed_off_events,
                "highest_source_frame": self._highest_source_frame, "last": copy.deepcopy(self._last_classification)},
            "frame_rejections": dict(self._rejections), "last_frame_rejection": copy.deepcopy(self._last_rejection),
            "last_product_event": copy.deepcopy(self._last_event), "off": copy.deepcopy(self._off),
            "release": copy.deepcopy(self._release_result)}

    def release(self):
        """Release only owned subscriptions/annotators/product; never step/stop."""
        self._lifecycle["release_calls"] += 1
        if self._released:
            return copy.deepcopy(self._release_result)
        errors = []
        def attempt(label, callback):
            try:
                callback()
            except Exception as exc:
                errors.append({"action": label, "type": type(exc).__name__, "message": str(exc)})
        self._accepting = False
        if self._product is not None:
            attempt("product_off", lambda: self._set_updates(False, "release_off"))
        if self._camera is not None:
            attempt("camera_pause", self._camera.pause)
            self._camera._stage_open_callback = None
            self._camera._timer_reset_callback = None
            for name in ("_rgb_annotator", "_fabric_time_annotator"):
                annotator = getattr(self._camera, name, None)
                if annotator is not None:
                    attempt("detach_" + name, lambda a=annotator: a.detach([self.product_path]))
        self._observer = None
        if self._product is not None:
            attempt("destroy_owned_product", self._product.destroy)
        self._released = True
        self._lifecycle["release_effective_count"] += 1
        self._release_result = {"complete": not errors, "errors": errors,
                                "render_product_path": self.product_path, "camera_prim_preserved": True}
        if errors:
            raise CameraCaptureError("camera_release", "Owned resource release encountered errors", errors=errors)
        return copy.deepcopy(self._release_result)


def verify_camera_isolation(captures):
    """Require disjoint device resources; source frame/time need not be disjoint."""
    captures = tuple(captures)
    if len(captures) != 2 or captures[0] is captures[1]:
        raise CameraCaptureError('camera_device_identity', 'Exactly two independent captures are required')
    identities = [item.device_identity() for item in captures]
    keys = ('camera_id', 'product_id', 'hydra_texture_id', 'observer_id', 'rgb_annotator_id',
            'reference_time_annotator_id', 'render_product_path', 'camera_prim_path')
    for key in keys:
        if any(item[key] is None for item in identities) or identities[0][key] == identities[1][key]:
            raise CameraCaptureError('camera_device_identity', 'Camera resources alias or are uninitialized', field=key)
    for owner in captures:
        owner._verify_product_binding()
    paths = [item.product_path for item in captures]
    if paths[0].startswith(paths[1]) or paths[1].startswith(paths[0]):
        raise CameraCaptureError('camera_device_identity', 'Owned product namespace prefixes overlap')
    if captures[0].camera._current_frame is captures[1].camera._current_frame:
        raise CameraCaptureError('camera_device_identity', 'Camera frame dictionaries alias')
    return {'pass': True, 'identities': identities, 'distinct_fields': list(keys),
            'frame_dictionaries_distinct': True, 'source_frame_uniqueness_scope': 'per product'}


def save_rgba_png(path, rgba):
    """Save the owned raw RGBA snapshot without image edits or overwriting files."""
    import numpy as np
    data = np.asarray(rgba)
    if data.ndim != 3 or data.shape[2] != 4 or data.dtype != np.uint8 or min(data.shape[:2]) <= 0:
        raise ValueError("Expected nonempty HxWx4 uint8 RGBA")
    height, width, _ = data.shape
    def chunk(tag, payload):
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff)
    rows = b"".join(b"\0" + row.tobytes() for row in data)
    output = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
              + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))
    path = Path(path)
    with path.open("xb") as handle:
        handle.write(output)
    return {"path": str(path.resolve()), "bytes": len(output), "sha256": hashlib.sha256(output).hexdigest(),
            "width": width, "height": height, "channels": 4, "channel_name": "RGBA", "saved_wall_time": time.time()}
