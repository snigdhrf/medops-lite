variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "medops-lite"
}

variable "image_tag" {
  type        = string
  default     = ""
  description = "Immutable ECR image tag, such as a Git SHA. Set with model_artifact_key to deploy."

  validation {
    condition     = var.image_tag == "" || can(regex("^[A-Za-z0-9_][A-Za-z0-9._-]{0,127}$", var.image_tag))
    error_message = "image_tag must be a valid ECR image tag."
  }
}

variable "model_artifact_key" {
  type        = string
  default     = ""
  description = "Immutable S3 key for model.tar.gz, such as models/<model-version>/model.tar.gz. Set with image_tag to deploy."

  validation {
    condition     = var.model_artifact_key == "" || can(regex("^models/[^/]+/model\\.tar\\.gz$", var.model_artifact_key))
    error_message = "model_artifact_key must match models/<model-version>/model.tar.gz."
  }
}
