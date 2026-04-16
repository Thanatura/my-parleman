output "bucket_name" {
  description = "Terraform state bucket name."
  value       = google_storage_bucket.tf_state.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository created in bootstrap."
  value       = google_artifact_registry_repository.docker.repository_id
}