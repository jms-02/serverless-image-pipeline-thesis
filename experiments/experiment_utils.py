"""
모든 실험 스크립트가 from experiment_utils import * 로 가져다 씀
"""
import boto3, time, csv, os
from dotenv import load_dotenv

load_dotenv()  # .env 파일에서 설정 로드

# S3 버킷 이름 설정
BUCKET  = os.environ['ORIGINAL_BUCKET']   # thesis-images-original-2026

# AWS 서비스 연결 객체 생성
s3 = boto3.client('s3', region_name='ap-northeast-2')
db = boto3.resource('dynamodb', region_name='ap-northeast-2').Table('ImageMetadata')

def wait_done(image_id: str, timeout: int = 60) -> dict:
    # DynamoDB에 결과가 저장될 때까지 polling
    deadline = time.time() + timeout
    while time.time() < deadline:
        # DB에서 해당 이미지 ID의 행(row)을 가져옴
        resp = db.get_item(Key={'image_id': image_id})
        item = resp.get('Item')

        # 상태가 'success'(성공) 또는 'error'(실패)로 바뀌었는지 확인
        if item and item.get('status') in ('success', 'error'):
            return item # 결과가 나왔으면 데이터 반환
        
        time.sleep(0.5)
    return {'status': 'timeout'} # 60초가 지나도 결과가 없으면 타임아웃 반환

def upload(key: str, body: bytes) -> float:
    # S3 업로드 후 업로드 시작 타임스탬프 반환
    t0 = time.time()
    s3.put_object(Bucket=BUCKET, Key=key, Body=body)
    return t0

def save_csv(rows: list, filename: str):
    # 결과를 analysis/data/ 폴더에 CSV로 저장
    path = os.path.join('analysis', 'data', filename)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys()) # 리스트 내 첫 번째 딕셔너리의 키값들을 컬럼 헤더(제목)로 사용
        writer.writeheader() # CSV 헤더 쓰기
        writer.writerows(rows) # 실제 데이터 쓰기
    print(f"저장 완료: {path} ({len(rows)}행)")