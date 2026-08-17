"""Store-lifecycle panel — the shared base for every analysis.

One row per store: when it first appeared, when it last left, how many separate
authorization spells it held. Every entry/exit/stock figure in the posts is a
group-by on this table, so they cannot drift from each other.

The subtlety this table exists to handle: 37,941 stores hold multiple spells
because authorizations lapse and resume. A store that lapses in 2014 and returns
in 2016 is not a new store in 2016, and counting spells instead of stores
overstates both entries and exits. `first_auth`/`last_end` collapse each store
to one lifespan; `n_spells` keeps the lapses visible.
"""
from datetime import date

from config import connect

# Only stores the map would draw: excludes missing, off-world and wrong-state
# coordinates. Keeps every figure consistent with the published map.
PANEL_SQL = """
CREATE OR REPLACE TEMP TABLE panel AS
SELECT
    d.record_id,
    d.format,
    d.store_type_usda,
    d.brand,
    d.ownership,
    d.state,
    d.county,
    d.zip_code,
    d.city,
    d.name_norm,
    d.latitude,
    d.longitude,
    lower(trim(d.street_number)) || '|' || lower(trim(d.street_name)) || '|' ||
    lower(trim(d.city)) || '|' || d.state                       AS address_key,
    min(f.auth_date)                                            AS first_auth,
    CASE WHEN bool_or(f.end_date IS NULL) THEN NULL
         ELSE max(f.end_date) END                               AS last_end,
    count(*)                                                    AS n_spells
FROM dim_store d
JOIN fact_spell f USING (record_id)
WHERE d.mappable AND NOT f.date_anomaly
GROUP BY ALL
"""

# Stock has to come from spells, not from first_auth/last_end: a store that
# lapsed across a year-end is not active on that date even though its lifespan
# brackets it.
STOCK_SQL = """
CREATE OR REPLACE TEMP TABLE stock AS
SELECT y.yr, d.format, d.brand, count(DISTINCT f.record_id) AS n
FROM generate_series(?, ?) AS y(yr)
JOIN fact_spell f ON f.auth_date <= make_date(y.yr, 12, 31)
                 AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr, 12, 31))
                 AND NOT f.date_anomaly
JOIN dim_store d ON d.record_id = f.record_id AND d.mappable
GROUP BY ALL
"""

FIRST_YEAR, LAST_YEAR = 2006, 2025


def build(con=None):
    """Create the `panel` and `stock` temp tables on a connection."""
    own = con or connect(read_only=True)
    own.execute(PANEL_SQL)
    own.execute(STOCK_SQL, [FIRST_YEAR, LAST_YEAR])
    return own


def lifecycle(con, by="format", where="TRUE"):
    """Entries, exits and stock per year for each value of `by`.

    Entries count stores whose FIRST authorization falls in the year, so a
    reinstatement is not an entry. Exits count stores whose LAST authorization
    ended in the year, so a lapse that later resumed is not an exit.
    """
    return con.execute(f"""
        WITH ent AS (
            SELECT year(first_auth) AS yr, {by} AS k, count(*) AS entries
            FROM panel WHERE {where} GROUP BY 1, 2),
        ext AS (
            SELECT year(last_end) AS yr, {by} AS k, count(*) AS exits
            FROM panel WHERE {where} AND last_end IS NOT NULL GROUP BY 1, 2),
        stk AS (
            SELECT s.yr, {'s.format' if by == 'format' else 's.brand'} AS k,
                   sum(s.n) AS stock
            FROM stock s GROUP BY 1, 2)
        SELECT stk.yr, stk.k,
               coalesce(ent.entries, 0) AS entries,
               coalesce(ext.exits, 0)   AS exits,
               stk.stock
        FROM stk
        LEFT JOIN ent ON ent.yr = stk.yr AND ent.k IS NOT DISTINCT FROM stk.k
        LEFT JOIN ext ON ext.yr = stk.yr AND ext.k IS NOT DISTINCT FROM stk.k
        WHERE stk.yr BETWEEN {FIRST_YEAR} AND {LAST_YEAR}
        ORDER BY stk.k, stk.yr
    """).df()


def flows(con, by="format", where="TRUE"):
    """Exact year-over-year decomposition of the active set.

    stock(y) - stock(y-1) == new + returning - departed - lapsed, with no
    residual. Splitting arrivals into genuinely new stores versus reinstatements,
    and departures into permanent exits versus lapses that later resume, is what
    separates "the format stopped attracting new stores" from "these stores
    died" — the distinction post 2 turns on.
    """
    return con.execute(f"""
        WITH act AS (
            SELECT y.yr, f.record_id
            FROM generate_series({FIRST_YEAR}, {LAST_YEAR}) AS y(yr)
            JOIN fact_spell f ON f.auth_date <= make_date(y.yr, 12, 31)
                             AND (f.end_date IS NULL OR f.end_date >= make_date(y.yr, 12, 31))
                             AND NOT f.date_anomaly
            GROUP BY 1, 2),
        tagged AS (
            SELECT a.yr, a.record_id, p.{by} AS k, p.first_auth, p.last_end
            FROM act a JOIN panel p USING (record_id)
            WHERE {where}),
        pairs AS (
            SELECT coalesce(cur.yr, prev.yr + 1) AS yr,
                   coalesce(cur.k, prev.k)       AS k,
                   cur.record_id IS NOT NULL     AS in_now,
                   prev.record_id IS NOT NULL    AS in_prev,
                   coalesce(cur.first_auth, prev.first_auth) AS first_auth,
                   coalesce(cur.last_end, prev.last_end)     AS last_end
            FROM tagged cur
            FULL OUTER JOIN tagged prev
              ON prev.record_id = cur.record_id AND prev.yr = cur.yr - 1)
        SELECT yr, k,
            count(*) FILTER (WHERE in_now AND NOT in_prev
                             AND first_auth > make_date(yr - 1, 12, 31))      AS new,
            count(*) FILTER (WHERE in_now AND NOT in_prev
                             AND first_auth <= make_date(yr - 1, 12, 31))     AS returning,
            count(*) FILTER (WHERE in_prev AND NOT in_now
                             AND last_end IS NOT NULL
                             AND last_end <= make_date(yr, 12, 31))           AS departed,
            count(*) FILTER (WHERE in_prev AND NOT in_now
                             AND (last_end IS NULL
                                  OR last_end > make_date(yr, 12, 31)))       AS lapsed,
            count(*) FILTER (WHERE in_now)                                    AS stock
        FROM pairs
        WHERE yr BETWEEN {FIRST_YEAR + 1} AND {LAST_YEAR}
        GROUP BY 1, 2 ORDER BY 2, 1
    """).df()


def verify(con) -> None:
    """Assert the panel agrees with the shipped pipeline and is self-consistent."""
    from snapshot import snapshot

    failures = []

    def check(name, actual, expected, tol=0):
        ok = abs(actual - expected) <= tol
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {actual:,} (expected {expected:,}"
              f"{f' ±{tol}' if tol else ''})")
        if not ok:
            failures.append(name)

    print("\n1. Panel reconciles to snapshot() — the figure the map ships")
    for yr in (2006, 2015, 2025):
        snap = snapshot(date(yr, 12, 31), con=con)
        want = int(snap["mappable"].sum())
        got = con.execute("SELECT sum(n) FROM stock WHERE yr = ?", [yr]).fetchone()[0]
        check(f"{yr} total stock", int(got), want)

    print("\n2. Flow decomposition closes exactly (no residual)")
    fl = flows(con)
    tot = fl.groupby("yr")[["new", "returning", "departed", "lapsed", "stock"]].sum()
    tot["prev"] = tot["stock"].shift(1)
    tot["resid"] = (tot["stock"] - tot["prev"]) - (
        tot["new"] + tot["returning"] - tot["departed"] - tot["lapsed"])
    worst = tot["resid"].abs().max()
    check("largest residual across all 19 year-pairs", int(worst), 0)
    print("     national flows:  yr     new  return  depart   lapse    stock")
    for yr in (2012, 2018, 2024):
        r = tot.loc[yr]
        print(f"                    {yr}  {int(r['new']):>6,} {int(r['returning']):>7,}"
              f" {int(r['departed']):>7,} {int(r['lapsed']):>7,} {int(r['stock']):>8,}")

    print("\n3. Anchors measured before this code existed")
    q = lambda s, p=None: con.execute(s, p or []).fetchone()[0]
    check("Dollar Store stock 2024",
          int(q("SELECT sum(n) FROM stock WHERE yr=2024 AND format='Dollar Store'")), 36_964)
    check("Grocery (Small) entries 2018",
          q("SELECT count(*) FROM panel WHERE format='Grocery (Small)' "
            "AND year(first_auth)=2018"), 1_051)
    check("Grocery (Small) stock 2024",
          int(q("SELECT sum(n) FROM stock WHERE yr=2024 AND format='Grocery (Small)'")), 8_398)
    check("stores holding multiple spells",
          q("SELECT count(*) FROM panel WHERE n_spells > 1"), 37_908)

    if failures:
        raise SystemExit("PANEL VERIFICATION FAILED: " + ", ".join(failures))
    print("\n  panel verified")


if __name__ == "__main__":
    con = build()
    verify(con)
