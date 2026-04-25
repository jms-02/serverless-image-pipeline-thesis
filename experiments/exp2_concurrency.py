"""실험 2: 동시 업로드 수 vs 처리 완료 시간"""
import uuid, time
from concurrent.futures import ThreadPoolExecutor # 병렬 처리를 위한 도구
from experiment_utils import s3, wait_done, save_csv, BUCKET

CONCURRENCIES = [1, 5, 10, 20] # 동시에 업로드할 파일 개수 (1개씩, 5개씩... 20개씩)
TRIALS        = 10 # 각 조건당 10번씩 반복
IMG_PATH      = '../scripts/test_images/test_1024kb.jpg' # 1MB 이미지로 고정

def run():
    img = open(IMG_PATH, 'rb').read()
    rows = []

    for c in CONCURRENCIES:
        for trial in range(TRIALS):
            # 한 번에 보낼 파일들의 고유 이름(Key) 리스트 생성
            keys = [f"uploads/exp2/c{c}_t{trial}_{uuid.uuid4().hex[:4]}.jpg" for _ in range(c)] 

            # 동시 업로드
            t_start = time.time()
            with ThreadPoolExecutor(max_workers=c) as ex: # ThreadPoolExecutor를 사용해 'c'개의 쓰레드를 생성 (동시 업로드 시작)
                list(ex.map(
                    lambda k: s3.put_object(Bucket=BUCKET, Key=k, Body=img),
                    keys
                ))

            # 모든 파일 처리 완료 대기
            results = [wait_done(k) for k in keys]
            total_ms = int((time.time() - t_start) * 1000) # 모든 파일이 처리 완료된 시점의 전체 소요 시간 계산
            completed = sum(1 for r in results if r.get('status') == 'success') # 성공적으로 처리된 파일의 개수 카운트

            rows.append({
                'concurrency':  c,
                'trial':        trial,
                'total_files':  c,
                'completed':    completed,
                'total_ms':     total_ms,
                'avg_per_file': total_ms // c # 파일 1개당 평균 처리 시간
            })
            print(f"동시성:{c} 시도:{trial+1}/{TRIALS} 완료:{completed}/{c} 총:{total_ms}ms")
            time.sleep(5)  # 다음 실험 전 Lambda 안정화 대기

    save_csv(rows, 'exp2_concurrency.csv')

if __name__ == '__main__':
    run()
