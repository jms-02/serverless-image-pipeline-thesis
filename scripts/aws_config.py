"""
버킷명, ARN 등 프로젝트 전체에서 쓰는 상수.
실제 값은 .env 파일에서 불러옴.
"""
import os
from dotenv import load_dotenv
load_dotenv()

ORIGINAL_BUCKET = os.environ.get('ORIGINAL_BUCKET', 'thesis-images-original-2026')
RESULT_BUCKET   = os.environ.get('RESULT_BUCKET', 'thesis-images-result-2026')
DYNAMODB_TABLE  = os.environ.get('DYNAMODB_TABLE', 'ImageMetadata')
SNS_ARN         = os.environ.get('SNS_ARN', 'arn:aws:sns:ap-northeast-2:238479992071:thesis-notify')
REGION          = 'ap-northeast-2'