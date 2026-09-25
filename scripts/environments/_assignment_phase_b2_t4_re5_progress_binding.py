"""Test-side RE5 binding of the reviewed RE3 engine to immutable PW progress.

Only the generated test runner's one transaction function is rebound.  The
production adapter, learner and historical runner files are never edited.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Any

import _assignment_phase_b2_t4_windows_evidence_persistence as PW


PW_SHA256 = "e1c5dd249a845efd188fadd841202133d1aa363f162398930199837157f2e76b"
CRITIC_PER_TX = 41
ACTOR_FACTOR_PER_TX = 4


def _replace_once(source: str, old: str, new: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"STOP — B2-T4-RE5 PROGRESS-BINDING-SOURCE-DRIFT: {old[:100]!r} count={count}")
    return source.replace(old, new)


def _function_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    matches = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name]
    if len(matches) != 1:
        raise RuntimeError("STOP — B2-T4-RE5 PROGRESS-BINDING-FUNCTION-DRIFT")
    node = matches[0]
    lines = source.splitlines(keepends=True)
    return "".join(lines[node.lineno - 1:node.end_lineno])


def bind_progress(engine: dict[str, Any], generated_source: str) -> dict[str, Any]:
    """Replace exactly one test function in a fresh generated-engine namespace.

    The old fixed-target progress publication is absent from the replacement
    function.  Its S10 durable-artifact references resolve to the final PW
    records.  No second publication or mutable compatibility snapshot exists.
    """
    helper_path = Path(PW.__file__).resolve()
    actual_sha = hashlib.sha256(helper_path.read_bytes()).hexdigest()
    if actual_sha != PW_SHA256:
        raise RuntimeError("STOP — B2-T4-RE5 PW-HELPER-IDENTITY-MISMATCH")
    function = _function_source(generated_source, "_run_repeated_smoke")
    old_paths = '''        factor_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_actor_factor_progress"
        )
        critic_path = _artifact_path(
            artifact_prefix, f"tx{transaction_index}_critic_progress"
        )'''
    new_paths = '''        pw_root = Path(resources["_re5_pw_root"])
        pw_run_id = str(resources["_re5_run_id"])
        factor_path = _RE5_PW._path(
            pw_root, pw_run_id, transaction_index, "actor", 4
        )
        critic_path = _RE5_PW._path(
            pw_root, pw_run_id, transaction_index, "critic", 41
        )'''
    function = _replace_once(function, old_paths, new_paths)
    old_callback = '''        def persist_progress(
            path: Path,
            events: list[object],
            payload: Mapping[str, object],
        ) -> None:
            for key in progress_counts:
                if key in payload:
                    progress_counts[key] = int(payload[key])
            event = V2.normalize(
                {**tx_identity, **progress_counts, **payload}
            )
            events.append(event)
            _atomic_json(
                path,
                {
                    **tx_identity,
                    **progress_counts,
                    "stage": payload["stage"],
                    "events": events,
                    "event_count": len(events),
                },
            )

        def persist_factor(payload: Mapping[str, object]) -> None:
            persist_progress(factor_path, factor_events, payload)

        def persist_critic(payload: Mapping[str, object]) -> None:
            persist_progress(critic_path, critic_events, payload)'''
    new_callback = '''        def persist_progress(
            side: str,
            events: list[object],
            payload: Mapping[str, object],
            planned: int,
        ) -> None:
            for key in progress_counts:
                if key in payload:
                    progress_counts[key] = int(payload[key])
            event = V2.normalize(
                {**tx_identity, **progress_counts, **payload}
            )
            sequence = len(events) + 1
            if sequence > planned:
                raise RuntimeError("STOP — B2-T4-RE5 PROGRESS-SEQUENCE-OVERFLOW")
            stage = str(payload["stage"])
            record_payload = V2.normalize({
                **tx_identity,
                **progress_counts,
                "run_id": pw_run_id,
                "tx_id": transaction_index,
                "actor_or_critic": side,
                "stage": stage,
                "events": [*events, event],
                "event_count": sequence,
            })
            published = _RE5_PW.write_record(
                pw_root, run_id=pw_run_id, tx_id=transaction_index,
                stage=stage, actor_or_critic=side,
                progress_sequence=sequence, planned_sequence_count=planned,
                payload=record_payload,
            )
            expected = factor_path if side == "actor" else critic_path
            if sequence == planned and published != expected:
                raise RuntimeError("STOP — B2-T4-RE5 PROGRESS-FINAL-PATH-MISMATCH")
            events.append(event)

        def persist_factor(payload: Mapping[str, object]) -> None:
            persist_progress("actor", factor_events, payload, 4)

        def persist_critic(payload: Mapping[str, object]) -> None:
            persist_progress("critic", critic_events, payload, 41)'''
    function = _replace_once(function, old_callback, new_callback)
    # Full-set verification precedes test-side S10 artifact publication.  The
    # production S10 inside execute_real_isaac_single_transaction_v1 remains
    # the unchanged learner authority.
    old_close = '''        pre_mutation_payload = json.loads(pre_mutation_path.read_text(encoding="utf-8"))
        transaction_record = {'''
    new_close = '''        actor_pw_records = _RE5_PW.verify_transaction(
            pw_root, run_id=pw_run_id, tx_id=transaction_index,
            side="actor", planned_count=4,
        )
        critic_pw_records = _RE5_PW.verify_transaction(
            pw_root, run_id=pw_run_id, tx_id=transaction_index,
            side="critic", planned_count=41,
        )
        if len(actor_pw_records) != 4 or len(critic_pw_records) != 41:
            raise RuntimeError("STOP — B2-T4-RE5 PW-TRANSACTION-COUNT-MISMATCH")
        pre_mutation_payload = json.loads(pre_mutation_path.read_text(encoding="utf-8"))
        transaction_record = {'''
    function = _replace_once(function, old_close, new_close)
    function = _replace_once(
        function,
        '        resources["completed_transactions"] = transaction_index\n',
        '''        resources["completed_transactions"] = transaction_index
        resources["_re5_after_tx"](pw_root, pw_run_id, transaction_index)
        if transaction_index == 130:
            resources["_re5_tx130_comparison"](pw_root, pw_run_id)
''',
    )
    if "persist_progress(factor_path" in function or "persist_progress(critic_path" in function:
        raise RuntimeError("STOP — B2-T4-RE5 OLD-PROGRESS-CALL-REMAINS")
    if '"actor_factor_progress"' not in function or '"critic_progress"' not in function:
        raise RuntimeError("STOP — B2-T4-RE5 S10-PROGRESS-REFERENCE-DRIFT")
    if engine.get("_run_repeated_smoke") is None:
        raise RuntimeError("STOP — B2-T4-RE5 ENGINE-FUNCTION-MISSING")
    engine["_RE5_PW"] = PW
    engine["_re5_bound_progress_function_source"] = function
    code = compile(function, str(Path(__file__).resolve()), "exec")
    exec(code, engine)
    result = {
        "schema_version": "b2_t4_re5_progress_binding_v1",
        "source_function_sha256": hashlib.sha256(_function_source(generated_source, "_run_repeated_smoke").encode()).hexdigest(),
        "bound_function_sha256": hashlib.sha256(function.encode()).hexdigest(),
        "pw_helper_sha256": actual_sha,
        "critic_progress_per_tx": CRITIC_PER_TX,
        "critic_progress_160": CRITIC_PER_TX * 160,
        "expected_actor_factor_progress_per_tx": ACTOR_FACTOR_PER_TX,
        "expected_actor_factor_progress_160": ACTOR_FACTOR_PER_TX * 160,
        "old_mutable_progress_publication_reachable": False,
        "duplicate_old_new_publication": False,
        "s10_references_final_pw_records": True,
        "pass": True,
    }
    return result
