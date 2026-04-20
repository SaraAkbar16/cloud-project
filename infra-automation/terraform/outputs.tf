
output "ec2_public_ip" {
  description = "Public IP of the Ubuntu EC2 instance"
  value       = aws_instance.ubuntu_k8s_lab.public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the Ubuntu EC2 instance"
  value       = aws_instance.ubuntu_k8s_lab.public_dns
}

output "ssh_example" {
  description = "Example SSH command (replace with your local .pem path)"
  value       = "ssh -i /path/to/your-key.pem ubuntu@${aws_instance.ubuntu_k8s_lab.public_ip}"
}

output "effective_security_group_id" {
  description = "Security group attached to the EC2 instance"
  value       = var.existing_security_group_id != "" ? var.existing_security_group_id : aws_security_group.k8s_lab_sg[0].id
}
