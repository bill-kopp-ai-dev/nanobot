# Percival TUI and packaging source lineage

**Candidate revision:** `51a5d3821bce6082bd448dcd9cd8b9e213cad95b`
**Files covered:** 91
**Attributed contiguous hunks:** 2516
**Method:** Git `blame --line-porcelain`, preserving upstream commit attribution and local edits. Coverage includes TUI source, package/relinking/release files, shared client-events, launcher and packaging tests; generated `tui/dist/` artifacts are excluded. This is a technical provenance map, not a legal opinion or B13 approval.

**Historical snapshot:** this map records files present at candidate `51a5d382`. Bill's 2026-10-30 decision to remove `tui/SOURCE_OFFER.md` and `tui/RELINKING.md` is recorded in the active Stage-2 tracker; their historical attribution rows below are retained as provenance, not current release requirements.

| File | Lines | Commit | Author recorded by Git | Commit subject recorded by Git |
|---|---:|---|---|---|
| `nanobot/cli/tui_launcher.py` | 1-11 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 12-12 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 13-14 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 15-15 | `cfc1fae8b5f6` | Xubin Ren | feat(cli): expose nanobot process identities |
| `nanobot/cli/tui_launcher.py` | 16-18 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 19-19 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `nanobot/cli/tui_launcher.py` | 20-20 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `nanobot/cli/tui_launcher.py` | 21-21 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 22-23 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 24-24 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 25-25 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 26-26 | `f9d449ef6c6d` | chengyongru | refactor(webui): isolate websocket application orchestration (#5548) |
| `nanobot/cli/tui_launcher.py` | 27-27 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 28-30 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 31-35 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 36-39 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `nanobot/cli/tui_launcher.py` | 40-41 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `nanobot/cli/tui_launcher.py` | 42-43 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 44-45 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `nanobot/cli/tui_launcher.py` | 46-46 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 47-47 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `nanobot/cli/tui_launcher.py` | 48-48 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 49-49 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 50-56 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 57-57 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `nanobot/cli/tui_launcher.py` | 58-58 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `nanobot/cli/tui_launcher.py` | 59-59 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 60-60 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `nanobot/cli/tui_launcher.py` | 61-62 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `nanobot/cli/tui_launcher.py` | 63-63 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 64-64 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 65-66 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 67-67 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 68-68 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 69-70 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 71-72 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 73-74 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 75-75 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 76-79 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `nanobot/cli/tui_launcher.py` | 80-80 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 81-81 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 82-83 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 84-84 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `nanobot/cli/tui_launcher.py` | 85-89 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 90-94 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `nanobot/cli/tui_launcher.py` | 95-96 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 97-101 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 102-105 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 106-115 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 116-122 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `nanobot/cli/tui_launcher.py` | 123-131 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 132-132 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 133-133 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 134-134 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 135-138 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 139-140 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 141-141 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 142-157 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 158-162 | `14c5607e5e79` | Xubin Ren | fix(tui): enforce supported platform boundaries |
| `nanobot/cli/tui_launcher.py` | 163-163 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 164-171 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `nanobot/cli/tui_launcher.py` | 172-172 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 173-173 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `nanobot/cli/tui_launcher.py` | 174-178 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 179-181 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `nanobot/cli/tui_launcher.py` | 182-184 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 185-186 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `nanobot/cli/tui_launcher.py` | 187-191 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `nanobot/cli/tui_launcher.py` | 192-197 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `nanobot/cli/tui_launcher.py` | 198-200 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 201-215 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `nanobot/cli/tui_launcher.py` | 216-218 | `cfc1fae8b5f6` | Xubin Ren | feat(cli): expose nanobot process identities |
| `nanobot/cli/tui_launcher.py` | 219-219 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `nanobot/cli/tui_launcher.py` | 220-221 | `cfc1fae8b5f6` | Xubin Ren | feat(cli): expose nanobot process identities |
| `nanobot/cli/tui_launcher.py` | 222-223 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `nanobot/cli/tui_launcher.py` | 224-228 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 229-229 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 230-230 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `nanobot/cli/tui_launcher.py` | 231-232 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 233-233 | `c671acd6a836` | Xubin Ren | fix(gateway): preserve shared runtime identity |
| `nanobot/cli/tui_launcher.py` | 234-235 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 236-236 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 237-237 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 238-238 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 239-241 | `c671acd6a836` | Xubin Ren | fix(gateway): preserve shared runtime identity |
| `nanobot/cli/tui_launcher.py` | 242-242 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 243-243 | `c671acd6a836` | Xubin Ren | fix(gateway): preserve shared runtime identity |
| `nanobot/cli/tui_launcher.py` | 244-246 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 247-279 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 280-286 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 287-287 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 288-288 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 289-292 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 293-293 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `nanobot/cli/tui_launcher.py` | 294-295 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 296-297 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `nanobot/cli/tui_launcher.py` | 298-298 | `cd6a11b3c59f` | Xubin Ren | fix(gateway): harden shared client lifecycle |
| `nanobot/cli/tui_launcher.py` | 299-299 | `c671acd6a836` | Xubin Ren | fix(gateway): preserve shared runtime identity |
| `nanobot/cli/tui_launcher.py` | 300-300 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 301-306 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 307-314 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 315-316 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 317-317 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `nanobot/cli/tui_launcher.py` | 318-320 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `nanobot/cli/tui_launcher.py` | 321-322 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 323-323 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 324-330 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 331-333 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 334-334 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 335-337 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `nanobot/cli/tui_launcher.py` | 338-338 | `0432f252b900` | Bill Kopp | feat(auth): route all WebUI and MCP Docker access through the verifier |
| `nanobot/cli/tui_launcher.py` | 339-342 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `nanobot/cli/tui_launcher.py` | 343-344 | `f9d449ef6c6d` | chengyongru | refactor(webui): isolate websocket application orchestration (#5548) |
| `nanobot/cli/tui_launcher.py` | 345-345 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `nanobot/cli/tui_launcher.py` | 346-346 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `nanobot/cli/tui_launcher.py` | 347-350 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `nanobot/cli/tui_launcher.py` | 351-352 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `nanobot/cli/tui_launcher.py` | 353-354 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `nanobot/cli/tui_launcher.py` | 355-356 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `nanobot/cli/tui_launcher.py` | 357-357 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `nanobot/cli/tui_launcher.py` | 358-359 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `nanobot/cli/tui_launcher.py` | 360-363 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `packages/client-events/fixtures.json` | 1-8 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/fixtures.json` | 9-13 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/fixtures.json` | 14-14 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 1-16 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 17-24 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/notifications.ts` | 25-25 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 26-26 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/notifications.ts` | 27-60 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 61-61 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/notifications.ts` | 62-62 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 63-65 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/notifications.ts` | 66-72 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `packages/client-events/notifications.ts` | 73-89 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `packages/client-events/notifications.ts` | 90-96 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `tests/cli/test_tui_launcher.py` | 1-1 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 2-5 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 6-6 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 7-7 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 8-8 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `tests/cli/test_tui_launcher.py` | 9-10 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 11-11 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `tests/cli/test_tui_launcher.py` | 12-12 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 13-13 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `tests/cli/test_tui_launcher.py` | 14-14 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tests/cli/test_tui_launcher.py` | 15-15 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 16-16 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 17-17 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 18-18 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 19-19 | `9a594f74ff89` | Xubin Ren | fix(cli): isolate Desktop compatibility probes [skip ci] |
| `tests/cli/test_tui_launcher.py` | 20-20 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 21-21 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 22-34 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 35-35 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 36-36 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `tests/cli/test_tui_launcher.py` | 37-39 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 40-42 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 43-44 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tests/cli/test_tui_launcher.py` | 45-52 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 53-53 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tests/cli/test_tui_launcher.py` | 54-55 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 56-56 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 57-57 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tests/cli/test_tui_launcher.py` | 58-61 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 62-64 | `6c24a19d7297` | Bill Kopp | test(perfs): cover single-password auth end-to-end |
| `tests/cli/test_tui_launcher.py` | 65-67 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 68-70 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 71-71 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 72-74 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 75-76 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 77-77 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 78-78 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 79-79 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 80-83 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 84-84 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 85-85 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 86-88 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 89-89 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 90-95 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 96-97 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 98-99 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 100-100 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 101-101 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 102-113 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 114-114 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 115-117 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 118-120 | `6c24a19d7297` | Bill Kopp | test(perfs): cover single-password auth end-to-end |
| `tests/cli/test_tui_launcher.py` | 121-121 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tests/cli/test_tui_launcher.py` | 122-124 | `6c24a19d7297` | Bill Kopp | test(perfs): cover single-password auth end-to-end |
| `tests/cli/test_tui_launcher.py` | 125-126 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 127-127 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `tests/cli/test_tui_launcher.py` | 128-128 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tests/cli/test_tui_launcher.py` | 129-129 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 130-130 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 131-132 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tests/cli/test_tui_launcher.py` | 133-153 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 154-154 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 155-172 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 173-207 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 208-208 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 209-210 | `9a594f74ff89` | Xubin Ren | fix(cli): isolate Desktop compatibility probes [skip ci] |
| `tests/cli/test_tui_launcher.py` | 211-211 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 212-217 | `9a594f74ff89` | Xubin Ren | fix(cli): isolate Desktop compatibility probes [skip ci] |
| `tests/cli/test_tui_launcher.py` | 218-250 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 251-272 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tests/cli/test_tui_launcher.py` | 273-273 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 274-304 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tests/cli/test_tui_launcher.py` | 305-311 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 312-312 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 313-314 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 315-315 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 316-322 | `14c5607e5e79` | Xubin Ren | fix(tui): enforce supported platform boundaries |
| `tests/cli/test_tui_launcher.py` | 323-323 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 324-325 | `14c5607e5e79` | Xubin Ren | fix(tui): enforce supported platform boundaries |
| `tests/cli/test_tui_launcher.py` | 326-338 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `tests/cli/test_tui_launcher.py` | 339-339 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tests/cli/test_tui_launcher.py` | 340-359 | `7384fbfffcad` | Xubin Ren | fix(packaging): keep source clients in lockstep |
| `tests/cli/test_tui_launcher.py` | 360-386 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 387-387 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tests/cli/test_tui_launcher.py` | 388-394 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 395-395 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tests/cli/test_tui_launcher.py` | 396-398 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tests/cli/test_tui_launcher.py` | 399-434 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 435-456 | `ed796332fe4b` | Xubin Ren | refactor(tui): retire the direct session default |
| `tests/cli/test_tui_launcher.py` | 457-521 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 522-525 | `cfc1fae8b5f6` | Xubin Ren | feat(cli): expose nanobot process identities |
| `tests/cli/test_tui_launcher.py` | 526-527 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 528-528 | `cfc1fae8b5f6` | Xubin Ren | feat(cli): expose nanobot process identities |
| `tests/cli/test_tui_launcher.py` | 529-547 | `9514b9b909c1` | Xubin Ren | fix(tui): require the native interactive client |
| `tests/cli/test_tui_launcher.py` | 548-548 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 549-551 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `tests/cli/test_tui_launcher.py` | 552-559 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 560-560 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tests/cli/test_tui_launcher.py` | 561-562 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 563-564 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tests/cli/test_tui_launcher.py` | 565-565 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 566-568 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tests/cli/test_tui_launcher.py` | 569-572 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 573-573 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tests/cli/test_tui_launcher.py` | 574-574 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_launcher.py` | 575-624 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `tests/cli/test_tui_launcher.py` | 625-628 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 629-629 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `tests/cli/test_tui_launcher.py` | 630-630 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 631-635 | `347583d3f7f3` | Xubin Ren | fix(tui): preserve gateway and cache boundaries |
| `tests/cli/test_tui_launcher.py` | 636-638 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 639-639 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 640-643 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 644-644 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 645-650 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 651-658 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 659-660 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 661-674 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 675-684 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 685-773 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 774-775 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tests/cli/test_tui_launcher.py` | 776-776 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 777-781 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 782-782 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 783-802 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 803-808 | `cd6a11b3c59f` | Xubin Ren | fix(gateway): harden shared client lifecycle |
| `tests/cli/test_tui_launcher.py` | 809-813 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_launcher.py` | 814-814 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 815-816 | `eafc0bc6eb1d` | Xubin Ren | fix(gateway): serialize shared runtime lifecycle |
| `tests/cli/test_tui_launcher.py` | 817-821 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 822-825 | `d8b4f612f270` | chengyongru | fix(gateway): recover degraded WebSocket listener (#5544) |
| `tests/cli/test_tui_launcher.py` | 826-834 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tests/cli/test_tui_launcher.py` | 835-837 | `74c11e5d28da` | Xubin Ren | fix(cli): share on-demand gateway lifecycle |
| `tests/cli/test_tui_release_packaging.py` | 1-36 | `d24ae0611779` | Xubin Ren | fix(release): verify TUI materials before tagging |
| `tests/cli/test_tui_wheels.py` | 1-56 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tests/cli/test_tui_wheels.py` | 57-57 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_wheels.py` | 58-123 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tests/cli/test_tui_wheels.py` | 124-124 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_wheels.py` | 125-162 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tests/cli/test_tui_wheels.py` | 163-163 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tests/cli/test_tui_wheels.py` | 164-186 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tui/README.md` | 1-11 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/README.md` | 12-21 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/README.md` | 22-22 | `7fc90ca6aac2` | Xubin Ren | feat(cli): make nanobot launch the terminal agent |
| `tui/README.md` | 23-23 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/README.md` | 24-24 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/README.md` | 25-25 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/README.md` | 26-29 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/README.md` | 30-34 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/README.md` | 35-35 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/README.md` | 36-36 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/README.md` | 37-37 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/README.md` | 38-38 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/README.md` | 39-42 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/README.md` | 43-44 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/README.md` | 45-48 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/README.md` | 49-49 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/README.md` | 50-53 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/README.md` | 54-54 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/README.md` | 55-56 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/README.md` | 57-57 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/README.md` | 58-58 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/README.md` | 59-61 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/README.md` | 62-63 | `99ba062a976d` | chengyongru | fix(tui): accept goal requests during active turns (#5981) |
| `tui/README.md` | 64-65 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/README.md` | 66-67 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/README.md` | 68-69 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/README.md` | 70-71 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/README.md` | 72-74 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/README.md` | 75-75 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/README.md` | 76-83 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/README.md` | 84-87 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/README.md` | 88-91 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/README.md` | 92-92 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/README.md` | 93-105 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/README.md` | 106-108 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/README.md` | 109-110 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/RELINKING.md` | 1-4 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/RELINKING.md` | 5-5 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/RELINKING.md` | 6-10 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/RELINKING.md` | 11-11 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `tui/RELINKING.md` | 12-15 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/RELINKING.md` | 16-17 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/RELINKING.md` | 18-18 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/RELINKING.md` | 19-19 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/RELINKING.md` | 20-24 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/RELINKING.md` | 25-25 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `tui/RELINKING.md` | 26-34 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/SOURCE_OFFER.md` | 1-15 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/bun.lock` | 1-7 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 8-8 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 9-10 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 11-11 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/bun.lock` | 12-16 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 17-17 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 18-18 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 19-19 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 20-20 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 21-21 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 22-22 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 23-23 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 24-24 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 25-25 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 26-26 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 27-27 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 28-28 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 29-29 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 30-30 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 31-31 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 32-32 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 33-33 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/bun.lock` | 34-34 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 35-35 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/bun.lock` | 36-42 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/bun.lock` | 43-43 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/bun.lock` | 44-63 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/licenses/BUN-1.4.4-LICENSE.md` | 1-113 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/licenses/LGPL-2.0.txt` | 1-480 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/licenses/LGPL-2.1.txt` | 1-501 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/package.json` | 1-12 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/package.json` | 13-13 | `6bf604d43c2e` | chengyongru | fix(tui): make Markdown links clickable (#5829) |
| `tui/package.json` | 14-15 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/package.json` | 16-16 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/package.json` | 17-19 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/build.ts` | 1-5 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/build.ts` | 6-12 | `14c5607e5e79` | Xubin Ren | fix(tui): enforce supported platform boundaries |
| `tui/scripts/build.ts` | 13-13 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/build.ts` | 14-14 | `14c5607e5e79` | Xubin Ren | fix(tui): enforce supported platform boundaries |
| `tui/scripts/build.ts` | 15-18 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/build.ts` | 19-20 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tui/scripts/build.ts` | 21-28 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/build.ts` | 29-29 | `d8efb852dafd` | Xubin Ren | build: bundle native TUI in platform wheels |
| `tui/scripts/build.ts` | 30-43 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/scripts/conpty_smoke.py` | 1-15 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 16-16 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/conpty_smoke.py` | 17-40 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 41-43 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/conpty_smoke.py` | 44-52 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 53-53 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/conpty_smoke.py` | 54-74 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 75-75 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/conpty_smoke.py` | 76-84 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 85-86 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/conpty_smoke.py` | 87-108 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 109-110 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/conpty_smoke.py` | 111-112 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 113-113 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/conpty_smoke.py` | 114-115 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 116-116 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/conpty_smoke.py` | 117-128 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/conpty_smoke.py` | 129-133 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/conpty_smoke.py` | 134-138 | `7ed37e5b700b` | Xubin Ren | test(tui): exercise Windows ConPTY boundary |
| `tui/scripts/package-release.py` | 1-6 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 7-8 | `d24ae0611779` | Xubin Ren | fix(release): verify TUI materials before tagging |
| `tui/scripts/package-release.py` | 9-26 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 27-40 | `d24ae0611779` | Xubin Ren | fix(release): verify TUI materials before tagging |
| `tui/scripts/package-release.py` | 41-61 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 62-65 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `tui/scripts/package-release.py` | 66-79 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 80-81 | `d24ae0611779` | Xubin Ren | fix(release): verify TUI materials before tagging |
| `tui/scripts/package-release.py` | 82-84 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 85-85 | `d24ae0611779` | Xubin Ren | fix(release): verify TUI materials before tagging |
| `tui/scripts/package-release.py` | 86-88 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/package-release.py` | 89-89 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/scripts/package-release.py` | 90-110 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/prepare-target.ts` | 1-41 | `92727c99a86c` | Xubin Ren | ci(tui): cross-build releases on free runners |
| `tui/scripts/pty_smoke.py` | 1-26 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 27-27 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/pty_smoke.py` | 28-71 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 72-72 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/pty_smoke.py` | 73-77 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 78-90 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tui/scripts/pty_smoke.py` | 91-95 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 96-96 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/pty_smoke.py` | 97-104 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 105-106 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/pty_smoke.py` | 107-110 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 111-111 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tui/scripts/pty_smoke.py` | 112-133 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 134-135 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/pty_smoke.py` | 136-137 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 138-138 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/scripts/pty_smoke.py` | 139-140 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 141-141 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/pty_smoke.py` | 142-161 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/pty_smoke.py` | 162-165 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/scripts/pty_smoke.py` | 166-175 | `a583b1ffda10` | Xubin Ren | fix(tui): inherit terminal background |
| `tui/scripts/pty_smoke.py` | 176-176 | `a51802103a1c` | Bill Kopp | fix(stage-2): remediate Percival local findings |
| `tui/scripts/pty_smoke.py` | 177-181 | `a80993e41303` | Xubin Ren | test(tui): verify real terminal boundaries |
| `tui/scripts/release-notices.ts` | 1-110 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/release-notices.ts` | 111-111 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/scripts/release-notices.ts` | 112-117 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/release-notices.ts` | 118-118 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/scripts/release-notices.ts` | 119-119 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/scripts/release-notices.ts` | 120-120 | `51a5d3821bce` | Bill Kopp | feat(stage-2): harden MCP bridge and runtime packaging |
| `tui/scripts/release-notices.ts` | 121-137 | `b17f227eb98d` | Xubin Ren | fix(release): package TUI compliance materials |
| `tui/src/app/app-event-queue.test.ts` | 1-6 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app-event-queue.test.ts` | 7-7 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app-event-queue.test.ts` | 8-167 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 1-8 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 9-9 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 10-10 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 11-11 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/app/app.ts` | 12-12 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 13-14 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 15-15 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 16-16 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 17-17 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 18-21 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 22-22 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 23-23 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 24-24 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 25-25 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 26-26 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 27-27 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 28-28 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 29-29 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 30-30 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 31-31 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 32-32 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 33-33 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 34-34 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 35-35 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 36-36 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 37-37 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 38-38 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 39-39 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 40-41 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 42-42 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 43-43 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 44-44 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 45-45 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 46-46 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 47-47 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 48-48 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 49-52 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 53-56 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 57-60 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 61-63 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 64-66 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 67-68 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 69-74 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 75-75 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 76-80 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 81-85 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 86-87 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 88-88 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 89-89 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 90-127 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 128-128 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/app/app.ts` | 129-129 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 130-132 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 133-133 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 134-134 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 135-135 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 136-136 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 137-137 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 138-138 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 139-139 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 140-140 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 141-142 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 143-143 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 144-144 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 145-145 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 146-146 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 147-147 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 148-148 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 149-150 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 151-151 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 152-153 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 154-154 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 155-155 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 156-157 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 158-158 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 159-159 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 160-160 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 161-161 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 162-162 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 163-163 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 164-164 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 165-165 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 166-166 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 167-167 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 168-168 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 169-171 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 172-173 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 174-174 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 175-175 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 176-178 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 179-179 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 180-180 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/app/app.ts` | 181-182 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 183-185 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 186-187 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 188-188 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/app/app.ts` | 189-190 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 191-193 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 194-198 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 199-200 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 201-204 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 205-205 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 206-207 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 208-209 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 210-210 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 211-211 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 212-212 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 213-214 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 215-216 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 217-217 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 218-218 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 219-219 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 220-220 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 221-225 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 226-226 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 227-231 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 232-232 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 233-233 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 234-234 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 235-235 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 236-236 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 237-238 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 239-239 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/app/app.ts` | 240-240 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 241-241 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 242-243 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 244-244 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 245-245 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 246-246 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 247-248 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/app/app.ts` | 249-249 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 250-250 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 251-254 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 255-258 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 259-259 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 260-260 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/app/app.ts` | 261-261 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 262-262 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 263-263 | `dc13dff3ffa2` | chengyongru | refactor(tui): use local command catalog directly |
| `tui/src/app/app.ts` | 264-268 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/app/app.ts` | 269-269 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 270-270 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 271-271 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 272-272 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 273-273 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 274-278 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 279-279 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 280-287 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 288-288 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 289-295 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 296-298 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 299-299 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/app/app.ts` | 300-302 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 303-305 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 306-309 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 310-310 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 311-314 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 315-315 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 316-316 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 317-319 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/app/app.ts` | 320-320 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 321-321 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 322-323 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 324-333 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 334-334 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 335-337 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/app/app.ts` | 338-349 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 350-353 | `c5d2e0ddf18b` | Xubin Ren | fix(tui): restore composer focus after runtime controls |
| `tui/src/app/app.ts` | 354-355 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 356-373 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 374-374 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 375-396 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 397-397 | `eebe3ca2927a` | chengyongru | fix(tui): preserve input typed after submit |
| `tui/src/app/app.ts` | 398-404 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 405-408 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 409-409 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 410-411 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 412-412 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 413-414 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 415-415 | `3cf6ed60ced4` | chengyongru | fix(tui): remove redundant launch header details |
| `tui/src/app/app.ts` | 416-418 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 419-419 | `1c1b13a3a963` | Kail Tian | fix(tui): preserve cursor position on Windows exit |
| `tui/src/app/app.ts` | 420-420 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 421-424 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 425-425 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 426-426 | `5feb21543cc5` | Xubin Ren | fix(tui): reflow layout on terminal resize |
| `tui/src/app/app.ts` | 427-428 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 429-429 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 430-431 | `5feb21543cc5` | Xubin Ren | fix(tui): reflow layout on terminal resize |
| `tui/src/app/app.ts` | 432-436 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 437-437 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 438-438 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 439-439 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 440-447 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 448-449 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 450-450 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 451-456 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/app/app.ts` | 457-457 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 458-458 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/app/app.ts` | 459-459 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 460-460 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 461-462 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/app/app.ts` | 463-467 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 468-469 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 470-476 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 477-477 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/app/app.ts` | 478-484 | `eebe3ca2927a` | chengyongru | fix(tui): preserve input typed after submit |
| `tui/src/app/app.ts` | 485-487 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 488-488 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 489-489 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 490-491 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 492-492 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 493-493 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/app/app.ts` | 494-494 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 495-498 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 499-502 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 503-504 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 505-505 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 506-507 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 508-517 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 518-526 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 527-527 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 528-528 | `1018bdb7fee3` | Kail Tian | fix(tui): expose /exit in command menu |
| `tui/src/app/app.ts` | 529-531 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 532-532 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 533-536 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 537-541 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 542-542 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 543-548 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 549-549 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 550-553 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 554-555 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 556-556 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 557-557 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 558-558 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 559-559 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 560-560 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/app/app.ts` | 561-561 | `1018bdb7fee3` | Kail Tian | fix(tui): expose /exit in command menu |
| `tui/src/app/app.ts` | 562-562 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 563-564 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 565-565 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 566-567 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 568-569 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 570-573 | `c320d08dfec8` | Xubin Ren | feat(tui): run bang commands through the gateway |
| `tui/src/app/app.ts` | 574-574 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 575-575 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 576-577 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 578-579 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 580-580 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 581-581 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 582-583 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 584-588 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 589-589 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 590-590 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 591-592 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 593-593 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 594-594 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 595-595 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 596-596 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 597-597 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 598-598 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 599-599 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 600-600 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 601-606 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 607-607 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 608-608 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 609-609 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/src/app/app.ts` | 610-612 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 613-617 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 618-619 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 620-620 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 621-622 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 623-623 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 624-624 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 625-641 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 642-643 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 644-646 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 647-647 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 648-650 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 651-651 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 652-653 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 654-654 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 655-655 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 656-657 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 658-658 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 659-659 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 660-663 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 664-664 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 665-665 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 666-667 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 668-671 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 672-678 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 679-681 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 682-683 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 684-684 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 685-692 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 693-696 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 697-698 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 699-700 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/app/app.ts` | 701-701 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 702-702 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/app/app.ts` | 703-703 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 704-706 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 707-707 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 708-708 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 709-713 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 714-714 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 715-715 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 716-716 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 717-717 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 718-718 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 719-719 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 720-720 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 721-722 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 723-725 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 726-729 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 730-730 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 731-733 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 734-734 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 735-738 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 739-739 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 740-740 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 741-741 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 742-742 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 743-747 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 748-748 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 749-749 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 750-750 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 751-752 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 753-753 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 754-755 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 756-756 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 757-757 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 758-758 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 759-760 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 761-762 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 763-763 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 764-769 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 770-770 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 771-791 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 792-792 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 793-793 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 794-797 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 798-807 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 808-808 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 809-811 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 812-812 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 813-813 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 814-814 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 815-818 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 819-819 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 820-821 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 822-824 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 825-825 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 826-828 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 829-829 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 830-830 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 831-831 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 832-832 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 833-833 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 834-834 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 835-835 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 836-836 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 837-844 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 845-847 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 848-848 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 849-851 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 852-852 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 853-854 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 855-855 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 856-856 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 857-857 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 858-858 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 859-867 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 868-868 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 869-869 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 870-872 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 873-873 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 874-874 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 875-878 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 879-879 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 880-880 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 881-885 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 886-887 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 888-888 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 889-893 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 894-894 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 895-895 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 896-896 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 897-897 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 898-900 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 901-903 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 904-909 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 910-910 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 911-917 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 918-918 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 919-920 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 921-921 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 922-922 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 923-924 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 925-925 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 926-927 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 928-929 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 930-930 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 931-932 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 933-933 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 934-934 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 935-935 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 936-936 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 937-937 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 938-940 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 941-943 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 944-945 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 946-947 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 948-970 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 971-973 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/app/app.ts` | 974-1016 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 1017-1017 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1018-1020 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 1021-1024 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1025-1026 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 1027-1027 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1028-1029 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/app/app.ts` | 1030-1036 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1037-1037 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 1038-1038 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1039-1039 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/app/app.ts` | 1040-1041 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1042-1042 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 1043-1053 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1054-1061 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1062-1065 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 1066-1066 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 1067-1072 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 1073-1073 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1074-1076 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/app/app.ts` | 1077-1077 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1078-1078 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1079-1079 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1080-1081 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1082-1082 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1083-1083 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1084-1085 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1086-1088 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1089-1089 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1090-1090 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1091-1091 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1092-1093 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1094-1094 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1095-1095 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1096-1096 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1097-1097 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1098-1098 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1099-1100 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1101-1115 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1116-1120 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1121-1121 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1122-1122 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/app/app.ts` | 1123-1123 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/app/app.ts` | 1124-1124 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1125-1125 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1126-1126 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1127-1127 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1128-1128 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1129-1130 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1131-1131 | `6eba62606c46` | Xubin Ren | refactor(tui): modernize active status animation |
| `tui/src/app/app.ts` | 1132-1135 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1136-1136 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 1137-1140 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1141-1141 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 1142-1147 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/app/app.ts` | 1148-1149 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1150-1150 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1151-1152 | `6eba62606c46` | Xubin Ren | refactor(tui): modernize active status animation |
| `tui/src/app/app.ts` | 1153-1153 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/app/app.ts` | 1154-1156 | `6eba62606c46` | Xubin Ren | refactor(tui): modernize active status animation |
| `tui/src/app/app.ts` | 1157-1158 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1159-1159 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1160-1160 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1161-1165 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1166-1166 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 1167-1169 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1170-1171 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1172-1173 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 1174-1174 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 1175-1176 | `2fb16593988b` | chengyongru | fix(tui): keep input responsive during agent output (#5791) |
| `tui/src/app/app.ts` | 1177-1178 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1179-1179 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1180-1182 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1183-1192 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 1193-1222 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1223-1225 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1226-1226 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1227-1230 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1231-1233 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1234-1237 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1238-1241 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1242-1250 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1251-1251 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1252-1277 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1278-1282 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1283-1285 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1286-1294 | `eebe3ca2927a` | chengyongru | fix(tui): preserve input typed after submit |
| `tui/src/app/app.ts` | 1295-1300 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1301-1301 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1302-1306 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1307-1308 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1309-1309 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 1310-1321 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1322-1323 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 1324-1324 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1325-1328 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 1329-1330 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1331-1331 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1332-1334 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1335-1335 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1336-1347 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1348-1379 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1380-1395 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1396-1397 | `c83ed041ea98` | chengyongru | fix(tui): prevent unmatched skill completion from queuing |
| `tui/src/app/app.ts` | 1398-1406 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1407-1429 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1430-1441 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1442-1450 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1451-1457 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1458-1458 | `cb13a1578055` | Xubin Ren | fix(tui): preserve streamed code on completion |
| `tui/src/app/app.ts` | 1459-1459 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1460-1460 | `cb13a1578055` | Xubin Ren | fix(tui): preserve streamed code on completion |
| `tui/src/app/app.ts` | 1461-1462 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1463-1463 | `cb13a1578055` | Xubin Ren | fix(tui): preserve streamed code on completion |
| `tui/src/app/app.ts` | 1464-1467 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1468-1481 | `cb13a1578055` | Xubin Ren | fix(tui): preserve streamed code on completion |
| `tui/src/app/app.ts` | 1482-1485 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1486-1499 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1500-1501 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1502-1506 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1507-1507 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1508-1508 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1509-1515 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1516-1517 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1518-1518 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1519-1522 | `7f288a49fc06` | chengyongru | fix(tui): preserve shell after Ctrl+C (#5502) |
| `tui/src/app/app.ts` | 1523-1528 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1529-1532 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1533-1536 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 1537-1545 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1546-1546 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1547-1553 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1554-1554 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1555-1560 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1561-1562 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1563-1567 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 1568-1571 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 1572-1576 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 1577-1579 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1580-1581 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/app/app.ts` | 1582-1582 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1583-1583 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1584-1584 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1585-1585 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1586-1586 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1587-1587 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1588-1588 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1589-1589 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 1590-1590 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1591-1591 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1592-1592 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1593-1593 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 1594-1594 | `9d7453a53e8a` | Xubin Ren | style(tui): simplify the composer surface |
| `tui/src/app/app.ts` | 1595-1597 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1598-1602 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1603-1604 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1605-1605 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1606-1608 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1609-1609 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1610-1610 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/src/app/app.ts` | 1611-1611 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 1612-1612 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1613-1613 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 1614-1614 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 1615-1615 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1616-1616 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1617-1620 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/app/app.ts` | 1621-1622 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1623-1623 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1624-1624 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 1625-1631 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1632-1633 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 1634-1635 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/app/app.ts` | 1636-1639 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 1640-1643 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1644-1645 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/app/app.ts` | 1646-1646 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1647-1648 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 1649-1649 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 1650-1650 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/app/app.ts` | 1651-1651 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 1652-1654 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1655-1668 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 1669-1672 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1673-1682 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 1683-1683 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1684-1685 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1686-1686 | `e69159cdae96` | chengyongru | style(tui): replace header dots with spacing |
| `tui/src/app/app.ts` | 1687-1688 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1689-1690 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1691-1692 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 1693-1693 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1694-1701 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 1702-1705 | `9d7453a53e8a` | Xubin Ren | style(tui): simplify the composer surface |
| `tui/src/app/app.ts` | 1706-1706 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/app/app.ts` | 1707-1712 | `9d7453a53e8a` | Xubin Ren | style(tui): simplify the composer surface |
| `tui/src/app/app.ts` | 1713-1713 | `40aa99f45638` | chengyongru | fix(tui): keep composer visible and focused |
| `tui/src/app/app.ts` | 1714-1715 | `9d7453a53e8a` | Xubin Ren | style(tui): simplify the composer surface |
| `tui/src/app/app.ts` | 1716-1716 | `40aa99f45638` | chengyongru | fix(tui): keep composer visible and focused |
| `tui/src/app/app.ts` | 1717-1718 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 1719-1722 | `411f9f0e90d6` | Xubin Ren | fix(tui): clear stale composer placeholder |
| `tui/src/app/app.ts` | 1723-1725 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/src/app/app.ts` | 1726-1727 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1728-1729 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1730-1731 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/app/app.ts` | 1732-1732 | `3ee37916269d` | chengyongru | refactor(tui): clarify active composer actions (#5538) |
| `tui/src/app/app.ts` | 1733-1735 | `411f9f0e90d6` | Xubin Ren | fix(tui): clear stale composer placeholder |
| `tui/src/app/app.ts` | 1736-1736 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1737-1737 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/app/app.ts` | 1738-1741 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1742-1742 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1743-1748 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1749-1749 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1750-1750 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1751-1752 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1753-1753 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1754-1757 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1758-1766 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1767-1769 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1770-1775 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1776-1784 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1785-1785 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1786-1791 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1792-1805 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1806-1839 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1840-1840 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 1841-1853 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1854-1854 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1855-1858 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1859-1871 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1872-1886 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1887-1888 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1889-1889 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1890-1890 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1891-1891 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1892-1895 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1896-1896 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1897-1897 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 1898-1933 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 1934-1946 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 1947-1947 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1948-1948 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1949-1949 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1950-1950 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1951-1952 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1953-1953 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1954-1954 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1955-1955 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1956-1956 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1957-1957 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 1958-1958 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1959-1959 | `dc13dff3ffa2` | chengyongru | refactor(tui): use local command catalog directly |
| `tui/src/app/app.ts` | 1960-1962 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 1963-1964 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1965-1965 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 1966-1966 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1967-1967 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1968-1969 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1970-1970 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 1971-1971 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1972-1972 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 1973-1974 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1975-1978 | `f1ebd8c4c614` | Xubin Ren | fix(tui): dismiss runtime pickers on outside click |
| `tui/src/app/app.ts` | 1979-1984 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 1985-1989 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1990-1990 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 1991-1997 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 1998-2016 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 2017-2026 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2027-2027 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2028-2036 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2037-2037 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2038-2046 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2047-2048 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2049-2068 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2069-2069 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 2070-2071 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2072-2072 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 2073-2096 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2097-2097 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2098-2098 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2099-2099 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2100-2100 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/app/app.ts` | 2101-2101 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2102-2102 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 2103-2103 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2104-2104 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2105-2105 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2106-2109 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2110-2114 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2115-2116 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2117-2119 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2120-2120 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2121-2121 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2122-2122 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 2123-2124 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2125-2125 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2126-2131 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/app/app.ts` | 2132-2132 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2133-2133 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2134-2143 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2144-2144 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2145-2145 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2146-2147 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2148-2148 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2149-2149 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2150-2150 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 2151-2151 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2152-2152 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2153-2154 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2155-2159 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2160-2161 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2162-2163 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 2164-2164 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 2165-2165 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 2166-2166 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2167-2167 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 2168-2168 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2169-2169 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2170-2170 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2171-2171 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2172-2173 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2174-2174 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2175-2175 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2176-2176 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2177-2182 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2183-2183 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2184-2187 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2188-2191 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2192-2192 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2193-2193 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2194-2194 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2195-2195 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 2196-2196 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2197-2197 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2198-2198 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2199-2200 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2201-2201 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/app/app.ts` | 2202-2202 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/app/app.ts` | 2203-2203 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2204-2204 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/app/app.ts` | 2205-2205 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2206-2208 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2209-2209 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2210-2211 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2212-2212 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2213-2213 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2214-2214 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2215-2219 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2220-2222 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2223-2223 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2224-2224 | `c320d08dfec8` | Xubin Ren | feat(tui): run bang commands through the gateway |
| `tui/src/app/app.ts` | 2225-2226 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2227-2227 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 2228-2229 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2230-2231 | `99ba062a976d` | chengyongru | fix(tui): accept goal requests during active turns (#5981) |
| `tui/src/app/app.ts` | 2232-2235 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2236-2236 | `c320d08dfec8` | Xubin Ren | feat(tui): run bang commands through the gateway |
| `tui/src/app/app.ts` | 2237-2238 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 2239-2240 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2241-2241 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/app/app.ts` | 2242-2242 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2243-2243 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2244-2244 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2245-2245 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2246-2246 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2247-2248 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2249-2249 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2250-2250 | `99ba062a976d` | chengyongru | fix(tui): accept goal requests during active turns (#5981) |
| `tui/src/app/app.ts` | 2251-2251 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2252-2258 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2259-2259 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2260-2267 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2268-2268 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 2269-2274 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/app/app.ts` | 2275-2286 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2287-2289 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2290-2290 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2291-2291 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2292-2292 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2293-2293 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/app/app.ts` | 2294-2295 | `58a1cc48d8d5` | Xubin Ren | fix(tui): allow switching active sessions |
| `tui/src/app/app.ts` | 2296-2296 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/app/app.ts` | 2297-2298 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/app/app.ts` | 2299-2331 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2332-2336 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/app/app.ts` | 2337-2344 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2345-2352 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2353-2359 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2360-2360 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2361-2368 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2369-2370 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2371-2371 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2372-2377 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2378-2378 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2379-2379 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2380-2380 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2381-2382 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2383-2383 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2384-2384 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2385-2393 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2394-2396 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/app.ts` | 2397-2397 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2398-2398 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2399-2399 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2400-2400 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2401-2401 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2402-2402 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 2403-2403 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2404-2404 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2405-2410 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2411-2411 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2412-2416 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2417-2417 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2418-2418 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2419-2419 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2420-2427 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2428-2431 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2432-2436 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2437-2443 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2444-2444 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/app/app.ts` | 2445-2445 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/app/app.ts` | 2446-2457 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2458-2458 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2459-2459 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2460-2460 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2461-2461 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2462-2462 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2463-2463 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2464-2464 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2465-2465 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/app/app.ts` | 2466-2470 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2471-2471 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2472-2472 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2473-2473 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2474-2474 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2475-2475 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2476-2476 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/app/app.ts` | 2477-2477 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/app/app.ts` | 2478-2478 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2479-2479 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/app/app.ts` | 2480-2487 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2488-2504 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2505-2505 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/app/app.ts` | 2506-2508 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2509-2509 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2510-2522 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/app/app.ts` | 2523-2533 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/app/app.ts` | 2534-2534 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/app/app.ts` | 2535-2536 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2537-2538 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/app/app.ts` | 2539-2539 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2540-2540 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 2541-2542 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2543-2543 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/src/app/app.ts` | 2544-2545 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/app/app.ts` | 2546-2548 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2549-2549 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 2550-2550 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/app.ts` | 2551-2551 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/app.ts` | 2552-2552 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 2553-2553 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2554-2554 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/app/app.ts` | 2555-2555 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 2556-2556 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2557-2557 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/app/app.ts` | 2558-2558 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/app/app.ts` | 2559-2559 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/app/app.ts` | 2560-2563 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/app/app.ts` | 2564-2565 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/commands.ts` | 1-52 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/composer.test.ts` | 1-409 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/composer.test.ts` | 410-458 | `99ba062a976d` | chengyongru | fix(tui): accept goal requests during active turns (#5981) |
| `tui/src/app/composer.test.ts` | 459-810 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/event-queue.ts` | 1-94 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/host-lifecycle.test.ts` | 1-156 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/index.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/layout.test.ts` | 1-775 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/layout.ts` | 1-207 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/lifecycle.test.ts` | 1-552 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/sessions.test.ts` | 1-211 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/sessions.test.ts` | 212-212 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/app/sessions.test.ts` | 213-995 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/status.ts` | 1-66 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/test-support.ts` | 1-96 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/theme.ts` | 1-261 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/transcript.test.ts` | 1-450 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/types.ts` | 1-14 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/types.ts` | 15-15 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/app/types.ts` | 16-44 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/usage-app.test.ts` | 1-5 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 6-7 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/app/usage-app.test.ts` | 8-10 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 11-15 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/app/usage-app.test.ts` | 16-43 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 44-44 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/usage-app.test.ts` | 45-53 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 54-54 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/usage-app.test.ts` | 55-55 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 56-56 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/usage-app.test.ts` | 57-147 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 148-223 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/usage-app.test.ts` | 224-224 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/app/usage-app.test.ts` | 225-243 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/app/usage-app.test.ts` | 244-265 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/app/usage-app.test.ts` | 266-266 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/app/usage-app.test.ts` | 267-296 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/api.ts` | 1-529 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/client.test.ts` | 1-2 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 3-4 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 5-5 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 6-6 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 7-7 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/client/client.test.ts` | 8-8 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 9-9 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 10-10 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 11-11 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 12-12 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/client/client.test.ts` | 13-13 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 14-14 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 15-15 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 16-18 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 19-19 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 20-20 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/client.test.ts` | 21-21 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 22-47 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 48-53 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 54-110 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/client/client.test.ts` | 111-124 | `9a594f74ff89` | Xubin Ren | fix(cli): isolate Desktop compatibility probes [skip ci] |
| `tui/src/client/client.test.ts` | 125-133 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/client/client.test.ts` | 134-134 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 135-154 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 155-169 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 170-170 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 171-173 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 174-174 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 175-184 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 185-219 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 220-226 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 227-227 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 228-238 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 239-267 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/client/client.test.ts` | 268-287 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 288-288 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 289-290 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 291-294 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 295-309 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 310-310 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 311-355 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 356-359 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 360-360 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 361-377 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 378-378 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 379-405 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 406-406 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/client.test.ts` | 407-482 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 483-501 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/client/client.test.ts` | 502-503 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 504-512 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/client/client.test.ts` | 513-516 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 517-522 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/client/client.test.ts` | 523-542 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 543-546 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/client/client.test.ts` | 547-554 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 555-561 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/client/client.test.ts` | 562-562 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 563-563 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/client/client.test.ts` | 564-565 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 566-566 | `c320d08dfec8` | Xubin Ren | feat(tui): run bang commands through the gateway |
| `tui/src/client/client.test.ts` | 567-567 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 568-569 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 570-570 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 571-574 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/client/client.test.ts` | 575-580 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 581-581 | `c320d08dfec8` | Xubin Ren | feat(tui): run bang commands through the gateway |
| `tui/src/client/client.test.ts` | 582-584 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/client/client.test.ts` | 585-588 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 589-590 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 591-596 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 597-604 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/client/client.test.ts` | 605-605 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 606-610 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/client/client.test.ts` | 611-612 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 613-643 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/client/client.test.ts` | 644-651 | `baa02333779e` | Xubin Ren | fix(tui): preserve draft scope until first message |
| `tui/src/client/client.test.ts` | 652-652 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/client/client.test.ts` | 653-659 | `baa02333779e` | Xubin Ren | fix(tui): preserve draft scope until first message |
| `tui/src/client/client.test.ts` | 660-660 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/client/client.test.ts` | 661-671 | `baa02333779e` | Xubin Ren | fix(tui): preserve draft scope until first message |
| `tui/src/client/client.test.ts` | 672-673 | `c615aee2cad5` | chengyongru | feat(tui): start fresh chats in launch workspace |
| `tui/src/client/client.test.ts` | 674-676 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 677-718 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/client/client.test.ts` | 719-733 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 734-734 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 735-736 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 737-737 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 738-742 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 743-743 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 744-750 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/client/client.test.ts` | 751-761 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 762-764 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/client/client.test.ts` | 765-773 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/client/client.test.ts` | 774-776 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/client/client.test.ts` | 777-779 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/client/client.test.ts` | 780-782 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/client/client.test.ts` | 783-789 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/client/client.test.ts` | 790-791 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 792-792 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 793-793 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/client/client.test.ts` | 794-798 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/client/client.test.ts` | 799-799 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 800-804 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/client/client.test.ts` | 805-808 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/client.test.ts` | 809-809 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 810-857 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/client/client.test.ts` | 858-907 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/client/client.test.ts` | 908-985 | `b581a496a660` | chengyongru | fix(ui): surface model retry status (NAN-34) (#5504) |
| `tui/src/client/client.test.ts` | 986-986 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/client/client.test.ts` | 987-1000 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1001-1005 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 1006-1009 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1010-1010 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 1011-1012 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1013-1013 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 1014-1023 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1024-1032 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 1033-1037 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1038-1038 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/client/client.test.ts` | 1039-1044 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1045-1100 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/client/client.test.ts` | 1101-1101 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1102-1102 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1103-1105 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1106-1110 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1111-1112 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1113-1113 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1114-1114 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1115-1115 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1116-1116 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1117-1117 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1118-1118 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/client/client.test.ts` | 1119-1119 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1120-1120 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1121-1121 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1122-1128 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1129-1131 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/client/client.test.ts` | 1132-1135 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1136-1138 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/client/client.test.ts` | 1139-1141 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1142-1142 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/client/client.test.ts` | 1143-1143 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/client.test.ts` | 1144-1148 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/client/client.test.ts` | 1149-1159 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1160-1172 | `8bb382848731` | chengyongru | fix(tui): preserve usage telemetry fields |
| `tui/src/client/client.test.ts` | 1173-1184 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1185-1197 | `8bb382848731` | chengyongru | fix(tui): preserve usage telemetry fields |
| `tui/src/client/client.test.ts` | 1198-1202 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/client/client.test.ts` | 1203-1229 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 1230-1230 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/client/client.test.ts` | 1231-1237 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/client/client.test.ts` | 1238-1238 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 1239-1285 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/client/client.test.ts` | 1286-1303 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/client/client.test.ts` | 1304-1305 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 1306-1323 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1324-1324 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/client/client.test.ts` | 1325-1330 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1331-1334 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 1335-1335 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1336-1339 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 1340-1340 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/client/client.test.ts` | 1341-1342 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/client/client.test.ts` | 1343-1347 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/client/client.test.ts` | 1348-1404 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/client/client.test.ts` | 1405-1405 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/client/connection.ts` | 1-13 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/connection.ts` | 14-14 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/connection.ts` | 15-18 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/connection.ts` | 19-20 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/client/connection.ts` | 21-145 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/history.test.ts` | 1-1 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/history.test.ts` | 2-2 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/history.test.ts` | 3-104 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/index.ts` | 1-48 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/instance-login.ts` | 1-98 | `d773f8b5e9ec` | Bill Kopp | feat(tui): add interactive password prompt and login helper |
| `tui/src/client/nanobot-client.ts` | 1-415 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/types.ts` | 1-341 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/usage.test.ts` | 1-2 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 3-3 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/client/usage.test.ts` | 4-22 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 23-27 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 28-29 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 30-31 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 32-40 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 41-45 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 46-59 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 60-61 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 62-62 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 63-64 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 65-74 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 75-75 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 76-77 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 78-79 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 80-80 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 81-81 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 82-82 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 83-83 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 84-84 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 85-86 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 87-95 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 96-96 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 97-97 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 98-98 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 99-99 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 100-103 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 104-104 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 105-108 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 109-119 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 120-121 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 122-123 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 124-124 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 125-129 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 130-131 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 132-152 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 153-153 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 154-154 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 155-157 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 158-182 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 183-183 | `b8893aba5604` | chengyongru | fix(tui): restore session history from canonical events |
| `tui/src/client/usage.test.ts` | 184-199 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/usage.test.ts` | 200-244 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/client/usage.test.ts` | 245-257 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/client/validation.ts` | 1-237 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/composer/clipboard-image.test.ts` | 1-46 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/clipboard-image.ts` | 1-13 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/clipboard-image.ts` | 14-14 | `3ecc3d35566b` | chengyongru | refactor: remove unused helpers and internal exports |
| `tui/src/composer/clipboard-image.ts` | 15-64 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.test.ts` | 1-2 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.test.ts` | 3-3 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.test.ts` | 4-27 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.test.ts` | 28-150 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.test.ts` | 151-151 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/composer/composer-draft.ts` | 2-2 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 3-4 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 5-5 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 6-12 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 13-31 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 32-33 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 34-38 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 39-54 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 55-80 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 81-85 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 86-185 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 186-189 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 190-192 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 193-196 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/composer-draft.ts` | 197-197 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/composer-draft.ts` | 198-199 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/composer/prompt-queue.test.ts` | 1-7 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.test.ts` | 8-8 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/prompt-queue.test.ts` | 9-12 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.test.ts` | 13-14 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/prompt-queue.test.ts` | 15-27 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/composer/prompt-queue.ts` | 2-4 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.ts` | 5-5 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/composer/prompt-queue.ts` | 6-8 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.ts` | 9-9 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/prompt-queue.ts` | 10-20 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.ts` | 21-21 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/prompt-queue.ts` | 22-28 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/prompt-queue.ts` | 29-32 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/prompt-queue.ts` | 33-42 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/composer/queue-preview.test.ts` | 1-19 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.test.ts` | 20-20 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.test.ts` | 21-27 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.test.ts` | 28-28 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.test.ts` | 29-37 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 1-6 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 7-7 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/composer/queue-preview.ts` | 8-8 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 9-9 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/composer/queue-preview.ts` | 10-12 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 13-13 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/composer/queue-preview.ts` | 14-14 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.ts` | 15-15 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 16-18 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/composer/queue-preview.ts` | 19-27 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 28-28 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.ts` | 29-31 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 32-32 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.ts` | 33-33 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 34-34 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.ts` | 35-72 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 73-73 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/composer/queue-preview.ts` | 74-93 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 94-94 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/composer/queue-preview.ts` | 95-97 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/composer/queue-preview.ts` | 98-98 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/composer/queue-preview.ts` | 99-101 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/index.ts` | 1-1 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/src/index.ts` | 2-2 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/index.ts` | 3-3 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/index.ts` | 4-9 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 10-10 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/index.ts` | 11-13 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/index.ts` | 14-19 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/index.ts` | 20-20 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/index.ts` | 21-21 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/index.ts` | 22-22 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/index.ts` | 23-23 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/index.ts` | 24-24 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/index.ts` | 25-26 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/index.ts` | 27-27 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 28-29 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/index.ts` | 30-39 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/index.ts` | 40-40 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/index.ts` | 41-41 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 42-42 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/index.ts` | 43-43 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/index.ts` | 44-44 | `722eb962e9d8` | Bill Kopp | feat(webui,tui): drop local secret storage and sign in with the instance password |
| `tui/src/index.ts` | 45-45 | `3a62b0b74402` | chengyongru | fix(tui): surface chat connection failures (#5543) |
| `tui/src/index.ts` | 46-47 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/index.ts` | 48-51 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/index.ts` | 52-52 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/index.ts` | 53-53 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/index.ts` | 54-55 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/index.ts` | 56-56 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/index.ts` | 57-59 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/index.ts` | 60-61 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 62-62 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/index.ts` | 63-63 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/src/index.ts` | 64-64 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 65-65 | `415df576b464` | chengyongru | feat(tui): print resume command on exit |
| `tui/src/index.ts` | 66-67 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/src/index.ts` | 68-69 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/index.ts` | 70-71 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/index.ts` | 72-74 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/index.ts` | 75-80 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/index.ts` | 81-81 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/index.ts` | 82-83 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/index.ts` | 84-84 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 85-87 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/index.ts` | 88-88 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/index.ts` | 89-90 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/index.ts` | 91-92 | `e207269cf670` | Xubin Ren | fix(tui): close cross-platform lifecycle races |
| `tui/src/index.ts` | 93-93 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/menus/branch-menu.test.ts` | 1-15 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/branch-menu.ts` | 1-3 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/branch-menu.ts` | 4-4 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/branch-menu.ts` | 5-40 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/command-menu.test.ts` | 1-3 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.test.ts` | 4-4 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.test.ts` | 5-5 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/command-menu.test.ts` | 6-12 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.test.ts` | 13-13 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.test.ts` | 14-20 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.test.ts` | 21-21 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.test.ts` | 22-68 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.test.ts` | 69-95 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.test.ts` | 96-121 | `1018bdb7fee3` | Kail Tian | fix(tui): expose /exit in command menu |
| `tui/src/menus/command-menu.test.ts` | 122-135 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.test.ts` | 136-136 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 1-1 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 2-2 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 3-3 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/command-menu.ts` | 4-4 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 5-5 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 6-6 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 7-7 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 8-8 | `961b1fdd7d36` | chengyongru | refactor: remove remaining dead code |
| `tui/src/menus/command-menu.ts` | 9-11 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/menus/command-menu.ts` | 12-12 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/menus/command-menu.ts` | 13-16 | `26764f24235c` | chengyongru | feat(tui): add /detach command (#5461) |
| `tui/src/menus/command-menu.ts` | 17-48 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 49-51 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 52-53 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 54-56 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 57-58 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 59-59 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 60-60 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 61-61 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 62-69 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 70-72 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 73-73 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 74-74 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 75-77 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 78-78 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 79-80 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 81-88 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 89-91 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 92-102 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 103-110 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 111-112 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 113-115 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 116-116 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 117-120 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 121-126 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 127-130 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 131-133 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 134-134 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 135-136 | `b3c3a8207528` | Xubin Ren | fix(tui): preserve slash command semantics |
| `tui/src/menus/command-menu.ts` | 137-139 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 140-140 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 141-143 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/command-menu.ts` | 144-144 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/command-menu.ts` | 145-146 | `d094fd7f4d0c` | Xubin Ren | feat(tui): discover slash commands |
| `tui/src/menus/mention-menu.test.ts` | 1-3 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/mention-menu.test.ts` | 4-4 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/mention-menu.test.ts` | 5-49 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/mention-menu.ts` | 1-3 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/mention-menu.ts` | 4-4 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/mention-menu.ts` | 5-75 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/menus/picker-menu.test.ts` | 1-44 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.test.ts` | 45-45 | `509304f9bbd6` | chengyongru | style(tui): simplify picker overflow indicator |
| `tui/src/menus/picker-menu.test.ts` | 46-52 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.test.ts` | 53-53 | `509304f9bbd6` | chengyongru | style(tui): simplify picker overflow indicator |
| `tui/src/menus/picker-menu.test.ts` | 54-62 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.test.ts` | 63-63 | `509304f9bbd6` | chengyongru | style(tui): simplify picker overflow indicator |
| `tui/src/menus/picker-menu.test.ts` | 64-90 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.test.ts` | 91-91 | `509304f9bbd6` | chengyongru | style(tui): simplify picker overflow indicator |
| `tui/src/menus/picker-menu.test.ts` | 92-99 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 1-3 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 4-4 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 5-6 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 7-7 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 8-8 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 9-9 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 10-10 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 11-13 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 14-19 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 20-23 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 24-24 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/picker-menu.ts` | 25-25 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 26-26 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 27-27 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 28-29 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 30-37 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 38-38 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 39-49 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 50-50 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 51-59 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 60-65 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/menus/picker-menu.ts` | 66-78 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 79-88 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 89-91 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 92-93 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/picker-menu.ts` | 94-96 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 97-100 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 101-102 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/picker-menu.ts` | 103-103 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 104-113 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/picker-menu.ts` | 114-114 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 115-120 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 121-121 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 122-133 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 134-134 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 135-154 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 155-155 | `7e60d52f0ed2` | Xubin Ren | fix(tui): prevent terminal cell artifacts |
| `tui/src/menus/picker-menu.ts` | 156-158 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 159-161 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 162-162 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 163-169 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 170-171 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 172-172 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 173-176 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 177-177 | `7e60d52f0ed2` | Xubin Ren | fix(tui): prevent terminal cell artifacts |
| `tui/src/menus/picker-menu.ts` | 178-178 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 179-179 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 180-180 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 181-181 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 182-182 | `4561c748f652` | chengyongru | fix(tui): preserve keyboard picker selection |
| `tui/src/menus/picker-menu.ts` | 183-190 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 191-191 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/menus/picker-menu.ts` | 192-194 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/menus/picker-menu.ts` | 195-196 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 197-201 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 202-202 | `509304f9bbd6` | chengyongru | style(tui): simplify picker overflow indicator |
| `tui/src/menus/picker-menu.ts` | 203-224 | `740e39b1ca42` | chengyongru | fix(tui): keep picker overflow choices reachable |
| `tui/src/menus/picker-menu.ts` | 225-233 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/picker-menu.ts` | 234-234 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 235-235 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 236-238 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/picker-menu.ts` | 239-239 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/picker-menu.ts` | 240-241 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 1-3 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 4-4 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/menus/session-menu.test.ts` | 5-5 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/session-menu.test.ts` | 6-14 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 15-15 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.test.ts` | 16-17 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/menus/session-menu.test.ts` | 18-25 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 26-26 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.test.ts` | 27-31 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/menus/session-menu.test.ts` | 32-33 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/menus/session-menu.test.ts` | 34-50 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 51-52 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 53-54 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 55-55 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.test.ts` | 56-58 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 59-60 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.test.ts` | 61-64 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 65-65 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 66-67 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.test.ts` | 68-73 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/menus/session-menu.test.ts` | 74-74 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.test.ts` | 75-107 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 108-140 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.test.ts` | 141-146 | `4561c748f652` | chengyongru | fix(tui): preserve keyboard picker selection |
| `tui/src/menus/session-menu.test.ts` | 147-148 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 149-170 | `4561c748f652` | chengyongru | fix(tui): preserve keyboard picker selection |
| `tui/src/menus/session-menu.test.ts` | 171-176 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.test.ts` | 177-178 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.test.ts` | 179-235 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.test.ts` | 236-262 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.test.ts` | 263-263 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 1-1 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/session-menu.ts` | 2-3 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 4-4 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/session-menu.ts` | 5-5 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 6-8 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 9-9 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 10-12 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/menus/session-menu.ts` | 13-29 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 30-31 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 32-34 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 35-35 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 36-40 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 41-41 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 42-43 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/menus/session-menu.ts` | 44-44 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 45-47 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/menus/session-menu.ts` | 48-48 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 49-49 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 50-54 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.ts` | 55-56 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 57-58 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/menus/session-menu.ts` | 59-59 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.ts` | 60-60 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 61-61 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 62-62 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.ts` | 63-63 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 64-64 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 65-65 | `e77eed76c9f6` | Xubin Ren | fix(tui): track canonical model presets |
| `tui/src/menus/session-menu.ts` | 66-67 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 68-68 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 69-71 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 72-73 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 74-76 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 77-77 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 78-79 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 80-80 | `cf82b8930781` | Xubin Ren | feat(tui): make session title interactive |
| `tui/src/menus/session-menu.ts` | 81-88 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 89-95 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 96-101 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 102-107 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 108-118 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 119-119 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 120-125 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 126-127 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/menus/session-menu.ts` | 128-128 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 129-130 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/menus/session-menu.ts` | 131-132 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 133-133 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/menus/session-menu.ts` | 134-148 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 149-150 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 151-154 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 155-155 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 156-157 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 158-158 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 159-159 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/session-menu.ts` | 160-160 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 161-178 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 179-183 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/session-menu.ts` | 184-226 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 227-249 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 250-254 | `5accc903a0a2` | Xubin Ren | refactor(tui): simplify session rows |
| `tui/src/menus/session-menu.ts` | 255-256 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 257-257 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/session-menu.ts` | 258-260 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 261-261 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/menus/session-menu.ts` | 262-264 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/menus/session-menu.ts` | 265-275 | `4858da075943` | Xubin Ren | feat(tui): distinguish cross-workspace sessions |
| `tui/src/menus/session-menu.ts` | 276-276 | `2b666934ba36` | Xubin Ren | feat(tui): add session navigation |
| `tui/src/menus/session-menu.ts` | 277-289 | `1f0771c5553c` | Xubin Ren | feat(tui): refine session status navigation |
| `tui/src/menus/skill-menu.test.ts` | 1-4 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/menus/skill-menu.test.ts` | 5-5 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/skill-menu.test.ts` | 6-72 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/menus/skill-menu.ts` | 1-3 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/menus/skill-menu.ts` | 4-4 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/menus/skill-menu.ts` | 5-86 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/platform/clipboard.ts` | 1-18 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/platform/desktop.test.ts` | 1-62 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/platform/desktop.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/platform/desktop.ts` | 2-87 | `48e7c4f6979a` | Xubin Ren | feat(cli): attach terminal clients to the selected Desktop [skip ci] |
| `tui/src/platform/host.test.ts` | 1-2 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 3-6 | `1c1b13a3a963` | Kail Tian | fix(tui): preserve cursor position on Windows exit |
| `tui/src/platform/host.test.ts` | 7-8 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 9-9 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 10-13 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 14-34 | `1c1b13a3a963` | Kail Tian | fix(tui): preserve cursor position on Windows exit |
| `tui/src/platform/host.test.ts` | 35-38 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 39-39 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 40-45 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 46-46 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 47-47 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 48-48 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 49-49 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 50-51 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 52-53 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 54-54 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 55-56 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 57-57 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 58-59 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 60-60 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 61-63 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 64-68 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 69-70 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.test.ts` | 71-89 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.test.ts` | 90-91 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 1-1 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 2-2 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 3-10 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 11-23 | `1c1b13a3a963` | Kail Tian | fix(tui): preserve cursor position on Windows exit |
| `tui/src/platform/host.ts` | 24-24 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 25-25 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 26-31 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 32-32 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 33-40 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 41-41 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 42-42 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 43-45 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 46-49 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 50-50 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 51-51 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 52-52 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 53-57 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 58-58 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 59-72 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/host.ts` | 73-74 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/platform/host.ts` | 75-89 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/platform/platform-keys.ts` | 1-3 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/latex.test.ts` | 1-40 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.test.ts` | 41-42 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.test.ts` | 43-48 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.test.ts` | 49-50 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.test.ts` | 51-76 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.test.ts` | 77-77 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.test.ts` | 78-108 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.test.ts` | 109-114 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.test.ts` | 115-117 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.test.ts` | 118-121 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.test.ts` | 122-158 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 1-265 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 266-268 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 269-271 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 272-275 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 276-285 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 286-288 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 289-292 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 293-295 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 296-297 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 298-298 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 299-305 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 306-306 | `cbe4316e4b51` | chengyongru | perf(tui): avoid repeated LaTeX scans |
| `tui/src/rendering/latex.ts` | 307-307 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 308-312 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 313-338 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 339-339 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 340-384 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 385-385 | `cbe4316e4b51` | chengyongru | perf(tui): avoid repeated LaTeX scans |
| `tui/src/rendering/latex.ts` | 386-408 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 409-425 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 426-526 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 527-542 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 543-544 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 545-562 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 563-564 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 565-576 | `dd993b4f7072` | chengyongru | fix(tui): bound Markdown math preprocessing |
| `tui/src/rendering/latex.ts` | 577-585 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/latex.ts` | 586-593 | `cbe4316e4b51` | chengyongru | perf(tui): avoid repeated LaTeX scans |
| `tui/src/rendering/latex.ts` | 594-901 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/scrollbox.ts` | 1-14 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/rendering/tool-renderers.test.ts` | 1-5 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.test.ts` | 6-19 | `e0b8efa0beff` | chengyongru | feat(tools): use installed ripgrep for native file search (#5948) |
| `tui/src/rendering/tool-renderers.test.ts` | 20-24 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.test.ts` | 25-25 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/rendering/tool-renderers.test.ts` | 26-35 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.test.ts` | 36-42 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/rendering/tool-renderers.test.ts` | 43-66 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.test.ts` | 67-67 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/rendering/tool-renderers.ts` | 2-2 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 3-8 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 9-22 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 23-26 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 27-31 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 32-34 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 35-35 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/rendering/tool-renderers.ts` | 36-37 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 38-49 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/rendering/tool-renderers.ts` | 50-50 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 51-52 | `79d51be71fa7` | Xubin Ren | feat(tui): integrate with Herdr host |
| `tui/src/rendering/tool-renderers.ts` | 53-55 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 56-56 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 57-57 | `e0b8efa0beff` | chengyongru | feat(tools): use installed ripgrep for native file search (#5948) |
| `tui/src/rendering/tool-renderers.ts` | 58-65 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 66-66 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 67-71 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 72-72 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 73-73 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 74-74 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 75-75 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 76-80 | `e0b8efa0beff` | chengyongru | feat(tools): use installed ripgrep for native file search (#5948) |
| `tui/src/rendering/tool-renderers.ts` | 81-92 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 93-93 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 94-94 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/tool-renderers.ts` | 95-128 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/tool-renderers.ts` | 129-129 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 1-1 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/rendering/transcript.ts` | 2-3 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 4-4 | `455533169d5a` | Xubin Ren | fix(tui): distinguish fenced code blocks |
| `tui/src/rendering/transcript.ts` | 5-5 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 6-6 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 7-7 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 8-8 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 9-11 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 12-12 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 13-13 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 14-14 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 15-15 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 16-18 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 19-19 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 20-20 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 21-24 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 25-25 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/rendering/transcript.ts` | 26-26 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 27-27 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/rendering/transcript.ts` | 28-28 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 29-30 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 31-36 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 37-44 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 45-49 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 50-54 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 55-55 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 56-57 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 58-64 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/transcript.ts` | 65-69 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 70-70 | `455533169d5a` | Xubin Ren | fix(tui): distinguish fenced code blocks |
| `tui/src/rendering/transcript.ts` | 71-71 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 72-107 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 108-114 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 115-115 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 116-118 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 119-122 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 123-123 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 124-124 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 125-130 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 131-131 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 132-133 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 134-135 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 136-137 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 138-138 | `455533169d5a` | Xubin Ren | fix(tui): distinguish fenced code blocks |
| `tui/src/rendering/transcript.ts` | 139-143 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 144-144 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 145-145 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/transcript.ts` | 146-146 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 147-147 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 148-151 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 152-152 | `e427c9eeae3a` | Kail Tian | style(tui): keep short transcripts and composer top-aligned |
| `tui/src/rendering/transcript.ts` | 153-159 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 160-160 | `e427c9eeae3a` | Kail Tian | style(tui): keep short transcripts and composer top-aligned |
| `tui/src/rendering/transcript.ts` | 161-167 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 168-168 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 169-169 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 170-170 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/rendering/transcript.ts` | 171-173 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 174-174 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/rendering/transcript.ts` | 175-175 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 176-176 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 177-177 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 178-180 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 181-187 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 188-191 | `ba9f40090fe9` | Xubin Ren | fix(tui): inherit markdown foreground colors |
| `tui/src/rendering/transcript.ts` | 192-192 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 193-194 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 195-195 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 196-197 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 198-201 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/rendering/transcript.ts` | 202-204 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 205-214 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 215-215 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 216-216 | `3cf6ed60ced4` | chengyongru | fix(tui): remove redundant launch header details |
| `tui/src/rendering/transcript.ts` | 217-219 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 220-220 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 221-221 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 222-224 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 225-226 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 227-228 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 229-237 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 238-238 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 239-239 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 240-240 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 241-241 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 242-242 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 243-244 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 245-245 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 246-246 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/rendering/transcript.ts` | 247-247 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 248-248 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 249-252 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 253-254 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 255-256 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 257-263 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 264-267 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 268-268 | `a339966543d4` | chengyongru | fix(tui): preserve full UI in Herdr panes |
| `tui/src/rendering/transcript.ts` | 269-269 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 270-272 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 273-273 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 274-274 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 275-275 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 276-283 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 284-285 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 286-299 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 300-305 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 306-306 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 307-307 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 308-308 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 309-309 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 310-311 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/rendering/transcript.ts` | 312-315 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 316-316 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 317-321 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 322-322 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 323-323 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 324-324 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 325-326 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 327-329 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 330-330 | `192e2e90dc3f` | chengyongru | refactor(events): unify scoped runtime notifications across clients (#5670) |
| `tui/src/rendering/transcript.ts` | 331-356 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 357-358 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 359-359 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 360-362 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 363-363 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 364-365 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 366-367 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 368-368 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 369-373 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 374-376 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 377-377 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 378-381 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 382-382 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 383-391 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 392-393 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 394-394 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 395-395 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 396-398 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 399-399 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 400-400 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 401-401 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 402-402 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 403-408 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 409-410 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 411-429 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 430-430 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 431-434 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 435-436 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 437-439 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 440-440 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 441-442 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 443-444 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 445-445 | `5229989f281c` | chengyongru | feat: make context compaction visible in channels (#5656) |
| `tui/src/rendering/transcript.ts` | 446-446 | `f3386d965be4` | Xubin Ren | fix(tui): restore session header card |
| `tui/src/rendering/transcript.ts` | 447-447 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 448-448 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 449-449 | `35f2d086b0c8` | Xubin Ren | fix(tui): harden themes and platform coverage |
| `tui/src/rendering/transcript.ts` | 450-451 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 452-456 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 457-457 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 458-464 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/rendering/transcript.ts` | 465-498 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/rendering/transcript.ts` | 499-503 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 504-506 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 507-508 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 509-509 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 510-512 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 513-513 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 514-514 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 515-522 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 523-523 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 524-525 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 526-532 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 533-536 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 537-541 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 542-545 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 546-546 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/transcript.ts` | 547-547 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 548-548 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 549-549 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 550-551 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 552-552 | `4391bbf4da7f` | Xubin Ren | feat(tui): add agent interaction workflows |
| `tui/src/rendering/transcript.ts` | 553-564 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 565-569 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 570-577 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/transcript.ts` | 578-579 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 580-580 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 581-581 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 582-582 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 583-583 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 584-585 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 586-586 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 587-587 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 588-593 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 594-599 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 600-600 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 601-601 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 602-602 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 603-603 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 604-604 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 605-606 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 607-607 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 608-610 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 611-618 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 619-619 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 620-620 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 621-621 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 622-665 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 666-666 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 667-681 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 682-682 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/rendering/transcript.ts` | 683-691 | `4d204ba077a8` | chengyongru | feat(tui): support pasting clipboard images (#5563) |
| `tui/src/rendering/transcript.ts` | 692-693 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 694-710 | `455533169d5a` | Xubin Ren | fix(tui): distinguish fenced code blocks |
| `tui/src/rendering/transcript.ts` | 711-713 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 714-714 | `375185210b89` | chengyongru | feat(tui): render LaTeX as Unicode |
| `tui/src/rendering/transcript.ts` | 715-717 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 718-718 | `2d3045647ae7` | Xubin Ren | fix(tui): reflow markdown tables |
| `tui/src/rendering/transcript.ts` | 719-719 | `ba9f40090fe9` | Xubin Ren | fix(tui): inherit markdown foreground colors |
| `tui/src/rendering/transcript.ts` | 720-722 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 723-728 | `455533169d5a` | Xubin Ren | fix(tui): distinguish fenced code blocks |
| `tui/src/rendering/transcript.ts` | 729-734 | `2d3045647ae7` | Xubin Ren | fix(tui): reflow markdown tables |
| `tui/src/rendering/transcript.ts` | 735-740 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 741-742 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 743-744 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 745-745 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 746-746 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 747-747 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/rendering/transcript.ts` | 748-751 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 752-752 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/rendering/transcript.ts` | 753-753 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 754-754 | `8395bc825b4d` | Xubin Ren | refactor(tui): clarify conversation hierarchy |
| `tui/src/rendering/transcript.ts` | 755-762 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/rendering/transcript.ts` | 763-778 | `e9ac83d03f4c` | chengyongru | fix(tui): reduce redundant runtime chrome |
| `tui/src/rendering/transcript.ts` | 779-783 | `4f12e15237f8` | Xubin Ren | fix(tui): harden the interactive terminal experience |
| `tui/src/views/context-panel.test.ts` | 1-4 | `2b491340d808` | chengyongru | fix(tui): keep context view concise |
| `tui/src/views/context-panel.test.ts` | 5-5 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/context-panel.test.ts` | 6-43 | `2b491340d808` | chengyongru | fix(tui): keep context view concise |
| `tui/src/views/context-panel.ts` | 1-4 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 5-5 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/context-panel.ts` | 6-7 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 8-8 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/context-panel.ts` | 9-10 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 11-13 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/context-panel.ts` | 14-15 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 16-16 | `8f9bdb210e47` | Xubin Ren | feat(tui): refine quiet terminal interactions |
| `tui/src/views/context-panel.ts` | 17-31 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 32-32 | `2b491340d808` | chengyongru | fix(tui): keep context view concise |
| `tui/src/views/context-panel.ts` | 33-65 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 66-67 | `2b491340d808` | chengyongru | fix(tui): keep context view concise |
| `tui/src/views/context-panel.ts` | 68-79 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/context-panel.ts` | 80-80 | `2b491340d808` | chengyongru | fix(tui): keep context view concise |
| `tui/src/views/context-panel.ts` | 81-88 | `6301c0ab57c4` | Xubin Ren | feat(tui): unify session history and context |
| `tui/src/views/diff-viewer.test.ts` | 1-47 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 1-9 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 10-10 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/diff-viewer.ts` | 11-14 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 15-16 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/diff-viewer.ts` | 17-18 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 19-26 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/diff-viewer.ts` | 27-156 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 157-157 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/views/diff-viewer.ts` | 158-159 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/diff-viewer.ts` | 160-160 | `0035cd67cdba` | Xubin Ren | fix(tui): suppress terminal scrollbar glyphs |
| `tui/src/views/diff-viewer.ts` | 161-326 | `c0e9ce77efca` | Xubin Ren | feat(tui): complete session-native terminal workflow |
| `tui/src/views/footer-hints.test.ts` | 1-2 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.test.ts` | 3-3 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.test.ts` | 4-23 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.test.ts` | 24-26 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.test.ts` | 27-27 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.test.ts` | 28-29 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.test.ts` | 30-30 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.test.ts` | 31-31 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.test.ts` | 32-33 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 34-35 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.test.ts` | 36-36 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 37-37 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.test.ts` | 38-39 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.test.ts` | 40-41 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 42-43 | `c65127f791c3` | Xubin Ren | refine(tui): clarify model telemetry |
| `tui/src/views/footer-hints.test.ts` | 44-44 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 45-46 | `c65127f791c3` | Xubin Ren | refine(tui): clarify model telemetry |
| `tui/src/views/footer-hints.test.ts` | 47-50 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 51-51 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.test.ts` | 52-54 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.test.ts` | 55-55 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.test.ts` | 56-56 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 1-1 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/footer-hints.ts` | 2-9 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 10-13 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/footer-hints.ts` | 14-17 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 18-18 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/views/footer-hints.ts` | 19-19 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/footer-hints.ts` | 20-24 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 25-25 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/footer-hints.ts` | 26-32 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 33-34 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 35-35 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 36-38 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 39-39 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.ts` | 40-40 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 41-42 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.ts` | 43-44 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 45-56 | `5eb9039f0e58` | chengyongru | fix(tui): show context window usage in footer (#5679) |
| `tui/src/views/footer-hints.ts` | 57-70 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 71-74 | `9e47d8106cd5` | Xubin Ren | fix(tui): synchronize shared session clients |
| `tui/src/views/footer-hints.ts` | 75-77 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/footer-hints.ts` | 78-78 | `b218d3e7f83a` | chengyongru | feat(tui): autocomplete skill references |
| `tui/src/views/footer-hints.ts` | 79-80 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 81-81 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 82-90 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 91-91 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/footer-hints.ts` | 92-95 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 96-96 | `783d3817101a` | Xubin Ren | feat(tui): replace footer hints with model telemetry |
| `tui/src/views/footer-hints.ts` | 97-102 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 103-103 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/footer-hints.ts` | 104-106 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/footer-hints.ts` | 107-107 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/footer-hints.ts` | 108-110 | `2f78f7fbc5d7` | Xubin Ren | feat(tui): make follow-up queue explicit |
| `tui/src/views/recovery-notice.ts` | 1-6 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 7-7 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 8-8 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 9-9 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 10-12 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 13-13 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/recovery-notice.ts` | 14-15 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 16-21 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 22-31 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 32-33 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 34-46 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 47-47 | `8344066696ca` | Xubin Ren | style(tui): frame recovery decisions |
| `tui/src/views/recovery-notice.ts` | 48-48 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 49-49 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 50-52 | `8344066696ca` | Xubin Ren | style(tui): frame recovery decisions |
| `tui/src/views/recovery-notice.ts` | 53-57 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 58-67 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 68-74 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 75-81 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 82-83 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 84-88 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 89-114 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 115-115 | `8344066696ca` | Xubin Ren | style(tui): frame recovery decisions |
| `tui/src/views/recovery-notice.ts` | 116-154 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 155-155 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 156-156 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 157-159 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 160-160 | `2850114eab1a` | Xubin Ren | feat(tui): surface session activity states |
| `tui/src/views/recovery-notice.ts` | 161-162 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 163-163 | `7e66375f59a8` | Xubin Ren | fix(tui): clarify interrupted task actions |
| `tui/src/views/recovery-notice.ts` | 164-164 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 165-165 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 166-166 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 167-171 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 172-172 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 173-175 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/recovery-notice.ts` | 176-176 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/recovery-notice.ts` | 177-179 | `12029f88127f` | Xubin Ren | feat(runtime): add user-controlled turn recovery |
| `tui/src/views/runtime-controls.ts` | 1-4 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 5-5 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/runtime-controls.ts` | 6-10 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 11-11 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/views/runtime-controls.ts` | 12-12 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 13-14 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/runtime-controls.ts` | 15-16 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 17-18 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/runtime-controls.ts` | 19-24 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 25-26 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 27-33 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 34-34 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/views/runtime-controls.ts` | 35-35 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/views/runtime-controls.ts` | 36-40 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 41-41 | `c5d2e0ddf18b` | Xubin Ren | fix(tui): restore composer focus after runtime controls |
| `tui/src/views/runtime-controls.ts` | 42-56 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 57-57 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 58-89 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 90-90 | `7e60d52f0ed2` | Xubin Ren | fix(tui): prevent terminal cell artifacts |
| `tui/src/views/runtime-controls.ts` | 91-112 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 113-117 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 118-125 | `df14259717f1` | chengyongru | perf(tui): reduce cold-start latency |
| `tui/src/views/runtime-controls.ts` | 126-160 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 161-161 | `c5d2e0ddf18b` | Xubin Ren | fix(tui): restore composer focus after runtime controls |
| `tui/src/views/runtime-controls.ts` | 162-181 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 182-182 | `7e60d52f0ed2` | Xubin Ren | fix(tui): prevent terminal cell artifacts |
| `tui/src/views/runtime-controls.ts` | 183-188 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 189-189 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/views/runtime-controls.ts` | 190-196 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 197-199 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 200-203 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 204-204 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 205-207 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 208-212 | `467a7b533151` | chengyongru | fix(tui): refresh expired API credentials |
| `tui/src/views/runtime-controls.ts` | 213-225 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 226-226 | `0d54ad96e206` | Xubin Ren | perf(tui): keep long streams responsive |
| `tui/src/views/runtime-controls.ts` | 227-231 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 232-232 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/views/runtime-controls.ts` | 233-254 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 255-255 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/views/runtime-controls.ts` | 256-282 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 283-285 | `a6320171946f` | Xubin Ren | fix(tui): keep runtime controls interactive |
| `tui/src/views/runtime-controls.ts` | 286-290 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 291-291 | `c5d2e0ddf18b` | Xubin Ren | fix(tui): restore composer focus after runtime controls |
| `tui/src/views/runtime-controls.ts` | 292-312 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 313-313 | `6d6d58d329d1` | chengyongru | style(tui): simplify runtime header controls |
| `tui/src/views/runtime-controls.ts` | 314-314 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/runtime-controls.ts` | 315-315 | `e69159cdae96` | chengyongru | style(tui): replace header dots with spacing |
| `tui/src/views/runtime-controls.ts` | 316-331 | `03d982023aff` | Xubin Ren | feat(tui): add clickable runtime controls |
| `tui/src/views/usage-panel.test.ts` | 1-1 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 2-2 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/views/usage-panel.test.ts` | 3-5 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 6-6 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/usage-panel.test.ts` | 7-7 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 8-8 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.test.ts` | 9-10 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 11-11 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.test.ts` | 12-85 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 86-100 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.test.ts` | 101-195 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.test.ts` | 196-220 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/views/usage-panel.test.ts` | 221-243 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 1-5 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 6-6 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 7-7 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 8-8 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 9-12 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 13-13 | `f18423800ef1` | chengyongru | refactor(tui): organize source by feature boundaries (#5975) |
| `tui/src/views/usage-panel.ts` | 14-15 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 16-22 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 23-28 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 29-29 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 30-32 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 33-33 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 34-111 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 112-112 | `7d845046e0c6` | chengyongru | perf(tui): coalesce and cancel usage refreshes |
| `tui/src/views/usage-panel.ts` | 113-155 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 156-156 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 157-170 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 171-171 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 172-172 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/src/views/usage-panel.ts` | 173-173 | `cf25e91b1773` | chengyongru | fix(tui): preserve readability when terminal theme is unknown |
| `tui/src/views/usage-panel.ts` | 174-214 | `b7fc4146e023` | chengyongru | feat(tui): add /usage context and token charts |
| `tui/tsconfig.json` | 1-7 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/tsconfig.json` | 8-9 | `3fdf7ae64a46` | Xubin Ren | chore(tui): tighten TypeScript checks |
| `tui/tsconfig.json` | 10-10 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |
| `tui/tsconfig.json` | 11-12 | `3fdf7ae64a46` | Xubin Ren | chore(tui): tighten TypeScript checks |
| `tui/tsconfig.json` | 13-17 | `ce070c832d3d` | Xubin Ren | feat(cli): add native TypeScript terminal UI |

The code itself and the Git attribution were not rewritten. Commit authorship is historical metadata, not proof of copyright ownership or license compliance. Release notices and Bun/OpenTUI materials, exact clean-SHA build, applicable license review and owner review remain separate gates. The source-offer and relinking files listed in this historical map were removed by Bill's 2026-10-30 decision, recorded in the active Stage-2 tracker.
