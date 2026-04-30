from PIL import Image
import os, io, math
import numpy as np

os.makedirs('scripts/test_images', exist_ok=True)

SIZES = {
    '100kb':  100,
    '500kb':  500,
    '1024kb': 1024,
    '3072kb': 3072,
    '5120kb': 5120,
}

for name, target_kb in SIZES.items():
    target_bytes = target_kb * 1024
    
    side = int(math.sqrt(target_bytes * 1.2)) 
    
    noise = np.random.randint(0, 256, (side, side, 3), dtype=np.uint8)
    img = Image.fromarray(noise, 'RGB')
    
    path = f'scripts/test_images/test_{name}.jpg'
    
    best_buf = None
    best_diff = float('inf')
    best_q = 100
    
    # 1부터 100까지의 Quality를 전부 테스트하여 가장 오차가 적은 값을 탐색
    for q in range(1, 101):
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=q)
        current_size = buf.tell()
        
        diff = abs(current_size - target_bytes)
        
        if diff < best_diff:
            best_diff = diff
            best_q = q
            best_buf = buf.getvalue()
            
    # 가장 근접한 결과물 파일로 저장
    with open(path, 'wb') as f:
        f.write(best_buf)
        
    actual_kb = len(best_buf) / 1024
    print(f"생성: {path} ({actual_kb:.2f}KB)")