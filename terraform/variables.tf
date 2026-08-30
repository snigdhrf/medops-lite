variable "aws_region" {
  type    = string
  default = "eu-west-1"
}

variable "project_name" {
  type    = string
  default = "medops-lite"
}

variable "model_artifact_s3_uri" {
  type        = string
  default     = ""
  description = "s3:// URI for model.tar.gz. Leave empty to provision storage only."
}

variable "image_tag" {
  type        = string
  default     = "latest"
  description = "ECR image tag to deploy."
}

variable "deploy_endpoint" {
  type        = bool
  default     = false
  description = "Create a SageMaker serverless endpoint after model_artifact_s3_uri is set."
}
