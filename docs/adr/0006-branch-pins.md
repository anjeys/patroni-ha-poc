# ADR-0006: a package pin is a branch; the build is read at install time and recorded

- Status: accepted
- Date: 2026-11-24

## Context

`group_vars/all/versions.yml` pinned exact apt builds (`18.6-1.pgdg24.04+2`) on purpose: a
stale pin fails the run instead of installing something else. PGDG keeps only the latest
build of each package, and so does Ubuntu's archive for its security updates. The weekly
drills went red three weeks in a row (runs #15-#17) on exactly that: `postgresql-client-18`
had moved to `18.7-1.pgdg24.04+5` and apt could not satisfy the old pin. A pin against a
repository that keeps no history is a timer, not a guarantee, and the thing it guarantees -
that nobody installs a build the author did not see - is answered as well by recording
the build that was installed.

## Decision

An apt pin names a branch: `postgresql-18=18.*`, `patroni=4.1.*`, `pgbackrest=2.60.*`,
`pgbouncer=1.26.*`, `python3-psycopg2=2.9.*`, `haproxy=2.8.*`, `keepalived=1:2.2.*`. apt
and Ansible's apt module accept the glob and install the branch's current build; a second
run changes nothing (probed: resolved in check mode, installed, `changed=false` afterwards,
the epoch glob included). `scripts/lab.sh versions` reads the build every host actually has
(`dpkg-query`, the binaries' `--version`), checks each against its branch and writes
`evidence/versions-<utc>.json`; the drills workflow runs it, so every weekly run records what
it ran on. A new branch (PostgreSQL 19, pgBackRest 2.61) is a commit that changes the pin.

Release assets stay exact: etcd, Prometheus and postgres_exporter are a version and the
sha256 of the file, bumped together, because a GitHub release keeps its history and a
checksum of a file that moved is a file that moved.

## Consequences

A rebuild by PGDG no longer breaks the lab; a new upstream patch release within the branch
is installed on the next run and is visible in the evidence. What is lost is the exact
reproduction of one build on one day; what is kept is the proof of which build a run used.
A minor-version jump inside a branch (18.6 -> 18.7) is a PostgreSQL patch release and is
what the branch means. Not chosen: a mirror of the apt repository (a second system to run
for one lab) and pip-installed Patroni (the lab is packaged on purpose, ADR-0001).
