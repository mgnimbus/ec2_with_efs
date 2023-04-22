# resource "aws_s3_bucket" "foo" {
#   bucket        = "efs-test-trail-events"
#   force_destroy = true
# }

# data "aws_iam_policy_document" "foo" {
#   statement {
#     sid    = "AWSCloudTrailAclCheck"
#     effect = "Allow"

#     principals {
#       type        = "Service"
#       identifiers = ["cloudtrail.amazonaws.com"]
#     }

#     actions   = ["s3:GetBucketAcl"]
#     resources = [aws_s3_bucket.foo.arn]
#   }

#   statement {
#     sid    = "AWSCloudTrailWrite"
#     effect = "Allow"

#     principals {
#       type        = "Service"
#       identifiers = ["cloudtrail.amazonaws.com"]
#     }

#     actions   = ["s3:PutObject"]
#     resources = ["${aws_s3_bucket.foo.arn}/prefix/AWSLogs/${data.aws_caller_identity.current.account_id}/*"]

#     condition {
#       test     = "StringEquals"
#       variable = "s3:x-amz-acl"
#       values   = ["bucket-owner-full-control"]
#     }
#   }
# }
# resource "aws_s3_bucket_policy" "foo" {
#   bucket = aws_s3_bucket.foo.id
#   policy = data.aws_iam_policy_document.foo.json
# }

# data "aws_caller_identity" "current" {}

# resource "aws_cloudtrail" "foobar" {
#   name                          = "tf-trail-foobar"
#   s3_bucket_name                = aws_s3_bucket.foo.id
#   s3_key_prefix                 = "prefix"
#   include_global_service_events = false
#   cloud_watch_logs_group_arn    = "${aws_cloudwatch_log_group.example.arn}:*" # CloudTrail requires the Log Stream wildcard
#   #   event_selector {
#   #     read_write_type           = "All"
#   #     include_management_events = true

#   #     data_resource {
#   #       type   = "AwsApiCall"
#   #       values = ["arn:aws:elasticfilesystem"]
#   #     }
#   #   }
# }

# resource "aws_cloudwatch_log_group" "example" {
#   name = "efs-events-watcher"
# }
