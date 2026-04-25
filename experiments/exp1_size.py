"""실험 1: 이미지 파일 크기 vs 처리 시간"""
import uuid, time
from experiment_utils import upload, wait_done, save_csv, BUCKET

# 설정값
SIZES_KB = [100, 500, 1024, 3072, 5120]
TRIALS   = 30

def run():
    rows = []
    for kb in SIZES_KB: # 이미지 크기별 반복
        img = open(f'../scripts/test_images/test_{kb}kb.jpg', 'rb').read()
        for trial in range(TRIALS): # 총 30번 테스트
            key = f"uploads/exp1/{kb}kb_{uuid.uuid4().hex[:6]}.jpg" # 파일 이름 랜덤 생성
            t0 = upload(key, img) # upload 함수가 실행된 시점의 타임스탬프를 t0에 저장 (업로드 시작 시간)
            item = wait_done(key) # 서버가 처리를 완료할 때까지 기다린 후, 결과 데이터(item)를 받아옴
            e2e = int((time.time() - t0) * 1000) # 현재 시간에서 시작 시간(t0)을 빼서 전체 소요 시간(ms) 계산

            rows.append({
                'size_kb':        kb,
                'trial':          trial,
                'pillow_ms':      item.get('processing_time_ms', -1), # 내부 라이브러리(Pillow) 처리 시간
                'rekog_ms':       item.get('rekognition_time_ms', -1), # AWS Rekognition 등의 AI 분석 시간
                'total_ms':       item.get('total_time_ms', -1), # 서버 내부 전체 로직 처리 시간
                'e2e_ms':         e2e, # 클라이언트 기준 전체 왕복 시간 (네트워크 포함)
                'status':         item.get('status', 'unknown')
            })
            # 현재 진행 상황 출력
            print(f"크기:{kb}KB 시도:{trial+1}/{TRIALS} e2e:{e2e}ms")
            time.sleep(2) # API 과부하 방지 및 안정적인 측정을 위해 2초간 대기

    save_csv(rows, 'exp1_size.csv') # 모든 반복문이 끝나면 수집된 데이터를 CSV 파일로 저장

if __name__ == '__main__':
    run()