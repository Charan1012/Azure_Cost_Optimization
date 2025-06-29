import logging
import os
import azure.functions as func
from datetime import datetime, timedelta, timezone
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import json

def main(mytimer: func.TimerRequest) -> None:
    # Get configuration
    endpoint = os.environ["CosmosDB_Endpoint"]
    key = os.environ["CosmosDB_Key"]
    conn_str = os.environ["BlobStorage_ConnStr"]
    container_name = os.environ["ARCHIVE_CONTAINER"]
    database_name = os.environ["COSMOS_DATABASE"]
    container_hot = os.environ["COSMOS_CONTAINER"]
    
    # Initialize clients
    cosmos_client = CosmosClient(endpoint, key)
    blob_client = BlobServiceClient.from_connection_string(conn_str)
    container_client = blob_client.get_container_client(container_name)
    
    # Get database and container
    database = cosmos_client.get_database_client(database_name)
    container = database.get_container_client(container_hot)
    
    # Calculate cutoff time (180 days ago)
    cutoff = datetime.now(timezone.utc) - timedelta(days=180)
    
    # Query old records
    query = "SELECT * FROM c WHERE c.lastAccessed < @cutoff"
    params = [{"name": "@cutoff", "value": cutoff.isoformat()}]
    items = container.query_items(
        query=query,
        parameters=params,
        enable_cross_partition_query=True
    )
    
    # Archive each record
    for item in items:
        try:
            # Generate unique blob name
            blob_name = f"{item['id']}.json"
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload to blob storage
            blob_client.upload_blob(json.dumps(item), overwrite=True)
            
            # Delete from Cosmos DB
            container.delete_item(item['id'], partition_key=item['id'])
            
            logging.info(f"Archived record {item['id']}")
        except Exception as e:
            logging.error(f"Failed to archive {item['id']}: {str(e)}")