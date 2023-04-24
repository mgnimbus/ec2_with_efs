# Creating EFS file system
resource "aws_efs_file_system" "efs" {
  creation_token = "my-efs-test"
  tags = {
    Name = "MyProduct"
  }
}

# Creating Mount target of EFS
resource "aws_efs_mount_target" "mount" {
  file_system_id  = aws_efs_file_system.efs.id
  subnet_id       = "subnet-0e4c190e74b5852b0"
  security_groups = [aws_security_group.allow_efs.id]
}

output "file_system_id" {
  value = aws_efs_file_system.efs.id
}

resource "aws_cloudwatch_log_group" "efs" {
  name = "efs_mount_logs"
}
