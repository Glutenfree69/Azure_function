terraform {
  required_version = ">=1.7"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.0"
    }
  }

  backend "s3" {
    bucket = "state-yace"
    key    = "azure/azure_function/terraform.tfstate"
    region = "eu-west-3"
  }
}