import json
import os
import boto3
import urllib.request 
from decimal import Decimal
from datetime import datetime
import random 

# =========================================================================
# 1. ENVIRONMENT VARIABLES
# =========================================================================
TABLE_NAME = os.environ.get('TABLE_NAME')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN') 
GOLD_API_KEY = os.environ.get('GOLD_API_KEY') 

# AWS Clients
dynamodb = boto3.resource('dynamodb')
sns_client = boto3.client('sns')

if not TABLE_NAME:
    raise ValueError("TABLE_NAME environment variable is not set.")
    
table = dynamodb.Table(TABLE_NAME)

GOLD_API_URL = "https://api.metals.dev/v1/latest" 

# =========================================================================
# 2. ฟังก์ชันดึงราคาทองคำ (พร้อม Logic สำรอง Mocking)
# =========================================================================
def get_gold_price_from_api(product_name):
    if GOLD_API_KEY and GOLD_API_KEY.lower() != 'mock':
        try:
            currency_code = product_name.split('_')[-1].upper() 
            api_url = (
                f"{GOLD_API_URL}"
                f"?api_key={GOLD_API_KEY}"
                f"&currency={currency_code}"
                f"&metals=XAU" 
            )
            req = urllib.request.Request(
                api_url, 
                headers={'User-Agent': 'AWSLambdaFunction'}
            )
            with urllib.request.urlopen(req, timeout=10) as url:
                data = json.loads(url.read().decode())
            
            if 'metals' in data and 'XAU' in data['metals']:
                 price = data['metals']['XAU']
                 return Decimal(str(price)) 
        
        except Exception as e:
            print(f"Error fetching real gold prices: {e}. Falling back to mock data.")
    
    # Logic สำหรับข้อมูลจำลอง (Mocking)
    if product_name.upper() == 'GOLD_USD':
        current_price = 2500 + random.uniform(0, 100) # ประมาณ 2500 - 2600
    elif product_name.upper() == 'GOLD_THB':
        current_price = 60000 + random.uniform(0, 1500) # ประมาณ 60000 - 61500
    else:
        return None 
    
    return Decimal(str(round(current_price, 2))) 

# =========================================================================
# 3. Handler Function
# =========================================================================
def lambda_handler(event, context):
    print("Starting Gold Price Checker...")

    try:
        # 1. ดึง Configuration ทั้งหมดจาก DynamoDB
        response = table.scan()
        config_items = response.get('Items', [])
        
        alerts_sent = 0
        
        # 2. วนลูปตรวจสอบราคาทุก Item
        for item in config_items:
            product_name = item.get('productName')
            target_price = item.get('targetPrice', Decimal(0))
            
            # 3. ดึงราคาปัจจุบัน
            current_price = get_gold_price_from_api(product_name)

            if current_price is None:
                continue

            print(f"Checking {product_name}: Current Price = {current_price:.2f}, Target = {target_price:.2f}")

            # 4. Logic: ถ้าราคาปัจจุบันสูงกว่าหรือเท่ากับราคาเป้าหมาย
            if current_price >= target_price:
                
                subject = f"🔔 ALERT: ราคาทองคำ ({product_name}) ถึงเป้าหมาย!"
                message = (
                    f"สินค้า: {product_name}\n"
                    f"ราคาปัจจุบัน: {current_price:.2f}\n"
                    f"ราคาเป้าหมาย: {target_price:.2f}"
                )
                
                # 5. ส่งแจ้งเตือนผ่าน SNS
                if SNS_TOPIC_ARN:
                    sns_client.publish(
                        TopicArn=SNS_TOPIC_ARN,
                        Message=message,
                        Subject=subject
                    )
                    alerts_sent += 1
                
            # 6. อัปเดต lastCheckPrice
            table.update_item(
                Key={'productName': product_name},
                UpdateExpression="SET lastCheckPrice = :p, lastCheckTime = :t",
                ExpressionAttributeValues={
                    ':p': current_price,
                    ':t': datetime.now().isoformat()
                }
            )

        # 7. คืนค่าสถานะ
        return {
            'statusCode': 200,
            'body': json.dumps({'message': f'Gold price check completed. Alerts sent: {alerts_sent}'})
        }

    except Exception as e:
        print(f"Handler Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
