resource "google_storage_bucket" "tf_state" {
  name                        = var.bucket_name
  location                    = var.location
  project                     = var.project_id
  uniform_bucket_level_access = true
  public_access_prevention     = "enforced"

  versioning {
    enabled = true
  }

  labels = {
    app        = "parleman"
    managed_by = "terraform"
    purpose    = "terraform-state"
  }
}

resource "google_project_service" "artifact_registry" {
  project            = var.project_id
  service            = "artifactregistry.googleapis.com"
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "docker" {
  depends_on = [google_project_service.artifact_registry]

  project       = var.project_id
  location      = var.artifact_registry_location
  repository_id = var.artifact_registry_repository_id
  format        = "DOCKER"
  description   = "Docker images for the ParlemAN worker and related jobs."

  labels = {
    app        = "parleman"
    managed_by = "terraform"
    purpose    = "artifact-registry"
  }
}