import pytest, ebookonix
def test_onixproduct_escapes_titles():
    r = ebookonix.onix_product(
        "http://example.com/book.epub",
        "Examples & stuff")
    assert "Examples &amp; stuff" in r
