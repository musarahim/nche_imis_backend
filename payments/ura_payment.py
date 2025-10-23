import base64
import json
from dataclasses import dataclass
from typing import Any, Dict

import httpx
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from django.conf import settings


@dataclass
class UgHubClient:
    base_url: str = settings.UGHUB_BASE_URL
    tenant_path: str = settings.UGHUB_TENANT_PATH
    token_endpoint: str = settings.UGHUB_TOKEN_ENDPOINT
    consumer_key: str = settings.UGHUB_CONSUMER_KEY
    consumer_secret: str = settings.UGHUB_CONSUMER_SECRET

    def _basic_auth_header(self) -> str:
        creds = f"{self.consumer_key}:{self.consumer_secret}".encode("utf-8")
        return "Basic " + base64.b64encode(creds).decode("ascii")

    def get_access_token(self) -> str:
        """
        OAuth2 client_credentials, per spec:
        curl -d 'grant_type=client_credentials' -H 'Authorization: Basic <base64 key:secret>'
        POST {base_url}/token
        """
        headers = {
            "Authorization": self._basic_auth_header(),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {"grant_type": "client_credentials"}
        with httpx.Client(timeout=30.0, verify=True) as client:
            r = client.post(self.token_endpoint, data=data, headers=headers)
            r.raise_for_status()
            return r.json()["access_token"]


def _load_public_key_from_cert(cert_path: str):
    """
    Load URA public key from X.509 certificate (PEM).
    """
    with open(cert_path, "rb") as f:
        cert_pem = f.read()
    cert = x509.load_pem_x509_certificate(cert_pem, default_backend())
    return cert.public_key()


def _load_private_key(key_path: str, password: str | None):
    with open(key_path, "rb") as f:
        key_pem = f.read()
    return load_pem_private_key(
        key_pem,
        password=password.encode("utf-8") if password else None,
        backend=default_backend(),
    )


def build_backend_credentials() -> dict:
    """
    Creates:
      - userName
      - encryptedConcatenatedUsernamePassword
      - concatenatedUsernamePasswordSignature
    using:
      - concat = f"{BACKEND_USERNAME}{BACKEND_PASSWORD}"
      - encrypt concat with URA public cert (RSA/OAEP)
      - sign concat with MDA private key (RSA/PKCS#1 v1.5 or PSS; use what your endpoint expects)
    """
    concat = f"{settings.BACKEND_USERNAME}{settings.BACKEND_PASSWORD}".encode("utf-8")

    # Encrypt with URA public key
    pub = _load_public_key_from_cert(settings.URA_PUBLIC_CERT_PATH)
    encrypted = pub.encrypt(
        concat,
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
    )
    encrypted_b64 = base64.b64encode(encrypted).decode("ascii")

    # Sign with MDA private key
    priv = _load_private_key(settings.MDA_PRIVATE_KEY_PATH, settings.MDA_PRIVATE_KEY_PASSWORD)
    signature = priv.sign(
        concat,
        padding.PKCS1v15(),  # if the integration requires PSS, switch to padding.PSS(...)
        hashes.SHA256(),
    )
    signature_b64 = base64.b64encode(signature).decode("ascii")
    print(encrypted_b64, "encrypted b64")
    print(signature_b64, "signature b64")

    return {
        "userName": settings.BACKEND_USERNAME_FOR_PAYLOAD,
        "encryptedConcatenatedUsernamePassword": encrypted_b64,
        "concatenatedUsernamePasswordSignature": signature_b64,
    }


class UraMdaPaymentService:
    """
    Thin wrapper for the four POST endpoints:
      - /getPRN
      - /checkPRNStatus
      - /checkTaxClearanceStatus
      - /getClientRegistration
    """
    def __init__(self, client: UgHubClient | None = None):
        self.client = client or UgHubClient()

    def _post(self, resource: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        token = self.client.get_access_token()  # Bearer token, per spec
        url = f"{self.client.base_url}{self.client.tenant_path}/{resource}"
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
        auth = build_backend_credentials()
        body = {"PRNRequest": prn_request, **auth}
        return self._post("getPRN", body)

    # 2) Check PRN Status
    def check_prn_status(self, prn: str) -> Dict[str, Any]:
        auth = build_backend_credentials()
        body = {"CheckPRNStatus": {"strPRN": prn, **auth}}
        return self._post("checkPRNStatus", body)

    # 3) Check Tax Clearance Status
    def check_tax_clearance_status(self, certificate_number: str) -> Dict[str, Any]:
        auth = build_backend_credentials()
        body = {"CheckTaxClearanceStatus": {"certificateNumber": certificate_number, **auth}}
        return self._post("checkTaxClearanceStatus", body)

    # 4) Get Client Registration
    def get_client_registration(self, tin: str) -> Dict[str, Any]:
        auth = build_backend_credentials()
        body = {"GetClientRegistration": {"TIN": tin, **auth}}
        return self._post("getClientRegistration", body)
