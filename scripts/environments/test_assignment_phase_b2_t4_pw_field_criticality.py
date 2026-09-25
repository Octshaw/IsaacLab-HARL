"""Exhaustive field-level authority classification for retained tx130 progress."""

import json

from test_assignment_phase_b2_t4_pw_windows_evidence_persistence import artifact, dump


TOP_B = {
    "cumulative_actor_backward_count", "cumulative_actor_optimizer_step_count",
    "cumulative_critic_backward_count", "cumulative_critic_optimizer_step_count",
    "cumulative_live_valuenorm_update_count", "event_count", "events",
    "process_id", "run_identity", "source_config_identity_digest", "stage",
    "transaction_index", "update_id",
}
EVENT_B = {
    "backward_permit_id", "canonical_physical_rows", "critic_epoch", "critic_minibatch",
    "cumulative_actor_backward_count", "cumulative_actor_optimizer_step_count",
    "cumulative_critic_backward_count", "cumulative_critic_optimizer_step_count",
    "cumulative_live_valuenorm_update_count", "optimizer_step_permit_id",
    "process_id", "qualified_source_error", "receipt_complete", "run_identity",
    "schema_version", "source_config_identity_digest", "stage", "state_machine_stage",
    "transaction_index", "update_call_index", "update_id", "valuenorm_permit_id",
    "valuenorm_receipt_complete",
}


def main() -> None:
    source = json.loads(artifact("tx130_critic_progress.json.tmp").read_text(encoding="utf-8"))
    top = set(source)
    events = {key for event in source["events"] for key in event}
    assert top == TOP_B
    assert EVENT_B <= events
    rows = []
    for key in sorted(top):
        rows.append({"field": key, "class": "B_CRASH_FORENSICS_REQUIRED"})
    for key in sorted(events):
        rows.append({"field": f"events[].{key}",
                     "class": "B_CRASH_FORENSICS_REQUIRED" if key in EVENT_B
                              else "C_DIAGNOSTIC_CONTENT"})
    assert len(rows) == len(top) + len(events)
    dump("critic_progress_field_criticality.json", {
        "source": "preserved tx130 event-28 temp; read only",
        "transaction_critical_A_fields": [],
        "reason": "Production S10 plus transaction ledger are transaction authority; progress callback remains required fail-closed crash evidence, while numerical content does not itself qualify S10.",
        "top_level_fields": len(top), "unique_event_fields": len(events),
        "classified_fields": len(rows), "rows": rows,
        "contract_change": False,
    })


if __name__ == "__main__":
    main()
