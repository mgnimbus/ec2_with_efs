# cw - firehose role 
resource "aws_iam_role" "cwl_kf_role" {
  name = "cw_firehose_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "logs.amazonaws.com"
        }
      },
    ]
  })
}
resource "aws_iam_role_policy" "cwl_kf_policy" {
  name = "cw_firefose_policy"
  role = aws_iam_role.cwl_kf_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "firehose:PutRecord",
        ]
        Effect   = "Allow"
        Resource = "${aws_kinesis_firehose_delivery_stream.extended_s3_stream.arn}"
      },
    ]
  })
}

# cw subscription filter
resource "aws_cloudwatch_log_subscription_filter" "test_lambdafunction_logfilter" {
  name            = "firehose_logfilter"
  role_arn        = aws_iam_role.cwl_kf_role.arn
  log_group_name  = aws_cloudwatch_log_group.efs.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.extended_s3_stream.arn
}

# Firehose - s3 role 
resource "aws_iam_role" "firehose_role" {
  name                = "firehose_s3_role"
  assume_role_policy  = data.aws_iam_policy_document.firehose_assume_role.json
  managed_policy_arns = [aws_iam_policy.firehose_policy.arn]
}

data "aws_iam_policy_document" "firehose_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["firehose.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_policy" "firehose_policy" {
  name        = "firehose_s3_policy"
  path        = "/"
  description = "My firehose s3 policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject"
        ]
        Effect = "Allow"
        Resource = [
          "${aws_s3_bucket.bucket.arn}",
          "${aws_s3_bucket.bucket.arn}/*"
        ]
      },
      {
        Action = [
          "lambda:InvokeFunction",
        ]
        Effect = "Allow"
        Resource = [
          "${aws_lambda_function.lambda_processor.arn}:$LATEST",
        ]
      }
    ]
  })
}

# firehose stream
resource "aws_kinesis_firehose_delivery_stream" "extended_s3_stream" {
  name        = "efs_log_stream"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.firehose_role.arn
    bucket_arn = aws_s3_bucket.bucket.arn

    processing_configuration {
      enabled = "true"

      processors {
        type = "Lambda"

        parameters {
          parameter_name  = "LambdaArn"
          parameter_value = "${aws_lambda_function.lambda_processor.arn}:$LATEST"
        }
        parameters {
          parameter_name  = "BufferSizeInMBs"
          parameter_value = "1"
        }
      }
    }
  }
}

# logs bucket
resource "aws_s3_bucket" "bucket" {
  bucket = "efs-logs-bucky"
}

# resource "aws_s3_bucket_acl" "bucket_acl" {
#   bucket = aws_s3_bucket.bucket.id
#   acl    = "private"
# }

# Lambda role
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_iam" {
  name                = "lambda_iam"
  assume_role_policy  = data.aws_iam_policy_document.lambda_assume_role.json
  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"]
}

provider "archive" {}

data "archive_file" "zip" {
  type        = "zip"
  source_file = "./scripts/decomp/decomp.py"
  output_path = "./scripts/decomp/decomp.zip"
}

# Lambda Function
resource "aws_lambda_function" "lambda_processor" {
  function_name    = "firehose_lambda_processor"
  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256
  role             = aws_iam_role.lambda_iam.arn
  handler          = "decomp.lambda_handler"
  runtime          = "python3.8"
  timeout          = 60
}
