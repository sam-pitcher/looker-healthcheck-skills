variable "project_id" {
  type        = string
  description = "The Google Cloud project ID where Firestore will be provisioned."
}

variable "region" {
  type        = string
  description = "The default GCP region (e.g. us-central1)."
  default     = "us-central1"
}

variable "firestore_location_id" {
  type        = string
  description = "The location ID for Firestore (e.g. us-central1 or nam5 for multi-region US)."
  default     = "us-central1"
}

variable "database_id" {
  type        = string
  description = "The Firestore database ID. Using a named database like 'looker-healthcheck-db' allows Native mode alongside Datastore mode."
  default     = "looker-healthcheck-db"
}
