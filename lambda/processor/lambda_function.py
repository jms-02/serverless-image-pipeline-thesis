import boto3
import time
import os
import io
import json
from datetime import datetime
from decimal import Decimal
from image_processor import process_image 
from rekognition_analyzer import analyze_image

# AWS 연결, 환경 변수 설정
s3 = boto3.client('s3')
db = boto3.resource('dynamodb').Table('ImageMetadata')
sns = boto3.client('sns')

RESULT_BUCKET = 'thesis-images-result-2026'
SNS_TOPIC_ARN = 'arn:aws:sns:ap-northeast-2:238479992071:thesis-notify'

# JSON 변환 클래스
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj): # JSON으로 변환할 수 없는 객체가 들어오면 호출
        if isinstance(obj, Decimal): # 만약 객체가 Decimal 타입이면 float로 변환해서 반환
            return float(obj)
        return super().default(obj) # Decimal이 아니면 기본 JSON 처리

# 알림 발송 함수
def publish_sns(subject, message: dict):
    sns.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=subject,
        Message=json.dumps(message, ensure_ascii=False, indent=2, cls=DecimalEncoder) # dictionary를 JSON 문자열로 변환
    )

# 메인 Lambda 핸들러 함수
def lambda_handler(event, context):
    total_start = time.time() # 전체 작업 소요 시간을 측정
    
    # 업로드된 원본 이미지의 버킷 이름(bucket), 파일 경로와 이름(key), 파일 용량(size) 추출
    record = event['Records'][0]
    bucket = record['s3']['bucket']['name']
    key    = record['s3']['object']['key']
    size   = record['s3']['object']['size']

    # 메인 로직
    try:
        # 1. 원본 이미지 읽기
        response = s3.get_object(Bucket=bucket, Key=key)
        body = response['Body'].read()

        # 2. image_processor.py에 있는 함수 실행 (Pillow 처리)
        result = process_image(body)

        # 3. S3에 리사이징 결과 저장
        result_key = key.replace('uploads/', 'results/')
        s3.put_object(Bucket=RESULT_BUCKET, Key=result_key, Body=result['resized'], ContentType='image/jpeg')
        
        # 4. S3에 썸네일 결과 저장
        thumb_key = key.replace('uploads/', 'thumbs/')
        s3.put_object(Bucket=RESULT_BUCKET, Key=thumb_key, Body=result['thumbnail'], ContentType='image/jpeg')
        
        # Rekognition 분석
        #rekog_result = analyze_image(bucket, key)
        # lambda_handler 안의 Rekognition 호출 부분을 아래처럼 변경
        rekog_enabled = os.environ.get('REKOGNITION_ENABLED', 'true').lower() == 'true'

        if rekog_enabled:
            rekog_result = analyze_image(bucket, key)
        else:
            # OFF일 때는 빈 결과로 대체
            rekog_result = {'labels': [], 'rekognition_time_ms': 0}

        # 전체 소요 시간 계산 (ms 단위)
        total_ms = int((time.time() - total_start) * 1000)
        
        # 5. DynamoDB에 모든 실험 데이터 기록
        db.put_item(Item={
            'image_id': key,
            'original_key': f"{bucket}/{key}",
            'result_key': f"{RESULT_BUCKET}/{result_key}",
            'file_size_kb': Decimal(str(size // 1024)),
            'orig_width': Decimal(str(result['orig_width'])),
            'orig_height': Decimal(str(result['orig_height'])),

            'processing_time_ms': Decimal(str(result['pillow_ms'])),
            'rekognition_time_ms': Decimal(str(rekog_result['rekognition_time_ms'])),
            'total_time_ms': Decimal(str(total_ms)),

            'labels': rekog_result['labels'], # AI가 찾아낸 사물들
            'status': 'success',
            'created_at': datetime.utcnow().isoformat()
        })
        # SNS 알림
        publish_sns(
            subject='[성공] 이미지 처리 완료',
            message={
                'status': 'success',
                'image_key': key,
                'total_ms': total_ms,
                'labels': rekog_result['labels'],
                'timestamp': datetime.utcnow().isoformat()
            }
        )

    except Exception as e:
        # 에러 발생 시에도 DB에 기록
        db.put_item(Item={
            'image_id': key, 
            'status': 'error',
            'error_message': str(e),
            'created_at': datetime.utcnow().isoformat()
        })
        raise e