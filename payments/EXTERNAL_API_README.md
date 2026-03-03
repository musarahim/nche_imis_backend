# External Payment API Documentation

This document describes the external API endpoints for PRN (Payment Reference Number) generation and status checking, designed for integration with external systems.

## Authentication

All external API endpoints require **API Key authentication**. Include your API key in the request header:

```
X-Api-Key: YOUR_API_KEY_HERE
```

## API Endpoints

### 1. Generate PRN

**Endpoint:** `POST /api/payments/external/generate-prn/`

**Description:** Generate a new Payment Reference Number (PRN) for tax payments.

**Request Body:**

```json
{
  "amount": "1000",
  "referenceNo": "EXT_REF_12345",
  "taxHead": "NCHE001",
  "taxSubHead": "PAYE",
  "taxPayerName": "John Doe Company Ltd",
  "email": "finance@johndoe.com",
  "tin": "1234567890",
  "contactNo": "0700123456",
  "mobileNo": "0700123456",
  "plot": "Plot 123",
  "buildingName": "Commerce House",
  "street": "Kampala Road",
  "district": "Kampala",
  "county": "Kampala Central",
  "subCounty": "Central Division"
}
```

**Required Fields:**

- `amount` (integer): Payment amount (must be greater than 0)
- `referenceNo` (string): Unique external system reference number
- `taxHead` (string): Tax category
- `taxPayerName` (string): Name of the taxpayer
- `email` (string): Valid email address

**Optional Fields:**

- `taxSubHead`, `tin`, `contactNo`, `mobileNo`, `plot`, `buildingName`, `street`, `district`, `county`, `subCounty`, `parish`, `village`
- `paymentType` (default: "DT")
- `srcSystem` (default: "EXTERNAL_API")
- `expiryDays` (default: "30")

**Success Response (201):**

```json
{
  "success": true,
  "message": "PRN generated successfully",
  "data": {
    "id": 123,
    "referenceNo": "EXT_REF_12345",
    "prn": "9909876543210123",
    "amount": "1000",
    "taxPayerName": "John Doe Company Ltd",
    "email": "finance@johndoe.com",
    "statusCode": "00",
    "statusDesc": "SUCCESS",
    "expiryDate": "2026-04-02",
    "searchCode": "SC123456"
  }
}
```

**Error Response (400):**

```json
{
  "success": false,
  "message": "Validation failed",
  "errors": {
    "referenceNo": ["Reference number already exists."],
    "amount": ["Ensure this value is greater than or equal to 0.01."]
  }
}
```

### 2. Check PRN Status

**Endpoint:** `POST /api/payments/external/check-prn-status/`

**Description:** Check the payment status of an existing PRN.

**Request Body:**

```json
{
  "prn": "9909876543210123"
}
```

**Required Fields:**

- `prn` (string): The Payment Reference Number to check

**Success Response (200):**

```json
{
  "success": true,
  "message": "PRN status retrieved successfully",
  "data": {
    "prn": "9909876543210123",
    "referenceNo": "EXT_REF_12345",
    "amount": "1000",
    "taxPayerName": "John Doe Company Ltd",
    "statusCode": "00",
    "statusDesc": "SUCCESS",
    "expiryDate": "2026-04-02",
    "prn_reconciled": false,
    "ura_status": {
      "statusCode": "P",
      "statusDesc": "PENDING",
      "paymentDetails": {
        "amountPaid": "0.00",
        "paymentDate": null
      }
    }
  }
}
```

**Error Response (404):**

```json
{
  "success": false,
  "message": "PRN not found in system"
}
```

## Status Codes

### PRN Generation Status Codes

- `00`: Success - PRN generated successfully
- `01`: Failed - PRN generation failed

### Payment Status Codes (from URA)

- `P`: Pending - Payment not yet made
- `T`: Paid - Payment completed successfully
- `E`: Expired - PRN has expired
- `C`: Cancelled - PRN has been cancelled

## Error Handling

All API responses include a `success` field indicating whether the operation was successful. Error responses include:

- `success`: false
- `message`: Human-readable error description
- `errors` (optional): Detailed validation errors
- `error` (optional): Technical error details

## Rate Limiting

Please implement appropriate rate limiting on your end to avoid overwhelming the API. Recommended limits:

- PRN Generation: 10 requests per minute
- Status Check: 30 requests per minute

## Testing

Use the following test data for integration testing:

```json
{
  "amount": "100.00",
  "referenceNo": "TEST_REF_001",
  "taxHead": "TEST_TAX",
  "taxPayerName": "Test Company Ltd",
  "email": "test@example.com"
}
```

## Support

For API integration support or to request API keys, contact the system administrator.

## Note

1. The mobile number should start with a zero and must be valid
2. Incase a tin is provided, must be a valid tin of an existing tax payer

## Security Notes

1. **API Keys**: Keep your API keys secure and rotate them regularly
2. **HTTPS**: Always use HTTPS for API calls in production
3. **Reference Numbers**: Ensure reference numbers are unique across your system
4. **Data Validation**: Validate all data before sending API requests

## Changelog

- **v1.0** (March 2026): Initial release with PRN generation and status checking
