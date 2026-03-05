terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

resource "google_project_service" "vertex_ai" {
  service = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "text_to_speech" {
  service = "texttospeech.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "service_usage" {
  service = "serviceusage.googleapis.com"
  disable_on_destroy = false
}
