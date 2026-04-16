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

variable "prefect_server_allow_unauthenticated" {
  description = "Whether the Prefect server should be publicly invokable."
  type        = bool
  default     = true
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

variable "cloud_run_env_vars" {
  description = "Additional environment variables for the Cloud Run worker."
  type        = map(string)
  default     = {}
}