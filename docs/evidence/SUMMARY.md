# Evidence of CI run 45462777435

| Drill | When (UTC) | Numbers | Verdict |
|---|---|---|---|
| access | 2026-11-24T18:49:18+00:00 | VIP moved 4 s, first write 4 s | pass |
| failover | 2026-11-24T18:49:45+00:00 | new leader 22 s, first write 22 s, fence 17 s | pass |
| pitr | 2026-11-24T18:50:30+00:00 | restored to 2026-11-24 18:49:56 | pass |
| versions | 2026-11-24T18:49:13+00:00 | 11 packages and binaries resolved | pass |

4 evidence files, 0 not a pass
