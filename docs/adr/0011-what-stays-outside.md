# ADR-0011: the lab closed at v2.0 - what stays outside, and why

- Status: accepted
- Date: 2026-11-25

## Context

Ten decisions brought the lab from a three-node cluster with self-signed certificates and an exact
apt pin to one where every claim of the README is a number in `docs/evidence/`, the pins are
branches, nothing listens in plain text, and the pipeline proves every pull request. Each ADR left
something for "the next step"; at v2.0 those are either done or named here as outside the lab.

## Decision

Done, and where: a CA with every server verified (ADR-0009, ADR-0010); branch pins recorded per run
(ADR-0006); the evidence committed by a bot and released with every tag (ADR-0008); the checks and
the ruleset (ADR-0007). The TLS section of ADR-0005 is superseded by ADR-0009 and ADR-0010.

Outside the lab, for good - each a different system or a different measurement, not a missing piece
of this one:

- **A second site**: a standby cluster, an etcd witness, a second repository (ADR-0004).
- **Object storage for the repository**: the `repo2-type=s3` block and the bucket's shape are in
  ADR-0004; nothing here provides S3, and MinIO would prove the API and nothing above it.
- **Alertmanager and Grafana**: the rules are the contract; routing and dashboards are a site's.
- **Failover under load**: a different number from a different measurement (README).
- **A mirror of the apt repository**: ADR-0006 answers the same need by recording the build.
- **Client certificates and authentication on the read endpoints**: passwords over verified TLS
  to PostgreSQL, the CA alone for `/health` and `/metrics` (ADR-0009, ADR-0010).
- **A secret manager and managed host keys**: the secrets rest on the hosts in files their service
  reads, host keys are not checked - a real inventory brings both (README).
- **A real watchdog**: `soft_noboot=1` here; a host that owns its kernel reboots (ADR-0005).

## Consequences

The README's "What is not proved here" is the complete list of what this lab does not show; every
item there is either in this ADR or in the one it names. A change after v2.0 is a new decision with
a new ADR, not a line added to this one.
