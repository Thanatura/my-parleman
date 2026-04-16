variable "project_id" {
  description = "GCP project that hosts the Terraform state bucket. Can be set through TF_VAR_project_id."
  type        = string
  default     = null
  nullable    = true
}

variable "location" {
  description = "Location for the Terraform state bucket."
  type        = string
  default     = "EU"
}

variable "artifact_registry_location" {
  description = "Region for the Artifact Registry Docker repository."
  type        = string
  default     = "europe-west1"
}

variable "artifact_registry_repository_id" {
  description = "Artifact Registry repository name for ParlemAN images."
  type        = string
  default     = "parleman-artifact-repo"
}

variable "bucket_name" {
  description = "GCS bucket name used for the Terraform backend."
  type        = string
  default     = "my-parleman-tf-state"
}