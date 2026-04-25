import boto3, json
from decimal import Decimal
from urllib.parse import unquote

# DynamoDB 테이블 연결
db = boto3.resource('dynamodb').Table('ImageMetadata')

def lambda_handler(event, context):
    # API Gateway 경로 변수에서 id 추출 (URL 인코딩 해제 포함)
    image_id = unquote(event['pathParameters']['id'])
    item = db.get_item(Key={'image_id': image_id}).get('Item')

    # 예외 처리 (데이터가 없을 때)
    if not item:
        return {
            'statusCode': 404,
            'body': json.dumps({'error': 'not found'})
        }

    # DynamoDB 전용 타입인 Decimal을 float으로 변환
    def conv(o):
        if isinstance(o, Decimal): return float(o)
        if isinstance(o, list): return [conv(i) for i in o]
        if isinstance(o, dict): return {k: conv(v) for k, v in o.items()}
        return o

    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps(conv(item), ensure_ascii=False, indent=2)
    }