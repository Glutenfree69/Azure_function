terraform {
  required_version = ">= 1.7.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }

  backend "s3" {
    bucket = "state-yace"
    key    = "azure/azure_function/terraform.tfstate"
    region = "eu-west-3"
  }
}