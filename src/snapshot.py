"""Point-in-time views of SNAP-authorized retailers.

Every map version — the current snapshot and each historical year — comes
through here, so all of them share one taxonomy and one definition of "active".

A store is active on date D if any authorization spell covers D. Stores lapse
and are reinstated (37,941 have multiple spells), so this cannot be reduced to a
single date range per store.
"""
import sys
from datetime import date, datetime

from config import DATA_CUTOFF, EARLIEST_SNAPSHOT, connect

ACTIVE_SQL = """
SELECT d.*
FROM dim_store d
WHERE EXISTS (
    SELECT 1 FROM fact_spell f
    WHERE f.record_id = d.record_id
      AND NOT f.date_anomaly
      AND f.auth_date <= $asof
      AND (f.end_date IS NULL OR f.end_date >= $asof)
)
"""


def _coerce(d) -> date:
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.strptime(str(d), "%Y-%m-%d").date()


def snapshot(as_of=DATA_CUTOFF, con=None):
    """Return a DataFrame of stores authorized on `as_of`."""
    d = _coerce(as_of)
    if d < EARLIEST_SNAPSHOT:
        raise ValueError(
            f"{d} precedes the archive window. The file only contains retailers "
            f"authorized at some point in the last 20 years, so any snapshot "
            f"before {EARLIEST_SNAPSHOT} is incomplete by construction — stores "
            f"that opened and closed before the window are absent entirely."
        )
    if d > DATA_CUTOFF:
        print(
            f"warning: {d} is past the {DATA_CUTOFF} data cutoff; results reflect "
            f"the cutoff, not {d}.",
            file=sys.stderr,
        )

    own = con or connect(read_only=True)
    try:
        return own.execute(ACTIVE_SQL, {"asof": d}).df()
    finally:
        if con is None:
            own.close()


def counts(as_of=DATA_CUTOFF, by="format", con=None):
    """Active store counts on `as_of`, grouped by a dim_store column."""
    df = snapshot(as_of, con=con)
    return df.groupby(by, dropna=False).size().sort_values(ascending=False)


def series(start=2006, end=2025, month=12, day=31, by=None):
    """Active counts for each year — the backbone of the historical map."""
    con = connect(read_only=True)
    try:
        out = {}
        for yr in range(start, end + 1):
            d = min(date(yr, month, day), DATA_CUTOFF)
            out[yr] = counts(d, by=by, con=con) if by else len(snapshot(d, con=con))
        return out
    finally:
        con.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    by = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--by=")), None)
    as_of = args[0] if args else DATA_CUTOFF

    df = snapshot(as_of)
    print(f"Active SNAP retailers as of {_coerce(as_of)}: {len(df):,}\n")
    for col in ([by] if by else ["format", "ownership"]):
        print(f"by {col}:")
        for k, n in df.groupby(col, dropna=False).size().sort_values(ascending=False).items():
            print(f"  {str(k):28} {n:>8,}")
        print()
