output "postgres_public_ip" {
  description = "IP publique de la VM PostgreSQL"
  value       = google_compute_address.postgres_ip.address
}

output "connection_string" {
  description = "Chaîne de connexion PostgreSQL"
  value       = "postgresql+asyncpg://${var.prefect_db_user}:${var.prefect_db_password}@${google_compute_address.postgres_ip.address}:5432/${var.prefect_db_name}"
  sensitive   = true
}