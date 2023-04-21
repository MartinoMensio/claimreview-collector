url = "https://www.datacommons.org/factcheck/download#fcmt-data"
bitly_url = "https://bit.ly/test-bitly-datacommons"


def test_get():
    from claimreview_scraper.processing import cache_manager

    page = cache_manager.get(url)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page


def test_get_with_unshorten():
    from claimreview_scraper.processing import cache_manager

    page = cache_manager.get(bitly_url, unshorten=True, force_refresh=True)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page


def test_verify_false():
    from claimreview_scraper.processing import cache_manager

    page = cache_manager.get(url, unshorten=False, force_refresh=True, verify=False)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page
