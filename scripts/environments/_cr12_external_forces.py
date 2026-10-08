"""One explicit, transient PhysxSceneAPI override; no runtime imports or stepping.

Records are composed USD/schema observations. They are not native solver flag
getters or measurements of the internal external-force application schedule.
"""

from __future__ import annotations

import copy


PROPERTY_NAME = "physxScene:enableExternalForcesEveryIteration"
EXPECTED_VALUES = {"inherit": None, "on": True, "off": False}
EVIDENCE_LEVEL = "composed USD/schema only; no native scene flag getter"


class SceneExternalForcesError(RuntimeError):
    """Configuration failure with the available observations preserved."""

    def __init__(self, message, record):
        super().__init__(message)
        self.category = "external_forces_setup_config"
        self.record = record


def add_external_forces_arguments(parser):
    parser.add_argument("--external-forces-every-iteration", choices=tuple(EXPECTED_VALUES), default="inherit",
                        help="Explicit transient scene flag; inherit leaves its original value unchanged.")


def external_forces_source(argv):
    flag = "--external-forces-every-iteration"
    return "explicit_cli" if any(item == flag or item.startswith(flag + "=") for item in argv) else "default_inherit"


def _fail(record, message, *, phase):
    record["status"] = "SETUP_CONFIG_FAILED"
    record["failures"].append({"phase": phase, "message": str(message)})
    raise SceneExternalForcesError(str(message), record)


def _attribute(stage, scene_path, physx_schema, usd_physics):
    prim = stage.GetPrimAtPath(scene_path)
    if not prim or not prim.IsValid() or not prim.IsA(usd_physics.Scene):
        raise ValueError(f"Expected existing PhysicsScene at {scene_path}")
    if not prim.HasAPI(physx_schema.PhysxSceneAPI):
        raise ValueError(f"PhysicsScene has no applied PhysxSceneAPI at {scene_path}")
    api = physx_schema.PhysxSceneAPI(prim)
    getter = getattr(api, "GetEnableExternalForcesEveryIterationAttr", None)
    if getter is None:
        raise ValueError("Installed PhysxSceneAPI does not expose the requested field")
    attr = getter()
    if not attr or not attr.IsValid() or str(attr.GetTypeName()) != "bool":
        raise ValueError("External-forces attribute is missing or is not a valid bool")
    if str(attr.GetPath()) != f"{scene_path}.{PROPERTY_NAME}":
        raise ValueError("External-forces attribute path does not match the requested scene")
    return attr


def _snapshot(attr, default_time):
    resolved = attr.Get()
    if not isinstance(resolved, bool):
        raise ValueError("External-forces attribute did not resolve to a bool")
    stack = []
    for spec in attr.GetPropertyStack(default_time):
        authored = bool(spec.HasInfo("default"))
        value = spec.default if authored else None
        if authored and not isinstance(value, bool):
            raise ValueError("External-forces property stack contains a non-bool default opinion")
        stack.append({"layer": str(spec.layer.identifier), "path": str(spec.path),
                      "authored_default": authored, "default": value})
    return {"property": str(attr.GetPath()), "resolved": resolved,
            "authored": bool(attr.HasAuthoredValueOpinion()), "property_stack": stack,
            "evidence_level": EVIDENCE_LEVEL}


def _check_expected(record, snapshot, phase):
    inherit = record["mode"] == "inherit"
    expected = record["before"]["resolved"] if inherit else EXPECTED_VALUES[record["mode"]]
    expected_authored = record["before"]["authored"] if inherit else True
    matches = snapshot["resolved"] is expected and snapshot["authored"] is expected_authored
    if inherit:
        matches = matches and snapshot["property_stack"] == record["before"]["property_stack"]
    else:
        stack = snapshot["property_stack"]
        matches = (matches and bool(stack) and stack[0]["layer"] == record["session_layer"]
                   and stack[0]["authored_default"] and stack[0]["default"] is expected)
    snapshot["matches_expected"] = bool(matches)
    if not matches:
        _fail(record, f"{phase}: expected {expected} / authored={expected_authored}"
              + (" with the original inherited opinion unchanged" if inherit
                 else " with the explicit opinion in the session layer"), phase=phase)


def read_scene_external_forces(stage, record, phase, physx_schema, usd_physics, default_time):
    """Append a phase-labelled schema readback and retain the last readable value.

    A mismatch is sticky. Explicit on/off expectation comes only from mode;
    inherit preserves the original pre-setting snapshot. No Set/Save/Export.
    """
    try:
        snapshot = _snapshot(_attribute(stage, record["scene_path"], physx_schema, usd_physics), default_time)
        snapshot["phase"] = str(phase)
        record["readbacks"].append(snapshot)
        record["last_readback"] = snapshot
        _check_expected(record, snapshot, phase)
        return snapshot
    except SceneExternalForcesError:
        raise
    except Exception as exc:
        _fail(record, f"{type(exc).__name__}: {exc}", phase=phase)


def apply_scene_external_forces(stage, scene_path, mode, source, timing, physx_schema, usd_physics, default_time):
    """Apply on/off only to the unsaved session layer before first initialization.

    timing records caller-observed guards, not a native proof synthesized here.
    Required: before_first_physics_initialization=True, physics_initialized=False,
    physics_running=False, timeline_playing=False, reset_started=False. Optional physics_attached must
    also be False if available. The caller records the concrete callsite/evidence.
    inherit does not set a value, apply a schema, or switch the edit target.
    default_time is supplied as Usd.TimeCode.Default() by the runtime caller.
    """
    record = {"mode": mode, "source": source, "scene_path": str(scene_path), "property": PROPERTY_NAME,
              "expected": EXPECTED_VALUES.get(mode), "expected_initial": {"resolved": False, "authored": False},
              "timing": copy.deepcopy(timing), "before": None, "after": None, "session_layer": None,
              "edit_target_restored": None, "authored_by_helper": False, "readbacks": [], "last_readback": None,
              "initial_matches_false_baseline": None,
              "status": "PENDING", "failures": [], "evidence_level": EVIDENCE_LEVEL}
    try:
        if mode not in EXPECTED_VALUES or not isinstance(source, str) or not source:
            raise ValueError("Expected inherit/on/off and a nonempty option source")
        guards = {"before_first_physics_initialization": True, "physics_initialized": False,
                  "physics_running": False, "timeline_playing": False, "reset_started": False}
        if not isinstance(timing, dict) or any(timing.get(key) is not value for key, value in guards.items()):
            raise ValueError("Scene option must be selected before first physics initialization/attach/play/reset")
        if "physics_attached" in timing and timing["physics_attached"] is not False:
            raise ValueError("Scene option cannot be selected after physics attachment")
        attr = _attribute(stage, str(scene_path), physx_schema, usd_physics)
        record["before"] = _snapshot(attr, default_time)
        record["initial_matches_false_baseline"] = (record["before"]["resolved"] is False
                                                    and record["before"]["authored"] is False)
        if mode != "inherit" and not record["initial_matches_false_baseline"]:
            _fail(record, "Initial scene flag differs from the retained false/unauthed baseline; compare sources before running",
                  phase="before_apply")
        session = stage.GetSessionLayer()
        record["session_layer"] = None if session is None else str(session.identifier)
        if mode != "inherit":
            if session is None or not bool(session.anonymous):
                raise ValueError("An anonymous session layer is required; no file-backed layer will be authored")
            previous = stage.GetEditTarget()
            try:
                stage.SetEditTarget(session)
                if stage.GetEditTarget().GetLayer() != session:
                    raise ValueError("Session edit target did not become active; refusing to author into another layer")
                if attr.Set(EXPECTED_VALUES[mode]) is not True:
                    raise ValueError("External-forces attribute Set did not succeed")
                record["authored_by_helper"] = True
            finally:
                stage.SetEditTarget(previous)
                record["edit_target_restored"] = stage.GetEditTarget() == previous
            if not record["edit_target_restored"]:
                raise ValueError("Original edit target was not restored")
        else:
            record["expected"] = record["before"]["resolved"]
            record["edit_target_restored"] = True
        record["after"] = read_scene_external_forces(stage, record, "after_apply", physx_schema, usd_physics, default_time)
        record["status"] = "CONFIGURED"
        return record
    except SceneExternalForcesError:
        raise
    except Exception as exc:
        _fail(record, f"{type(exc).__name__}: {exc}", phase="apply")
