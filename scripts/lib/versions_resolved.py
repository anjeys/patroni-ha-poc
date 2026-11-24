"""The build every branch pin resolved to, read from the running lab and written as evidence.

ADR-0006: an apt pin is a branch, so the installed build is the fact a run must record.
dpkg-query on each container for the apt packages, the binaries' own --version for the
release assets; each resolved value is matched against its pin (fnmatch for a glob, a
substring for an exact version) and the run fails on a mismatch.
"""
import fnmatch
import json
import subprocess
import sys
from datetime import datetime, timezone

import yaml

NODES = ["node1", "node2", "node3"]
BALANCERS = ["balancer", "balancer2"]
BACKUP = ["backup"]


def docker_exec(host, argv):
    """stdout+stderr of a command in a container, stripped ('' when it failed)."""
    done = subprocess.run(["docker", "exec", host] + argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    return (done.stdout + done.stderr).strip() if done.returncode == 0 else ""


def dpkg_version(host, package):
    """The installed version of an apt package."""
    return docker_exec(host, ["dpkg-query", "-W", "-f=${Version}", package])


def binary_version(host, argv):
    """What a binary says about itself (first line)."""
    return docker_exec(host, argv).splitlines()[0] if docker_exec(host, argv) else ""


def main():
    """Resolve, compare, write evidence; exit 1 on any mismatch."""
    with open("group_vars/all/versions.yml", encoding="utf-8") as handle:
        pins = yaml.safe_load(handle)
    pg = pins["postgresql_version"]
    apt = [
        (NODES, "postgresql-%s" % pg, pins["postgresql_package_version"]),
        (NODES + BALANCERS + BACKUP, "postgresql-client-%s" % pg, pins["postgresql_package_version"]),
        (NODES, "patroni", pins["patroni_version"]),
        (NODES + BACKUP, "pgbackrest", pins["pgbackrest_version"]),
        (NODES, "python3-psycopg2", pins["psycopg2_version"]),
        (BALANCERS, "pgbouncer", pins["pgbouncer_version"]),
        (BALANCERS, "haproxy", pins["haproxy_version"]),
        (BALANCERS, "keepalived", pins["keepalived_version"]),
    ]
    binaries = [
        (NODES, "etcd", ["/usr/local/bin/etcd", "--version"], pins["etcd_version"]),
        (NODES, "postgres_exporter", ["/usr/local/bin/postgres_exporter", "--version"],
         pins["postgres_exporter_version"]),
        (BACKUP, "prometheus", ["/usr/local/bin/prometheus", "--version"], pins["prometheus_version"]),
    ]
    resolved = {}
    bad = 0
    for hosts, package, pin in apt:
        for host in hosts:
            got = dpkg_version(host, package)
            ok = bool(got) and fnmatch.fnmatchcase(got, pin)
            bad += not ok
            resolved.setdefault(package, {})[host] = got
            print("  %-4s %-9s %-22s pin %-10s got %s" % ("ok" if ok else "BAD", host, package, pin, got or "(none)"))
    for hosts, name, argv, pin in binaries:
        for host in hosts:
            got = binary_version(host, argv)
            ok = pin in got
            bad += not ok
            resolved.setdefault(name, {})[host] = got
            print("  %-4s %-9s %-22s pin %-10s got %s" % ("ok" if ok else "BAD", host, name, pin, got or "(none)"))
    stamp = datetime.now(timezone.utc)
    path = "evidence/versions-%s.json" % stamp.strftime("%Y%m%dT%H%M%SZ")
    subprocess.run(["mkdir", "-p", "evidence"], check=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({
            "schema": "patroni.versions.v1",
            "created_at": stamp.isoformat(timespec="seconds"),
            "pins": {key: value for key, value in pins.items() if key.endswith("_version")},
            "resolved": resolved,
            "every_build_in_its_branch": bad == 0,
        }, handle, indent=2)
        handle.write("\n")
    print("  evidence: %s (%d outside its branch)" % (path, bad))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
