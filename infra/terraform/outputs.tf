output "bigquery_dataset_id" {
  description = "BigQuery dataset created for the project."
  value       = google_bigquery_dataset.parleman.dataset_id
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository name."
  value       = var.artifact_registry_repository_id
}

output "cloud_run_worker_url" {
  description = "Cloud Run worker URL."
  value       = google_cloud_run_v2_service.prefect_worker.uri
}

output "prefect_server_url" {
  description = "Cloud Run Prefect server URL."
  value       = google_cloud_run_v2_service.prefect_server.uri
}

output "runner_service_account_email" {
  description = "BigQuery runner service account email."
  value       = google_service_account.runner.email
}

output "worker_service_account_email" {
  description = "Cloud Run worker service account email."
  value       = google_service_account.worker.email
}

output "worker_image" {
  description = "Container image used by the Cloud Run worker."
  value       = local.worker_image
}