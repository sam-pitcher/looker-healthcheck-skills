output "firestore_database_name" {
  value       = google_firestore_database.healthcheck_db.name
  description = "The name of the provisioned Firestore database."
}

output "firestore_collection" {
  value       = "looker_healthchecks"
  description = "The target collection name used by the Looker Healthcheck Agent."
}

output "env_configuration_snippet" {
  value = <<EOT
# Add the following to your .env file:
GOOGLE_CLOUD_PROJECT=${var.project_id}
FIRESTORE_DATABASE=${var.database_id}
FIRESTORE_COLLECTION=looker_healthchecks
EOT
  description = "Environment variables configuration snippet for the agent."
}
