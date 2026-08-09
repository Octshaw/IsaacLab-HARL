"""Pure Phase A4a-R V3 contract and V2/V3 semantic-dispatch tests.

The V2 fixtures below are compressed copies of canonical UTF-8 bytes captured
from the unchanged direct V2 API before this suite imported either new A4a
module.  This suite performs no checkpoint/file/tensor I/O and never imports
Isaac, HARL runtime, a policy, a trainer, or an environment.
"""

from __future__ import annotations

import argparse
import ast
import base64
import builtins
import contextlib
import copy
from dataclasses import fields, is_dataclass
import hashlib
import importlib.util
import io
import json
import logging
import math
import os
from pathlib import Path
import random
import re
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable, Mapping
from unittest import mock
import zlib


REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_SOURCE = (
    REPO_ROOT
    / "source"
    / "isaaclab_tasks"
    / "isaaclab_tasks"
    / "direct"
    / "scan_mobile_manipulator"
)
PACKAGE = "isaaclab_tasks.direct.scan_mobile_manipulator"
V2_KEY = f"{PACKAGE}.assignment_checkpoint_contract"
V3_KEY = f"{PACKAGE}.assignment_checkpoint_contract_v3"
DISPATCH_KEY = f"{PACKAGE}.assignment_checkpoint_semantic_dispatch"
AGGREGATE_KEY = f"{PACKAGE}.assignment_event_profile_schema_contract"

MODULE_PATHS = {
    V2_KEY: SCAN_SOURCE / "assignment_checkpoint_contract.py",
    V3_KEY: SCAN_SOURCE / "assignment_checkpoint_contract_v3.py",
    DISPATCH_KEY: SCAN_SOURCE / "assignment_checkpoint_semantic_dispatch.py",
}

TOP_LEVEL_KEYS = (
    "manifest_format_version",
    "manifest_kind",
    "identity",
    "scale",
    "actor_schema",
    "shared_schema",
    "action_contract",
    "transition_contract",
    "event_tick_contract",
    "local_candidate_contract",
    "cost_path_contract",
    "decision_valid_training_contract",
    "sequential_factor_contract",
    "component_contract",
    "reward_contract",
    "failure_termination_contract",
    "diagnostics_contract",
    "policy_sequence_contract",
    "model_structure",
    "training_contract",
    "runtime_readiness_contract",
)
SECTION_NAMES = TOP_LEVEL_KEYS[2:]
SECTION_CLASSES = (
    "CheckpointV3IdentitySection",
    "CheckpointV3ScaleSection",
    "CheckpointV3ActorSchemaSection",
    "CheckpointV3SharedSchemaSection",
    "CheckpointV3ActionContractSection",
    "CheckpointV3TransitionContractSection",
    "CheckpointV3EventTickContractSection",
    "CheckpointV3LocalCandidateContractSection",
    "CheckpointV3CostPathContractSection",
    "CheckpointV3DecisionValidTrainingContractSection",
    "CheckpointV3SequentialFactorContractSection",
    "CheckpointV3ComponentContractSection",
    "CheckpointV3RewardContractSection",
    "CheckpointV3FailureTerminationContractSection",
    "CheckpointV3DiagnosticsContractSection",
    "CheckpointV3PolicySequenceContractSection",
    "CheckpointV3ModelStructureSection",
    "CheckpointV3TrainingContractSection",
    "CheckpointV3RuntimeReadinessSection",
)
UNRESOLVED_PARAMETER_ORDER = (
    "top_k_tasks_per_robot",
    "local_robot_cap",
    "local_task_cap",
    "pair_abs_threshold",
    "pair_rel_threshold",
    "component_abs_threshold",
    "component_rel_threshold",
    "transfer_penalty",
    "rejection_penalty_scale",
    "alignment_time_constant",
    "assignment_retry_cadence",
)

# Frozen before A4a-R import/dispatch.  These compressed literals expand to the
# exact direct-V2 canonical bytes, and json.loads(bytes) is the frozen canonical
# mapping fixture.  They are intentionally not derived from the dispatcher.
V2_LEGACY_BYTE_LENGTH = 5509
V2_LEGACY_SHA256 = "1b525f3d577f0064dc86e1f2231c7569bf0e46fa9735960937d475323d5cf60f"
V2_CONTRACT_C_BYTE_LENGTH = 7234
V2_CONTRACT_C_SHA256 = "88c8000cae494af36c441288659cf84fa428324784d1ea807a0d8e48654ae398"
V2_SOURCE_SHA256 = "8f220bb62bcacf108876bf02d97141f77af8761cced7669e9f73406d00b90bc0"
V3_INTERFACE_SHA256_FIXTURE = (
    "03c33620e8324c034de5f9014dfd0cb76bef2fc06c99b15895f94b9981cb2b6a"
)

V2_LEGACY_CANONICAL_B85 = """
c-qZa+iu%95d9ZDXH(m4TG($zw?JRo4N#!_Py_@ejcp<nsgjg0De~`ohSbeUobDEzq7Mc{&Tu$~oXerVXR-*&8c|pi9KN&F_in0G6&a7OY;`ri=w^K_3lia2Q?|<fRK9Q&D7(mvwY4azuqBmZCv^k)AM<wJ$-Ph|?948*Al-(7Xw6mfkgZ-VA51IkI=hd%S|@z5rAoHGVLWneIa^*#XGMM#aziGfaW=O>%v#MfnxBjoanx^ST}cig)+9sY2re46CJ$p@zh`BOe66hvFBc44Ry@HF$?Sy9J-MA^6!BDCCAGRs<5iY`;GEXVPzi-vmZdTq;W2H3Dm>d(2W)SIv7!}2(QhSh{B`;I1_L8&zlG~TRV-d*h7Lj0R;%L3x1fC5-`mC&?B3@>nvXVDnmz(f-DnA@@6GN~@TrfS_SyZ#6EJIXB1nHLoZb6p0f-oxzxpYRZ@pI=gBS=Oq|<*pS;O0>;l$|V*oW!oLG!DS)Q)z_HeSent+0j!_I(~;^IwImJmNzYC<0PT_dG%O=2w9!>@F6U9dWIBrUd#w!Q7nIU^wnl;mtH{By8>GS*H@D(qgShm#K)tnJm^}v6To+gQ~oPip({MouYkhmEq_NB&#2&NUevl7ws|f@jMdudzj+PhL~#Q(UL^%?8cGjc~_lTHl)kLkel4w%>X&o!YOP=sIY1`0)eylDmJ$R>^&tv{y=^Q`7r&hk%63H!Ty}!a87VMC%7A7UTewmHC#+Pfd=W-XzT-AF3?bHMZw`~s?fzcY<ki-Nqp2YY;m2QkDZ&#;EfD{s+x5Q+hE+?+=-HwzSrcQpR{h!%vFgyRpA&}gWg!D!nP7^8X{F{3u9Y^x<KME%uy2*6=DWzXz0q>6dj159c-5UDxmF&(EIBcQ+AC8+wGC^gU^MW>QlTkotBrXhza1NGMwbd))=d7XD|UY8Wf~B7O<YvRw8uWDP?oH!r+9;jZ@X`L15xBi?Agl67f-G%HF&wnFS!`aAEYAfl_(Cc?RF6{iczwbe!;0cL$MA<}1#T$Gl4FQ5+TR-axoj^<&y}D0JgFC8AnniWtzhMuBdU0V|D0kmXim*$-g!1@gROsII*hOy4t-L<Pl~BYC`JR7OxIi`x{PgKcgBeDfSPt|^#Uo=|Pfs=P_}hnVIf{|*7dVT&4+_4IoqnHguZ%UN4?)voItxW1+@#hsB4Z?CWadht2f0`(Qyc^w--ueMbs(nNUVB(%RSu3lf@hw4@!U68@j6<Zak^*1Ys@uUpi2}5CT-EG!ucbk5B7soHYe4;Q&&+gR`?MW-dInmi%L%M`<Qc>7iJTNlr@UgK*YQY7ksd7YuU5f;_^%&c~M6|U$|3nm%*T)Lpz8i)&!|-0X;V>&2=lH(i>O6K|K&YjYRkm77?FsSHwp))NjR87N*>kdoakwTf!q)APRw>4(YulPKR^$+GP~=?bA?D3`jnhCwCdc%DvSJV<eOPEbS2Iqt0dCs6#h6si2yp=1Kx3ePj7R<{Jppko>3uf2h)5Ow-38pYCti-;hHad+)ojXFOrv$b2#1~Wa8!}o#IdH3A?r0qPtC=f#hZS<b2`_y;DCDSZP>mmb1w!=&+sywEq{vm_1=ALy}Nmu!cNi5e`_@J|A=PsTccUrL`HrR`j1iaj?<jP^!<ovO#bhI5_-RjB9s71EoL^m>N^D-R=Et=5nvZ6>N>V*TCY{1;$JOTu^6iTS#zy?YL7dMt&a~(#y;1vc(nOV*rMLT)<w3Fn2}Xp%BZ<y>l;~B?QqFMCrcHZGTg1%9WsdlwC$ym2hl4<?zqb4oS(MlOS+?>mA)-ybt0hJD{V~&E_#ZJi+OZgthkDlF#co0v`%9gSG=^bvs&AR>6jzgQd}GaV8uVrgtp#K4ukC{Av-!nGDu>Bp76s`f=NHhiDH9|i=$NsKiJ#Ua?|6^1-0fyX)bY}Ze^zr4jvf{+BE7V2aHSyo){*D?pBuZVhU-jVQSMFy`^I+`i+TEQ<3CE7!QU2#!oZK6<!t0m5G@?N6yJPJa#Lpsx>h=OKgGvij3Z07PhLax$NOze&MfA>7}7ejSK2hnE&sHCnOIXvh(y3p=4Jybs6Kl?TYOgOsftua8GKp4V>)q$UbKG_x}Je=Gi|
""".strip()

V2_CONTRACT_C_CANONICAL_B85 = """
c-rMzOK;ma5dJSZXH(nR>~4H3+5$any8#Mx4@E#w6lD{UNR_1gXp#TE-;mV9ik)_YrfAWF0g)UI=bIO2=+7A!UK!1V(ca=aTYm1Q3RO$(@Rcnu=V#rlYq*fi?;DvdvzN*VE4|FlGHp!53Mot>3%21^i}l~;Y2NZJQw8|U&N9#KN_v*q)qIyNf4{mnt#In>E}UvCb7C!Po@B##B-(s-d383OX8E4+mDB-_HM#L@){(~H{BXF4!~Q^H3uytQl-##gLQJhn>A>&9=d4KR%gS(nu^{lgrU`;6^@f?;NxR{MBxuIgyi%Xyc$q~o&{e6lEI`okqELFp9HzBb!Vzz^!||GF!_qPc-I~+EAFlqm!9erIts%QtH7zeQEq9(Zrcz>0mQXI9?@Vh2iT6%${l?^~l5YT~X)6w>uk_}ek>*E2yX@}l0ho=n%yW0ktl7FJ0SG^t|M@74&z(~%4L9(wxvl=Syn(b2!wDWr{twnqgXVi7X{_8R(>licz07FIaPHFpn}084#U39@AQAA2+oy55@8)pAY(jF`NXj)&6hPk+%*|mQhTt|P->gDb6njxgwwbd?b3q*Ar{}6-rIJ+<6DkDDLRw~P4ky(}(i@QQoc1fZZH&_7sb2E>3naX%hOuKwrKGAOF|Y+IigGN=Mmbzjtg&WgrK5RUpV&5p&VBcr*zjh69P{E7ww1`XYBK@>J2(|CyB+vFw7&ns`X{Up(;r*zrPZ{sJ+-hqwXi?6@M(m(tT_4FV3;(4%hIXQ*m;O7aJiUTdW)|qLFf12>0|{>;-ley4RbnDJ6$w`G~9bxH$)>$i*aYU1EPw%o{~y{jtczCP+UNTvD6?xBV(B@VvGs~^17ObVkS^GTv=8Eqa-^rSODU~$8Jz1r~(e6{63T<)yi1q*ELJ=jTmeUxU3OF3=v5>8{Mv~h692Om4dP+x*FVZ1D-{{3##j@tXJ2;K}`u!x-*8r>nb-Ug5Xy5nWQ@?GAon_m@QYDatV?`2m|7JiXo5=^SNAe#E3nt6>Y9CIH)1V`N3>aH3fSzzm}TCa!Vm_<`5=t3o1R5YL79PP=sBTTyZ3@Rm*K*Da9N^fwVZKb8&l3RzD`|5e=|F9JZ04ShrTqvAuF9s@9Qn1+vc5<i}Q_7M5Bh(UEdYg>A=pj55z4%KZ%@a_W=&gGjn0&w6rfz9SvPdX|+Gf+wUvvKO~8tcFAA9wWaZAGNKZ>iD2%z^uyK=nn`+x~X2k{U}6`JhQ%!SaB-xv)TD<o+dZl^#^0O{T<RVdHwwQ`k!a-yb-t<kXEk4E!LB*Re_LX4#@=69~PH?oZ*MGED)MVJ=}`5@-oSr2}yWj>e(<Y{npsqtf%e{eg7hipS^z@@<m!bc~;jgOzv~&NuG>r1fw5^tn_PxPAM}MA1kAI#VAv@bq*&mWx8aO#5n!}o|&4JgQbutT)28t|1-2cL)UXdE-6}T$==jWg%Sb~8g6-=ElXZG34cj7gM&i{XC9}3Q)@>ZvXpdz7`sJGMn|4*Pf2S`NbcSur&`~m%-gbrLQqUdOKr?#$FLCT!J&1OJSi#%#PRF|Gm@NGgbwKP55E2;X#H($XJMJxYEEns%ABvW!Cg{%G3s-ZtEKe!K;3mn7*j)J20O$M9bE+}ri>N{`UWX$vVTzz`$tXo#r&^}e!hd4S4NNrKGYGXZaQ~t(7?B^cByrLRK44a_aTXQ^Kj)pg){%L;mrRhoW+j~XYmC%$%p&W{z+Z#QHcKT!uDlae3w|9C)vBo)p^;tuR=?dthDJ?{fQxu@VLj=dH(C!dHyTfdGYJndGYhx`DRk%oO(m*YK$hp=ZOo-lDkpsI{C8#mjt>)8<s3J@S&}k%`W@y0N7N{Jx+#J7AWMa(8kHKR6>Qn39w@^RQM;^rS&O4>LyIHzsEB4Hr<mG+Q5}x(;p2p)Qu~S8D8fF50qELeMJutad<^T%L^46F^JocI8xJlOVPCyHQ%wGC_Hp5vpFSyQeTbsWN4qB7rZ`LfK^mwbO$a-iV_?1=&-QkGCVnir+#`UsIZMn+<34xRb^Ug>8<4HJqC&ZtnkkdtBi9KWf1?kNP<q03@f22o4hd;yz$3-=Fn7y&4H_h93*XQvqCY<tyd*&igU5w?RIwb@Y&F{qBTRwOAf=M!s9E2^qp0%f?)*LMpHYRnBK~LtnynOyr!0%VrD#K?jyY;%3N_5USA}vbwi$Wpoe2tQFT*EYRF@UNdKb+>Cc6!YopJ5_~-BG>ur4SQo4bG#<3nW#CPPf^Z0BgBVX1wMey^~1|=O#GZi9mE7fZ4DKGFn$(Y^U{Rb;jSXc
""".strip()


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _expect_error(
    function: Callable[[], Any],
    exception_types: type[BaseException] | tuple[type[BaseException], ...],
    *message_fragments: str,
) -> BaseException:
    try:
        function()
    except exception_types as exc:
        lowered = str(exc).lower()
        for fragment in message_fragments:
            _assert(fragment.lower() in lowered, f"missing error context {fragment!r}: {exc}")
        return exc
    except Exception as exc:
        raise AssertionError(f"unexpected {type(exc).__name__}: {exc}") from exc
    raise AssertionError("expected an exception")


def _install_namespace() -> None:
    packages = (
        ("isaaclab_tasks", REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks"),
        (
            "isaaclab_tasks.direct",
            REPO_ROOT / "source" / "isaaclab_tasks" / "isaaclab_tasks" / "direct",
        ),
        (PACKAGE, SCAN_SOURCE),
    )
    for name, path in packages:
        if name in sys.modules:
            continue
        module = ModuleType(name)
        module.__package__ = name
        module.__path__ = [str(path)]  # type: ignore[attr-defined]
        sys.modules[name] = module


def _load_exact(key: str, path: Path) -> ModuleType:
    existing = sys.modules.get(key)
    if existing is not None:
        _assert(Path(str(existing.__file__)).resolve() == path.resolve(), key)
        return existing
    spec = importlib.util.spec_from_file_location(key, path)
    _assert(spec is not None and spec.loader is not None, f"missing spec for {key}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[key] = module
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(key, None)
        raise
    finally:
        sys.dont_write_bytecode = previous
    return module


_install_namespace()
V2 = _load_exact(V2_KEY, MODULE_PATHS[V2_KEY])
V3 = _load_exact(V3_KEY, MODULE_PATHS[V3_KEY])
DISPATCH = _load_exact(DISPATCH_KEY, MODULE_PATHS[DISPATCH_KEY])
AGGREGATE = sys.modules[AGGREGATE_KEY]


def _frozen_v2_bytes(encoded: str) -> bytes:
    return zlib.decompress(base64.b85decode(encoded.encode("ascii")))


V2_LEGACY_BYTES = _frozen_v2_bytes(V2_LEGACY_CANONICAL_B85)
V2_CONTRACT_C_BYTES = _frozen_v2_bytes(V2_CONTRACT_C_CANONICAL_B85)
V2_LEGACY_MAPPING = json.loads(V2_LEGACY_BYTES.decode("utf-8"))
V2_CONTRACT_C_MAPPING = json.loads(V2_CONTRACT_C_BYTES.decode("utf-8"))


def _scale(*, reversed_agents: bool = False) -> Mapping[str, object]:
    names = ("robot_2", "robot_1", "robot_0") if reversed_agents else (
        "robot_0", "robot_1", "robot_2"
    )
    return AGGREGATE.build_event_gated_scale_contract(
        M=3,
        N=50,
        ordered_agent_names=names,
        ordered_task_ids=tuple(range(50)),
        scene_env_spacing=12.0,
        sim_dt_seconds=0.01,
        control_decimation=4,
        physical_control_step_seconds=0.04,
        episode_time_limit_seconds=40.01,
        episode_horizon_steps=1001,
    )


def _v3_manifest() -> object:
    return V3.build_interface_semantic_descriptor_v3(scale_contract=_scale())


def _v3_mapping() -> dict[str, Any]:
    return copy.deepcopy(_v3_manifest().to_mapping())


def _replace(mapping: Mapping[str, Any], path: str, value: Any) -> dict[str, Any]:
    result = copy.deepcopy(mapping)
    target: Any = result
    parts = path.split(".")
    for part in parts[:-1]:
        target = target[int(part)] if isinstance(target, list) else target[part]
    if isinstance(target, list):
        target[int(parts[-1])] = value
    else:
        target[parts[-1]] = value
    return result


def _reverse_mapping_insertion(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _reverse_mapping_insertion(value[key])
            for key in reversed(tuple(value))
        }
    if isinstance(value, list):
        return [_reverse_mapping_insertion(item) for item in value]
    return value


def _decision_signature(decision: object) -> tuple[Any, ...]:
    mapping = decision.to_mapping()
    return (
        mapping["allowed"],
        mapping["classification"],
        mapping["requested_purpose"],
        tuple(
            (item["field_path"], item["category"])
            for item in mapping["mismatches"]
        ),
        mapping["required_acknowledgement"],
        mapping["next_action"],
    )


def test_canonical_module_identity() -> None:
    _assert(V3.__name__ == V3_KEY, "V3 canonical module key")
    _assert(DISPATCH.__name__ == DISPATCH_KEY, "dispatcher canonical module key")
    _assert(V2.AssignmentCheckpointContractManifest.__module__ == V2_KEY,
            "V2 class must remain owned by the unchanged V2 module")
    _assert("assignment_checkpoint_contract_v3" not in sys.modules,
            "bare V3 alias exists")
    _assert("assignment_checkpoint_semantic_dispatch" not in sys.modules,
            "bare dispatcher alias exists")

    public_types = (
        V3.AssignmentCheckpointManifestKind,
        V3.AssignmentCheckpointV3Purpose,
        V3.AssignmentCheckpointV3ContractError,
        V3.UnsupportedCheckpointManifestVersionError,
        V3.UnsupportedCheckpointManifestKindError,
        V3.CheckpointManifestSchemaError,
        V3.CheckpointManifestPurposeError,
        V3.CheckpointReadyManifestNotAuthorizedError,
        V3.UnresolvedCheckpointParameterError,
        V3.CheckpointRuntimeReadinessError,
        V3.CheckpointManifestFamilyMismatchError,
        V3.CheckpointManifestInputError,
        *(getattr(V3, name) for name in SECTION_CLASSES),
        V3.AssignmentCheckpointContractManifestV3,
        V3.AssignmentCheckpointV3SemanticDecision,
    )
    for public_type in public_types:
        _assert(public_type.__module__ == V3_KEY, f"public type owner: {public_type}")

    for key, path in ((V3_KEY, MODULE_PATHS[V3_KEY]),
                      (DISPATCH_KEY, MODULE_PATHS[DISPATCH_KEY])):
        source = path.read_text(encoding="utf-8")
        guard = source.find("if __name__ !=")
        _assert(guard >= 0, f"identity guard absent: {key}")
        dependency_positions = [
            position for token in (
                "from dataclasses import", "from enum import", "from . import",
                "from .assignment_", "class Assignment",
            ) if (position := source.find(token)) >= 0
        ]
        _assert(dependency_positions and guard < min(dependency_positions),
                f"identity guard is not first: {key}")
        _assert("sys.modules[" not in source, f"module alias source in {key}")

        child = f"""
import importlib.util,json,pathlib,sys
p=pathlib.Path({str(path)!r})
spec=importlib.util.spec_from_file_location({path.stem!r},p)
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m
try:
    spec.loader.exec_module(m)
except Exception as exc:
    print(json.dumps({{'type':type(exc).__name__,'message':str(exc),
      'types':[name for name,value in vars(m).items() if isinstance(value,type)],
      'deps':[name for name in sys.modules if name.startswith({PACKAGE!r}+'.assignment_')]}}))
else:
    raise SystemExit('wrong-key import unexpectedly succeeded')
"""
        result = subprocess.run(
            [sys.executable, "-c", child], capture_output=True, text=True,
            check=False,
        )
        _assert(result.returncode == 0, result.stderr)
        payload = json.loads(result.stdout)
        _assert(payload["type"] == "ImportError", f"wrong-key type: {key}")
        _assert("canonical" in payload["message"].lower(), f"wrong-key message: {key}")
        _assert(payload["types"] == [], f"types declared before guard: {key}")
        _assert(payload["deps"] == [], f"dependencies imported before guard: {key}")


def test_v2_frozen_canonical_goldens() -> None:
    _assert(hashlib.sha256(MODULE_PATHS[V2_KEY].read_bytes()).hexdigest() ==
            V2_SOURCE_SHA256, "unchanged V2 source SHA-256")
    fixtures = (
        ("legacy", V2_LEGACY_BYTES, V2_LEGACY_MAPPING,
         V2_LEGACY_BYTE_LENGTH, V2_LEGACY_SHA256),
        ("lifecycle_contract_c", V2_CONTRACT_C_BYTES, V2_CONTRACT_C_MAPPING,
         V2_CONTRACT_C_BYTE_LENGTH, V2_CONTRACT_C_SHA256),
    )
    for name, frozen_bytes, frozen_mapping, expected_length, expected_hash in fixtures:
        _assert(len(frozen_bytes) == expected_length, f"frozen {name} byte length")
        _assert(hashlib.sha256(frozen_bytes).hexdigest() == expected_hash,
                f"frozen {name} literal hash")
        direct = V2.AssignmentCheckpointContractManifest.from_mapping(frozen_mapping)
        _assert(direct.to_mapping() == frozen_mapping, f"direct {name} mapping")
        _assert(V2.canonical_manifest_bytes(direct) == frozen_bytes,
                f"direct {name} canonical bytes")
        _assert(V2.compute_manifest_sha256(direct) == expected_hash,
                f"direct {name} SHA-256")

        parsed = DISPATCH.parse_assignment_checkpoint_manifest(frozen_mapping)
        _assert(type(parsed) is V2.AssignmentCheckpointContractManifest,
                f"dispatcher {name} native V2 type")
        _assert(parsed.to_mapping() == direct.to_mapping(),
                f"dispatcher {name} canonical mapping")
        _assert(
            DISPATCH.canonical_assignment_checkpoint_manifest_bytes(frozen_mapping)
            == frozen_bytes,
            f"dispatcher {name} frozen bytes",
        )
        _assert(
            DISPATCH.compute_assignment_checkpoint_manifest_sha256(frozen_mapping)
            == expected_hash,
            f"dispatcher {name} frozen SHA-256",
        )
        reordered = {key: frozen_mapping[key] for key in reversed(tuple(frozen_mapping))}
        _assert(
            DISPATCH.canonical_assignment_checkpoint_manifest_bytes(reordered)
            == frozen_bytes,
            f"V2 {name} insertion-order determinism",
        )


def _v2_manifest(mapping: Mapping[str, Any]) -> object:
    return V2.AssignmentCheckpointContractManifest.from_mapping(mapping)


def _v2_ablation_mapping() -> dict[str, Any]:
    result = copy.deepcopy(V2_CONTRACT_C_MAPPING)
    result["identity"]["profile_name"] = "lifecycle_ablation"
    result["identity"]["training_time_profile"] = "lifecycle_ablation"
    behavior = result["lifecycle_behavior_contract"]
    behavior["resolver_contract_version"] = "disabled"
    behavior["mask_contract_version"] = "lifecycle_ablation_physical_mask_v1"
    behavior["budget_release_contract_version"] = "disabled"
    return result


def _v2_artifact(role: str, filename: str, *, actor_identity: str | None = None) -> object:
    tensors = (
        V2.StateDictTensorInventoryEntry("act.linear.bias", (51,), "float32"),
        V2.StateDictTensorInventoryEntry(
            "base.mlp.fc.0.weight", (256, 1059), "torch.float32"
        ),
    )
    return V2.ArtifactFileInventoryEntry(
        artifact_role=role,
        relative_file_name=filename,
        file_size=1234,
        file_sha256=("a" if role == "actor" else "b") * 64,
        serialization_mode="state_dict",
        actor_identity=actor_identity,
        tensor_inventory=tensors,
        tensor_inventory_sha256=V2.compute_tensor_inventory_sha256(tensors),
    )


def _v2_training_state(
    manifest: object,
    *,
    include_critic: bool = True,
    include_value_norm: bool = True,
) -> object:
    fingerprint = V2.compute_manifest_sha256(manifest)
    names = tuple(manifest.scale["ordered_agent_names"])
    return V2.AssignmentTrainingStateManifest(
        contract_fingerprint=fingerprint,
        checkpoint_kind="temporary_test",
        checkpoint_generation=3,
        episode_or_update_index=7,
        continuation_classification="validated_weight_continuation",
        ordered_actor_identities=names,
        actor_artifacts=tuple(
            _v2_artifact("actor", f"actor_agent_{name}.pt", actor_identity=name)
            for name in names
        ),
        critic_artifact=(
            _v2_artifact("critic", "critic_agent.pt") if include_critic else None
        ),
        value_normalizer_artifact=(
            _v2_artifact("value_normalizer", "value_normalizer.pt")
            if include_value_norm else None
        ),
        actor_optimizer_available=False,
        critic_optimizer_available=False,
        training_counters_available=False,
        rng_state_available=False,
        environment_resolver_state_available=False,
        rollout_buffer_state_available=False,
    )


def _v2_direct_and_dispatch(
    *,
    purpose: object,
    checkpoint_mapping: Mapping[str, Any],
    current_mapping: Mapping[str, Any],
    checkpoint_fingerprint: str | None,
    explicit_ablation_name: str | None = None,
    training_state: object | None = None,
    acknowledged: bool = False,
) -> tuple[object, object]:
    checkpoint = _v2_manifest(checkpoint_mapping)
    current = _v2_manifest(current_mapping)
    direct = V2.evaluate_compatibility(
        V2.CompatibilityRequest(
            purpose=purpose,
            checkpoint_manifest=checkpoint,
            current_manifest=current,
            checkpoint_fingerprint=checkpoint_fingerprint,
            explicit_ablation_name=explicit_ablation_name,
            training_state_manifest=training_state,
            continuation_reset_acknowledged=acknowledged,
        )
    )
    dispatched = DISPATCH.evaluate_assignment_checkpoint_semantics(
        checkpoint_mapping,
        purpose=purpose,
        current_manifest=current_mapping,
        checkpoint_fingerprint=checkpoint_fingerprint,
        explicit_ablation_name=explicit_ablation_name,
        training_state_manifest=(
            None if training_state is None else training_state.to_mapping()
        ),
        continuation_reset_acknowledged=acknowledged,
    )
    _assert(type(dispatched) is V2.CompatibilityDecision,
            "dispatcher changed V2 decision class")
    _assert(dispatched.to_mapping() == direct.to_mapping(),
            "dispatcher changed full V2 compatibility decision")
    return direct, dispatched


def _assert_v2_decision(
    decision: object,
    *,
    allowed: bool,
    classification: str,
    purpose: str,
    mismatches: tuple[tuple[str, str], ...] = (),
) -> None:
    signature = _decision_signature(decision)
    _assert(signature[:4] == (allowed, classification, purpose, mismatches),
            f"V2 golden decision drift: {signature[:4]!r}")


def _frozen_v2_decision_mapping(
    *,
    allowed: bool,
    classification: str,
    purpose: str,
    reason: str,
    mismatches: tuple[tuple[str, str, Any, Any], ...] = (),
    required_acknowledgement: str | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    frozen_mismatches = [
        {
            "field_path": path,
            "category": category,
            "expected_value": expected,
            "actual_value": actual,
            "message": f"{path} differs for {category}",
        }
        for path, category, expected, actual in mismatches
    ]
    return {
        "allowed": allowed,
        "classification": classification,
        "requested_purpose": purpose,
        "mismatches": frozen_mismatches,
        "first_mismatch": frozen_mismatches[0] if frozen_mismatches else None,
        "reason": reason,
        "required_acknowledgement": required_acknowledgement,
        "next_action": next_action,
    }


def test_v2_direct_dispatch_compatibility_goldens() -> None:
    normal = V2.CompatibilityPurpose.NORMAL_EVALUATION
    structural = V2.CompatibilityPurpose.STRUCTURAL_INSPECTION
    ablation_purpose = V2.CompatibilityPurpose.EXPLICIT_ABLATION_EVALUATION
    continuation = V2.CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION
    ablation = _v2_ablation_mapping()

    evaluation_differences = (
        ("identity.profile_name", "evaluation_semantics"),
        ("identity.training_time_profile", "evaluation_semantics"),
        ("lifecycle_behavior_contract.budget_release_contract_version", "evaluation_semantics"),
        ("lifecycle_behavior_contract.mask_contract_version", "evaluation_semantics"),
        ("lifecycle_behavior_contract.resolver_contract_version", "evaluation_semantics"),
    )
    continuation_differences = tuple(
        (path, "validated_weight_continuation")
        for path, _ in evaluation_differences
    )

    frozen_full_decisions = {
        "legacy_native": _frozen_v2_decision_mapping(
            allowed=True, classification="normal_evaluation",
            purpose=normal.value,
            reason="checkpoint is compatible for normal evaluation",
        ),
        "contract_c_native": _frozen_v2_decision_mapping(
            allowed=True, classification="normal_evaluation",
            purpose=normal.value,
            reason="checkpoint is compatible for normal evaluation",
        ),
        "contract_c_structural": _frozen_v2_decision_mapping(
            allowed=True, classification="structurally_compatible",
            purpose=structural.value,
            reason="model/state-dict structures correspond",
            next_action="weights_only_state_dict_inventory_inspection",
        ),
        "contract_c_to_ablation": _frozen_v2_decision_mapping(
            allowed=True, classification="explicit_ablation_evaluation",
            purpose=ablation_purpose.value,
            reason=(
                "validator-owned lifecycle Contract C to lifecycle ablation "
                "evaluation is authorized"
            ),
        ),
        "ablation_normal": _frozen_v2_decision_mapping(
            allowed=False, classification="evaluation_semantic_mismatch",
            purpose=normal.value, reason="evaluation-semantic fields differ",
            mismatches=(
                ("identity.profile_name", "evaluation_semantics",
                 "lifecycle_contract_c", "lifecycle_ablation"),
                ("identity.training_time_profile", "evaluation_semantics",
                 "lifecycle_contract_c", "lifecycle_ablation"),
                ("lifecycle_behavior_contract.budget_release_contract_version",
                 "evaluation_semantics", "budget_release_v1", "disabled"),
                ("lifecycle_behavior_contract.mask_contract_version",
                 "evaluation_semantics", "lifecycle_contract_c_mask_v1",
                 "lifecycle_ablation_physical_mask_v1"),
                ("lifecycle_behavior_contract.resolver_contract_version",
                 "evaluation_semantics",
                 "assignment_lifecycle_resolver_contract_c_v1", "disabled"),
            ),
        ),
        "ablation_continuation": _frozen_v2_decision_mapping(
            allowed=False, classification="continuation_contract_mismatch",
            purpose=continuation.value,
            reason=(
                "validated weight continuation requires exact immutable "
                "contract equality"
            ),
            mismatches=(
                ("identity.profile_name", "validated_weight_continuation",
                 "lifecycle_contract_c", "lifecycle_ablation"),
                ("identity.training_time_profile", "validated_weight_continuation",
                 "lifecycle_contract_c", "lifecycle_ablation"),
                ("lifecycle_behavior_contract.budget_release_contract_version",
                 "validated_weight_continuation", "budget_release_v1", "disabled"),
                ("lifecycle_behavior_contract.mask_contract_version",
                 "validated_weight_continuation", "lifecycle_contract_c_mask_v1",
                 "lifecycle_ablation_physical_mask_v1"),
                ("lifecycle_behavior_contract.resolver_contract_version",
                 "validated_weight_continuation",
                 "assignment_lifecycle_resolver_contract_c_v1", "disabled"),
            ),
        ),
        "legacy_to_contract_structural": _frozen_v2_decision_mapping(
            allowed=False, classification="structural_mismatch",
            purpose=structural.value, reason="one or more structural fields differ",
            mismatches=(
                ("actor_schema.actor_dimension", "structural", 909, 1059),
                ("actor_schema.actor_dimension_by_agent", "structural",
                 {"robot_0": 909, "robot_1": 909, "robot_2": 909},
                 {"robot_0": 1059, "robot_1": 1059, "robot_2": 1059}),
                ("shared_schema.shared_dimension", "structural", 2727, 3183),
            ),
            next_action="weights_only_state_dict_inventory_inspection",
        ),
        "missing_ablation_name": _frozen_v2_decision_mapping(
            allowed=False, classification="unknown_or_missing_ablation",
            purpose=ablation_purpose.value,
            reason=(
                "explicit validator-owned ablation name "
                "'lifecycle_contract_c_checkpoint_to_lifecycle_ablation_"
                "evaluation_v1' is required"
            ),
        ),
        "training_init": _frozen_v2_decision_mapping(
            allowed=False, classification="unsupported_deferred",
            purpose=(
                V2.CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING.value
            ),
            reason=(
                "training initialization/fine-tuning is not supported by "
                "assignment checkpoint contract v1"
            ),
        ),
        "exact_resume": _frozen_v2_decision_mapping(
            allowed=False, classification="unsupported_exact_resume",
            purpose=V2.CompatibilityPurpose.EXACT_TRAINING_RESUME.value,
            reason=(
                "exact resume is unsupported: actor/critic optimizer state, "
                "training counters, best-reward state, RNG state, environment/"
                "resolver/budget state, and rollout-buffer state are unavailable"
            ),
        ),
    }

    cases = (
        ("legacy_native", normal, V2_LEGACY_MAPPING, V2_LEGACY_MAPPING, V2_LEGACY_SHA256,
         None, True, "normal_evaluation", ()),
        ("contract_c_native", normal, V2_CONTRACT_C_MAPPING, V2_CONTRACT_C_MAPPING,
         V2_CONTRACT_C_SHA256, None, True, "normal_evaluation", ()),
        ("contract_c_structural", structural, V2_CONTRACT_C_MAPPING, V2_CONTRACT_C_MAPPING,
         V2_CONTRACT_C_SHA256, None, True, "structurally_compatible", ()),
        ("contract_c_to_ablation", ablation_purpose, V2_CONTRACT_C_MAPPING, ablation,
         V2_CONTRACT_C_SHA256, V2.NAMED_LIFECYCLE_ABLATION, True,
         "explicit_ablation_evaluation", ()),
        ("ablation_normal", normal, V2_CONTRACT_C_MAPPING, ablation, V2_CONTRACT_C_SHA256,
         None, False, "evaluation_semantic_mismatch", evaluation_differences),
        ("ablation_continuation", continuation, V2_CONTRACT_C_MAPPING, ablation,
         V2_CONTRACT_C_SHA256, None, False, "continuation_contract_mismatch",
         continuation_differences),
        ("legacy_to_contract_structural", structural, V2_LEGACY_MAPPING, V2_CONTRACT_C_MAPPING,
         V2_LEGACY_SHA256, None, False, "structural_mismatch", (
             ("actor_schema.actor_dimension", "structural"),
             ("actor_schema.actor_dimension_by_agent", "structural"),
             ("shared_schema.shared_dimension", "structural"),
         )),
        ("missing_ablation_name", ablation_purpose, V2_CONTRACT_C_MAPPING, ablation,
         V2_CONTRACT_C_SHA256, None, False, "unknown_or_missing_ablation", ()),
    )
    for (
        case_name, purpose, checkpoint, current, fingerprint, ablation_name,
        allowed, classification, mismatch_order,
    ) in cases:
        direct, _ = _v2_direct_and_dispatch(
            purpose=purpose,
            checkpoint_mapping=checkpoint,
            current_mapping=current,
            checkpoint_fingerprint=fingerprint,
            explicit_ablation_name=ablation_name,
        )
        _assert_v2_decision(
            direct,
            allowed=allowed,
            classification=classification,
            purpose=purpose.value,
            mismatches=mismatch_order,
        )
        _assert(direct.to_mapping() == frozen_full_decisions[case_name],
                f"full frozen V2 decision drift: {case_name}")

    hidden = _replace(
        V2_CONTRACT_C_MAPPING,
        "model_structure.actor_hidden_sizes",
        [512, 256],
    )
    direct, _ = _v2_direct_and_dispatch(
        purpose=structural,
        checkpoint_mapping=V2_CONTRACT_C_MAPPING,
        current_mapping=hidden,
        checkpoint_fingerprint=V2_CONTRACT_C_SHA256,
    )
    _assert_v2_decision(
        direct, allowed=False, classification="structural_mismatch",
        purpose=structural.value,
        mismatches=(("model_structure.actor_hidden_sizes", "structural"),),
    )
    expected_hidden = _frozen_v2_decision_mapping(
        allowed=False, classification="structural_mismatch",
        purpose=structural.value, reason="one or more structural fields differ",
        mismatches=(("model_structure.actor_hidden_sizes", "structural",
                     [256, 256], [512, 256]),),
        next_action="weights_only_state_dict_inventory_inspection",
    )
    _assert(direct.to_mapping() == expected_hidden,
            "full frozen V2 actor-hidden decision drift")

    for purpose, classification in (
        (V2.CompatibilityPurpose.TRAINING_INITIALIZATION_OR_FINE_TUNING,
         "unsupported_deferred"),
        (V2.CompatibilityPurpose.EXACT_TRAINING_RESUME,
         "unsupported_exact_resume"),
    ):
        direct, _ = _v2_direct_and_dispatch(
            purpose=purpose,
            checkpoint_mapping=V2_CONTRACT_C_MAPPING,
            current_mapping=V2_CONTRACT_C_MAPPING,
            checkpoint_fingerprint=V2_CONTRACT_C_SHA256,
        )
        _assert_v2_decision(
            direct, allowed=False, classification=classification,
            purpose=purpose.value,
        )
        key = "training_init" if classification == "unsupported_deferred" else "exact_resume"
        _assert(direct.to_mapping() == frozen_full_decisions[key],
                f"full frozen V2 decision drift: {key}")


def test_v2_fingerprint_and_continuation_classification_order() -> None:
    normal = V2.CompatibilityPurpose.NORMAL_EVALUATION
    continuation = V2.CompatibilityPurpose.VALIDATED_WEIGHT_CONTINUATION
    fingerprint_cases = (
        (None, "missing_fingerprint",
         "checkpoint manifest integrity fingerprint is required"),
        ("z" * 64, "invalid_fingerprint",
         "expected_fingerprint must be 64 lowercase hexadecimal characters"),
        ("a" * 64, "fingerprint_mismatch",
         "checkpoint manifest SHA-256 verification failed"),
    )
    for fingerprint, classification, reason in fingerprint_cases:
        direct, _ = _v2_direct_and_dispatch(
            purpose=normal,
            checkpoint_mapping=V2_CONTRACT_C_MAPPING,
            current_mapping=V2_CONTRACT_C_MAPPING,
            checkpoint_fingerprint=fingerprint,
        )
        _assert_v2_decision(
            direct, allowed=False, classification=classification,
            purpose=normal.value,
        )
        _assert(direct.to_mapping() == _frozen_v2_decision_mapping(
            allowed=False, classification=classification,
            purpose=normal.value, reason=reason,
        ), f"full frozen V2 fingerprint decision drift: {classification}")

    checkpoint = _v2_manifest(V2_CONTRACT_C_MAPPING)
    missing_native = V2.evaluate_compatibility(
        V2.CompatibilityRequest(
            purpose=normal,
            checkpoint_manifest=None,
            current_manifest=checkpoint,
            checkpoint_fingerprint=None,
        )
    )
    _assert_v2_decision(
        missing_native, allowed=False, classification="missing_native_metadata",
        purpose=normal.value,
    )
    _assert(missing_native.to_mapping() == _frozen_v2_decision_mapping(
        allowed=False, classification="missing_native_metadata",
        purpose=normal.value,
        reason="native manifest metadata is required for this compatibility path",
    ), "full frozen V2 missing-metadata decision drift")

    valid_state = _v2_training_state(checkpoint)
    state_binding = copy.deepcopy(valid_state.to_mapping())
    state_binding["contract_fingerprint"] = "a" * 64
    wrong_binding = V2.AssignmentTrainingStateManifest.from_mapping(state_binding)

    wrong_actor_map = copy.deepcopy(valid_state.to_mapping())
    wrong_names = ("agent_0", "agent_1", "agent_2")
    wrong_actor_map["ordered_actor_identities"] = list(wrong_names)
    for artifact, name in zip(wrong_actor_map["actor_artifacts"], wrong_names, strict=True):
        artifact["actor_identity"] = name
    wrong_actor = V2.AssignmentTrainingStateManifest.from_mapping(wrong_actor_map)

    acknowledgement = (
        "actor and critic optimizers, training counters, best-reward state, RNG, "
        "environment, resolver, and rollout buffers reset"
    )
    continuation_cases = (
        (None, False, "missing_training_state_manifest", False,
         "validated weight continuation requires checkpoint-local training-state inventory",
         None),
        (wrong_binding, True, "training_state_binding_mismatch", False,
         "training-state manifest is not bound to the checkpoint contract fingerprint",
         None),
        (wrong_actor, True, "actor_inventory_identity_mismatch", False,
         "training-state actor inventory does not match the contract's ordered actors",
         None),
        (_v2_training_state(checkpoint, include_critic=False), True,
         "missing_critic_inventory", False,
         "validated weight continuation requires critic inventory", None),
        (_v2_training_state(checkpoint, include_value_norm=False), True,
         "missing_value_normalizer_inventory", False,
         "validated weight continuation requires ValueNorm inventory when enabled", None),
        (valid_state, False, "acknowledgement_required", False,
         "contract and artifact inventory pass; continuation reset acknowledgement is required",
         acknowledgement),
        (valid_state, True, "validated_weight_continuation", True,
         "exact contract and required weight inventory pass with reset acknowledgement",
         acknowledgement),
    )
    observed = []
    for state, acknowledged, classification, allowed, reason, required_ack in continuation_cases:
        direct, _ = _v2_direct_and_dispatch(
            purpose=continuation,
            checkpoint_mapping=V2_CONTRACT_C_MAPPING,
            current_mapping=V2_CONTRACT_C_MAPPING,
            checkpoint_fingerprint=V2_CONTRACT_C_SHA256,
            training_state=state,
            acknowledged=acknowledged,
        )
        observed.append(direct.classification)
        _assert_v2_decision(
            direct,
            allowed=allowed,
            classification=classification,
            purpose=continuation.value,
        )
        _assert(direct.to_mapping() == _frozen_v2_decision_mapping(
            allowed=allowed, classification=classification,
            purpose=continuation.value, reason=reason,
            required_acknowledgement=required_ack,
        ), f"full frozen V2 continuation decision drift: {classification}")
    _assert(tuple(observed) == tuple(item[2] for item in continuation_cases),
            "V2 continuation classification sequence drift")


def _deep_mutable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _deep_mutable(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_deep_mutable(item) for item in value)
    if isinstance(value, list):
        return [_deep_mutable(item) for item in value]
    return value


def _drift_first_leaf(value: Any) -> Any:
    """Return a deep copy with one deterministic semantic primitive changed."""

    if isinstance(value, Mapping):
        result = copy.deepcopy(value)
        first = next(iter(result))
        result[first] = _drift_first_leaf(result[first])
        return result
    if isinstance(value, list):
        result = copy.deepcopy(value)
        _assert(bool(result), "cannot drift an empty sequence")
        result[0] = _drift_first_leaf(result[0])
        return result
    if type(value) is str:
        return value + "_drift"
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is float:
        return value + 0.125
    raise AssertionError(f"unsupported drift leaf: {type(value).__name__}")


def test_v3_root_typed_schema_and_bindings() -> None:
    _assert(V3.MANIFEST_FORMAT_VERSION == "assignment_checkpoint_contract_v3",
            "V3 exact version")
    _assert(tuple(V3.TOP_LEVEL_KEY_ORDER) == TOP_LEVEL_KEYS,
            "V3 top-level inventory")
    _assert(tuple(V3.SEMANTIC_SECTION_NAMES) == SECTION_NAMES,
            "V3 19-section inventory")
    _assert(
        tuple(member.value for member in V3.AssignmentCheckpointManifestKind)
        == ("interface_semantic_descriptor", "checkpoint_ready_manifest"),
        "manifest-kind enum order",
    )
    _assert(
        tuple(member.value for member in V3.AssignmentCheckpointV3Purpose)
        == ("interface_audit",),
        "Phase-A purpose enum must be INTERFACE_AUDIT only",
    )

    manifest = _v3_manifest()
    mapping = manifest.to_mapping()
    _assert(type(manifest) is V3.AssignmentCheckpointContractManifestV3,
            "V3 manifest type")
    _assert(tuple(mapping) == TOP_LEVEL_KEYS and len(mapping) == 21,
            "exact 21-key V3 root order")
    _assert(mapping["manifest_format_version"] == V3.MANIFEST_FORMAT_VERSION,
            "V3 mapping version")
    _assert(mapping["manifest_kind"] == "interface_semantic_descriptor",
            "V3 interface kind")

    manifest_type = V3.AssignmentCheckpointContractManifestV3
    _assert(is_dataclass(manifest_type), "manifest must be a dataclass")
    _assert(manifest_type.__dataclass_params__.frozen, "manifest must be frozen")
    _assert("__slots__" in manifest_type.__dict__, "manifest must be slotted")
    _assert(tuple(field.name for field in fields(manifest_type)) == TOP_LEVEL_KEYS,
            "manifest field inventory/order")
    for section_name, class_name in zip(SECTION_NAMES, SECTION_CLASSES, strict=True):
        section_type = getattr(V3, class_name)
        section = getattr(manifest, section_name)
        _assert(type(section) is section_type, f"dedicated type for {section_name}")
        _assert(is_dataclass(section_type), f"dataclass for {section_name}")
        _assert(section_type.__dataclass_params__.frozen,
                f"frozen section {section_name}")
        _assert("__slots__" in section_type.__dict__, f"slotted section {section_name}")
        _assert(
            tuple(field.name for field in fields(section_type))
            == tuple(mapping[section_name]),
            f"named-field inventory differs from mapping for {section_name}",
        )
        _assert(not (
            len(fields(section_type)) == 1
            and fields(section_type)[0].name in ("payload", "data", "mapping")
        ), f"generic payload bag used for {section_name}")

    identity = mapping["identity"]
    _assert(identity == {
        "profile": "event_gated_local_mrta",
        "profile_contract_version": "assignment_resolved_profile_v1",
        "checkpoint_family": "assignment_checkpoint_contract_v3",
        "runtime_route": "event_gated_phase_a_interface_only_v1",
        "runtime_readiness": "interface_only",
        "event_target_semantics_contract": "event_gated_target_semantics_v1",
        "training_semantics": "event_gated_happo_ep_feed_forward_v1",
    }, "resolved event identity projection")
    for forbidden in (
        "event_gate_enabled", "resolver_enabled", "lifecycle_observation_enabled",
        "lifecycle_mask_enabled",
    ):
        _assert(forbidden not in identity, f"legacy runtime boolean leaked: {forbidden}")

    scale = mapping["scale"]
    _assert(tuple(scale) == (
        "contract_version", "M", "N", "ordered_agent_names",
        "ordered_task_ids", "scene_env_spacing", "sim_dt_seconds",
        "control_decimation", "physical_control_step_seconds",
        "episode_time_limit_seconds", "episode_horizon_steps",
    ), "scale exact projection")
    _assert(not {"num_agents", "action_dimension", "noop_raw_id",
                 "noop_decoded_value"}.intersection(scale),
            "action-owned fields leaked into scale")
    _assert(mapping["actor_schema"]["block_count"] == 15 and
            len(mapping["actor_schema"]["blocks"]) == 15 and
            len(mapping["actor_schema"]) == 18,
            "actor 18-key/15-block binding")
    _assert(mapping["actor_schema"]["reference_dimension"] == {
        "M": 3, "N": 50, "dimension": 1692,
    }, "actor reference dimension")
    _assert(mapping["shared_schema"]["block_count"] == 19 and
            len(mapping["shared_schema"]["blocks"]) == 19 and
            len(mapping["shared_schema"]) == 19,
            "shared 19-key/19-block binding")
    _assert(mapping["shared_schema"]["reference_dimension"] == {
        "M": 3, "N": 50, "semantic_dimension": 1751,
        "runner_agent_count": 3,
    }, "shared semantic reference dimension")
    _assert(mapping["shared_schema"]["semantic_state_shape"] == ["E", "S"] and
            mapping["shared_schema"]["runner_transport_shape"] == ["E", "M", "S"] and
            mapping["shared_schema"]["critic_input_shape"] == ["B", "S"],
            "shared semantic/transport/critic shapes")

    action = mapping["action_contract"]
    _assert(len(action) == 10 and action["contract_version"] ==
            "event_gated_action_contract_v1", "action descriptor binding")
    _assert(action["num_agents"] == "scale_contract.M" and
            action["action_dimension"] == "scale_contract.N + 1" and
            action["noop_raw_id"] == "scale_contract.N" and
            action["noop_decoded_value"] == -1,
            "action/scale invariants")
    _assert(mapping["model_structure"]["actor_hidden_sizes"] == [256, 256] and
            mapping["model_structure"]["critic_hidden_sizes"] == [256, 256],
            "model hidden-size binding")
    _assert("hidden_sizes_critic" not in mapping["model_structure"],
            "unconsumed YAML critic identity leaked")
    terminal = mapping["actor_schema"]["terminal_row_contract"]
    _assert(terminal["semantic_action_count"] == 0 and
            terminal["storage_row_present"] is False and
            terminal["forced_policy_action_id"] == -1 and
            terminal["resolver_consumption"] is False,
            "terminal zero-action/no-row binding")
    terminal_shared = mapping["shared_schema"]["terminal_shared_state_contract"]
    _assert(terminal_shared["pre_reset_sidecar_required"] is True and
            terminal_shared["storage_row_present"] is False and
            terminal_shared["critic_buffer_ordering"] ==
            "terminal_sidecar_before_new_episode_initial_row",
            "terminal pre-reset critic-sidecar binding")


def test_v3_ownership_driven_build_and_tamper_rejection() -> None:
    aggregate = AGGREGATE.get_assignment_event_profile_schema_descriptor(
        scale_contract=_scale()
    )
    ownership = aggregate["v3_section_ownership"]
    records = ownership["records"]
    _assert(len(records) == 19 and ownership["section_order"] == SECTION_NAMES,
            "19 ownership records/order")
    allowed_basenames = {
        "assignment_profile_contract",
        "assignment_event_profile_schema_contract",
        "assignment_lifecycle_transition_contract",
        "assignment_event_contract",
        "assignment_mrta_contract",
        "assignment_team_reward_contract",
        "assignment_event_gated_diagnostics_contract",
    }
    for expected_order, record in enumerate(records, 1):
        _assert(record["order"] == expected_order, "ownership row order")
        _assert(record["section_name"] == SECTION_NAMES[expected_order - 1],
                "ownership section order")
        _assert(record["owner_module"] in allowed_basenames,
                "ownership canonical basename")
        canonical_owner = f"{PACKAGE}.{record['owner_module']}"
        _assert(canonical_owner in sys.modules,
                f"owner not resolved canonically: {canonical_owner}")
        _assert(record["projection_mode"] in
                ("inline_owned_mapping", "canonical_reference"),
                "ownership projection mode")
        AGGREGATE.validate_event_profile_v3_section_ownership_record(
            record,
            aggregate_descriptor=aggregate,
        )

        for field_name, replacement in (
            ("owner_module", "not_an_authority"),
            ("owner_contract_version", "wrong_version"),
            ("descriptor_key_path", "wrong.path"),
            ("projection_mode", "wrong_mode"),
        ):
            tampered_record = dict(record)
            tampered_record[field_name] = replacement
            _expect_error(
                lambda item=tampered_record: (
                    AGGREGATE.validate_event_profile_v3_section_ownership_record(
                        item,
                        aggregate_descriptor=aggregate,
                    )
                ),
                AGGREGATE.AssignmentEventProfileSchemaContractError,
            )

    original_getter = V3.get_assignment_event_profile_schema_descriptor
    original_builder = V3.build_assignment_event_profile_schema_descriptor
    try:
        for field_name, replacement in (
            ("owner_module", "not_an_authority"),
            ("owner_contract_version", "wrong_version"),
            ("descriptor_key_path", "wrong.path"),
            ("projection_mode", "wrong_mode"),
        ):
            tampered = _deep_mutable(aggregate)
            tampered_records = list(tampered["v3_section_ownership"]["records"])
            tampered_record = dict(tampered_records[0])
            tampered_record[field_name] = replacement
            tampered_records[0] = tampered_record
            tampered["v3_section_ownership"]["records"] = tuple(tampered_records)
            V3.get_assignment_event_profile_schema_descriptor = (
                lambda *, scale_contract, value=tampered: value
            )
            V3.build_assignment_event_profile_schema_descriptor = (
                lambda *, scale_contract, value=tampered: value
            )
            _expect_error(
                lambda: V3.build_interface_semantic_descriptor_v3(
                    scale_contract=_scale()
                ),
                V3.AssignmentCheckpointV3ContractError,
            )
        V3.build_assignment_event_profile_schema_descriptor = original_builder
        tampered_content = _deep_mutable(aggregate)
        tampered_content["actor_schema"]["scope"] = (
            "equal_shape_but_noncanonical_actor_semantics"
        )
        V3.get_assignment_event_profile_schema_descriptor = (
            lambda *, scale_contract, value=tampered_content: value
        )
        _expect_error(
            lambda: V3.build_interface_semantic_descriptor_v3(
                scale_contract=_scale()
            ),
            V3.AssignmentCheckpointV3ContractError,
        )
    finally:
        V3.get_assignment_event_profile_schema_descriptor = original_getter
        V3.build_assignment_event_profile_schema_descriptor = original_builder

    wrong_content = _replace(
        _v3_mapping(), "actor_schema.scope", "equal_shape_wrong_semantics"
    )
    _expect_error(
        lambda: V3.AssignmentCheckpointContractManifestV3.from_mapping(
            wrong_content
        ),
        V3.AssignmentCheckpointV3ContractError,
    )
    canonical_mapping = _v3_mapping()
    for section_name in SECTION_NAMES:
        drifted = copy.deepcopy(canonical_mapping)
        drifted[section_name] = _drift_first_leaf(drifted[section_name])
        _expect_error(
            lambda value=drifted: V3.AssignmentCheckpointContractManifestV3.from_mapping(value),
            V3.AssignmentCheckpointV3ContractError,
        )


def _assert_hash_changes_or_validation_fails(
    original_hash: str,
    mapping: Mapping[str, Any],
    message: str,
) -> None:
    try:
        changed_hash = V3.compute_assignment_checkpoint_manifest_v3_sha256(mapping)
    except V3.AssignmentCheckpointV3ContractError:
        return
    _assert(changed_hash != original_hash, message)


def test_v3_actor_shared_semantic_hash_sensitivity() -> None:
    mapping = _v3_mapping()
    original_hash = V3.compute_assignment_checkpoint_manifest_v3_sha256(mapping)
    mutations = (
        ("actor_schema.blocks.0.normalization_rule", "different_normalization"),
        ("shared_schema.blocks.0.semantic_source", "different_shared_source"),
        ("actor_schema.normalization_contract.position_length_denominator_source",
         "different_scale_source"),
        ("actor_schema.terminal_row_contract.storage_row_present", True),
        ("shared_schema.runner_transport_mode", "different_transport"),
        ("actor_schema.scope", "same_dimension_different_semantic_literal"),
    )
    for path, value in mutations:
        _assert_hash_changes_or_validation_fails(
            original_hash, _replace(mapping, path, value),
            f"semantic mutation did not affect hash: {path}",
        )


def test_v3_unresolved_inventory_and_ready_fail_closed() -> None:
    mapping = _v3_mapping()
    readiness = mapping["runtime_readiness_contract"]
    inventory = readiness["unresolved_parameter_inventory_projection"]
    _assert(inventory["unresolved_parameter_order"] ==
            list(UNRESOLVED_PARAMETER_ORDER), "exact 11 unresolved order")
    references = inventory["unresolved_parameter_references"]
    _assert(len(references) == 11, "no twelfth unresolved parameter")
    reference_keys = (
        "name", "triple_owner_module", "triple_owner_contract_version",
        "triple_descriptor_key_path", "expected_concrete_type", "unit",
        "legal_domain",
    )
    _assert(inventory["reference_record_field_order"] == list(reference_keys),
            "unresolved reference record inventory")
    for expected_name, reference in zip(
        UNRESOLVED_PARAMETER_ORDER, references, strict=True
    ):
        _assert(tuple(reference) == reference_keys, "unresolved reference keys")
        _assert(reference["name"] == expected_name, "unresolved name order")
        _assert(reference["triple_owner_module"].startswith(f"{PACKAGE}."),
                "unresolved canonical owner module")
        for key in (
            "triple_owner_contract_version", "triple_descriptor_key_path",
            "expected_concrete_type", "unit", "legal_domain",
        ):
            _assert(type(reference[key]) is str and reference[key],
                    f"unresolved identity missing: {expected_name}.{key}")

    serialized = json.dumps(mapping, sort_keys=True)
    _assert('"TBD"' not in serialized and '"tbd"' not in serialized,
            "bare TBD leaked into V3")
    bare_tbd = copy.deepcopy(mapping)
    bare_tbd["runtime_readiness_contract"][
        "unresolved_parameter_inventory_projection"
    ]["unresolved_parameter_references"][0]["legal_domain"] = "TBD"
    _expect_error(
        lambda: V3.AssignmentCheckpointContractManifestV3.from_mapping(bare_tbd),
        V3.AssignmentCheckpointV3ContractError,
    )
    _assert(readiness["unresolved_parameter_resolution_status"] ==
            "all_11_unresolved", "unresolved status")
    _assert(readiness["runtime_execution_authorized"] is False and
            readiness["checkpoint_weight_use_authorized"] is False,
            "interface-only authorization boundary")

    original_hash = V3.compute_assignment_checkpoint_manifest_v3_sha256(mapping)
    reordered = copy.deepcopy(mapping)
    reordered_inventory = reordered["runtime_readiness_contract"][
        "unresolved_parameter_inventory_projection"
    ]
    reordered_inventory["unresolved_parameter_order"] = list(
        reversed(reordered_inventory["unresolved_parameter_order"])
    )
    _assert_hash_changes_or_validation_fails(
        original_hash, reordered, "unresolved order did not affect semantics"
    )
    domain_drift = copy.deepcopy(mapping)
    domain_drift["runtime_readiness_contract"][
        "unresolved_parameter_inventory_projection"
    ]["unresolved_parameter_references"][0]["legal_domain"] = "value >= 0"
    _expect_error(
        lambda: V3.AssignmentCheckpointContractManifestV3.from_mapping(domain_drift),
        V3.AssignmentCheckpointV3ContractError,
    )
    _assert(mapping["reward_contract"]["contract_version"] ==
            "assignment_team_reward_contract_v1", "reward v1 unchanged")

    resolved = {
        "top_k_tasks_per_robot": 5,
        "local_robot_cap": 3,
        "local_task_cap": 20,
        "pair_abs_threshold": 1.0,
        "pair_rel_threshold": 0.1,
        "component_abs_threshold": 1.0,
        "component_rel_threshold": 0.1,
        "transfer_penalty": 0.0,
        "rejection_penalty_scale": 0.0,
        "alignment_time_constant": (1.0, 1.0, 1.0),
        "assignment_retry_cadence": 1,
    }
    ready_cases = (
        (None, None, None, "all_11_unresolved", "deferred"),
        (
            resolved,
            None,
            None,
            "all_11_caller_values_present_but_unverified_and_not_authorized",
            "deferred",
        ),
        (
            resolved,
            {"runtime_execution_evidence": "caller_supplied"},
            {"actor": "caller_supplied"},
            "all_11_caller_values_present_but_unverified_and_not_authorized",
            "caller_inventory_present_but_phase_a_state_dict_inventory_deferred",
        ),
    )
    for (
        resolved_parameters,
        runtime_evidence,
        state_dict_inventory,
        expected_parameter_status,
        expected_inventory_status,
    ) in ready_cases:
        exc = _expect_error(
            lambda values=resolved_parameters, evidence=runtime_evidence,
            inventory_value=state_dict_inventory: V3.build_checkpoint_ready_v3(
                scale_contract=_scale(), resolved_parameters=values,
                runtime_evidence=evidence,
                state_dict_inventory=inventory_value,
            ),
            V3.CheckpointReadyManifestNotAuthorizedError,
            "checkpoint_ready_manifest", "interface_only",
        )
        _assert(
            exc.requested_kind is
            V3.AssignmentCheckpointManifestKind.CHECKPOINT_READY_MANIFEST,
            "ready rejection requested kind",
        )
        _assert(exc.runtime_readiness == "interface_only",
                "ready rejection runtime boundary")
        _assert(exc.parameter_status == expected_parameter_status,
                "ready rejection parameter status")
        _assert(exc.state_dict_inventory_status == expected_inventory_status,
                "ready rejection inventory status")
        _assert(bool(exc.missing_runtime_evidence_categories),
                "ready rejection evidence categories")
        text = str(exc).lower()
        for fragment in ("parameter", "runtime evidence", "state-dict"):
            _assert(fragment in text, f"ready rejection missing {fragment!r}")


def test_v3_canonical_bytes_numeric_and_provenance() -> None:
    manifest = _v3_manifest()
    mapping = manifest.to_mapping()
    canonical = V3.canonical_assignment_checkpoint_manifest_v3_bytes(manifest)
    fingerprint = V3.compute_assignment_checkpoint_manifest_v3_sha256(manifest)
    _assert(canonical == json.dumps(
        json.loads(canonical.decode("utf-8")), ensure_ascii=True,
        allow_nan=False, separators=(",", ":"), sort_keys=True,
    ).encode("utf-8"), "canonical JSON rules")
    _assert(not canonical.startswith(b"\xef\xbb\xbf") and
            not canonical.endswith(b"\n"), "no BOM/newline")
    _assert(re.fullmatch(r"[0-9a-f]{64}", fingerprint) is not None,
            "lowercase V3 SHA-256")
    _assert(fingerprint == V3_INTERFACE_SHA256_FIXTURE,
            "frozen V3 interface semantic fingerprint drift")
    _assert(hashlib.sha256(canonical).hexdigest() == fingerprint,
            "V3 fingerprint binds canonical bytes")
    _assert(DISPATCH.canonical_assignment_checkpoint_manifest_bytes(mapping) ==
            canonical, "dispatcher exact V3 canonical bytes")
    _assert(DISPATCH.compute_assignment_checkpoint_manifest_sha256(mapping) ==
            fingerprint, "dispatcher exact V3 fingerprint")

    reordered = _reverse_mapping_insertion(mapping)
    _assert(V3.canonical_assignment_checkpoint_manifest_v3_bytes(reordered) ==
            canonical, "V3 mapping insertion-order determinism")
    pretty = json.loads(json.dumps(mapping, indent=4, ensure_ascii=True))
    _assert(V3.canonical_assignment_checkpoint_manifest_v3_bytes(pretty) ==
            canonical, "pretty JSON does not affect V3 canonical bytes")

    reordered_semantics = V3.build_interface_semantic_descriptor_v3(
        scale_contract=_scale(reversed_agents=True)
    )
    _assert(V3.compute_assignment_checkpoint_manifest_v3_sha256(
        reordered_semantics
    ) != fingerprint, "semantic tuple order must affect V3 hash")

    for numeric in (float("nan"), float("inf"), float("-inf")):
        invalid = _replace(mapping, "scale.scene_env_spacing", numeric)
        _expect_error(
            lambda value=invalid: V3.canonical_assignment_checkpoint_manifest_v3_bytes(value),
            V3.AssignmentCheckpointV3ContractError,
        )
    bool_as_int = _replace(
        mapping, "runtime_readiness_contract.runtime_execution_authorized", 0
    )
    _expect_error(
        lambda: V3.AssignmentCheckpointContractManifestV3.from_mapping(bool_as_int),
        V3.AssignmentCheckpointV3ContractError,
    )

    for key, value in (
        ("absolute_path", r"C:\\checkpoint\\model.pt"),
        ("timestamp", "2026-08-07T12:00:00"),
        ("host", "machine-a"),
        ("user", "someone"),
        ("pid", 1234),
    ):
        contaminated = copy.deepcopy(mapping)
        contaminated[key] = value
        _expect_error(
            lambda item=contaminated: V3.AssignmentCheckpointContractManifestV3.from_mapping(item),
            V3.AssignmentCheckpointV3ContractError,
        )

def test_dispatcher_matrix_and_interface_semantics() -> None:
    mapping = _v3_mapping()
    parsed = DISPATCH.parse_assignment_checkpoint_manifest(mapping)
    _assert(type(parsed) is V3.AssignmentCheckpointContractManifestV3,
            "dispatcher V3 native type")
    _assert(parsed.to_mapping() == mapping, "dispatcher V3 exact mapping")
    decision = DISPATCH.evaluate_assignment_checkpoint_semantics(
        mapping,
        purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        current_manifest=mapping,
    )
    _assert(type(decision) is V3.AssignmentCheckpointV3SemanticDecision,
            "V3 semantic decision type")
    decision_mapping = decision.to_mapping()
    _assert(decision_mapping["schema_valid"] is True and
            decision_mapping["interface_semantics_valid"] is True and
            decision_mapping["runtime_ready"] is False and
            decision_mapping["weight_use_authorized"] is False,
            "V3 interface-only semantic result")

    ready_claim = copy.deepcopy(mapping)
    ready_claim["manifest_kind"] = "checkpoint_ready_manifest"
    _expect_error(
        lambda: DISPATCH.parse_assignment_checkpoint_manifest(ready_claim),
        V3.CheckpointReadyManifestNotAuthorizedError,
    )
    unknown_kind = copy.deepcopy(mapping)
    unknown_kind["manifest_kind"] = "unknown_manifest_kind"
    _expect_error(
        lambda: DISPATCH.parse_assignment_checkpoint_manifest(unknown_kind),
        V3.UnsupportedCheckpointManifestKindError,
    )
    enum_kind = copy.deepcopy(mapping)
    enum_kind["manifest_kind"] = (
        V3.AssignmentCheckpointManifestKind.INTERFACE_SEMANTIC_DESCRIPTOR
    )
    _expect_error(
        lambda: DISPATCH.parse_assignment_checkpoint_manifest(enum_kind),
        V3.UnsupportedCheckpointManifestKindError,
        "exact string",
    )
    missing_root = copy.deepcopy(mapping)
    missing_root.pop("diagnostics_contract")
    extra_root = copy.deepcopy(mapping)
    extra_root["unexpected_section"] = {}
    missing_nested = copy.deepcopy(mapping)
    missing_nested["actor_schema"].pop("scope")
    extra_nested = copy.deepcopy(mapping)
    extra_nested["actor_schema"]["unexpected_field"] = "forbidden"
    for malformed in (missing_root, extra_root, missing_nested, extra_nested):
        _expect_error(
            lambda value=malformed: DISPATCH.parse_assignment_checkpoint_manifest(value),
            V3.CheckpointManifestSchemaError,
        )
    _expect_error(
        lambda: DISPATCH.parse_assignment_checkpoint_manifest({}),
        V3.UnsupportedCheckpointManifestVersionError,
    )
    _expect_error(
        lambda: DISPATCH.parse_assignment_checkpoint_manifest({
            "manifest_format_version": "assignment_checkpoint_contract_v99"
        }),
        V3.UnsupportedCheckpointManifestVersionError,
    )
    for value in (None, [], "manifest"):
        _expect_error(
            lambda item=value: DISPATCH.parse_assignment_checkpoint_manifest(item),
            V3.CheckpointManifestInputError,
        )
    _expect_error(
        lambda: DISPATCH.evaluate_assignment_checkpoint_semantics(
            V2_CONTRACT_C_MAPPING,
            purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
        ),
        V3.CheckpointManifestInputError,
        "current_manifest",
    )

    # Make the visible M/N/action/actor/shared/hidden-size values match V2.
    # Family comparison must run before attempting to validate this deliberately
    # shape-matched cross-family current mapping.
    equal_shape_v3 = copy.deepcopy(mapping)
    equal_shape_v3["actor_schema"]["reference_dimension"]["dimension"] = 1059
    equal_shape_v3["shared_schema"]["reference_dimension"][
        "semantic_dimension"
    ] = 3183
    _assert(equal_shape_v3["scale"]["M"] == V2_CONTRACT_C_MAPPING["scale"]["M"] and
            equal_shape_v3["scale"]["N"] == V2_CONTRACT_C_MAPPING["scale"]["N"],
            "equal-shape test M/N setup")
    _assert(equal_shape_v3["model_structure"]["actor_hidden_sizes"] ==
            V2_CONTRACT_C_MAPPING["model_structure"]["actor_hidden_sizes"],
            "equal-shape hidden-size setup")
    _expect_error(
        lambda: DISPATCH.evaluate_assignment_checkpoint_semantics(
            V2_CONTRACT_C_MAPPING,
            purpose=V2.CompatibilityPurpose.NORMAL_EVALUATION,
            current_manifest=equal_shape_v3,
        ),
        V3.CheckpointManifestFamilyMismatchError,
        "families differ", "equal tensor or observation shapes",
    )
    _expect_error(
        lambda: DISPATCH.evaluate_assignment_checkpoint_semantics(
            mapping,
            purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
            current_manifest=V2_CONTRACT_C_MAPPING,
        ),
        V3.CheckpointManifestFamilyMismatchError,
        "families differ", "equal tensor or observation shapes",
    )

    semantically_different = V3.build_interface_semantic_descriptor_v3(
        scale_contract=_scale(reversed_agents=True)
    ).to_mapping()
    mismatch = DISPATCH.evaluate_assignment_checkpoint_semantics(
        mapping,
        purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        current_manifest=semantically_different,
    )
    _assert(
        mismatch.schema_valid is True and
        mismatch.family_match is True and
        mismatch.interface_semantics_valid is False and
        mismatch.semantic_fingerprint_match is False and
        mismatch.runtime_ready is False and
        mismatch.weight_use_authorized is False and
        mismatch.classification == "interface_semantic_mismatch",
        "valid V3 semantic mismatch decision",
    )

    manifest = _v3_manifest()
    manifest_kwargs = {
        field.name: getattr(manifest, field.name)
        for field in fields(V3.AssignmentCheckpointContractManifestV3)
    }

    class ForgedReadyManifest(V3.AssignmentCheckpointContractManifestV3):
        def to_mapping(self) -> dict[str, object]:
            forged = super().to_mapping()
            forged["manifest_kind"] = "checkpoint_ready_manifest"
            return forged

    forged_ready = ForgedReadyManifest(**manifest_kwargs)
    for operation in (
        lambda: V3.canonical_assignment_checkpoint_manifest_v3_bytes(forged_ready),
        lambda: V3.evaluate_assignment_checkpoint_manifest_v3_semantics(
            forged_ready,
            purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        ),
    ):
        _expect_error(
            operation,
            V3.CheckpointReadyManifestNotAuthorizedError,
            "checkpoint-ready", "not authorized",
        )

    class ForgedHostManifest(V3.AssignmentCheckpointContractManifestV3):
        def to_mapping(self) -> dict[str, object]:
            forged = super().to_mapping()
            forged["host"] = "forbidden-host"
            return forged

    forged_host = ForgedHostManifest(**manifest_kwargs)
    for operation in (
        lambda: V3.canonical_assignment_checkpoint_manifest_v3_bytes(forged_host),
        lambda: V3.evaluate_assignment_checkpoint_manifest_v3_semantics(
            forged_host,
            purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        ),
    ):
        _expect_error(operation, V3.CheckpointManifestSchemaError)

    for purpose in (
        "training", "continuation", "evaluation", "playback", "weight_load"
    ):
        _expect_error(
            lambda value=purpose: V3.evaluate_assignment_checkpoint_manifest_v3_semantics(
                mapping, purpose=value
            ),
            V3.CheckpointManifestPurposeError,
        )
        _expect_error(
            lambda value=purpose: DISPATCH.evaluate_assignment_checkpoint_semantics(
                mapping, purpose=value
            ),
            V3.CheckpointManifestPurposeError,
        )


def _called_name(node: ast.Call) -> str:
    parts: list[str] = []
    current: ast.expr = node.func
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def test_no_io_static_and_runtime_spies() -> None:
    forbidden_exact_calls = {
        "open", "io.open", "os.open", "os.listdir", "os.scandir", "os.walk",
        "torch.load", "torch.save", "load_state_dict",
    }
    forbidden_call_suffixes = (
        ".open", ".read_text", ".write_text", ".read_bytes", ".write_bytes",
        ".glob", ".rglob", ".iterdir", ".listdir", ".scandir", ".walk",
        ".load_state_dict",
    )
    forbidden_import_roots = ("torch", "harl", "isaaclab.app", "numpy")
    for path in (MODULE_PATHS[V3_KEY], MODULE_PATHS[DISPATCH_KEY]):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imports.add(node.module)
        _assert(
            not any(
                name == root or name.startswith(f"{root}.")
                for name in imports
                for root in forbidden_import_roots
            ),
            f"runtime import in {path.name}",
        )
        calls = {_called_name(node) for node in ast.walk(tree)
                 if isinstance(node, ast.Call)}
        forbidden_calls = {
            name for name in calls
            if name in forbidden_exact_calls or
            any(name.endswith(suffix) for suffix in forbidden_call_suffixes)
        }
        _assert(not forbidden_calls,
                f"I/O/runtime call in {path.name}: {forbidden_calls}")

    def blocked(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("I/O attempted by pure A4a facade")

    patchers = [
        mock.patch.object(builtins, "open", side_effect=blocked),
        mock.patch.object(io, "open", side_effect=blocked),
        mock.patch.object(Path, "open", side_effect=blocked),
        mock.patch.object(Path, "read_text", side_effect=blocked),
        mock.patch.object(Path, "write_text", side_effect=blocked),
        mock.patch.object(Path, "read_bytes", side_effect=blocked),
        mock.patch.object(Path, "write_bytes", side_effect=blocked),
        mock.patch.object(Path, "glob", side_effect=blocked),
        mock.patch.object(Path, "rglob", side_effect=blocked),
        mock.patch.object(Path, "iterdir", side_effect=blocked),
        mock.patch.object(os, "open", side_effect=blocked),
        mock.patch.object(os, "listdir", side_effect=blocked),
        mock.patch.object(os, "scandir", side_effect=blocked),
        mock.patch.object(os, "walk", side_effect=blocked),
    ]
    torch_module = sys.modules.get("torch")
    if torch_module is not None:
        patchers.extend((
            mock.patch.object(torch_module, "load", side_effect=blocked),
            mock.patch.object(torch_module, "save", side_effect=blocked),
        ))

    mapping = _v3_mapping()
    with contextlib.ExitStack() as stack:
        for patcher in patchers:
            stack.enter_context(patcher)
        built = V3.build_interface_semantic_descriptor_v3(scale_contract=_scale())
        parsed = DISPATCH.parse_assignment_checkpoint_manifest(mapping)
        V3.canonical_assignment_checkpoint_manifest_v3_bytes(built)
        DISPATCH.compute_assignment_checkpoint_manifest_sha256(mapping)
        DISPATCH.evaluate_assignment_checkpoint_semantics(
            parsed.to_mapping(),
            purpose=V3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT,
        )


def test_clean_child_deterministic_side_effects() -> None:
    expected_hash = V3.compute_assignment_checkpoint_manifest_v3_sha256(_v3_manifest())
    child = f"""
import contextlib,importlib.util,io,json,logging,os,pathlib,random,sys
from types import ModuleType
root=pathlib.Path({str(REPO_ROOT)!r}); scan=pathlib.Path({str(SCAN_SOURCE)!r}); package={PACKAGE!r}
for name,path in (("isaaclab_tasks",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'),
                  ("isaaclab_tasks.direct",root/'source'/'isaaclab_tasks'/'isaaclab_tasks'/'direct'),
                  (package,scan)):
    m=ModuleType(name); m.__package__=name; m.__path__=[str(path)]; sys.modules[name]=m
def load(key,path):
    spec=importlib.util.spec_from_file_location(key,path); m=importlib.util.module_from_spec(spec)
    sys.modules[key]=m; old=sys.dont_write_bytecode
    try: sys.dont_write_bytecode=True; spec.loader.exec_module(m)
    finally: sys.dont_write_bytecode=old
    return m
profile=load(package+'.assignment_profile_contract',scan/'assignment_profile_contract.py')
registry_before=repr(profile.get_assignment_profile_registry())
import torch
cwd=os.getcwd(); env=dict(os.environ); syspath=tuple(sys.path)
handlers=tuple(logging.getLogger().handlers); level=logging.getLogger().level
def logger_state():
    return tuple(sorted((name,type(value).__name__,getattr(value,'level',None),
      getattr(value,'propagate',None),getattr(value,'disabled',None),
      tuple(id(handler) for handler in getattr(value,'handlers',())))
      for name,value in logging.Logger.manager.loggerDict.items()))
named_loggers=logger_state()
py=random.getstate(); trng=torch.random.get_rng_state().clone(); numpy_before='numpy' in sys.modules
modules_before=set(sys.modules); files=tuple(pathlib.Path.cwd().iterdir())
out=io.StringIO(); err=io.StringIO()
with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
    v3=load(package+'.assignment_checkpoint_contract_v3',scan/'assignment_checkpoint_contract_v3.py')
    dispatch=load(package+'.assignment_checkpoint_semantic_dispatch',scan/'assignment_checkpoint_semantic_dispatch.py')
    aggregate=sys.modules[package+'.assignment_event_profile_schema_contract']
    scale=aggregate.build_event_gated_scale_contract(M=3,N=50,
      ordered_agent_names=('robot_0','robot_1','robot_2'),ordered_task_ids=tuple(range(50)),
      scene_env_spacing=12.0,sim_dt_seconds=0.01,control_decimation=4,
      physical_control_step_seconds=0.04,episode_time_limit_seconds=40.01,
      episode_horizon_steps=1001)
    manifest=v3.build_interface_semantic_descriptor_v3(scale_contract=scale)
    mapping=manifest.to_mapping(); parsed=dispatch.parse_assignment_checkpoint_manifest(mapping)
    fingerprint=dispatch.compute_assignment_checkpoint_manifest_sha256(mapping)
    decision=dispatch.evaluate_assignment_checkpoint_semantics(
      parsed.to_mapping(),purpose=v3.AssignmentCheckpointV3Purpose.INTERFACE_AUDIT)
new=set(sys.modules)-modules_before
result={{'hash':fingerprint,'stdout':out.getvalue(),'stderr':err.getvalue(),
 'cwd':os.getcwd()==cwd,'env':dict(os.environ)==env,'path':tuple(sys.path)==syspath,
 'handlers':tuple(logging.getLogger().handlers)==handlers,'level':logging.getLogger().level==level,
 'named_loggers':logger_state()==named_loggers,
 'python_rng':random.getstate()==py,'torch_rng':torch.equal(torch.random.get_rng_state(),trng),
 'numpy':('numpy' in sys.modules)==numpy_before,'files':tuple(pathlib.Path.cwd().iterdir())==files,
 'registry':repr(profile.get_assignment_profile_registry())==registry_before,
 'bare':not any(name in sys.modules for name in ('assignment_checkpoint_contract_v3','assignment_checkpoint_semantic_dispatch')),
 'source_keys':all(len([name for name,value in sys.modules.items() if getattr(value,'__file__',None)
   and pathlib.Path(value.__file__).resolve()==(scan/(base+'.py')).resolve()])==1
   for base in ('assignment_checkpoint_contract_v3','assignment_checkpoint_semantic_dispatch')),
 'forbidden':not any(name.startswith(('omni','isaaclab.app','harl')) or
   any(token in name for token in ('assignment_harl_training','scan_mobile_manipulator_env')) for name in new),
 'decision':decision.schema_valid and decision.interface_semantics_valid and
   not decision.runtime_ready and not decision.weight_use_authorized}}
print(json.dumps(result,sort_keys=True))
"""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = subprocess.run(
            [sys.executable, "-c", child], cwd=temp_dir,
            capture_output=True, text=True, check=False,
        )
    _assert(result.returncode == 0, result.stderr)
    payload = json.loads(result.stdout)
    _assert(payload.pop("hash") == expected_hash, "clean-child V3 hash drift")
    _assert(payload.pop("stdout") == "" and payload.pop("stderr") == "",
            "clean-child import/build output")
    for key, value in payload.items():
        _assert(value is True, f"clean-child side effect: {key}")


TESTS: tuple[tuple[str, Callable[[], None]], ...] = (
    ("canonical_module_identity", test_canonical_module_identity),
    ("v2_frozen_canonical_goldens", test_v2_frozen_canonical_goldens),
    ("v2_direct_dispatch_compatibility_goldens",
     test_v2_direct_dispatch_compatibility_goldens),
    ("v2_fingerprint_and_continuation_classification_order",
     test_v2_fingerprint_and_continuation_classification_order),
    ("v3_root_typed_schema_and_bindings", test_v3_root_typed_schema_and_bindings),
    ("v3_ownership_driven_build_and_tamper_rejection",
     test_v3_ownership_driven_build_and_tamper_rejection),
    ("v3_actor_shared_semantic_hash_sensitivity",
     test_v3_actor_shared_semantic_hash_sensitivity),
    ("v3_unresolved_inventory_and_ready_fail_closed",
     test_v3_unresolved_inventory_and_ready_fail_closed),
    ("v3_canonical_bytes_numeric_and_provenance",
     test_v3_canonical_bytes_numeric_and_provenance),
    ("dispatcher_matrix_and_interface_semantics",
     test_dispatcher_matrix_and_interface_semantics),
    ("no_io_static_and_runtime_spies", test_no_io_static_and_runtime_spies),
    ("clean_child_deterministic_side_effects",
     test_clean_child_deterministic_side_effects),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    results: list[dict[str, object]] = []
    for name, test in TESTS:
        try:
            test()
        except Exception as exc:
            results.append({
                "name": name,
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
            })
        else:
            results.append({"name": name, "status": "passed"})
    passed = sum(item["status"] == "passed" for item in results)
    payload = {
        "suite": "assignment_checkpoint_semantic_dispatch",
        "passed": passed,
        "total": len(results),
        "v2_legacy_canonical_byte_length": V2_LEGACY_BYTE_LENGTH,
        "v2_legacy_sha256": V2_LEGACY_SHA256,
        "v2_contract_c_canonical_byte_length": V2_CONTRACT_C_BYTE_LENGTH,
        "v2_contract_c_sha256": V2_CONTRACT_C_SHA256,
        "v3_interface_sha256": (
            V3_INTERFACE_SHA256_FIXTURE
            if passed == len(results) else None
        ),
        "results": results,
    }
    if args.json:
        print(json.dumps(payload, sort_keys=True))
    else:
        for item in results:
            suffix = "" if item["status"] == "passed" else f": {item['error']}"
            print(f"{item['status'].upper():6} {item['name']}{suffix}")
        print(f"{passed}/{len(results)} passed")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
