import boto3
import time
from decimal import Decimal

rekognition = boto3.client('rekognition', region_name='ap-northeast-2')

def analyze_image(bucket: str, key: str) -> dict:
    # Rekognition으로 이미지 분석, 처리 시간도 측정
    t0 = time.time()

    resp = rekognition.detect_labels(
        Image={
            'S3Object': { # 분석할 이미지가 저장된 S3의 위치(bucket 이름과 key) 지정
                'Bucket': bucket, 
                'Name': key
            }
        },
        MaxLabels=10, # 레이블의 최대 개수를 10개
        MinConfidence=70 # 신뢰도가 70% 이상인 결과만 반환
    )

    rekog_ms = int((time.time() - t0) * 1000) # 소요 시간 계산

    labels = [ # API 응답에서 필요한 정보(Name, Confidence)만 추출
        {
            'name': label['Name'],
            'confidence': Decimal(str(round(label['Confidence'], 1)))
        }
        for label in resp['Labels']
    ]

    return { # 결과 반환
        'labels': labels,
        'rekognition_time_ms': rekog_ms
    }
