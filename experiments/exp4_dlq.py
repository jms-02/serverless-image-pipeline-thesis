"""실험 4: 에러 처리 — 손상된 파일 업로드 시 DLQ 동작 검증"""
import boto3, time, uuid
from experiment_utils import s3, wait_done, save_csv, BUCKET

SQS_QUEUE_URL = 'https://sqs.ap-northeast-2.amazonaws.com/238479992071/thesis-dlq'
TRIALS = 5

sqs = boto3.client('sqs', region_name='ap-northeast-2')

def count_dlq_messages() -> int:
    """DLQ에 현재 쌓인 메시지 수 반환"""
    resp = sqs.get_queue_attributes(
        QueueUrl=SQS_QUEUE_URL,
        AttributeNames=['ApproximateNumberOfMessages'] # 대기 중인 메시지 수 요청
    )
    return int(resp['Attributes']['ApproximateNumberOfMessages'])

def run():
    rows = []

    for trial in range(TRIALS):
        key = f"uploads/exp4/broken_{uuid.uuid4().hex[:6]}.jpg"

        # 실제 이미지 바이너리가 아닌 단순 텍스트를 이미지 파일인 척 업로드
        broken_body = b"THIS IS NOT A VALID IMAGE FILE - INTENTIONALLY BROKEN"

        dlq_before = count_dlq_messages() # 실험 전 DLQ 개수 저장
        t0 = time.time()

        s3.put_object(Bucket=BUCKET, Key=key, Body=broken_body)
        print(f"[{trial+1}] 손상 파일 업로드: {key}")

        # Lambda가 3번 재시도 후 DLQ로 보낼 때까지 대기 (최대 3분)
        item = wait_done(key, timeout=180)
        elapsed_ms = int((time.time() - t0) * 1000)

        # SQS에 메시지가 도달하기까지의 물리적 지연 시간을 고려하여 10초 대기
        time.sleep(60)
        dlq_after = count_dlq_messages()

        rows.append({
            'trial':          trial,
            'key':            key,
            'status':         item.get('status', 'unknown'),
            'error_message':  item.get('error_message', ''),
            'elapsed_ms':     elapsed_ms,
            'dlq_before':     dlq_before,
            'dlq_after':      dlq_after,
            'dlq_increased':  dlq_after > dlq_before
        })

        print(f"  상태: {item.get('status')} | DLQ: {dlq_before}→{dlq_after} | {elapsed_ms}ms")
        time.sleep(10)

    save_csv(rows, 'exp4_dlq.csv')

    # 결과 요약 출력
    errors    = sum(1 for r in rows if r['status'] == 'error')
    dlq_hits  = sum(1 for r in rows if r['dlq_increased'])
    print(f"\n요약: {TRIALS}번 시도 중 에러 {errors}건, DLQ 도달 {dlq_hits}건")

if __name__ == '__main__':
    run()
