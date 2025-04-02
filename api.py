import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import boto3
from uuid import uuid4
from botocore.exceptions import ClientError
from mangum import Mangum

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI"}

handler = Mangum(app)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('AI_Articles')  # Your DynamoDB table name

# Pydantic models for request validation
class Article(BaseModel):
    title: str
    url: str
    published_date: str
    content: str

# Create a new article (Create)
@app.post("/articles/")
async def create_article(article: Article):
    # Check if an article with the same URL already exists
    response = table.query(
        IndexName="url-index",
        KeyConditionExpression=boto3.dynamodb.conditions.Key('url').eq(article.url)
    )
    
    items = response.get('Items', [])
    
    if items:
        raise HTTPException(status_code=400, detail="Article with this URL already exists.")

    # Proceed with article creation if no duplicate found
    article_id = str(uuid4())  # Generate a unique article ID

    try:
        table.put_item(
            Item={
                'article_id': article_id,
                'title': article.title,
                'url': article.url,
                'published_date': article.published_date,
                'content': article.content
            }
        )
        return {"article_id": article_id}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {e.response['Error']['Message']}")


# Read an article by article_id (Read)
@app.get("/articles/{article_id}")
async def read_article(article_id: str):
    try:
        response = table.get_item(Key={'article_id': article_id})
        item = response.get('Item')

        if not item:
            raise HTTPException(status_code=404, detail="Article not found")

        return item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve article: {e.response['Error']['Message']}")

# Modified to log and print error messages
@app.get("/articles/")
async def get_article_by_url(url: str):
    try:
        # Assuming 'url' is a secondary index (GSI) in DynamoDB
        response = table.query(
            IndexName="url-index",  # Name of the index for URL (you need to create it in DynamoDB)
            KeyConditionExpression=boto3.dynamodb.conditions.Key('url').eq(url)
        )

        items = response.get('Items', [])
        if not items:
            raise HTTPException(status_code=404, detail="Article not found")

        return items[0]  # Assuming the article with the given URL is unique
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error fetching article: {e.response['Error']['Message']}")

# Update an article (Update)
@app.put("/articles/{article_id}")
async def update_article(article_id: str, article: Article):
    try:
        response = table.update_item(
            Key={'article_id': article_id},
            UpdateExpression="SET title = :title, url = :url, published_date = :published_date, content = :content",
            ExpressionAttributeValues={
                ':title': article.title,
                ':url': article.url,
                ':published_date': article.published_date,
                ':content': article.content
            },
            ReturnValues="UPDATED_NEW"
        )

        updated_item = response.get('Attributes')
        if not updated_item:
            raise HTTPException(status_code=404, detail="Article not found")

        return updated_item
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to update article: {e.response['Error']['Message']}")

# Delete an article (Delete)
@app.delete("/articles/{article_id}")
async def delete_article(article_id: str):
    try:
        response = table.delete_item(Key={'article_id': article_id})
        if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
            return {"message": "Article deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Article not found")
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete article: {e.response['Error']['Message']}")
