data "aws_cloudformation_stack" "vpc" {
  name = "duncman-common-core-vpc"
}
data "aws_cloudformation_stack" "security" {
  name = "duncman-common-core-securitygroups"
}
resource "aws_security_group" "TF-LB-SG" {
  name        = "allow_http_any_to_lb_${terraform.workspace}"
  description = "Allow HTTP Any to LB"
  vpc_id      = data.aws_cloudformation_stack.vpc.outputs.VPC

  ingress {
    description      = "HTTP from Any"
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "allow_http_any_to_lb"
  }
}

resource "aws_security_group" "TF-Server-SG" {
  name        = "allow_http_lb_to_servers_${terraform.workspace}"
  description = "Allow HTTP LB to Servers"
  vpc_id      = data.aws_cloudformation_stack.vpc.outputs.VPC

  ingress {
    description     = "HTTP from LB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.TF-LB-SG.id]
  }
  ingress {
    description = "SSH from Home IP"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["70.94.153.20/32"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name = "allow_http_lb_to_servers"
  }
}

#EC2 Instance Profile
resource "aws_iam_instance_profile" "EC2_Profile" {
  name = "${terraform.workspace}-EC2-Instance-Profile"
  role = aws_iam_role.ec2role.name
}

#EC2 IAM Role
resource "aws_iam_role" "ec2role" {
  name = "${terraform.workspace}-EC2-Instance-Role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}


#IAM Policies
resource "aws_iam_policy" "s3getputdelete" {
  name = "img-mgr-policy-${terraform.workspace}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.imgmgrs3bucket.arn}"
        ]
      },
      {
        Action = [
          "s3:DescribeTags"
        ],
        Effect = "Allow",
        Resource = [
          "*"
        ]
      },
      {
        Action = [
          "s3:ListBucket"
        ],
        Effect = "Allow",
        Resource = [
          "${aws_s3_bucket.imgmgrs3bucket.arn}"
        ]
      }
    ]
  })
}

#Policy Attachments
resource "aws_iam_role_policy_attachment" "s3getputdelete" {
  role       = aws_iam_role.ec2role.name
  policy_arn = aws_iam_policy.s3getputdelete.arn
}
resource "aws_iam_role_policy_attachment" "awsec2ssmpolicy" {
  role       = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforSSM"
}

#S3 Bucket
resource "aws_s3_bucket" "imgmgrs3bucket" {
  acl = "private"
}

#Launch Configuration
resource "aws_launch_configuration" "imgmgrlaunchconfig" {
  name_prefix          = "${terraform.workspace}-img-mgr"
  image_id             = var.ImageId
  key_name             = var.ssh_key
  instance_type        = "t2.micro"
  iam_instance_profile = aws_iam_instance_profile.EC2_Profile.id
  security_groups      = [aws_security_group.TF-Server-SG.id, data.aws_cloudformation_stack.security.outputs.AllSecurityGroup]
  user_data            = <<E0F
#!/bin/sh
yum install -y git jq
amazon-linux-extras install -y nginx1
pip3 install pipenv

cd ~ec2-user/
cat > ~/.ssh/config << EOF
Host *
    StrictHostKeyChecking no
EOF
chmod 600 ~/.ssh/config
git clone https://github.com/dianephan/flask-aws-storage.git
cd flask-aws-storage
mkdir uploads
chown -R ec2-user:ec2-user .
cat > run.sh << EOF
#!/bin/sh
pipenv install
pipenv run pip3 install -r requirements.txt
REGION=\$(curl http://169.254.169.254/latest/meta-data/placement/region)
IID=\$(curl http://169.254.169.254/latest/meta-data/instance-id)
ENV=\$(aws --region \$REGION ec2 describe-tags --filters Name=resource-id,Values=\$IID | jq -r '.Tags[]|select(.Key == "environment")|.Value')
FLASK_ENV=\$ENV pipenv run flask run
EOF
chmod 755 run.sh

cat > /etc/systemd/system/imgmgr.service << EOF
[Unit]
Description=Image manager app
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/flask-aws-storage
ExecStart=/home/ec2-user/flask-aws-storage/run.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sed -i s/lats-image-data/${aws_s3_bucket.imgmgrs3bucket.id}/ app.py
systemctl daemon-reload
systemctl start imgmgr

cat > /etc/nginx/conf.d/myapp.conf << EOF
server {
   listen 80;
   server_name localhost;
   location / {
        proxy_set_header Host \$http_host;
        proxy_pass http://127.0.0.1:5000;
    }
}
EOF
systemctl restart nginx.service
E0F
}
# building ELb
resource "aws_elb" "img-mgr-tf-lb" {
  name    = "img-mgr-tf-lb-${terraform.workspace}"
  subnets = ["${data.aws_cloudformation_stack.vpc.outputs.PubSubnet1}", "${data.aws_cloudformation_stack.vpc.outputs.PubSubnet2}"]
  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  health_check {
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    target              = "HTTP:80/"
    interval            = 10
  }

  security_groups             = [aws_security_group.TF-LB-SG.id]
  cross_zone_load_balancing   = true
  idle_timeout                = 400
  connection_draining         = true
  connection_draining_timeout = 400

  tags = {
    Name = "img-mgr-tf-lb"
  }
}
# ASG
resource "aws_autoscaling_group" "img-mgr-tf-ASG" {
  name                      = "img-mgr-tf-ASG-${terraform.workspace}"
  max_size                  = 1
  min_size                  = 1
  health_check_grace_period = 300
  health_check_type         = "ELB"
  launch_configuration      = aws_launch_configuration.imgmgrlaunchconfig.name
  load_balancers            = [aws_elb.img-mgr-tf-lb.id]
  vpc_zone_identifier       = [data.aws_cloudformation_stack.vpc.outputs.PriSubnet1, data.aws_cloudformation_stack.vpc.outputs.PriSubnet2]

  tag {
    key                 = "Name"
    value               = "Web-${terraform.workspace}"
    propagate_at_launch = true
  }
}
