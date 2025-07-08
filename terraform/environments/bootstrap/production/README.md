# GCP Bootstrap for Workload Identity Federation

This Terraform configuration is for a **one-time manual setup** to establish a secure, keyless connection between your GitHub repository and Google Cloud.

It creates:

1.  A **Workload Identity Pool** and **OIDC Provider** to trust GitHub Actions.
2.  A dedicated **Service Account for Terraform** (`promptly-tf`).
3.  IAM bindings to give the Terraform SA owner permissions (for simplicity) and allow GitHub Actions from your repository to impersonate it.

## Manual Setup Steps

You only need to do this once per GCP project.

### 1. Prerequisites

- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/install) installed.
- [Terraform](https://developer.hashicorp.com/terraform/install) installed.
- You must be authenticated with GCP with a user that has `roles/owner` permissions on the target project.
  ```sh
  gcloud auth application-default login
  gcloud config set project YOUR_PROJECT_ID
  ```

### 2. Configure Variables

Create a `terraform.tfvars` file in this directory (`terraform/bootstrap`):

```hcl
# terraform/bootstrap/terraform.tfvars

project_id  = "your-gcp-project-id"
github_repo = "your-github-owner/your-github-repo"
```

- `project_id`: The ID of your GCP project.
- `github_repo`: The path to your repository (e.g., `promptly-social/promptly-social`).

### 3. Apply Terraform

Run the following commands from this directory (`terraform/bootstrap`):

```sh
terraform init
terraform plan -out=bootstrap.plan
terraform apply "bootstrap.plan"
```

### 4. Set GitHub Secrets

After Terraform successfully applies, it will output three values. **You must add these as secrets** to your GitHub repository under `Settings > Secrets and variables > Actions`:

- `GCP_PROJECT_ID`: The ID of your GCP project.
- `GCP_WIF_PROVIDER`: The full ID of the Workload Identity Provider.
  - e.g., `projects/123456789/locations/global/workloadIdentityPools/promptly-github-pool/providers/github-provider`
- `GCP_TERRAFORM_SA_EMAIL`: The email of the service account created for Terraform CI/CD.
  - e.g., `promptly-tf-sa@your-project-id.iam.gserviceaccount.com`

**Important**: Your CI/CD pipelines will now use these secrets to authenticate without a key. You no longer need the `GCP_SA_KEY` secret.
