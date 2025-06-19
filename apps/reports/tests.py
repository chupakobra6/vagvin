import pytest
from unittest.mock import patch
from django.urls import reverse
from django.test import Client
from apps.accounts.factories import UserFactory
from django.core.cache import cache
from unittest.mock import MagicMock
import requests
from apps.reports.services import (
    AutotekaService,
    CarfaxService,
    VinhistoryService,
    AuctionService,
    AvitoAuthService,
    AvitoService,
)


@pytest.mark.django_db
class TestReportAPIViews:

    @pytest.fixture
    def client(self):
        return Client()

    @pytest.fixture
    def superuser(self):
        return UserFactory(is_superuser=True)

    @patch("apps.reports.services.AutotekaService.check")
    def test_autoteka_check_view(self, mock_autoteka_check, client, superuser):
        """Test the Autoteka check API endpoint."""
        mock_autoteka_check.return_value = {"success": True, "message": "VIN found"}

        # Test as anonymous user (as per views logic)
        response = client.post(
            reverse("reports:api_check_autoteka"), {"vin": "TESTVIN1234567890"}
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "VIN found"}
        mock_autoteka_check.assert_called_once_with("TESTVIN1234567890", "vin")

    @patch("apps.reports.services.CarfaxService.check")
    def test_carfax_check_view(self, mock_carfax_check, client, superuser):
        """Test the Carfax/Autocheck check API endpoint."""
        mock_carfax_check.return_value = {"success": True, "message": "Carfax found"}

        response = client.post(
            reverse("reports:api_check_carfax_autocheck"), {"vin": "TESTVIN1234567890"}
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Carfax found"}
        mock_carfax_check.assert_called_once_with("TESTVIN1234567890")

    @patch("apps.reports.services.VinhistoryService.check")
    def test_vinhistory_check_view(self, mock_vinhistory_check, client, superuser):
        """Test the Vinhistory check API endpoint."""
        mock_vinhistory_check.return_value = {
            "success": True,
            "message": "Vinhistory found",
        }

        response = client.post(
            reverse("reports:api_check_vinhistory"), {"vin": "TESTVIN1234567890"}
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Vinhistory found"}
        mock_vinhistory_check.assert_called_once_with("TESTVIN1234567890")

    @patch("apps.reports.services.AuctionService.check")
    def test_auction_check_view(self, mock_auction_check, client, superuser):
        """Test the Auction check API endpoint."""
        mock_auction_check.return_value = {"success": True, "message": "Auction found"}

        response = client.post(
            reverse("reports:api_check_auction"), {"vin": "TESTVIN1234567890"}
        )

        assert response.status_code == 200
        assert response.json() == {"success": True, "message": "Auction found"}
        mock_auction_check.assert_called_once_with("TESTVIN1234567890")


@pytest.mark.django_db
class TestReportServices:

    def setup_method(self, method):
        """Clear cache before each test."""
        cache.clear()

    @patch("apps.reports.services.requests.post")
    def test_avito_auth_service_get_token(self, mock_post):
        """Test Avito token retrieval and caching."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # First call, should fetch from API
        token = AvitoAuthService.get_token()
        assert token == "test_token"
        mock_post.assert_called_once()
        assert cache.get("avito_token") == "test_token"

        # Second call, should use cache
        token2 = AvitoAuthService.get_token()
        assert token2 == "test_token"
        mock_post.assert_called_once()  # Should not be called again

    @patch("apps.reports.services.AvitoAuthService.get_token")
    @patch("apps.reports.services.requests.post")
    def test_autoteka_service_check_not_found(self, mock_post, mock_get_token):
        """Test AutotekaService when VIN is not found."""
        mock_get_token.return_value = "fake_token"

        # Mock response for preview request
        mock_preview_response = MagicMock()
        mock_preview_response.status_code = 200
        mock_preview_response.json.return_value = {
            "result": {"preview": {"status": "notFound"}}
        }
        mock_post.return_value = mock_preview_response

        result = AutotekaService.check("UNKNOWNVIN", "vin")
        assert result["success"] is False
        assert "отсутствует в Автотеке" in result["message"]

    @patch("apps.reports.services.requests.get")
    def test_carfax_service_check_error(self, mock_get):
        """Test CarfaxService handling of API errors."""
        mock_get.side_effect = requests.exceptions.RequestException("API is down")

        result = CarfaxService.check("VALIDVIN123456789")
        assert "error" in result
        assert "Ошибка сети при запросе к Carstat" in result["error"]

    @patch("apps.reports.services.requests.get")
    def test_vinhistory_service_check_no_images(self, mock_get):
        """Test VinhistoryService when data is found but no images."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "vehicle": {"make": "TOYOTA", "model": "CAMRY", "year": 2020},
            "images": 0,
        }
        mock_get.return_value = mock_response

        result = VinhistoryService.check("VALIDVIN123456789")
        assert result["success"] is True
        assert "фото отсутствуют" in result["message"]

    @patch("apps.reports.services.requests.get")
    def test_auction_service_check_exists(self, mock_get):
        """Test AuctionService when auction data exists."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "exists": True,
            "domains": ["iaai.com", "copart.com"],
        }
        mock_get.return_value = mock_response

        result = AuctionService.check("VALIDVIN123456789")
        assert result["success"] is True
        assert result["auction_count"] == 2
        assert "Найдены записи об аукционах" in result["message"]

    @patch("apps.reports.services.AvitoAuthService.get_token")
    @patch("apps.reports.services.requests.post")
    @patch("apps.reports.services.requests.get")
    def test_autoteka_service_check_success_polling(
        self, mock_get, mock_post, mock_get_token
    ):
        """Test AutotekaService with a successful result after polling."""
        mock_get_token.return_value = "fake_token"

        # 1. Mock response for preview request
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"result": {"preview": {"previewId": "12345"}}},
        )

        # 2. Mock responses for status polling
        mock_get.side_effect = [
            # First poll: processing
            MagicMock(
                status_code=200,
                json=lambda: {"result": {"preview": {"status": "processing"}}},
            ),
            # Second poll: success
            MagicMock(
                status_code=200,
                json=lambda: {
                    "result": {
                        "preview": {
                            "status": "success",
                            "data": {"brand": "LADA", "model": "Vesta", "year": 2021},
                        }
                    }
                },
            ),
        ]

        result = AutotekaService.check("TESTVIN1234567890", "vin")

        assert result["success"] is True
        assert result["data"]["Марка"] == "LADA"
        assert mock_post.call_count == 1
        assert mock_get.call_count == 2

    def test_avito_service_extract_id(self):
        """Test Avito ID extraction from different URL formats."""
        url_with_path = (
            "https://www.avito.ru/moskva/avtomobili/vaz_lada_vesta_2021_2345678910"
        )
        url_with_query = "https://www.avito.ru/moskva/avtomobili/item?id=123456789"
        invalid_url = "https://example.com"

        assert AvitoService.extract_id(url_with_path) == "2345678910"
        assert AvitoService.extract_id(url_with_query) == "123456789"
        assert AvitoService.extract_id(invalid_url) == ""
