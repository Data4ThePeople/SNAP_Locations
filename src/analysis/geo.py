"""Great-circle distance on a KD-tree.

A KD-tree works in euclidean space, so lat/lon cannot go in directly. Projecting
onto the unit sphere and searching in 3-D gives chord length, which converts
back to great-circle miles exactly. That makes nearest-store queries over tens
of thousands of points effectively instant.

These are straight-line distances. Road distance typically runs 1.2-1.4x, so a
20-mile drive standard sits nearer a 15-mile straight line. Anything reported
from these numbers should say "straight-line" and, where the claim is about
whether someone can actually get somewhere, report a ladder of radii rather
than resting on one threshold.

Extracted from the retired Walmart analysis (post3_walmart.py), which is where
these first ran.
"""
import numpy as np

R_MI = 3958.7613          # earth radius, miles


def xyz(lat, lon):
    """Unit-sphere cartesian, so a KD-tree can answer great-circle queries."""
    la, lo = np.radians(lat), np.radians(lon)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


def chord(miles):
    """Chord length on the unit sphere for a given great-circle distance."""
    return 2 * np.sin(miles / (2 * R_MI))


def gc_miles(chord_len):
    return 2 * R_MI * np.arcsin(np.clip(chord_len / 2, 0, 1))
