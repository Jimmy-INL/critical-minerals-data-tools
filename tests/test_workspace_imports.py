"""Smoke test: verify all workspace packages can be imported."""

import importlib

import pytest

WORKSPACE_PACKAGES = [
    "cmm_data",
    "arxiv_mcp",
    "bgs_mcp",
    "claimm_mcp",
    "cmm_api",
    "google_scholar_mcp",
    "osti_mcp",
    "uncomtrade_mcp",
    "usgs_mcp",
    "unified_data_api",
]


@pytest.mark.parametrize("package", WORKSPACE_PACKAGES)
def test_package_importable(package: str):
    """Each workspace member should be importable after uv sync."""
    mod = importlib.import_module(package)
    assert mod is not None
