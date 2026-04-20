# AWS EC2 + microk8s Lab (Terraform + Ansible)

This setup creates one Ubuntu EC2 instance, configures it with Docker + microk8s using Ansible, verifies Kubernetes is running, and then removes all created infrastructure with Terraform destroy.

## Folder structure

```text
infra-automation/
  terraform/
    versions.tf
    variables.tf
    main.tf
    outputs.tf
    terraform.tfvars.example
  ansible/
    inventory.ini.example
    playbook.yml
```

## Prerequisites on Windows

1. Install Terraform.
2. Install AWS CLI and run `aws configure` with your IAM credentials.
3. Ensure you already have an AWS EC2 key pair in your target region and the matching local `.pem` file.
4. Install Ansible:
   - Recommended: WSL (Ubuntu) and install Ansible there.
   - Optional: Native Ansible on Windows if your setup supports it.

## 1) Provision EC2 with Terraform

Open PowerShell in the repository root.

```powershell
cd .\infra-automation\terraform
Copy-Item .\terraform.tfvars.example .\terraform.tfvars
# Edit terraform.tfvars and set:
# - vpc_id
# - subnet_id
# - ami_id (Ubuntu AMI ID in your chosen region)
# - key_pair_name

terraform init
terraform apply -auto-approve
terraform output ec2_public_ip
```

Short explanation:
- `terraform init` downloads provider plugins.
- `terraform apply` creates a security group + EC2 in the VPC/subnet you provide.
- `terraform output ec2_public_ip` gives the host IP for SSH/Ansible.

## IAM error you just hit (UnauthorizedOperation)

If you see errors like `ec2:DescribeVpcs` or `ec2:DescribeImages` denied, your IAM user lacks EC2 read permissions.

This Terraform code now avoids those lookups by requiring manual IDs, but you still need permissions to create/delete resources.

Minimum actions usually needed for this lab:
- `ec2:RunInstances`
- `ec2:TerminateInstances`
- `ec2:CreateSecurityGroup`
- `ec2:DeleteSecurityGroup`
- `ec2:AuthorizeSecurityGroupIngress`
- `ec2:RevokeSecurityGroupIngress`
- `ec2:CreateTags`
- `ec2:DeleteTags`
- `ec2:DescribeInstances` (for Terraform refresh/output)
- `ec2:DescribeSecurityGroups` (for Terraform refresh/state)

Optional (if you want Terraform to auto-discover instead of manual IDs in a future variant):
- `ec2:DescribeVpcs`
- `ec2:DescribeSubnets`
- `ec2:DescribeImages`

If you cannot get `ec2:CreateSecurityGroup`, use an existing SG instead:
- Set `existing_security_group_id` in `terraform.tfvars` (for example `sg-0123456789abcdef0`).
- Ensure that SG already allows inbound SSH (`22`) from your IP.
- Optional: allow `16443` if you want direct microk8s API access.
- With `existing_security_group_id` set, Terraform skips creating a new security group.

## 2) Configure host with Ansible (from Windows via WSL)

Use the Terraform output public IP to fill your Ansible inventory.

Example inventory creation in WSL shell:

```bash
cd /mnt/c/Users/Sara/Desktop/hw1-phase-1-semantic-search-module-SaraAkbar16/infra-automation/ansible
cp inventory.ini.example inventory.ini
# Edit inventory.ini:
# - Replace REPLACE_WITH_TERRAFORM_PUBLIC_IP
# - Replace REPLACE_KEY.pem with your key filename in ~/.ssh/
```

Run playbook:

```bash
ansible-playbook -i inventory.ini playbook.yml
```

Short explanation:
- Playbook updates the host.
- Installs Docker.
- Installs microk8s using snap.
- Adds ubuntu user to `docker` and `microk8s` groups.
- Verifies with `microk8s status` and `microk8s kubectl get nodes`.

## 3) Verify by SSH

From PowerShell:

```powershell
ssh -i C:\path\to\your-key.pem ubuntu@<EC2_PUBLIC_IP>
```

On the EC2 host:

```bash
microk8s status --wait-ready
microk8s kubectl get nodes
```

You should see one node in `Ready` state.

## 4) Cleanup everything with Terraform destroy

From PowerShell:

```powershell
cd .\infra-automation\terraform
terraform destroy -auto-approve
```

Validate nothing remains from this lab:

```powershell
terraform state list
```

`terraform state list` should return no managed resources after destroy.

Important cleanup note:
- If the Terraform state is empty and destroy succeeded, no Terraform-managed AWS resources from this lab should remain.