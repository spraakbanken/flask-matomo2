"""Trackers for time measurements.

>>> scope = {"tracking_data": {}}
>>> with PerfMsTracker(scope, key="pf_srv"):
...     _a = 2 + 2 # do computation
>>> assert "pf_srv" in scope["tracking_data"]
"""

from matomo_core.trackers import PerfMsTracker

__all__ = ["PerfMsTracker"]
