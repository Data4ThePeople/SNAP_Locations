"""Derive the two classification axes onto dim_store.

Axis 1 — format: USDA's store type, cleaned, with Dollar Store split out of the
Combination Grocery/Other bucket (~23% of all retailers and the fastest-growing
segment in the 20-year history).

Axis 2 — ownership: chain / independent / unknown, derived from store names via
the curated crosswalk. Kept deliberately separate from format so a map version
can slice either way, or cross them ("independent supermarkets").

Name frequency is computed over ALL 661,456 stores, never over a single
snapshot, so a store's ownership label does not drift between map versions.
"""
import pandas as pd

from brands import normalize, resolve
from config import connect

# USDA store type -> display format. Specialty sub-types are preserved.
FORMAT_MAP = {
    "Supermarket": "Supermarket",
    "Super Store": "Super Store",
    "Large Grocery Store": "Grocery (Large)",
    "Medium Grocery Store": "Grocery (Medium)",
    "Small Grocery Store": "Grocery (Small)",
    "Convenience Store": "Convenience Store",
    "Combination Grocery/Other": "Combination Grocery/Other",
    "Meat/Poultry Specialty": "Specialty (Meat/Poultry)",
    "Bakery Specialty": "Specialty (Bakery)",
    "Seafood Specialty": "Specialty (Seafood)",
    "Fruits/Veg Specialty": "Specialty (Fruits/Veg)",
    "Farmers' Market": "Farmers' Market",
    "Military Commissary": "Military Commissary",
    "Delivery Route": "Delivery Route",
    "Food Buying Co-op": "Food Buying Co-op",
    "Wholesaler": "Wholesaler",
    "Unknown": "Unknown",
}

DOLLAR_FORMAT = "Dollar Store"

# Categories that establish common ownership. fuel_branded is excluded on
# purpose: a Shell or BP banner identifies the fuel supplier, not the store
# operator, and those sites are overwhelmingly franchisee-owned. Calling them
# "chain" would silently inflate chain counts, so they resolve to unknown.
CHAIN_CATEGORIES = {
    "dollar", "drug", "mass", "club", "grocery", "convenience", "variety", "specialty",
}
UNKNOWN_CATEGORIES = {"fuel_branded", "generic"}

# Voluntary alliances and co-ops: the storefront carries a shared banner but the
# store is independently owned. IGA is literally the Independent Grocers
# Alliance, so counting its members as chain would invert the axis for them.
# The brand is still recorded; only the ownership call differs.
BANNER_CATEGORIES = {"banner"}

# An unresolved name held by at most this many stores nationally is treated as
# independent. Small local operators legitimately run a handful of locations; a
# name above this that escaped the crosswalk is more likely a regional chain, so
# it stays unknown rather than being forced either way.
INDEPENDENT_MAX_LOCATIONS = 4


def classify() -> None:
    con = connect()
    df = con.execute(
        "SELECT record_id, store_name, store_type_usda, state FROM dim_store"
    ).df()
    print(f"Classifying {len(df):,} stores")

    df["name_norm"] = df["store_name"].fillna("").map(normalize)
    print(f"  {df['name_norm'].nunique():,} distinct normalized names")

    # Resolution is per store because some rules are qualified by state or
    # store type — "Metro Market" is Kroger's in Wisconsin and unrelated
    # convenience stores in California. The pattern match itself is cached per
    # distinct name inside brands.candidates().
    resolved = [
        resolve(n, s, t)
        for n, s, t in zip(df["name_norm"], df["state"], df["store_type_usda"])
    ]
    df["brand"] = [r[0] for r in resolved]
    df["chain_category"] = [r[1] for r in resolved]

    freq = df["name_norm"].value_counts()
    df["name_freq"] = df["name_norm"].map(freq)

    def ownership(row):
        cat = row["chain_category"]
        if cat in CHAIN_CATEGORIES:
            return "chain"
        if cat in BANNER_CATEGORIES:
            return "independent"
        if cat in UNKNOWN_CATEGORIES:
            return "unknown"
        if not row["name_norm"]:
            return "unknown"
        return "independent" if row["name_freq"] <= INDEPENDENT_MAX_LOCATIONS else "unknown"

    df["ownership"] = df.apply(ownership, axis=1)
    df["is_dollar_store"] = df["chain_category"].eq("dollar")
    df["format"] = df["store_type_usda"].map(FORMAT_MAP).fillna(df["store_type_usda"])
    df.loc[df["is_dollar_store"], "format"] = DOLLAR_FORMAT

    out = df[["record_id", "name_norm", "brand", "chain_category",
              "ownership", "is_dollar_store", "format", "name_freq"]]
    con.register("classified", out)
    con.execute("""
        ALTER TABLE dim_store ADD COLUMN IF NOT EXISTS chain_category VARCHAR;
        ALTER TABLE dim_store ADD COLUMN IF NOT EXISTS name_freq BIGINT;
    """)
    con.execute("""
        UPDATE dim_store d SET
            name_norm       = c.name_norm,
            brand           = c.brand,
            chain_category  = c.chain_category,
            ownership       = c.ownership,
            is_dollar_store = c.is_dollar_store,
            format          = c.format,
            name_freq       = c.name_freq
        FROM classified c
        WHERE d.record_id = c.record_id
    """)

    print("\n  ownership (all stores):")
    for own, n in con.execute(
        "SELECT ownership, count(*) FROM dim_store GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall():
        print(f"    {own:14} {n:>8,}")

    print("\n  chain_category (all stores):")
    for cat, n in con.execute(
        "SELECT coalesce(chain_category,'(unresolved)'), count(*) "
        "FROM dim_store GROUP BY 1 ORDER BY 2 DESC"
    ).fetchall():
        print(f"    {cat:14} {n:>8,}")
    con.close()


if __name__ == "__main__":
    classify()
