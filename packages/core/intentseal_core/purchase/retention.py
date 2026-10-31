import argparse
from .common import db, now


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--days", type=int, default=7)
    p.add_argument("--apply", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    if a.days < 1:
        raise ValueError("Minimum one day")
    cutoff = now() - a.days * 86400
    with db() as c:
        expired = c.execute("SELECT count(*) n FROM sessions WHERE expires<%s", (now(),)).fetchone()["n"]
        callbacks = c.execute(
            "SELECT count(*) n FROM callbacks WHERE (body->>'timestamp')::double precision<%s", (cutoff,)
        ).fetchone()["n"]
        print(
            {
                "expired_sessions": expired,
                "old_callbacks": callbacks,
                "apply": a.apply and not a.dry_run,
                "audit_and_effect_history_retained": True,
            }
        )
        if a.apply and not a.dry_run:
            c.execute("DELETE FROM sessions WHERE expires<%s", (now(),))
            c.execute("DELETE FROM callbacks WHERE (body->>'timestamp')::double precision<%s", (cutoff,))


if __name__ == "__main__":
    main()
