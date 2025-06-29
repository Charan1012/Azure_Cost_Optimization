# Azure Data Archival & Compliance Solution
terraform {
  #   required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.80"
    }
  }
}

provider "azurerm" {
  features {
    resource_group {
      prevent_deletion_if_contains_resources = true
    }
  }
}

###########################
# VARIABLES
###########################

variable "project_name" {
  type        = string
  description = "Project name for naming resources"
  default     = "cosmos-archival"
}

variable "location" {
  type        = string
  description = "Azure region"
  default     = "canadacentral"
}

###########################
# RESOURCE GROUP
###########################

resource "azurerm_resource_group" "main" {
  name     = "${var.project_name}-rg"
  location = var.location
}

###########################
# COSMOS DB ACCOUNT
###########################

resource "azurerm_cosmosdb_account" "db" {
  name                = "${var.project_name}-db"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level = "Session"
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }
  timeouts {
    create = "30m"
    update = "30m"
  }
}

###########################
# COSMOS DB SQL CONTAINER
###########################

resource "azurerm_cosmosdb_sql_database" "maindb" {
  name                = "maindb"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.db.name
}

resource "azurerm_cosmosdb_sql_container" "hot_data" {
  name                = "hotdata"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.db.name
  database_name       = azurerm_cosmosdb_sql_database.maindb.name
  partition_key_paths = ["/id"]
}

###########################
# BLOB STORAGE (COOL TIER)
###########################

resource "azurerm_storage_account" "archive" {
  name                     = "${replace(var.project_name, "-", "")}archive"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  access_tier              = "Cool"
}

resource "azurerm_storage_container" "archive" {
  name                 = "archived-data"
  storage_account_name = azurerm_storage_account.archive.name
}

###########################
# FUNCTION APP STORAGE ACCOUNT
###########################

resource "azurerm_storage_account" "functions" {
  name                     = "${replace(var.project_name, "-", "")}funcsa"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
}

###########################
# SERVICE PLAN FOR FUNCTIONS
###########################

resource "azurerm_service_plan" "main" {
  name                = "${var.project_name}-plan"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku_name            = "Y1"
  os_type             = "Linux"
}

###########################
# LINUX FUNCTION APP
###########################

resource "azurerm_linux_function_app" "main" {
  name                = "${var.project_name}-funcapp"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  depends_on = [
    azurerm_cosmosdb_sql_database.maindb,
    azurerm_cosmosdb_sql_container.hot_data
  ]

  storage_account_name       = azurerm_storage_account.functions.name
  storage_account_access_key = azurerm_storage_account.functions.primary_access_key

  site_config {
    application_stack {
      python_version = "3.12"
    }
  }

  app_settings = {
    "CosmosDB_Endpoint"   = azurerm_cosmosdb_account.db.endpoint
    "CosmosDB_Key"        = azurerm_cosmosdb_account.db.primary_key
    "BlobStorage_ConnStr" = azurerm_storage_account.archive.primary_connection_string
    "ARCHIVE_CONTAINER"   = azurerm_storage_container.archive.name
    "COSMOS_DATABASE"     = azurerm_cosmosdb_sql_database.maindb.name
    "COSMOS_CONTAINER"    = azurerm_cosmosdb_sql_container.hot_data.name
  }
}
