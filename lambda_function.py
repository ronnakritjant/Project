# handler.py สำหรับ StudentAPI Lambda
import json
import os
import boto3
from decimal import Decimal
from datetime import datetime

# Class สำหรับจัดการการแปลง Decimal ให้เป็น String ก่อนทำ JSON Serialize
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)

# เชื่อมต่อกับ DynamoDB
dynamodb = boto3.resource('dynamodb')
# อ่านชื่อตารางจาก Environment Variable
TABLE_NAME = os.environ.get('TABLE_NAME')
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    # กำหนด CORS Header เพื่อให้ Frontend (Amplify) สามารถเรียกใช้ API ได้
    headers = {
        "Access-Control-Allow-Origin": "https://staging.d3k3ygxgvu5ype.amplifyapp.com",
        "Access-Control-Allow-Headers": "Content-Type",
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
        "Access-Control-Allow-Credentials": "true"
    }

    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    
    # อ่าน path
    path = event.get('path', '')

    # Preflight OPTIONS
    if http_method == 'OPTIONS':
        return {'statusCode': 200, 'headers': headers, 'body': ''}

    # รองรับเฉพาะ /V1/students
    if path != '/V1/students':
        return {'statusCode': 404, 'headers': headers, 'body': json.dumps({"error": "Not Found"})}

    # GET
    if http_method == 'GET':
        response = table.scan()
        items = response['Items']
        return {'statusCode': 200, 'headers': headers, 'body': json.dumps(items, cls=DecimalEncoder)}

    # POST
    if http_method == 'POST':
        if 'body' not in event:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "Missing request body"})}
        body = json.loads(event['body'])
        student_id = body.get('student_id')
        name = body.get('name')
        major = body.get('major')
        if not student_id or not name or not major:
            return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "Missing required fields (student_id, name, major)"})}
        table.put_item(Item={'student_id': student_id, 'name': name, 'major': major, 'timestamp': datetime.now().isoformat()})
        return {'statusCode': 201, 'headers': headers, 'body': json.dumps({"message": f"Student {student_id} added successfully"})}

    # Method อื่นๆ
    return {'statusCode': 405, 'headers': headers, 'body': json.dumps({"error": "Method not allowed"})}
    
    # try:
    #     http_method = event.get('httpMethod')
        
    #     # 1. GET Method: ดึงรายการข้อมูลทั้งหมด
    #     if http_method == 'GET':
    #         # ใช้ Scan เพื่อดึงข้อมูลทั้งหมดในตาราง
    #         response = table.scan()
    #         items = response['Items']
    #         # ส่งข้อมูลกลับไปในรูปแบบ JSON
    #         return {'statusCode': 200, 'headers': headers, 'body': json.dumps(items, cls=DecimalEncoder)}

    #     # 2. POST Method: เพิ่มข้อมูลใหม่
    #     elif http_method == 'POST':
    #         if 'body' not in event:
    #             return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "Missing request body"})}

    #         body = json.loads(event['body'])
    #         student_id = body.get('student_id')
    #         name = body.get('name')
    #         major = body.get('major')
            
    #         # ตรวจสอบค่าที่จำเป็น
    #         if not student_id or not name or not major:
    #             return {'statusCode': 400, 'headers': headers, 'body': json.dumps({"error": "Missing required fields (student_id, name, major)"})}

    #         # บันทึกข้อมูลลง DynamoDB
    #         table.put_item(
    #             Item={'student_id': student_id, 'name': name, 'major': major, 'timestamp': datetime.now().isoformat()}
    #         )
    #         return {'statusCode': 201, 'headers': headers, 'body': json.dumps({"message": f"Student {student_id} added successfully"})}
        
    #     # 3. OPTIONS Method: สำหรับการตรวจสอบ CORS ก่อนส่งข้อมูลจริง
    #     elif http_method == 'OPTIONS':
    #         return {'statusCode': 200, 'headers': headers, 'body': ''}

    #     # Method อื่นๆ ที่ไม่ได้อนุญาต
    #     return {'statusCode': 405, 'headers': headers, 'body': json.dumps({"error": "Method not allowed"})}

    # except Exception as e:
    #     print(f"Error: {e}")
    #     return {'statusCode': 500, 'headers': headers, 'body': json.dumps({"error": str(e), "message": "Internal Server Error"})}
