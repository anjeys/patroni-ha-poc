# ADR-0010: the periphery on the PKI - the REST API, the monitoring, the backup repository

- Status: accepted
- Date: 2026-11-24

## Context

ADR-0009 put the data plane on the lab CA and left the rest as ADR-0005 had it: Patroni's REST
API on plain http (HAProxy's health checks and Prometheus read it), the metrics of the exporter,
HAProxy and Prometheus in plain text, the exporter connected as the superuser over the unix
socket, the backup repository unencrypted. Read on the live lab: Patroni 4.1.5's `restapi` takes
`certfile`, `keyfile` and `cafile` and `ctl.cacert` is what the other members verify with; HAProxy
2.8 accepts `check-ssl ca-file ... verify required` on a server and `bind ... ssl crt` on a
frontend; postgres_exporter 0.21 and Prometheus 3.16 take `--web.config.file` (the exporter
toolkit's `tls_server_config`); a scrape config with `scheme: https` and `tls_config.ca_file`
passes promtool; pgBackRest 2.60 encrypts a repository with `repo-cipher-type aes-256-cbc` and a
passphrase, client-side.

## Decision

The REST API serves the node's certificate; HAProxy's health checks verify it against the lab CA
(the chain, not the name: it addresses nodes by address); `ctl.cacert` makes patronictl and the
inter-node requests verify it too. The stats and metrics frontend of HAProxy, the exporter and
Prometheus serve TLS with their host's certificate through the exporter toolkit's web config, and
Prometheus verifies every target against the CA. The exporter connects as `postgres_exporter`, a
role with `pg_monitor` and a generated password, over TLS to the loopback with `verify-full` - no
superuser in a unit file. The backup repository is encrypted with a passphrase from the secrets;
the repository host's config, which carries it, is readable by postgres only. `scripts/lab.sh
status` reaches Prometheus over https with the CA.

## Consequences

Nothing of the lab listens in plain text. Two more secrets (the exporter's password, the
repository passphrase) are generated once by `lab.sh`; a repository made without a cipher cannot
be switched to one, so a lab that predates this decision is reset. Patroni's REST API still has no
client authentication on its read endpoints - HAProxy and Prometheus read them with the CA only;
the write endpoints keep their password. Alertmanager and Grafana stay outside the lab (ADR-0005).
