#!/usr/bin/env bash
# etcd authentication, once (ADR-0009): root with its password, a patroni user whose role may read
# and write the Patroni namespace only, authentication enabled. Idempotent: a member that already
# authenticates reports STATE=enabled and nothing is touched. Passwords come from the environment
# and are never printed; a wrong root password on an authenticating cluster fails here, loudly.
set -euo pipefail
ctl() { etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/etcd/pki/ca.crt "$@"; }
if ctl --user "root:$ETCD_ROOT_PW" auth status 2>/dev/null | grep -q 'Authentication Status: true'; then
  echo STATE=enabled
  exit 0
fi
ctl user list | grep -qx root || ctl user add "root:$ETCD_ROOT_PW" >/dev/null
ctl role list | grep -qx patroni || ctl role add patroni >/dev/null
ctl role grant-permission --prefix=true patroni readwrite /db/ >/dev/null
ctl user list | grep -qx patroni || ctl user add "patroni:$ETCD_PATRONI_PW" >/dev/null
ctl user grant-role patroni patroni >/dev/null
ctl auth enable >/dev/null
echo STATE=changed
