resource "google_project_service" "services" {
  for_each = local.project_services

  project           = var.project_id
  service           = each.value
  disable_on_destroy = false
}

resource "google_service_account" "runner" {
  account_id   = var.runner_service_account_id
  display_name = "ParlemAN BigQuery Runner"
  project      = var.project_id
}

resource "google_service_account_key" "runner" {
  service_account_id = google_service_account.runner.name
  private_key_type   = "TYPE_GOOGLE_CREDENTIALS_FILE"
}

resource "google_service_account" "worker" {
  account_id   = var.worker_service_account_id
  display_name = "ParlemAN Prefect Worker"
  project      = var.project_id
}

resource "google_service_account" "server" {
  account_id   = var.server_service_account_id
  display_name = "ParlemAN Prefect Server"
  project      = var.project_id
}

resource "google_service_account" "backend" {
  account_id   = var.backend_service_account_id
  display_name = "ParlemAN Backend (FastAPI)"
  project      = var.project_id
}

resource "google_service_account" "frontend" {
  account_id   = var.frontend_service_account_id
  display_name = "ParlemAN Frontend (Streamlit)"
  project      = var.project_id
}

resource "google_bigquery_dataset" "parleman" {
  dataset_id                 = var.bq_dataset_id
  description                = "Core analytical dataset for ParlemAN."
  delete_contents_on_destroy = false
  friendly_name              = "ParlemAN"
  location                   = var.bq_location
  project                    = var.project_id
  labels                     = local.labels
}

resource "google_bigquery_dataset_access" "runner_writer" {
  dataset_id    = google_bigquery_dataset.parleman.dataset_id
  project       = var.project_id
  role          = "WRITER"
  user_by_email = google_service_account.runner.email
}

resource "google_project_iam_member" "runner_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.runner.email}"
}

resource "google_project_iam_member" "worker_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "server_run_viewer" {
  project = var.project_id
  role    = "roles/run.viewer"
  member  = "serviceAccount:${google_service_account.server.email}"
}

resource "google_project_iam_member" "backend_bigquery_reader" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "backend_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "frontend_artifact_registry_reader" {
  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = "serviceAccount:${google_service_account.frontend.email}"
}

module "vm_db" {
  source = "./vm_db"

  project_id          = var.project_id
  region              = var.region
  zone                = var.vm_db_zone
  prefect_db_user     = var.prefect_db_user
  prefect_db_password = var.prefect_db_password
  prefect_db_name     = var.prefect_db_name
  postgres_source_ranges = var.vm_db_postgres_source_ranges
  enable_ssh          = var.vm_db_enable_ssh
  ssh_source_ranges   = var.vm_db_ssh_source_ranges
}

resource "google_cloud_run_v2_service" "prefect_worker" {
  depends_on = [
    google_project_service.services,
    google_service_account.worker,
  ]

  deletion_protection = false
  location            = var.region
  name                = var.cloud_run_service_name
  project             = var.project_id
  labels              = local.labels

  template {
    service_account = google_service_account.worker.email

    scaling {
      min_instance_count = 1
    }

    containers {
      image  = local.worker_image
      command = ["prefect", "worker", "start", "--install-policy", "never", "--with-healthcheck", "-p", "parleman-work-pool", "-t", "cloud-run"]

      dynamic "env" {
        for_each = local.worker_env

        content {
          name  = env.key
          value = env.value
        }
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "4Gi"
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "prefect_server" {
  depends_on = [
    google_project_service.services,
    google_service_account.server,
    google_project_iam_member.server_run_viewer,
  ]

  deletion_protection = false
  location            = var.region
  name                = var.prefect_server_service_name
  project             = var.project_id
  labels              = local.labels

  template {
    service_account = google_service_account.server.email

    scaling {
      min_instance_count = var.prefect_server_min_instances
      max_instance_count = var.prefect_server_max_instances
    }

    containers {
      image = local.server_image

      dynamic "env" {
        for_each = var.prefect_server_api_auth_string == null ? {} : {
          PREFECT_SERVER_API_AUTH_STRING = var.prefect_server_api_auth_string
        }

        content {
          name  = env.key
          value = env.value
        }
      }

      env {
        name = "PREFECT_SERVER_PORT"
        value = tostring(var.prefect_server_port)
      }

      env {
        name = "GCP_PROJECT"
        value = var.project_id
      }

      env {
        name  = "PREFECT_UI_API_URL"
        value = "/api"
      }

      env {
        name  = "PREFECT_API_DATABASE_CONNECTION_URL"
        value = module.vm_db.connection_string
      }

      ports {
        container_port = var.prefect_server_port
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "2Gi"
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "prefect_server_public_invoker" {
  count = var.prefect_server_allow_unauthenticated ? 1 : 0

  location = google_cloud_run_v2_service.prefect_server.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.prefect_server.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "backend" {
  depends_on = [
    google_project_service.services,
    google_service_account.backend,
    google_project_iam_member.backend_bigquery_reader,
  ]

  deletion_protection = false
  location            = var.region
  name                = var.cloud_run_backend_service_name
  project             = var.project_id
  labels              = local.labels

  template {
    service_account = google_service_account.backend.email

    scaling {
      min_instance_count = 1
    }

    containers {
      image = local.backend_image

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }

      env {
        name  = "BQ_DATASET"
        value = var.bq_dataset_id
      }

      env {
        name  = "PARLEMAN_API_KEY"
        value = var.parleman_api_key
      }

      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "backend_public_invoker" {
  location = google_cloud_run_v2_service.backend.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "frontend" {
  depends_on = [
    google_project_service.services,
    google_service_account.frontend,
    google_cloud_run_v2_service.backend,
  ]

  deletion_protection = false
  location            = var.region
  name                = var.cloud_run_frontend_service_name
  project             = var.project_id
  labels              = local.labels

  template {
    service_account = google_service_account.frontend.email

    scaling {
      min_instance_count = 1
    }

    containers {
      image = local.frontend_image

      env {
        name  = "PARLEMAN_API_URL"
        value = google_cloud_run_v2_service.backend.uri
      }

      env {
        name  = "PARLEMAN_API_KEY"
        value = var.parleman_api_key
      }

      env {
        name  = "STREAMLIT_SERVER_HEADLESS"
        value = "true"
      }

      env {
        name  = "STREAMLIT_SERVER_ADDRESS"
        value = "0.0.0.0"
      }

      env {
        name  = "STREAMLIT_SERVER_PORT"
        value = "8501"
      }

      ports {
        container_port = 8501
      }

      resources {
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "frontend_public_invoker" {
  location = google_cloud_run_v2_service.frontend.location
  project  = var.project_id
  service  = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}