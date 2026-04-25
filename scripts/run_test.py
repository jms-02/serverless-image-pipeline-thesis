import boto3
import time
from decimal import Decimal

BUCKET_NAME = 'thesis-images-original-2026'
TABLE_NAME  = 'ImageMetadata'
TEST_IMAGE  = 'test.jpg'
S3_KEY      = 'uploads/test.jpg'

s3 = boto3.client('s3')
db = boto3.resource('dynamodb').Table(TABLE_NAME)

def convert_decimals(obj):
    """DynamoDB Decimal → int/float 재귀 변환"""
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def wait_until_done(image_id, timeout=60):
    deadline = time.time() + timeout
    attempt  = 0
    while time.time() < deadline:
        attempt += 1
        resp = db.get_item(Key={'image_id': image_id})
        item = resp.get('Item')
        if item and item.get('status') in ('success', 'error'):
            print(f"  → {attempt}번 시도 만에 완료 감지")
            return convert_decimals(item)  # 변환
        print(f"  → [{attempt}] 아직 처리 중... 재시도")
        time.sleep(2)
    return None

def run_test():
    db.delete_item(Key={'image_id': S3_KEY})

    print(f"[1/3] 이미지 업로드 중: {TEST_IMAGE}...")
    with open(TEST_IMAGE, 'rb') as f:
        s3.put_object(Bucket=BUCKET_NAME, Key=S3_KEY, Body=f)

    print("[2/3] AWS에서 처리 중... (최대 60초 대기)")
    item = wait_until_done(S3_KEY, timeout=60)

    print("[3/3] 결과 확인")
    print("-" * 40)

    if not item:
        print("시간 초과: 60초 내에 처리가 완료되지 않았습니다.")
        return

    if item.get('status') == 'error':
        print(f"처리 실패: {item.get('error_message')}")
        return

    print(f"처리 성공!")
    print(f"파일 크기:         {item.get('file_size_kb')} KB")
    print(f"원본 해상도:       {item.get('orig_width')} x {item.get('orig_height')}")
    print(f"Pillow 처리 시간:  {item.get('processing_time_ms')} ms")
    print(f"Rekognition 시간:  {item.get('rekognition_time_ms')} ms")
    print(f"전체 처리 시간:    {item.get('total_time_ms')} ms")
    print(f"탐지된 라벨:")
    for label in item.get('labels', []):
        print(f"  - {label['name']} ({label['confidence']}%)")
    print("-" * 40)

if __name__ == "__main__":
    run_test()