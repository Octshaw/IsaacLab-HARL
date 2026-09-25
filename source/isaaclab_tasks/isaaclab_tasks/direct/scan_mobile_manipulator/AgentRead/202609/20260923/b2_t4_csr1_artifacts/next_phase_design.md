# Proposed next executable phase — B2-T4-CKPT1

Status: DESIGN ONLY / NOT AUTHORIZED.

## Purpose

Implement complete optimization-continuation checkpoint state before any runtime attempt. Extend the native assignment checkpoint contract to atomically save and strictly restore all ordered actor optimizer states, critic optimizer state, ValueNorm state, and the completed update/episode progression needed by linear LR decay. Preserve the existing semantic manifest, tensor inventory, digest, completion-marker-last, and all-or-rollback rules.

## Static/pure acceptance first

- Exact inventories for actor/critic weights, all Adam states, ValueNorm, progression counter, and actor ordering.
- Failure injection before and after each artifact and before the completion marker.
- Strict CPU-only roundtrip using small synthetic modules; compare every parameter, optimizer moment/step, ValueNorm field, and counter.
- Negative tests for missing, extra, reordered, corrupt, wrong-shape, wrong-dtype, wrong-contract, and partial artifacts.
- No Isaac, CUDA, learner construction, or checkpoint runtime until a later explicit authorization.

## Later bounded runtime design

After implementation review and separate authorization: fresh learner -> short valid training -> quiescent post-update save -> process exit -> fresh process/environment -> strict load -> state equality -> several valid post-load updates -> continuity and quiescence -> exit. This is checkpoint-focused and does not repeat 160 transactions or require PPQ/Layer-A/RACQ forensic aggregation.

## Nonclaims

This design is not authorization, does not establish checkpoint continuation, does not authorize R15, and does not authorize paper-scale training or evaluation/playback.
