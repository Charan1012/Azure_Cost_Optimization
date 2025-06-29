import logging
import os
import azure.functions as func
from azure.cosmos import CosmosClient
from azure.storage.blob import BlobServiceClient
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Get configuration
    endpoint = os.environ["CosmosDB_Endpoint"]
    key = os.environ["CosmosDB_Key"]
    conn_str = os.environ["BlobStorage_ConnStr"]
    container_name = os.environ["ARCHIVE_CONTAINER"]
    database_name = os.environ["COSMOS_DATABASE"]
    container_hot = os.environ["COSMOS_CONTAINER"]
    
    # Get record ID from request
    record_id = req.params.get('id')
    if not record_id:
        return func.HttpResponse("Missing record ID", status_code=400)
    
    # Initialize clients
    cosmos_client = CosmosClient(endpoint, key)
    blob_client = BlobServiceClient.from_connection_string(conn_str)
    container_blob = blob_client.get_container_client(container_name)
    
    # Check hot data in Cosmos DB
    try:
        database = cosmos_client.get_database_client(database_name)
        container = database.get_container_client(container_hot)
        record = container.read_item(record_id, partition_key=record_id)
        return func.HttpResponse(
            json.dumps(record),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"Failed to read hot data: {e}")

    # Check archive in Blob Storage
    try:
        blob_name = f"{record_id}.json"
        blob_client = container_blob.get_blob_client(blob_name)
        data = blob_client.download_blob().readall()
        return func.HttpResponse(
            data,
            mimetype="application/json",
            headers={"X-Data-Source": "archive"}
        )
    except:
        return func.HttpResponse(
            "Record not found",
            status_code=404
        )