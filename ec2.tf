# resource "aws_instance" "example" {
#   ami               = "ami-069aabeee6f53e7bf"
#   instance_type     = "t2.micro"
#   availability_zone = "us-east-1a"
#   key_name          = "tfkey"
#   user_data         = file("${path.module}/user_data.sh")
#   #   user_data            = <<EOF
#   #     #!/bin/bash
#   #     sudo yum update -y
#   #     sudo yum install -y awslogs
#   #     sudo systemctl start awslogsd
#   #     sudo systemctl enable awslogsd.service
#   #     EOF
#   security_groups      = [aws_security_group.allow_efs.name]
#   iam_instance_profile = aws_iam_instance_profile.ec2-iam-profile.name
#   tags = {
#     Name = "mgm-efs-logs"
#   }
#   depends_on = [
#     aws_efs_mount_target.mount
#   ]
# }

resource "aws_instance" "efs" {
  ami               = "ami-069aabeee6f53e7bf"
  instance_type     = "t2.micro"
  availability_zone = "us-east-1a"
  key_name          = "tfkey"
  user_data = templatefile("${path.module}/scripts/efs_logs.tpl.sh", {
    log_group_name = "${aws_cloudwatch_log_group.efs.name}"
    efs_id         = "${aws_efs_file_system.efs.id}"
  })
  security_groups      = [aws_security_group.allow_efs.name]
  iam_instance_profile = aws_iam_instance_profile.ec2-iam-profile.name
  tags = {
    Name = "mgm-efs2-logs"
  }
}

resource "aws_security_group" "allow_efs" {
  name        = "allow_EFS"
  description = "Allow EFS inbound traffic"
  vpc_id      = "vpc-0aa0cdbe4c44c04a3"

  ingress {
    description = "NFS from VPC"
    from_port   = 2049
    to_port     = 2049
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_nfs"
  }
}

# aws cloudwatch get-metric-statistics --metric-name StorageBytes --start-time 2023-04-19T22:32:51 --end-time 2023-04-19T22:40:59 --period 900 --statistics Sum --namespace AWS/EFS --dimensions Name=FileSystemId,Value=fs-070268fe0f240916f Name=StorageClass,Value=Total
