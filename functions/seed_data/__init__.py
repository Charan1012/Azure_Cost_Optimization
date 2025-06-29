import azure.functions as func
import os
from azure.cosmos import CosmosClient
from datetime import datetime, timedelta
import uuid

def main(req: func.HttpRequest) -> func.HttpResponse:
    # Get Cosmos DB config
    endpoint = os.environ["CosmosDB_Endpoint"]
    key = os.environ["CosmosDB_Key"]
    database_name = os.environ["COSMOS_DATABASE"]
    container_name = os.environ["COSMOS_CONTAINER"]
    
    # Initialize client
    client = CosmosClient(endpoint, key)
    container = client.get_database_client(database_name).get_container_client(container_name)
    
    # Generate test data
    records = []
    for i in range(10):
        record = {
            "id": str(uuid.uuid4()),
            "data": f"Sample record {i}",
            "lastAccessed": (datetime.utcnow() - timedelta(days=200 if i < 5 else 30)).isoformat(),
            "partitionKey": "seed-data"
        }
        container.upsert_item(record)
        records.append(record['id'])
    
    return func.HttpResponse(f"Seeded {len(records)} records: {records}", status_code=200)