# Backend setup
terraform {
  backend "s3" {
    key = "img-mgr.tfstate"
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 2.0"
    }
  }
}

# Provider and access setup
provider "aws" {
  region = var.region
}
