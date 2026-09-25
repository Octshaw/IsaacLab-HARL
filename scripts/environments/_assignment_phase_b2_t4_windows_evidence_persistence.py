"""PW v1: immutable, fail-closed, test-side progress evidence on Windows.

This module has no Isaac, learner, or production import. It deliberately never
replaces an existing destination. A same-directory hard link publishes a fully
fsynced private temp file atomically with create-if-absent semantics.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping


SCHEMA = "b2_t4_pw_immutable_progress_v1"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")


class EvidencePersistenceError(RuntimeError):
    """An evidence operation did not reach the qualified durable state."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise EvidencePersistenceError("MALFORMED_PAYLOAD") from exc


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _identity(run_id: str, tx_id: int, stage: str, actor_or_critic: str,
              progress_sequence: int, planned_sequence_count: int) -> dict[str, Any]:
    if not isinstance(run_id, str) or not _ID.fullmatch(run_id):
        raise EvidencePersistenceError("INVALID_RUN_ID")
    if not isinstance(stage, str) or not _ID.fullmatch(stage):
        raise EvidencePersistenceError("INVALID_STAGE")
    if actor_or_critic not in ("actor", "critic"):
        raise EvidencePersistenceError("INVALID_SIDE")
    if type(tx_id) is not int or tx_id < 1:
        raise EvidencePersistenceError("INVALID_TX_ID")
    if (type(progress_sequence) is not int or type(planned_sequence_count) is not int
            or not 1 <= progress_sequence <= planned_sequence_count <= 100000):
        raise EvidencePersistenceError("INVALID_SEQUENCE")
    return {"run_id": run_id, "tx_id": tx_id, "stage": stage,
            "actor_or_critic": actor_or_critic,
            "progress_sequence": progress_sequence,
            "planned_sequence_count": planned_sequence_count}


def _directory(root: Path, run_id: str, tx_id: int) -> Path:
    return root / run_id / f"tx{tx_id:03d}"


def _path(root: Path, run_id: str, tx_id: int, side: str, sequence: int) -> Path:
    return _directory(root, run_id, tx_id) / f"{side}_progress_{sequence:05d}.json"


def read_record(path: Path, *, run_id: str, tx_id: int, side: str,
                sequence: int, planned_count: int) -> dict[str, Any]:
    """Validate a single final record; temp files are never authoritative."""
    try:
        raw = path.read_bytes()
        record = json.loads(raw)
    except (OSError, ValueError, UnicodeError) as exc:
        raise EvidencePersistenceError("RECORD_MISSING_OR_MALFORMED") from exc
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA:
        raise EvidencePersistenceError("RECORD_SCHEMA_MISMATCH")
    identity = record.get("identity")
    if not isinstance(identity, dict):
        raise EvidencePersistenceError("RECORD_IDENTITY_MISSING")
    expected = {"run_id": run_id, "tx_id": tx_id, "actor_or_critic": side,
                "progress_sequence": sequence,
                "planned_sequence_count": planned_count}
    if any(identity.get(k) != v for k, v in expected.items()):
        raise EvidencePersistenceError("RECORD_IDENTITY_MISMATCH")
    if not isinstance(identity.get("stage"), str) or not _ID.fullmatch(identity["stage"]):
        raise EvidencePersistenceError("RECORD_STAGE_INVALID")
    if record.get("payload_sha256") != _digest(record.get("payload")):
        raise EvidencePersistenceError("PAYLOAD_DIGEST_MISMATCH")
    if record.get("record_sha256") != _digest({k: v for k, v in record.items() if k != "record_sha256"}):
        raise EvidencePersistenceError("RECORD_DIGEST_MISMATCH")
    return record


def write_record(root: Path, *, run_id: str, tx_id: int, stage: str,
                 actor_or_critic: str, progress_sequence: int,
                 planned_sequence_count: int, payload: Mapping[str, Any]) -> Path:
    """Write one immutable record; no retry and no overwrite of prior evidence.

    On any failure, including temp cleanup or readback, raise. A failed attempt
    can leave a temp or final; recovery requires explicit external adjudication.
    """
    identity = _identity(run_id, tx_id, stage, actor_or_critic,
                         progress_sequence, planned_sequence_count)
    if not isinstance(payload, Mapping):
        raise EvidencePersistenceError("MALFORMED_PAYLOAD")
    payload = dict(payload)
    if payload.get("run_id") != run_id or payload.get("tx_id") != tx_id:
        raise EvidencePersistenceError("PAYLOAD_RUN_TX_MISMATCH")
    if payload.get("stage") != stage or payload.get("actor_or_critic") != actor_or_critic:
        raise EvidencePersistenceError("PAYLOAD_STAGE_SIDE_MISMATCH")
    final = _path(root, run_id, tx_id, actor_or_critic, progress_sequence)
    final.parent.mkdir(parents=True, exist_ok=True)
    if final.exists():
        raise EvidencePersistenceError("DUPLICATE_PROGRESS_IDENTITY")
    if any(final.parent.glob(final.name + ".tmp.*")):
        raise EvidencePersistenceError("STALE_TEMP_REQUIRES_REVIEW")
    if progress_sequence > 1:
        previous = _path(root, run_id, tx_id, actor_or_critic, progress_sequence - 1)
        read_record(previous, run_id=run_id, tx_id=tx_id, side=actor_or_critic,
                    sequence=progress_sequence - 1, planned_count=planned_sequence_count)
    record: dict[str, Any] = {"schema_version": SCHEMA, "identity": identity,
                              "payload": payload, "payload_sha256": _digest(payload)}
    record["record_sha256"] = _digest(record)
    encoded = _canonical(record) + b"\n"
    temporary = final.with_name(final.name + f".tmp.{os.getpid()}.{uuid.uuid4().hex}")
    with temporary.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    # Same-volume hard-link creation is atomic and fails if final exists.
    # Unlike os.replace, it never asks Windows to replace a held-open final.
    os.link(temporary, final)
    temporary.unlink()
    observed = read_record(final, run_id=run_id, tx_id=tx_id,
                           side=actor_or_critic, sequence=progress_sequence,
                           planned_count=planned_sequence_count)
    if observed != record or final.read_bytes() != encoded:
        raise EvidencePersistenceError("READBACK_MISMATCH")
    return final


def verify_transaction(root: Path, *, run_id: str, tx_id: int, side: str,
                       planned_count: int) -> tuple[dict[str, Any], ...]:
    _identity(run_id, tx_id, "VERIFY", side, 1, planned_count)
    directory = _directory(root, run_id, tx_id)
    if any(directory.glob("*.tmp.*")):
        raise EvidencePersistenceError("TEMP_RESIDUE_REQUIRES_REVIEW")
    expected = {_path(root, run_id, tx_id, side, n).name
                for n in range(1, planned_count + 1)}
    observed = {p.name for p in directory.glob(f"{side}_progress_*.json")}
    if observed != expected:
        raise EvidencePersistenceError("MISSING_OR_EXTRA_REQUIRED_RECORD")
    return tuple(read_record(_path(root, run_id, tx_id, side, n),
                             run_id=run_id, tx_id=tx_id, side=side,
                             sequence=n, planned_count=planned_count)
                 for n in range(1, planned_count + 1))
