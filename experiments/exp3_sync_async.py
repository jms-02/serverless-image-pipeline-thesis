"""실험 3: 동기(API Gateway 직접 호출) vs 비동기(S3 이벤트) 응답 특성 비교"""
import uuid, time, requests
from experiment_utils import s3, wait_done, save_csv, BUCKET

# API Gateway 엔드포인트 — 배포 후 실제 URL로 교체
API_URL = 'https://wd2xo0cerk.execute-api.ap-northeast-2.amazonaws.com/images'
TRIALS  = 30
IMG_PATH = '../scripts/test_images/test_1024kb.jpg'

def run():
    img = open(IMG_PATH, 'rb').read()
    rows = []

    for trial in range(TRIALS):
        # --- 비동기 방식: S3 업로드 후 폴링 ---
        key = f"uploads/exp3/async_{uuid.uuid4().hex[:6]}.jpg"
        t0 = time.time()
        s3.put_object(Bucket=BUCKET, Key=key, Body=img)
        client_response_ms = int((time.time() - t0) * 1000)  # 업로드 즉시 반환

        item = wait_done(key)
        async_e2e_ms = int((time.time() - t0) * 1000)        # 처리 완료까지

        # --- 동기 방식: 조회 API로 결과 확인까지 대기 ---
        # (동기 처리 전용 API가 있다면 여기서 호출, 없으면 폴링으로 비교)
        t1 = time.time()
        try:
            import urllib.parse
            encoded_key = urllib.parse.quote(key, safe='')
            resp = requests.get(f"{API_URL}/{encoded_key}", timeout=10)
            sync_total_ms = int((time.time() - t1) * 1000)
            sync_status = 'success' if resp.status_code == 200 else 'error'
        except Exception as e:
            sync_total_ms = -1
            sync_status = f'error: {e}'


        rows.append({
            'trial':               trial,
            'async_upload_ms':     client_response_ms,  # 클라이언트 즉시 응답
            'async_e2e_ms':        async_e2e_ms,         # 실제 처리 완료까지
            'sync_total_ms':       sync_total_ms,         # 동기 완료까지
            'async_status':        item.get('status'),
            'sync_status':         sync_status
        })
        print(f"시도:{trial+1}/{TRIALS} "
              f"비동기업로드:{client_response_ms}ms E2E:{async_e2e_ms}ms | "
              f"동기API:{sync_total_ms}ms")
        time.sleep(3)

    save_csv(rows, 'exp3_sync_async.csv')

if __name__ == '__main__':
    run()
