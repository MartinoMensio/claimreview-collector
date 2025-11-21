from claimreview_collector.processing import cache_manager

url = "https://datacommons.org/factcheck/download#fcmt-data"
#bitly_url = "https://bit.ly/test-bitly-datacommons"
tinyurl_url = "https://tinyurl.com/test-tinyurl-datacommons"
large_url = (
    "https://storage.googleapis.com/datacommons-feeds/factcheck/latest/data.json"
)


def test_get():
    page = cache_manager.get(url)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page


def test_get_with_unshorten():
    page = cache_manager.get(tinyurl_url, unshorten=True, force_refresh=True)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page


def test_verify_false():
    page = cache_manager.get(url, unshorten=False, verify=False)
    assert "DataCommons.org" in page
    assert "ClaimReview" in page


def test_large_file():
    page = cache_manager.get(large_url)
    assert "TOO LARGE" in page
