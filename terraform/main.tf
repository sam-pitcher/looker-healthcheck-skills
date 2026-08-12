terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Required Google Cloud APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "bigquery.googleapis.com",
    "serviceusage.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# 2. Provision Firestore Database in Native Mode
resource "google_firestore_database" "healthcheck_db" {
  project                     = var.project_id
  name                        = var.database_id
  location_id                 = var.firestore_location_id
  type                        = "FIRESTORE_NATIVE"
  concurrency_mode            = "OPTIMISTIC"
  app_engine_integration_mode = "DISABLED"
  deletion_policy             = "ABANDON"

  depends_on = [
    google_project_service.required_apis
  ]
}

# 3. Create Composite Index for Multi-Tenant Time-Series Querying (Instance-Level)
resource "google_firestore_index" "healthcheck_timeseries_index" {
  project    = var.project_id
  database   = google_firestore_database.healthcheck_db.name
  collection = "looker_healthchecks"

  fields {
    field_path = "instance_url"
    order      = "ASCENDING"
  }

  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }

  depends_on = [
    google_firestore_database.healthcheck_db
  ]
}

# 4. Create Composite Index for Model-Scoped Historical Trend Querying
resource "google_firestore_index" "healthcheck_model_timeseries_index" {
  project    = var.project_id
  database   = google_firestore_database.healthcheck_db.name
  collection = "looker_healthchecks"

  fields {
    field_path = "target_scope.model_name"
    order      = "ASCENDING"
  }

  fields {
    field_path = "timestamp"
    order      = "DESCENDING"
  }

  depends_on = [
    google_firestore_database.healthcheck_db
  ]
}
