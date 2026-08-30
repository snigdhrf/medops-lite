variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "medops-lite"
}

variable "image_digest" {
  type        = string
  default     = ""
  description = "Immutable ECR image digest. Set with model_artifact_key to deploy."

  validation {
    condition     = var.image_digest == "" || can(regex("^sha256:[0-9a-f]{64}$", var.image_digest))
    error_message = "image_digest must match sha256:<64 lowercase hexadecimal characters>."
  }
}

variable "model_artifact_key" {
  type        = string
  default     = ""
  description = "Content-addressed S3 key for model.tar.gz. Set with image_digest to deploy."

  validation {
    condition     = var.model_artifact_key == "" || can(regex("^models/[0-9a-f]{64}/model\\.tar\\.gz$", var.model_artifact_key))
    error_message = "model_artifact_key must match models/<64-character-sha256>/model.tar.gz."
  }
}
