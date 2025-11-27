import base64
import json

import requests

# ----------------------------------------------------------
# CONFIG — fill in your values here
# ----------------------------------------------------------
BASE_URL = "https://api-uat.integration.go.ug"      # e.g. https://api.ughub.go.ug
CONSUMER_KEY = "6gSEZIXWKTPzNlff7iZfLNOcxSca"
CONSUMER_SECRET = "ZK4e02zZIumsrRJgj0rtI19lg9wa"

MOLG_AUD_AUTH_TOKEN = "your-MOLG-AUD-Auth-Token"  # You need to get this from MOLG

# ----------------------------------------------------------
# Helper: Pretty print JSON
# ----------------------------------------------------------
def pretty(data):
    print(json.dumps(data, indent=4))


# ----------------------------------------------------------
# Helper: Validate credentials against curl example
# ----------------------------------------------------------
def validate_credentials():
    """
    Validate that our credentials match the curl example:
    NmdTRVpJWFdLVFB6TmxmZjdpWmZMTk9jeFNjYTpaSzRlMDJ6Wkl1bXNyUkpnajBydEkxOWxnOXdh
    """
    combo = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    encoded = base64.b64encode(combo.encode()).decode()
    
    expected = "NmdTRVpJWFdLVFB6TmxmZjdpWmZMTk9jeFNjYTpaSzRlMDJ6Wkl1bXNyUkpnajBydEkxOWxnOXdh"
    
    print(f"Our encoded credentials: {encoded}")
    print(f"Expected from curl:      {expected}")
    print(f"Match: {encoded == expected}")
    
    if encoded != expected:
        print("WARNING: Credentials don't match the curl example!")
        # Decode the expected to see what it should be
        try:
            decoded_expected = base64.b64decode(expected).decode()
            print(f"Expected credentials should be: {decoded_expected}")
        except Exception as e:
            print(f"Could not decode expected credentials: {e}")
    
    return encoded == expected


# ----------------------------------------------------------
# STEP 1: Generate OAuth2 access token  (page 4 of PDF)
# ----------------------------------------------------------
def get_access_token():
    print("=== Generating Access Token ===")

    combo = f"{CONSUMER_KEY}:{CONSUMER_SECRET}"
    encoded = base64.b64encode(combo.encode()).decode()
    print(f"Base64 encoded credentials: {encoded}")

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    url = f"{BASE_URL}/token"
    payload = {"grant_type": "client_credentials"}
    
    print(f"Token URL: {url}")
    print(f"Headers: {headers}")

    try:
        response = requests.post(url, data=payload, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        result = response.json()
        pretty(result)
        return result.get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error getting access token: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None


# ----------------------------------------------------------
# Generic GET Request for all endpoints
# ----------------------------------------------------------
def molg_get(resource, token, params=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "MOLG-AUD-Auth-Token": MOLG_AUD_AUTH_TOKEN
    }

    url = f"{BASE_URL}/t/molg.go.ug/molg/1.0.0/{resource}"
    print(f"\n=== GET {url} ===")
    
    try:
        response = requests.get(url, headers=headers, params=params, verify=False, timeout=30)
        response.raise_for_status()
        pretty(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None


# ----------------------------------------------------------
# Resource Test Functions
# ----------------------------------------------------------
def test_regions(token):
    return molg_get("regions", token, {"start": 0, "limit": 10})

def test_sub_regions(token):
    return molg_get("sub_regions", token, {"start": 0, "limit": 10, "region_id": 1})

def test_districts(token):
    return molg_get("districts", token, {"start": 0, "limit": 10, "region_id": 1, "sub_region_id": 1})

def test_counties(token):
    return molg_get("counties", token, {"start": 0, "limit": 10, "region_id": 1,
                                 "sub_region_id": 1, "district_id": 1})

def test_constituencies(token):
    return molg_get("constituencies", token, {"start": 0, "limit": 10, "region_id": 1,
                                       "sub_region_id": 1, "district_id": 1,
                                       "county_id": 1})

def test_sub_counties(token):
    return molg_get("sub_counties", token, {"start": 0, "limit": 10, "region_id": 1,
                                     "sub_region_id": 1, "district_id": 1,
                                     "county_id": 1})

def test_parish(token):
    return molg_get("parish", token, {"start": 0, "limit": 10, "region_id": 1,
                               "sub_region_id": 1, "district_id": 1,
                               "county_id": 1, "constituency_id": 1,
                               "sub_county_id": 1})

def test_villages(token):
    return molg_get("villages", token, {"start": 0, "limit": 10, "region_id": 1,
                                 "sub_region_id": 1, "district_id": 1,
                                 "county_id": 1, "constituency_id": 1,
                                 "sub_county_id": 1, "parish_id": 1})

def test_token_regenerate(token):
    return molg_get("tokenRegenerate", token)


# ----------------------------------------------------------
# RUN EVERYTHING
# ----------------------------------------------------------
if __name__ == "__main__":
    print("=== Validating Credentials ===")
    validate_credentials()
    
    access_token = get_access_token()
    
    if access_token:
        print(f"\nAccess token obtained: {access_token[:20]}...")
        
        # Test one endpoint at a time to debug
        print("\n" + "="*50)
        print("Testing MOLG API endpoints...")
        print("="*50)
        
        # Start with regions as it's the base level
        test_regions(access_token)
        
        # Uncomment other tests one by one after regions works
        # test_sub_regions(access_token)
        # test_districts(access_token)
        # test_counties(access_token)
        # test_constituencies(access_token)
        # test_sub_counties(access_token)
        # test_parish(access_token)
        # test_villages(access_token)
        # test_token_regenerate(access_token)
    else:
        print("Failed to obtain access token. Cannot proceed with API tests.")
