provider "aws" {
  region = var.aws_region
}

locals {
  use_existing_security_group = trimspace(var.existing_security_group_id) != ""
}

resource "aws_security_group" "k8s_lab_sg" {
  count       = local.use_existing_security_group ? 0 : 1
  name        = "k8s-lab-sg"
  description = "Security group for SSH and microk8s API"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_ingress_cidr]
  }

  ingress {
    description = "microk8s API server"
    from_port   = 16443
    to_port     = 16443
    protocol    = "tcp"
    cidr_blocks = [var.k8s_api_ingress_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "k8s-lab-sg"
  }
}

resource "aws_instance" "ubuntu_k8s_lab" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  key_name                    = var.key_pair_name
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = local.use_existing_security_group ? [var.existing_security_group_id] : [aws_security_group.k8s_lab_sg[0].id]
  associate_public_ip_address = true

  root_block_device {
    volume_size = 16
    volume_type = "gp3"
  }

  tags = {
    Name = "ubuntu-k8s-lab"
  }
}
