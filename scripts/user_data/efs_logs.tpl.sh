  #!/bin/bash
  sudo mkdir /home/ec2-user/efs
  sudo pip3 install botocore --upgrade
  sudo yum install -y amazon-efs-utils
  sudo sed -i -e '/\[cloudwatch-log\]/{N;s/# enabled = true/enabled = true/}' /etc/amazon/efs/efs-utils.conf
  sudo sed -i "s/^log_group_name = .*/log_group_name = ${log_group_name}/g" /etc/amazon/efs/efs-utils.conf
  sudo sh -c "cd /home/ec2-user; mount -t efs -o tls ${efs_id}:/ efs" 
