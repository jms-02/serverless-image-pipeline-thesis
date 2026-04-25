"""실험 5: Rekognition 포함 vs 미포함 처리 시간 비교"""
import boto3, uuid, time
from experiment_utils import s3, wait_done, save_csv, BUCKET

TRIALS       = 30
IMG_PATH     = '../scripts/test_images/test_1024kb.jpg'
FUNC_NAME    = 'thesis-image-processor'

lam = boto3.client('lambda', region_name='ap-northeast-2')

def set_rekognition(enabled: bool):
    """Lambda 환경변수로 Rekognition ON/OFF 전환"""
    # boto3의 update_function_configuration을 사용하여 Lambda의 환경변수를 수정합니다.
    lam.update_function_configuration(
        FunctionName=FUNC_NAME,
        Environment={
            'Variables': {
                # 이 값이 Lambda 코드 내부에서 'if'문의 조건으로 사용됨
                'REKOGNITION_ENABLED': 'true' if enabled else 'false',
                'RESULT_BUCKET':       'thesis-images-result-2026',
                'SNS_TOPIC_ARN':             'arn:aws:sns:ap-northeast-2:238479992071:thesis-notify'
            }
        }
    )
    time.sleep(15)  # 설정 반영 대기
    print(f"Rekognition {'ON' if enabled else 'OFF'} 설정 완료")

def run():
    img  = open(IMG_PATH, 'rb').read()
    rows = []

    for enabled in [True, False]: # 먼저 켬(True) 상태로 30번, 그다음 끔(False) 상태로 30번
        set_rekognition(enabled) # 환경변수 변경

        for trial in range(TRIALS):
            key = f"uploads/exp5/rekog_{str(enabled).lower()}_{uuid.uuid4().hex[:6]}.jpg"
            t0  = time.time()
            s3.put_object(Bucket=BUCKET, Key=key, Body=img)

            # 처리가 끝날 때까지 대기 (wait_done은 DynamoDB 결과를 가져옴)
            item = wait_done(key)
            e2e_ms = int((time.time() - t0) * 1000)

            rows.append({
                'rekog_enabled':  enabled,
                'trial':          trial,
                'pillow_ms':      item.get('processing_time_ms', -1),
                'rekog_ms':       item.get('rekognition_time_ms', 0),
                'total_ms':       item.get('total_time_ms', -1),
                'e2e_ms':         e2e_ms,
                'label_count':    len(item.get('labels', [])),
                'status':         item.get('status', 'unknown')
            })
            print(f"Rekog:{'ON' if enabled else 'OFF'} "
                  f"시도:{trial+1}/{TRIALS} "
                  f"total:{item.get('total_time_ms')}ms e2e:{e2e_ms}ms")
            time.sleep(2)

    # 실험 끝나면 Rekognition 다시 ON으로 복원
    set_rekognition(True)

    save_csv(rows, 'exp5_rekognition.csv')

    # pandas 라이브러리를 사용해 수집된 데이터의 평균과 표준편차를 즉석에서 계산합니다.
    import pandas as pd
    df = pd.DataFrame(rows)
    df['total_ms'] = df['total_ms'].astype(float)
    for en in [True, False]:
        sub = df[df['rekog_enabled'] == en]['total_ms']
        print(f"Rekog {'ON ' if en else 'OFF'}: 평균 {sub.mean():.1f}ms / 표준편차 {sub.std():.1f}ms")

if __name__ == '__main__':
    run()
