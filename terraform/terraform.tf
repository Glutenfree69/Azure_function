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

provider "azurerm" {
  features {}
  subscription_id = "249471bf-b8ae-4c8a-abf4-f9e67509e192"
}