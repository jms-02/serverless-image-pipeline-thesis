"""단건 이미지 업로드 유틸 — 수동 테스트용"""
import boto3, sys, os, time
from decimal import Decimal

BUCKET     = 'thesis-images-original-2026'
TABLE_NAME = 'ImageMetadata'

s3 = boto3.client('s3', region_name='ap-northeast-2')
db = boto3.resource('dynamodb', region_name='ap-northeast-2').Table(TABLE_NAME)

def convert_decimals(obj):
    if isinstance(obj, list):  return [convert_decimals(i) for i in obj]
    if isinstance(obj, dict):  return {k: convert_decimals(v) for k, v in obj.items()}
    if isinstance(obj, Decimal): return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def wait_done(image_id: str, timeout: int = 60) -> dict:
    deadline = time.time() + timeout
    attempt  = 0
    while time.time() < deadline:
        attempt += 1
        item = db.get_item(Key={'image_id': image_id}).get('Item')
        if item and item.get('status') in ('success', 'error'):
            print(f"  → {attempt}번 만에 완료")
            return convert_decimals(item)
        print(f"  [{attempt}] 처리 중...")
        time.sleep(2)
    return {}

def upload_and_check(filepath: str):
    if not os.path.exists(filepath):
        print(f"파일 없음: {filepath}")
        sys.exit(1)

    filename = os.path.basename(filepath)
    s3_key   = f"uploads/{filename}"

    # 기존 DynamoDB 레코드 삭제 (재실험 시 충돌 방지)
    db.delete_item(Key={'image_id': s3_key})

    print(f"업로드 중: {filepath} → s3://{BUCKET}/{s3_key}")
    with open(filepath, 'rb') as f:
        s3.put_object(Bucket=BUCKET, Key=s3_key, Body=f)

    print("처리 대기 중...")
    item = wait_done(s3_key)

    if not item:
        print("시간 초과 — 60초 내 처리 안 됨")
        return

    print("\n결과:")
    print(f"  상태:              {item.get('status')}")
    print(f"  파일 크기:         {item.get('file_size_kb')} KB")
    print(f"  원본 해상도:       {item.get('orig_width')} x {item.get('orig_height')}")
    print(f"  Pillow 처리 시간:  {item.get('processing_time_ms')} ms")
    print(f"  Rekognition 시간:  {item.get('rekognition_time_ms')} ms")
    print(f"  전체 처리 시간:    {item.get('total_time_ms')} ms")
    print(f"  탐지 라벨:")
    for label in item.get('labels', []):
        name = label.get('name', '')
        conf = label.get('confidence', 0)
        print(f"    - {name} ({conf}%)")

if __name__ == '__main__':
    # 사용법: python upload.py test.jpg
    # 인자 없으면 기본값 test.jpg
    target = sys.argv[1] if len(sys.argv) > 1 else 'test.jpg'
    upload_and_check(target)
