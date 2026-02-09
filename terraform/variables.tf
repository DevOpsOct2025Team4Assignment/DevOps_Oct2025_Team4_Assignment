variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "file-manager"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "flask_secret_key" {
  type      = string
  sensitive = true
}

variable "ssh_public_key" {
  type = string
}
