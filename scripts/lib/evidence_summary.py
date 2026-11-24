"""A markdown table of every evidence file in evidence/: the drill, when, its numbers, the verdict.

The drills workflow appends it to the job summary (ADR-0007); on a laptop it prints. Exit 1 when
any row is not a pass, so a summary of a bad run is red too.
"""
import glob
import json
import sys


def row(doc):
    """One table row; (text, passed)."""
    kind = doc["schema"].split(".")[-2]
    if kind == "failover":
        watchdog = doc.get("watchdog", {})
        numbers = "new leader %s s, first write %s s, fence %s s" % (
            doc["seconds_to_new_leader"], doc["seconds_to_first_write"],
            watchdog.get("fired_seconds_after_kill", "off"))
        # files older than 9e2e194 carry no flag: the drill's rule, fired < ttl, decides them
        fired = watchdog.get("fired_seconds_after_kill")
        ttl = int(doc.get("dcs", {}).get("ttl", 0))
        by_numbers = fired is not None and ttl > 0 and fired < ttl
        fenced = watchdog.get("fence_before_key_expiry", by_numbers or watchdog.get("mode") == "off")
        passed = bool(doc["marker_survived"] and fenced)
    elif kind == "access":
        numbers = "VIP moved %s s, first write %s s" % (doc["seconds_to_vip_move"], doc["seconds_to_first_write"])
        passed = bool(doc["marker_survived"])
    elif kind == "pitr":
        numbers = "restored to %s" % doc["restore_target"]
        passed = bool(doc["marker_restored"])
    elif kind == "versions":
        numbers = "%d packages and binaries resolved" % len(doc["resolved"])
        passed = bool(doc["every_build_in_its_branch"])
    else:
        numbers, passed = "unknown schema", False
    return "| %s | %s | %s | %s |" % (kind, doc["created_at"], numbers, "pass" if passed else "FAIL"), passed


def main():
    """Print the table; exit 1 on any FAIL or when there is no evidence at all."""
    files = sorted(glob.glob("evidence/*.json"))
    print("| Drill | When (UTC) | Numbers | Verdict |")
    print("|---|---|---|---|")
    bad = 0
    for name in files:
        with open(name, encoding="utf-8") as handle:
            text, passed = row(json.load(handle))
        print(text)
        bad += not passed
    print()
    print("%d evidence files, %d not a pass" % (len(files), bad))
    sys.exit(1 if bad or not files else 0)


if __name__ == "__main__":
    main()
