import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

import httpx
from django.conf import settings


@dataclass
class UgHubClient:
    base_url: str = settings.URA_BASE_URL
    token_endpoint: str = settings.URA_TOKEN_ENDPOINT
    consumer_key: str = settings.URA_CONSUMER_KEY
    consumer_secret: str = settings.URA_CONSUMER_SECRET

    def _basic_auth_header(self) -> str:
        creds = f"{self.consumer_key}:{self.consumer_secret}".encode("utf-8")
        return "Basic " + base64.b64encode(creds).decode("ascii")

    def get_access_token(self) -> str:
        """
        OAuth2 client_credentials grant with basic auth and scope, per spec:
        curl -d 'grant_type=client_credentials&scope=prn-services/generate-prn prn-services/get-prn-details' \
             -H 'Authorization: Basic <base64 consumer_key:consumer_secret>' \
             POST {base_url}/token
        """
        headers = {
            "Authorization": self._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "prn-services/generate-prn prn-services/get-prn-details"
        }
        
        with httpx.Client(timeout=30.0, verify=True) as client:
            r = client.post(self.token_endpoint, data=data, headers=headers)
            r.raise_for_status()
            print(r.json())
            return r.json()["access_token"]




class UraMdaPaymentService:
    """
    Thin wrapper for the four POST endpoints:
      - /getPRN
      - /prn-services/get-prn-details
      - /checkTaxClearanceStatus
      - /getClientRegistration
    """
    def __init__(self, client: UgHubClient | None = None):
        self.client = client or UgHubClient()

    def _post(self, resource: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        token = self.client.get_access_token()  # Bearer token, per spec
        url = f"{self.client.base_url}/{resource}"
        print(f"POST {url} with payload: {json.dumps(payload)}")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60.0, verify=True) as http:
            r = http.post(url, json=payload, headers=headers)
            # Handle typical error envelopes from spec (401 invalid creds, 400 invalid data, etc.)
            if r.status_code >= 400:
                # Let the caller see the exact spec payload for debugging/UX
                raise httpx.HTTPStatusError(f"{r.status_code}: {r.text}", request=r.request, response=r)
            return r.json()

    # 1) Get PRN
    def get_prn(self, prn_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Body must be: { "PRNRequest": {...}, <backend-cred-fields> }
        Sample PRNRequest fields are in the spec (Amount, PaymentMode, TaxHead, etc.).
        """
        body = {"PRNRequest": prn_request}
        return self._post("getPRN", body)

    # 2) Check PRN Status
    def check_prn_status(self, prn: str) -> Dict[str, Any]:
        body = {"prn": prn}
        return self._post("prn-services/get-prn-details", body)

    # 3) Check Tax Clearance Status
    def check_tax_clearance_status(self, certificate_number: str) -> Dict[str, Any]:
        body = {"CheckTaxClearanceStatus": {"certificateNumber": certificate_number}}
        return self._post("checkTaxClearanceStatus", body)

    # 4) Get Client Registration
    def get_client_registration(self, tin: str) -> Dict[str, Any]:
        body = {"GetClientRegistration": {"TIN": tin}}
        return self._post("getClientRegistration", body)
