import pytest
from app.utils import normalize_instagram_url, extract_shortcode

def test_normalize():
    u = normalize_instagram_url("https://instagram.com/p/ABC123/?utm_source=x")
    assert u == "https://www.instagram.com/p/ABC123/"

def test_shortcode():
    code = extract_shortcode("https://www.instagram.com/reel/XYZ987/")
    assert code == "XYZ987"
