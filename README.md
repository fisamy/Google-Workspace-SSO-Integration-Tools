# 1Password SSO Configuration with Google Cloud

This repository contains scripts to automate the configuration of 1Password Single Sign-On (SSO) with Google Cloud. The scripts help you set up the 1Password SCIM Bridge on Google Cloud Platform and configure Google Identity integration.

## Prerequisites

- Google Cloud Platform account with administrative access
- Google Workspace Administrator access
- 1Password Business or Enterprise account with SSO capabilities
- `gcloud` CLI installed and configured
- Python 3.6+ installed

## Getting Started

### Option 1: Using the Shell Script

1. Make the script executable:

```bash
chmod +x 1password_sso_setup.sh
```

2. Run the script with required parameters:

```bash
./1password_sso_setup.sh --project-id=your-gcp-project-id \
                        --domain=your-domain.com \
                        --admin-email=admin@your-domain.com
```

### Option 2: Using the Python Script

1. Install required dependencies:

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

2. Run the script:

```bash
python 1password_sso_setup.py --project-id=your-gcp-project-id \
                             --domain=your-domain.com \
                             --admin-email=admin@your-domain.com \
                             --service-account-file=path/to/your-service-account-key.json
```

## Parameters

Both scripts accept the following parameters:

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `--project-id` | Google Cloud Project ID | Yes | - |
| `--region` | GCP Region for Cloud Run deployment | No | us-central1 |
| `--service-account-name` | Service Account Name for SCIM Bridge | No | scim-bridge-sa |
| `--scim-bridge-image` | Docker image for SCIM Bridge | No | 1password/scim-bridge:latest |
| `--domain` | Your organization's domain name | Yes | - |
| `--admin-email` | Google Workspace Admin Email | Yes | - |
| `--service-account-file` | Path to service account key file (Python script only) | Yes (Python only) | - |

## Workflow

The scripts perform the following steps:

1. Authenticate with Google Cloud Platform
2. Create a service account for the SCIM Bridge
3. Assign necessary IAM roles to the service account
4. Deploy the 1Password SCIM Bridge on Google Cloud Run
5. Prepare configuration for Google Identity integration
6. Provide instructions for manual SAML application setup in Google Workspace

## Manual Steps Required

After running the script, you'll need to:

1. Generate a service account key if using the shell script
2. Set up a custom SAML application in Google Workspace Admin Console
3. Configure 1Password Admin Console for SCIM integration
4. Assign users/groups to the SAML application

These steps require manual intervention as they involve web UIs and cannot be fully automated.

## Security Considerations

- The SCIM Bridge is deployed with public access (`--allow-unauthenticated`), but it uses bearer tokens for authentication
- Store service account keys securely and follow the principle of least privilege
- Regularly rotate credentials used for the SCIM Bridge

## Additional Resources

- [1Password SCIM Bridge Documentation](https://support.1password.com/scim/)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Workspace SAML Apps](https://support.google.com/a/answer/6087519)

## Troubleshooting

If you encounter issues during setup:

1. Check the Google Cloud Run logs for the SCIM Bridge deployment
2. Verify IAM permissions for the service account
3. Ensure the SAML configuration in Google Workspace is correct
4. Test the SCIM Bridge endpoint with a curl request to check if it's responding

For more detailed troubleshooting, refer to the 1Password SCIM Bridge documentation.