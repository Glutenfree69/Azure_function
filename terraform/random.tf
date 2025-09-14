# Create a random pet to generate a unique resource group name
resource "random_pet" "rg_name" {
  prefix = "rg"
}

# Random String for unique naming of resources
resource "random_string" "name" {
  length  = 8
  special = false
  upper   = false
  lower   = true
  numeric = false
}