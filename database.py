import boto3
import uuid  # To generate unique article_id

# Initialize DynamoDB resource with the correct region
dynamodb = boto3.resource("dynamodb", region_name="us-east-1")  
table = dynamodb.Table("AI_Articles")  

def store_in_dynamodb(title, url, published_date, content):
    """Stores scraped data in AWS DynamoDB, but only if the URL doesn't already exist."""
    try:
        # Check if the article with the same URL already exists
        response = table.query(
            IndexName="url-index",  # Assuming you have a GSI for 'url'
            KeyConditionExpression=boto3.dynamodb.conditions.Key('url').eq(url)
        )
        
        items = response.get('Items', [])
        
        if items:
            print(f"Article with URL {url} already exists. Skipping insert.")
            return  # If the article already exists, do not insert
        
        # If no article with the same URL, proceed with insertion
        table.put_item(
            Item={
                "article_id": str(uuid.uuid4()),  # Generate unique ID
                "title": title,
                "url": url,
                "published_date": published_date,
                "content": content
            }
        )
        print("Data stored successfully!")
    except Exception as e:
        print(f"Error storing data: {e}")
