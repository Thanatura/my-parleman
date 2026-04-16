terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 6.0.0"
    }
  }
}

# Static external IP
resource "google_compute_address" "postgres_ip" {
  name = "postgres-static-ip"
}

# Firewall rule for PostgreSQL (port 5432)
resource "google_compute_firewall" "allow_postgres" {
  name    = "allow-postgres"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["5432"]
  }

  # Restrict to trusted CIDRs in production.
  source_ranges = var.postgres_source_ranges
  target_tags   = ["postgres-server"]
}

# SSH firewall rule (optional, for VM administration)
resource "google_compute_firewall" "allow_ssh" {
  count   = var.enable_ssh ? 1 : 0
  name    = "allow-ssh-postgres"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }

  source_ranges = var.ssh_source_ranges
  target_tags   = ["postgres-server"]
}

# The VM
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

  # PostgreSQL bootstrap script externalized in a readable template
  metadata_startup_script = templatefile("${path.module}/scripts/postgres_startup.sh.tftpl", {
    prefect_db_user     = var.prefect_db_user
    prefect_db_password = replace(var.prefect_db_password, "'", "''")
    prefect_db_name     = var.prefect_db_name
  })

  service_account {
    scopes = ["cloud-platform"]
  }
}