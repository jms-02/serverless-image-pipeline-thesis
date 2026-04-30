"""실험 3: Lambda 콜드 스타트 vs 웜 스타트 지연 시간 비교"""
import uuid, time, boto3
from experiment_utils import upload, wait_done, save_csv, BUCKET

WARM_INTERVAL_SEC  = 10    # 웜 상태 유지: 요청 간격 10초
COLD_INTERVAL_SEC  = 600   # 콜드 유발: 10분 방치 후 요청
TRIALS_PER_STATE   = 15    # 각 상태당 15번 반복

lam = boto3.client('lambda', region_name='ap-northeast-2')
IMG  = open('../scripts/test_images/test_1024kb.jpg', 'rb').read()

def get_cold_start_flag(key: str) -> bool:
    """DynamoDB에서 Lambda가 기록한 init_type 확인"""
    from experiment_utils import db
    resp = db.get_item(Key={'image_id': key})
    item = resp.get('Item', {})
    # Lambda 코드 내부에서 /tmp 파일 존재 여부로 콜드/웜 판별 후 DynamoDB에 기록 필요
    return item.get('is_cold_start', False)

def run():
    rows = []

    # ── 웜 스타트 측정 ──────────────────────────────
    print("=== 웜 스타트 측정 시작 ===")
    for trial in range(TRIALS_PER_STATE):
        key = f"uploads/exp3/warm_{uuid.uuid4().hex[:6]}.jpg"
        t0  = upload(key, IMG)
        item = wait_done(key)
        e2e  = int((time.time() - t0) * 1000)

        rows.append({
            'state':    'warm',
            'trial':    trial,
            'e2e_ms':   e2e,
            'total_ms': item.get('total_time_ms', -1),
            'status':   item.get('status', 'unknown')
        })
        print(f"  웜 시도:{trial+1} e2e:{e2e}ms")
        time.sleep(WARM_INTERVAL_SEC)  # 짧은 간격 → Lambda 컨테이너 유지

    # ── 콜드 스타트 유발 ────────────────────────────
    print(f"\n=== {COLD_INTERVAL_SEC//60}분 대기 중 (Lambda 컨테이너 종료 유도) ===")
    time.sleep(COLD_INTERVAL_SEC)

    # ── 콜드 스타트 측정 ────────────────────────────
    print("=== 콜드 스타트 측정 시작 ===")
    for trial in range(TRIALS_PER_STATE):
        key = f"uploads/exp3/cold_{uuid.uuid4().hex[:6]}.jpg"
        t0  = upload(key, IMG)
        item = wait_done(key)
        e2e  = int((time.time() - t0) * 1000)

        rows.append({
            'state':    'cold',
            'trial':    trial,
            'e2e_ms':   e2e,
            'total_ms': item.get('total_time_ms', -1),
            'status':   item.get('status', 'unknown')
        })
        print(f"  콜드 시도:{trial+1} e2e:{e2e}ms")
        time.sleep(COLD_INTERVAL_SEC)  # 매번 콜드 유발

    save_csv(rows, 'exp3_coldstart.csv')

    import pandas as pd
    df = pd.DataFrame(rows)
    for s in ['warm', 'cold']:
        sub = df[df['state'] == s]['e2e_ms']
        print(f"{s.upper()}: 평균 {sub.mean():.1f}ms / 표준편차 {sub.std():.1f}ms")

if __name__ == '__main__':
    run()