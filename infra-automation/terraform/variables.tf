variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC ID where resources will be created (provide manually from AWS console)"
  type        = string
}

variable "subnet_id" {
  description = "Subnet ID for the EC2 instance (provide manually from AWS console)"
  type        = string
}

variable "ami_id" {
  description = "Ubuntu AMI ID for the selected region (provide manually from AWS console)"
  type        = string
}

variable "existing_security_group_id" {
  description = "Optional existing security group ID to reuse (set to bypass SG creation permission requirements)"
  type        = string
  default     = ""
}

variable "key_pair_name" {
  description = "Existing AWS EC2 key pair name (not the .pem file path)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for the lab host"
  type        = string
  default     = "t3.medium"
}

variable "ssh_ingress_cidr" {
  description = "CIDR allowed to SSH to the instance"
  type        = string
  default     = "0.0.0.0/0"
}

variable "k8s_api_ingress_cidr" {
  description = "CIDR allowed to access microk8s API server (16443)"
  type        = string
  default     = "0.0.0.0/0"
}
