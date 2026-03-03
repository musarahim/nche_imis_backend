from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_api_key.models import APIKey

from .models import ApplicationPRNS
from .ura_payment import UraMdaPaymentService


class ExternalAPITestCase(APITestCase):
    """Test cases for external API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        # Create API key for testing
        self.api_key, self.key = APIKey.objects.create_key(name="test_external_system")
        self.api_key_header = {'HTTP_X_API_KEY': self.key}
        
        # Test data
        self.valid_prn_data = {
            "amount": "1000.50",
            "referenceNo": "TEST_REF_123",
            "taxHead": "LICENSE_FEE",
            "taxPayerName": "Test Company Ltd",
            "email": "test@example.com",
            "tin": "1234567890"
        }
        
        self.mock_ura_response = {
            "prn": "9909876543210123",
            "statusCode": "00",
            "statusDesc": "SUCCESS",
            "searchCode": "SC123456",
            "expiryDate": "2026-04-02"
        }
    
    @patch('payments.views.UraMdaPaymentService')
    def test_generate_prn_success(self, mock_service_class):
        """Test successful PRN generation."""
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock ApplicationPRNS object
        mock_app_prn = MagicMock()
        mock_app_prn.id = 1
        mock_app_prn.referenceNo = "TEST_REF_123"
        mock_app_prn.prn = "9909876543210123"
        mock_app_prn.amount = Decimal("1000.50")
        mock_app_prn.taxPayerName = "Test Company Ltd"
        mock_app_prn.email = "test@example.com"
        mock_app_prn.statusCode = "00"
        mock_app_prn.statusDesc = "SUCCESS"
        mock_app_prn.expiryDate = "2026-04-02"
        mock_app_prn.searchCode = "SC123456"
        
        mock_service.generate_and_save_prn.return_value = mock_app_prn
        
        url = reverse('payments:external-generate-prn')
        response = self.client.post(url, self.valid_prn_data, format='json', **self.api_key_header)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'PRN generated successfully')
        self.assertIn('data', response.data)
        
    def test_generate_prn_without_api_key(self):
        """Test PRN generation without API key."""
        url = reverse('payments:external-generate-prn')
        response = self.client.post(url, self.valid_prn_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_generate_prn_invalid_data(self):
        """Test PRN generation with invalid data."""
        invalid_data = {
            "amount": "-100",  # Invalid negative amount
            "referenceNo": "",  # Empty reference
            "taxHead": "",
            "taxPayerName": "",
            "email": "invalid-email"
        }
        
        url = reverse('payments:external-generate-prn')
        response = self.client.post(url, invalid_data, format='json', **self.api_key_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_generate_prn_duplicate_reference(self):
        """Test PRN generation with duplicate reference number."""
        # Create existing PRN record
        ApplicationPRNS.objects.create(
            referenceNo="TEST_REF_123",
            amount=Decimal("500.00"),
            prn="existing_prn"
        )
        
        url = reverse('payments:external-generate-prn')
        response = self.client.post(url, self.valid_prn_data, format='json', **self.api_key_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
        self.assertIn('referenceNo', response.data['errors'])
    
    @patch('payments.views.UraMdaPaymentService')
    def test_check_prn_status_success(self, mock_service_class):
        """Test successful PRN status check."""
        # Create test PRN record
        test_prn = ApplicationPRNS.objects.create(
            referenceNo="TEST_REF_123",
            amount=Decimal("1000.50"),
            prn="9909876543210123",
            taxPayerName="Test Company Ltd",
            statusCode="00",
            statusDesc="SUCCESS",
            expiryDate="2026-04-02",
            prn_reconciled=False
        )
        
        # Mock the service
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.check_prn_status.return_value = {
            "statusCode": "P",
            "statusDesc": "PENDING",
            "paymentDetails": {"amountPaid": "0.00", "paymentDate": None}
        }
        
        url = reverse('payments:external-check-prn-status')
        response = self.client.post(
            url, 
            {'prn': test_prn.prn}, 
            format='json', 
            **self.api_key_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'PRN status retrieved successfully')
        self.assertIn('data', response.data)
        self.assertEqual(response.data['data']['prn'], test_prn.prn)
    
    def test_check_prn_status_not_found(self):
        """Test PRN status check for non-existent PRN."""
        url = reverse('payments:external-check-prn-status')
        response = self.client.post(
            url, 
            {'prn': 'non_existent_prn'}, 
            format='json', 
            **self.api_key_header
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)
    
    def test_check_prn_status_without_api_key(self):
        """Test PRN status check without API key."""
        url = reverse('payments:external-check-prn-status')
        response = self.client.post(url, {'prn': 'some_prn'}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class APIKeyManagementTestCase(TestCase):
    """Test cases for API key management."""
    
    def test_api_key_creation(self):
        """Test API key creation."""
        api_key, key = APIKey.objects.create_key(name="test_system")
        
        self.assertIsNotNone(api_key.id)
        self.assertEqual(api_key.name, "test_system")
        self.assertIsNotNone(key)
        self.assertTrue(len(key) > 20)  # API keys should be sufficiently long
    
    def test_api_key_validation(self):
        """Test API key validation."""
        api_key, key = APIKey.objects.create_key(name="test_system")
        
        # Valid key should work
        self.assertTrue(APIKey.objects.is_valid(key))
        
        # Invalid key should not work
        self.assertFalse(APIKey.objects.is_valid("invalid_key"))


class PRNDataValidationTestCase(TestCase):
    """Test cases for PRN data validation."""
    
    def test_tin_validation(self):
        """Test TIN format validation."""
        from .serializers import PRNGenerationRequestSerializer

        # Valid TIN
        valid_data = {
            "amount": "1000.00",
            "referenceNo": "TEST_REF",
            "taxHead": "LICENSE",
            "taxPayerName": "Test Company",
            "email": "test@example.com",
            "tin": "1234567890"
        }
        
        serializer = PRNGenerationRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid TIN (not 10 digits)
        invalid_data = valid_data.copy()
        invalid_data["tin"] = "12345"
        
        serializer = PRNGenerationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('tin', serializer.errors)
    
    def test_amount_validation(self):
        """Test amount validation."""
        from .serializers import PRNGenerationRequestSerializer
        
        base_data = {
            "referenceNo": "TEST_REF",
            "taxHead": "LICENSE",
            "taxPayerName": "Test Company",
            "email": "test@example.com"
        }
        
        # Valid amount
        valid_data = base_data.copy()
        valid_data["amount"] = "1000.50"
        serializer = PRNGenerationRequestSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Invalid amount (zero)
        invalid_data = base_data.copy()
        invalid_data["amount"] = "0.00"
        serializer = PRNGenerationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        
        # Invalid amount (negative)
        invalid_data["amount"] = "-100.00"
        serializer = PRNGenerationRequestSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())