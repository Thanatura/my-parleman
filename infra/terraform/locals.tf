locals {
  labels = {
    app         = "parleman"
    environment = var.environment
    managed_by  = "terraform"
  }

  project_services = toset([
    "bigquery.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
  ])

  worker_image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${var.cloud_run_worker_image_name}:${var.cloud_run_worker_image_tag}"
  server_image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_registry_repository_id}/${var.cloud_run_server_image_name}:${var.cloud_run_server_image_tag}"

  prefect_api_url = "${google_cloud_run_v2_service.prefect_server.uri}/api"

  worker_env = merge(
    {
      GCP_PROJECT = var.project_id
      BQ_DATASET  = var.bq_dataset_id
      PREFECT_API_URL = local.prefect_api_url
    },
    var.prefect_server_api_auth_string == null ? {} : {
      PREFECT_API_AUTH_STRING = var.prefect_server_api_auth_string
    },
    var.cloud_run_env_vars,
  )
}