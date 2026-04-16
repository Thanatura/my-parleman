terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }
  }
}

# IP statique externe
resource "google_compute_address" "postgres_ip" {
  name = "postgres-static-ip"
}

# Règle de firewall pour PostgreSQL (port 5432)
resource "google_compute_firewall" "allow_postgres" {
  name    = "allow-postgres"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  # ⚠️ Restreindre à tes IPs en production !
  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["postgres-server"]
}

# Règle firewall SSH (optionnel, pour administrer la VM)
resource "google_compute_firewall" "allow_ssh" {
  name    = "allow-ssh-postgres"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["postgres-server"]
}

# La VM
resource "google_compute_instance" "postgres_vm" {
  name         = "postgres-vm"
  machine_type = "e2-medium"
  zone         = var.zone

  tags = ["postgres-server"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2204-lts"
      size  = 50  # Go
      type  = "pd-ssd"
    }
  }

  network_interface {
    network = "default"

    access_config {
      nat_ip = google_compute_address.postgres_ip.address
    }
  }

  # Script de bootstrap PostgreSQL externalise dans un template lisible
  metadata_startup_script = templatefile("${path.module}/scripts/postgres_startup.sh.tftpl", {
    prefect_db_user     = var.prefect_db_user
    prefect_db_password = replace(var.prefect_db_password, "'", "''")
    prefect_db_name     = var.prefect_db_name
  })

  service_account {
    scopes = ["cloud-platform"]
  }
}