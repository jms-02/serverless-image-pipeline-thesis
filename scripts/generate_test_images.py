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
    side = int(math.sqrt(target_kb * 1024 / 3))
    
    # 랜덤 노이즈 이미지 생성
    noise = np.random.randint(0, 256, (side, side, 3), dtype=np.uint8)
    img = Image.fromarray(noise, 'RGB')
    
    path = f'scripts/test_images/test_{name}.jpg'
    saved = False
    
    for q in range(95, 10, -5):
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=q)
        if buf.tell() >= target_kb * 1024 * 0.9: # 목표 용량의 90% 이상이면
            with open(path, 'wb') as f:
                f.write(buf.getvalue()) # 메모리 데이터를 실제 파일로 저장
            actual_kb = os.path.getsize(path) // 1024
            print(f"생성: {path} ({actual_kb}KB)")
            saved = True
            break
    
    # 
    if not saved:
        img.save(path, format='JPEG', quality=95)
        actual_kb = os.path.getsize(path) // 1024
        print(f"생성(최대 quality): {path} ({actual_kb}KB)")