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

variable "postgres_source_ranges" {
  description = "CIDR autorisés vers PostgreSQL (port 5432)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "enable_ssh" {
  description = "Activer la règle firewall SSH sur la VM"
  type        = bool
  default     = false
}

variable "ssh_source_ranges" {
  description = "CIDR autorisés pour SSH quand enable_ssh=true"
  type        = list(string)
  default     = []
}