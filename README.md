# Google Workspace SSO Integration Tools

A Streamlit application for email verification and list management using multiple verification services.

## Current Features

- Single Email Verification
- Bulk Email Verification
- Email List Management
- Multiple Service Integration:
  - ZeroBounce
  - MailboxLayer
  - NeutrinoAPI
  - Spokeo
  - Hunter.io
- Database Storage for Verification History
- Streamlit Dashboard Interface

## Coming Soon

- 1Password SSO configuration with Google Cloud
- Google Workspace SAML application setup
- Gmail API integration
- Custom SAML Applications Setup
- Automated Service Account Management

## Prerequisites

- Python 3.11+
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Start the Streamlit application:
```bash
streamlit run app.py
```

## Configuration

1. Configure API keys for verification services:
   - ZeroBounce
   - MailboxLayer
   - NeutrinoAPI
   - Spokeo
   - Hunter.io

2. Access the dashboard at http://localhost:5000

## Scripts

- `app.py`: Main Streamlit application
- `email_verification_manager.py`: Email verification logic
- `email_list_manager.py`: List management functionality
- `database.py`: Database operations

## License

MIT License