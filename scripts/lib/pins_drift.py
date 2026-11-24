"""Every pin of versions.yml against what the repositories offer now: a markdown table, DRIFT rows.

ADR-0006: an apt pin is a branch; the candidate build must match it (fnmatch), else the branch
has moved. A release asset pin is exact; a newer release is a drift too. The pins-watch workflow
runs this on a runner that has the PGDG repository (apt-cache policy) and gh (the release API).
"""
import fnmatch
import json
import subprocess
import sys

import yaml

APT = [
    ("postgresql-%(pg)s", "postgresql_package_version"),
    ("postgresql-client-%(pg)s", "postgresql_package_version"),
    ("patroni", "patroni_version"),
    ("pgbackrest", "pgbackrest_version"),
    ("pgbouncer", "pgbouncer_version"),
    ("python3-psycopg2", "psycopg2_version"),
    ("haproxy", "haproxy_version"),
    ("keepalived", "keepalived_version"),
]
RELEASES = [
    ("etcd-io/etcd", "etcd_version"),
    ("prometheus/prometheus", "prometheus_version"),
    ("prometheus-community/postgres_exporter", "postgres_exporter_version"),
]


def candidate(package):
    """The Candidate line of apt-cache policy ('' when none)."""
    out = subprocess.run(["apt-cache", "policy", package], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.strip().startswith("Candidate:"):
            return line.split(":", 1)[1].strip()
    return ""


def latest_release(project):
    """The latest release tag of a GitHub project, without a leading v ('' when gh failed)."""
    done = subprocess.run(["gh", "api", "repos/%s/releases/latest" % project], capture_output=True, text=True)
    if done.returncode != 0:
        return ""
    return json.loads(done.stdout).get("tag_name", "").lstrip("v")


def main():
    """Print the table; the exit code is 0 either way (the workflow reads the DRIFT rows)."""
    with open("group_vars/all/versions.yml", encoding="utf-8") as handle:
        pins = yaml.safe_load(handle)
    print("| State | What | Pin | Now |")
    print("|---|---|---|---|")
    for pattern, key in APT:
        package = pattern % {"pg": pins["postgresql_version"]}
        now = candidate(package)
        ok = bool(now) and fnmatch.fnmatchcase(now, pins[key])
        print("| %s | apt %s | `%s` | `%s` |" % ("ok" if ok else "DRIFT", package, pins[key], now or "(none)"))
    for project, key in RELEASES:
        now = latest_release(project)
        ok = bool(now) and now == pins[key]
        print("| %s | release %s | `%s` | `%s` |" % ("ok" if ok else "DRIFT", project, pins[key], now or "(none)"))
    sys.exit(0)


if __name__ == "__main__":
    main()
