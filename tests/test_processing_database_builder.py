import pytest

from claimreview_scraper.processing import database_builder


def test_clean_db():
    database_builder.clean_db()


def test_add_claimreviews_raw():
    cr = {"url": "https://www.datacommons.org/factcheck/download#fcmt-data"}
    database_builder.add_claimreviews_raw([cr], clean=False)
    database_builder.add_claimreviews_raw([cr], clean=True)


def test_add_ClaimReviews():
    cr = {"url": "https://www.datacommons.org/factcheck/download#fcmt-data"}
    database_builder.add_ClaimReviews("test", [cr], clean=True)
    # check what is inside
    res = database_builder.get_ClaimRewiews_from("test")
    assert len(list(res)) == 1
    # now clean
    database_builder.delete_ClaimReviews_from("test")
    res = database_builder.get_ClaimRewiews_from("test")
    assert len(list(res)) == 0


def test_save_original_data():
    data = {"url": "https://www.datacommons.org/factcheck/download#fcmt-data"}
    database_builder.save_original_data("test", [data])
    # now check
    res = database_builder.get_original_data("test")
    assert len(list(res)) == 1


def test_get_all_factchecking_urls():
    database_builder.clean_db()
    res = database_builder.get_all_factchecking_urls()
    assert len(list(res)) == 0
    cr = {"url": "https://www.datacommons.org/factcheck/download#fcmt-data"}
    database_builder.add_ClaimReviews("test", [cr], clean=True)
    res = database_builder.get_all_factchecking_urls()
    assert len(list(res)) == 1
    cr = {"url": "https://www.datacommons.org/factcheck/download#fcmt-data2"}
    database_builder.add_ClaimReviews("test", [cr], clean=False)
    res = database_builder.get_all_factchecking_urls()
    assert len(list(res)) == 2
