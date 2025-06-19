import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
@pytest.mark.parametrize("page_name", ["home", "about", "faq"])
def test_static_pages_status_code(page_name: str):
    """Test that static pages return a 200 status code."""
    client = Client()
    response = client.get(reverse(f"pages:{page_name}"))
    assert response.status_code == 200
