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

locals {
  deployment_requested = var.image_tag != "" || var.model_artifact_key != ""
}

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
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [aws_s3_bucket.artifacts.arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject"]
        Resource = ["${aws_s3_bucket.artifacts.arn}/*"]
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = [aws_ecr_repository.inference.arn]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "ecr:GetAuthorizationToken",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:DescribeLogStreams",
          "logs:PutLogEvents",
        ]
        Resource = ["*"]
      },
    ]
  })
}

resource "aws_sagemaker_model" "inference" {
  count              = local.deployment_requested ? 1 : 0
  execution_role_arn = aws_iam_role.sagemaker.arn
  # aws_sagemaker_model has no name_prefix argument. Omitting name gives each replacement a unique name.
  primary_container {
    image          = "${aws_ecr_repository.inference.repository_url}:${var.image_tag}"
    model_data_url = "s3://${aws_s3_bucket.artifacts.bucket}/${var.model_artifact_key}"
    environment    = { MODEL_PATH = "/opt/ml/model/model.pt" }
  }
  lifecycle {
    create_before_destroy = true
    precondition {
      condition     = var.image_tag != "" && var.model_artifact_key != ""
      error_message = "image_tag and model_artifact_key must be set together."
    }
  }
}

resource "aws_sagemaker_endpoint_configuration" "inference" {
  count       = local.deployment_requested ? 1 : 0
  name_prefix = "${var.project_name}-config-"
  production_variants {
    variant_name = "AllTraffic"
    model_name   = aws_sagemaker_model.inference[0].name
    serverless_config {
      max_concurrency   = 2
      memory_size_in_mb = 2048
    }
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_cloudwatch_log_group" "sagemaker_endpoint" {
  count             = local.deployment_requested ? 1 : 0
  name              = "/aws/sagemaker/Endpoints/${var.project_name}"
  retention_in_days = 14
}

resource "aws_sagemaker_endpoint" "inference" {
  count                = local.deployment_requested ? 1 : 0
  name                 = var.project_name
  endpoint_config_name = aws_sagemaker_endpoint_configuration.inference[0].name
  depends_on           = [aws_cloudwatch_log_group.sagemaker_endpoint]
}
