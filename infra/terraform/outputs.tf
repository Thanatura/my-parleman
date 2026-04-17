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

output "runner_service_account_key_name" {
  description = "Resource name of the runner service account key."
  value       = google_service_account_key.runner.name
}

output "runner_service_account_key_json" {
  description = "Runner service account key JSON for external integrations."
  value       = base64decode(google_service_account_key.runner.private_key)
  sensitive   = true
}

output "worker_service_account_email" {
  description = "Cloud Run worker service account email."
  value       = google_service_account.worker.email
}

output "worker_image" {
  description = "Container image used by the Cloud Run worker."
  value       = local.worker_image
}

output "prefect_db_public_ip" {
  description = "Public IP of the PostgreSQL VM used by Prefect server."
  value       = module.vm_db.postgres_public_ip
}

output "prefect_server_database_connection_url" {
  description = "Database connection URL injected into PREFECT_SERVER_DATABASE_CONNECTION_URL."
  value       = module.vm_db.connection_string
  sensitive   = true
}

output "backend_url" {
  description = "Cloud Run backend (FastAPI) URL."
  value       = google_cloud_run_v2_service.backend.uri
}

output "backend_service_account_email" {
  description = "Backend Cloud Run service account email."
  value       = google_service_account.backend.email
}

output "frontend_url" {
  description = "Cloud Run frontend (Streamlit) URL."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "frontend_service_account_email" {
  description = "Frontend Cloud Run service account email."
  value       = google_service_account.frontend.email
}