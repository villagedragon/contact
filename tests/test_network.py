"""Test behavior related to the current network status."""

import urllib.request

import pytest


def test_sb_domain_reachable(sb_test_url: str) -> None:
    """Sanity check to make sure domain is reachable."""
    # attempt to reach domain
    try:
        # get response from request
        response = urllib.request.urlopen(sb_test_url)

        # check status code is 200
        assert response.getcode() == 200

    except urllib.error.URLError:
        # notify failure to reach
        pytest.fail(f"Could not reach domain {sb_test_url:!r}")
