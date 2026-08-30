terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "artifacts" {
  bucket_prefix = "${var.project_name}-"
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

resource "aws_ecr_repository" "inference" {
  name                 = var.project_name
  image_tag_mutability = "IMMUTABLE"
  image_scanning_configuration { scan_on_push = true }
}

resource "aws_iam_role" "sagemaker" {
  name = "${var.project_name}-sagemaker"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "sagemaker.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "sagemaker" {
  role = aws_iam_role.sagemaker.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"]
    }]
  })
}

resource "aws_sagemaker_model" "inference" {
  count              = var.deploy_endpoint && var.model_artifact_s3_uri != "" ? 1 : 0
  name               = var.project_name
  execution_role_arn = aws_iam_role.sagemaker.arn
  primary_container {
    image          = "${aws_ecr_repository.inference.repository_url}:${var.image_tag}"
    model_data_url = var.model_artifact_s3_uri
    environment    = { MODEL_PATH = "/opt/ml/model/model.pt" }
  }
}

resource "aws_sagemaker_endpoint_configuration" "inference" {
  count = var.deploy_endpoint && var.model_artifact_s3_uri != "" ? 1 : 0
  name  = var.project_name
  production_variants {
    variant_name           = "AllTraffic"
    model_name             = aws_sagemaker_model.inference[0].name
    initial_instance_count = 1
    instance_type          = "ml.t2.medium"
    initial_variant_weight = 1
  }
}

resource "aws_sagemaker_endpoint" "inference" {
  count                = var.deploy_endpoint && var.model_artifact_s3_uri != "" ? 1 : 0
  name                 = var.project_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.inference[0].name
}
