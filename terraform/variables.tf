variable "resource_group_name" {
  type        = string
  description = "The name of the Azure resource group. If blank, a random name will be generated."
}

variable "resource_group_location" {
  type        = string
  description = "Location of the resource group."
}

variable "sa_account_tier" {
  description = "The tier of the storage account. Possible values are Standard and Premium."
  type        = string
}

variable "sa_account_replication_type" {
  description = "The replication type of the storage account. Possible values are LRS, GRS, RAGRS, and ZRS."
  type        = string
}

variable "sa_name" {
  description = "The name of the storage account. If blank, a random name will be generated."
  type        = string
}

variable "ws_name" {
  description = "The name of the Log Analytics workspace. If blank, a random name will be generated."
  type        = string
}

variable "ai_name" {
  description = "The name of the Application Insights instance. If blank, a random name will be generated."
  type        = string
}

variable "asp_name" {
  description = "The name of the App Service Plan. If blank, a random name will be generated."
  type        = string
}

variable "fa_name" {
  description = "The name of the Function App. If blank, a random name will be generated."
  type        = string
}

variable "runtime_name" {
  description = "The name of the language worker runtime."
  type        = string
}

variable "runtime_version" {
  description = "The version of the language worker runtime."
  type        = string
}

# Variables pour le service principal GitHub (créé manuellement)
variable "github_actions_object_id" {
  description = "Object ID of the manually created GitHub Actions service principal"
  type        = string
}

variable "cosmos_account_name" {
  description = "Name of the Cosmos DB account (if null, will be generated)"
  type        = string
}