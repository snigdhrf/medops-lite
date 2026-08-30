output "artifacts_bucket" { value = aws_s3_bucket.artifacts.bucket }
output "ecr_repository_url" { value = aws_ecr_repository.inference.repository_url }
output "sagemaker_role_arn" { value = aws_iam_role.sagemaker.arn }
output "sagemaker_endpoint_name" {
  value = try(aws_sagemaker_endpoint.inference[0].name, null)
}
