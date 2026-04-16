variable "project_id" {
  description = "ID du projet GCP"
  type        = string
}

variable "region" {
  description = "Région GCP"
  type        = string
  default     = "europe-west1"
}

variable "zone" {
  description = "Zone GCP"
  type        = string
  default     = "europe-west1-b"
}

variable "prefect_db_user" {
  description = "Utilisateur PostgreSQL"
  type        = string
  default     = "prefect"
}

variable "prefect_db_password" {
  description = "Mot de passe PostgreSQL"
  type        = string
  sensitive   = true
}

variable "prefect_db_name" {
  description = "Nom de la base de données"
  type        = string
  default     = "prefect"
}