# firehose stream
resource "aws_kinesis_firehose_delivery_stream" "extended_s3_stream" {
  name        = "efs_log_stream"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn    = aws_iam_role.firehose_s3_role.arn
    bucket_arn  = data.aws_s3_bucket.bucket.arn
    buffer_size = 128
    prefix      = "efs_logs_parquet/"

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
          parameter_value = "2"
        }
        parameters {
          parameter_name  = "BufferIntervalInSeconds"
          parameter_value = "64"
        }
      }
    }
    data_format_conversion_configuration {
      enabled = true
      input_format_configuration {
        deserializer {
          open_x_json_ser_de {
            case_insensitive                         = true
            column_to_json_key_mappings              = {}
            convert_dots_in_json_keys_to_underscores = false
          }
        }
      }

      output_format_configuration {
        serializer {
          parquet_ser_de {
            compression = "GZIP"
          }
        }
      }

      schema_configuration {
        database_name = "default"
        role_arn      = aws_iam_role.firehose_s3_role.arn
        table_name    = aws_glue_catalog_table.aws_glue_catalog_table.name
      }
    }

  }
}

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
resource "aws_iam_role" "firehose_s3_role" {
  name                = "firehose_s3_role_efs"
  assume_role_policy  = data.aws_iam_policy_document.firehose_assume_role.json
  managed_policy_arns = [aws_iam_policy.firehose_policy.arn, "arn:aws:iam::aws:policy/service-role/AWSGlueServiceRole"]
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
          "${data.aws_s3_bucket.bucket.arn}",
          "${data.aws_s3_bucket.bucket.arn}/*"
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



# logs bucket
data "aws_s3_bucket" "bucket" {
  bucket = "efs-logs-bucky"
}


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
  source_file = "./scripts/decomp/json_decomp.py"
  output_path = "./scripts/decomp/json_decomp.zip"
}

# Lambda Function
resource "aws_lambda_function" "lambda_processor" {
  function_name    = "firehose_lambda_processor"
  filename         = data.archive_file.zip.output_path
  source_code_hash = data.archive_file.zip.output_base64sha256
  role             = aws_iam_role.lambda_iam.arn
  handler          = "json_decomp.lambda_handler"
  runtime          = "python3.8"
  timeout          = 60
}

resource "aws_glue_catalog_table" "aws_glue_catalog_table" {
  name          = "ohmyefstabs"
  database_name = "default"

  table_type = "EXTERNAL_TABLE"

  parameters = {
    EXTERNAL = "TRUE"
  }

  storage_descriptor {
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      name                  = "json"
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"

      parameters = {
        "serialization.format" = 1
      }
    }

    columns {
      name = "mount_status"
      type = "string"
    }
  }
}
