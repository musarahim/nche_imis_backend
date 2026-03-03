#!/usr/bin/env python3
"""
Example script demonstrating how to integrate with the NCHE IMIS Payment API.
This script shows how external systems can generate PRNs and check their status.

Requirements:
    pip install requests

Usage:
    python external_api_example.py
"""

import json
from datetime import datetime

import requests


class IMISPaymentAPIClient:
    """Client for interacting with NCHE IMIS Payment API."""
    
    def __init__(self, base_url, api_key):
        """
        Initialize the API client.
        
        Args:
            base_url (str): Base URL of the IMIS API (e.g., 'https://imis.nche.go.ug/api')
            api_key (str): Your API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            'Authorization': f'Api-Key {api_key}',
            'Content-Type': 'application/json'
        }
    
    def generate_prn(self, prn_data):
        """
        Generate a new PRN.
        
        Args:
            prn_data (dict): PRN generation data
            
        Returns:
            dict: API response
        """
        url = f"{self.base_url}/payments/external/generate-prn/"
        
        try:
            response = requests.post(url, headers=self.headers, json=prn_data, timeout=30)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def check_prn_status(self, prn):
        """
        Check PRN payment status.
        
        Args:
            prn (str): Payment Reference Number
            
        Returns:
            dict: API response
        """
        url = f"{self.base_url}/payments/external/check-prn-status/"
        
        try:
            response = requests.post(url, headers=self.headers, json={'prn': prn}, timeout=30)
            return self._handle_response(response)
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_response(self, response):
        """Handle API response."""
        try:
            data = response.json()
            if response.status_code >= 400:
                data['status_code'] = response.status_code
            return data
        except json.JSONDecodeError:
            return {
                'success': False, 
                'error': f'Invalid JSON response. Status: {response.status_code}',
                'response_text': response.text
            }


def example_usage():
    """Demonstrate API usage with example data."""
    
    # Configuration - UPDATE THESE VALUES
    API_BASE_URL = "http://localhost:8000/api"  # Update with your actual API URL
    API_KEY = "YOUR_API_KEY_HERE"  # Update with your actual API key
    
    # Initialize client
    client = IMISPaymentAPIClient(API_BASE_URL, API_KEY)
    
    print("🚀 NCHE IMIS Payment API Integration Example")
    print("=" * 50)
    
    # Example PRN generation data
    prn_data = {
        "amount": "250000.00",
        "referenceNo": f"EXT_DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "taxHead": "LICENSE_FEE",
        "taxSubHead": "INSTITUTIONAL_LICENSE",
        "taxPayerName": "Demo University Ltd",
        "email": "finance@demouniversity.ac.ug",
        "tin": "1234567890",
        "contactNo": "+256700123456",
        "mobileNo": "+256700123456",
        "plot": "Plot 456",
        "buildingName": "Administration Block",
        "street": "University Avenue",
        "district": "Kampala",
        "county": "Kampala Central",
        "subCounty": "Central Division"
    }
    
    # Step 1: Generate PRN
    print("\\n📝 Step 1: Generating PRN...")
    print(f"Reference No: {prn_data['referenceNo']}")
    print(f"Amount: UGX {prn_data['amount']}")
    
    result = client.generate_prn(prn_data)
    
    if result.get('success'):
        prn_info = result['data']
        print("✅ PRN Generated Successfully!")
        print(f"   PRN: {prn_info['prn']}")
        print(f"   Reference: {prn_info['referenceNo']}")
        print(f"   Status: {prn_info['statusDesc']}")
        print(f"   Expiry Date: {prn_info['expiryDate']}")
        
        # Step 2: Check PRN Status
        print("\\n🔍 Step 2: Checking PRN Status...")
        
        status_result = client.check_prn_status(prn_info['prn'])
        
        if status_result.get('success'):
            status_data = status_result['data']
            print("✅ PRN Status Retrieved Successfully!")
            print(f"   PRN: {status_data['prn']}")
            print(f"   Payment Status: {status_data['ura_status']['statusDesc']}")
            print(f"   Reconciled: {'Yes' if status_data['prn_reconciled'] else 'No'}")
            print(f"   Amount Paid: UGX {status_data['ura_status'].get('paymentDetails', {}).get('amountPaid', '0.00')}")
        else:
            print("❌ Failed to check PRN status:")
            print(f"   Error: {status_result.get('message', 'Unknown error')}")
            
    else:
        print("❌ Failed to generate PRN:")
        print(f"   Error: {result.get('message', 'Unknown error')}")
        if 'errors' in result:
            print("   Validation Errors:")
            for field, errors in result['errors'].items():
                print(f"     - {field}: {', '.join(errors)}")


def batch_status_check_example():
    """Example of checking multiple PRN statuses in batch."""
    
    API_BASE_URL = "http://localhost:8000/api"
    API_KEY = "YOUR_API_KEY_HERE"
    
    client = IMISPaymentAPIClient(API_BASE_URL, API_KEY)
    
    # List of PRNs to check (replace with actual PRNs)
    prns_to_check = [
        "9909876543210123",
        "9909876543210124", 
        "9909876543210125"
    ]
    
    print("\\n📊 Batch PRN Status Check Example")
    print("=" * 40)
    
    for prn in prns_to_check:
        print(f"\\nChecking PRN: {prn}")
        result = client.check_prn_status(prn)
        
        if result.get('success'):
            data = result['data']
            status = data['ura_status']['statusDesc']
            reconciled = "Yes" if data['prn_reconciled'] else "No"
            print(f"  Status: {status} | Reconciled: {reconciled}")
        else:
            print(f"  Error: {result.get('message', 'Failed to check status')}")


if __name__ == "__main__":
    print("⚠️  IMPORTANT: Update API_BASE_URL and API_KEY in the script before running!")
    print("   Contact your system administrator for API credentials.\\n")
    
    try:
        example_usage()
        # batch_status_check_example()  # Uncomment to run batch example
        
        print("\\n🎉 Integration example completed!")
        print("\\nNext Steps:")
        print("1. Update the API credentials in this script")
        print("2. Test with your actual data")  
        print("3. Implement error handling and logging in your production code")
        print("4. Consider implementing retry logic for network failures")
        
    except KeyboardInterrupt:
        print("\\n👋 Example interrupted by user")
    except Exception as e:
        print(f"\\n💥 Unexpected error: {e}")
        print("Check your API credentials and network connection.")