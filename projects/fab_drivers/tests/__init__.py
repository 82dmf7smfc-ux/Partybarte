"""Tests for the fab_drivers core layer.

Every test here runs with no hardware attached. That is deliberate. The mock
serial class stands in for a real port, so the same tests run on a laptop, on the
bench, and on the GitHub runner, which has no serial ports at all.
"""
