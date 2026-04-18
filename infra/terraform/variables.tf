variable "project_id" {
  description = "GCP project that hosts the ParlemAN infrastructure. Can be set through TF_VAR_project_id."
  type        = string
  default     = null
  nullable    = true
}

variable "region" {
  description = "Default GCP region for regional resources."
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Logical environment label used for resource tags."
  type        = string
  default     = "prod"
}

variable "bq_dataset_id" {
  description = "BigQuery dataset that stores the project tables. Can be set through TF_VAR_bq_dataset_id."
  type        = string
  default     = null
  nullable    = true
}

variable "bq_location" {
  description = "BigQuery dataset location."
  type        = string
  default     = "EU"
}

variable "bq_delete_contents_on_destroy" {
  description = "Whether Terraform should delete all dataset contents before deleting the BigQuery dataset during destroy."
  type        = bool
  default     = true
}

variable "artifact_registry_repository_id" {
  description = "Docker repository that stores the Prefect worker image."
  type        = string
  default     = "parleman-artifact-repo"
}

variable "runner_service_account_id" {
  description = "Service account that runs BigQuery loads."
  type        = string
  default     = "parleman-bq-runner"
}

variable "worker_service_account_id" {
  description = "Service account that runs the Cloud Run worker."
  type        = string
  default     = "parleman-prefect-worker"
}

variable "server_service_account_id" {
  description = "Service account that runs the Cloud Run Prefect server."
  type        = string
  default     = "parleman-prefect-server"
}

variable "cloud_run_service_name" {
  description = "Cloud Run service name for the Prefect worker."
  type        = string
  default     = "prefect-worker"
}

variable "cloud_run_worker_image_name" {
  description = "Container image name for the Prefect worker."
  type        = string
  default     = "prefect-worker"
}

variable "cloud_run_worker_image_tag" {
  description = "Container image tag for the Prefect worker."
  type        = string
  default     = "latest"
}

variable "cloud_run_server_image_name" {
  description = "Container image name for the Prefect server."
  type        = string
  default     = "prefect-server"
}

variable "cloud_run_server_image_tag" {
  description = "Container image tag for the Prefect server."
  type        = string
  default     = "latest"
}

variable "prefect_server_service_name" {
  description = "Cloud Run service name for the Prefect server."
  type        = string
  default     = "prefect-server"
}

variable "prefect_server_port" {
  description = "Container port used by the Prefect server in Cloud Run."
  type        = number
  default     = 8080
}

variable "prefect_server_min_instances" {
  description = "Minimum number of running instances for the Prefect server."
  type        = number
  default     = 1
}

variable "prefect_server_max_instances" {
  description = "Maximum number of running instances for the Prefect server."
  type        = number
  default     = 3
}

variable "prefect_server_allow_unauthenticated" {
  description = "Whether the Prefect server should be publicly invokable."
  type        = bool
  default     = true
}

variable "prefect_server_api_auth_string" {
  description = "Prefect server API auth string in the form username:password. Required when public unauthenticated access is enabled."
  type        = string
  default     = null
  nullable    = true
  sensitive   = true

  validation {
    condition = (
      !var.prefect_server_allow_unauthenticated ||
      (
        var.prefect_server_api_auth_string != null &&
        can(regex("^[^:]+:.+$", var.prefect_server_api_auth_string))
      )
    )
    error_message = "When prefect_server_allow_unauthenticated is true, prefect_server_api_auth_string must be set as username:password."
  }
}

variable "vm_db_zone" {
  description = "GCP zone used for the PostgreSQL VM."
  type        = string
  default     = "europe-west1-b"
}

variable "prefect_db_user" {
  description = "PostgreSQL user for Prefect server database."
  type        = string
  default     = "prefect"
}

variable "prefect_db_password" {
  description = "PostgreSQL password for Prefect server database user."
  type        = string
  sensitive   = true
}

variable "prefect_db_name" {
  description = "PostgreSQL database name used by Prefect server."
  type        = string
  default     = "prefect"
}

variable "vm_db_postgres_source_ranges" {
  description = "CIDR ranges allowed to connect to PostgreSQL (port 5432). Restrict this in production."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "vm_db_enable_ssh" {
  description = "Whether to create an SSH firewall rule (port 22) for the DB VM."
  type        = bool
  default     = false
}

variable "vm_db_ssh_source_ranges" {
  description = "CIDR ranges allowed for SSH access to the DB VM when vm_db_enable_ssh is true."
  type        = list(string)
  default     = []
}

variable "cloud_run_backend_image_name" {
  description = "Container image name for the backend (FastAPI)."
  type        = string
  default     = "parleman-backend"
}

variable "cloud_run_backend_image_tag" {
  description = "Container image tag for the backend."
  type        = string
  default     = "latest"
}

variable "cloud_run_backend_service_name" {
  description = "Cloud Run service name for the backend."
  type        = string
  default     = "parleman-backend"
}

variable "backend_service_account_id" {
  description = "Service account that runs the backend Cloud Run service."
  type        = string
  default     = "parleman-backend"
}

variable "cloud_run_frontend_image_name" {
  description = "Container image name for the frontend (Streamlit)."
  type        = string
  default     = "parleman-frontend"
}

variable "cloud_run_frontend_image_tag" {
  description = "Container image tag for the frontend."
  type        = string
  default     = "latest"
}

variable "cloud_run_frontend_service_name" {
  description = "Cloud Run service name for the frontend."
  type        = string
  default     = "parleman-frontend"
}

variable "frontend_service_account_id" {
  description = "Service account that runs the frontend Cloud Run service."
  type        = string
  default     = "parleman-frontend"
}

variable "cloud_run_env_vars" {
  description = "Additional environment variables for the Cloud Run worker."
  type        = map(string)
  default     = {}
}

variable "parleman_api_key" {
  description = "API key for ParlemAN backend and frontend authentication."
  type        = string
  sensitive   = true
}