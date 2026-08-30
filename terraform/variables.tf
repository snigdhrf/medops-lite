variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "medops-lite"
}

variable "release_sha" {
  type        = string
  default     = ""
  description = "Git SHA used for the ECR image tag and S3 model key. Leave empty to provision storage only."

  validation {
    condition     = var.release_sha == "" || can(regex("^[0-9a-f]{7,40}$", var.release_sha))
    error_message = "release_sha must be a 7-to-40-character lowercase Git SHA."
  }
}
