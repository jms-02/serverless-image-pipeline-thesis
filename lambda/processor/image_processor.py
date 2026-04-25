from PIL import Image
import io, time

def process_image(body: bytes) -> dict:
    t0 = time.time()
    img = Image.open(io.BytesIO(body))
    orig_w, orig_h = img.size

    # 1. 리사이징 (최대 800px, 비율 유지)
    resized = img.copy()
    resized.thumbnail((800, 800), Image.LANCZOS)
    buf = io.BytesIO()
    resized.save(buf, format='JPEG', quality=85)
    resized_bytes = buf.getvalue()

    # 2. 썸네일 (150×150)
    thumb = img.copy()
    thumb.thumbnail((150, 150), Image.LANCZOS)
    tbuf = io.BytesIO()
    thumb.save(tbuf, format='JPEG', quality=70)
    thumb_bytes = tbuf.getvalue()

    # 3. EXIF 추출
    exif = {}
    try:
        from PIL.ExifTags import TAGS
        raw = img._getexif()
        if raw:
            exif = {TAGS.get(k,k): str(v) for k,v in raw.items()}
    except Exception:
        pass

    pillow_ms = int((time.time() - t0) * 1000)

    return {
        'resized': resized_bytes,
        'thumbnail': thumb_bytes,
        'orig_width': orig_w,
        'orig_height': orig_h,
        'exif': exif,
        'pillow_ms': pillow_ms   # Pillow 처리 시간 별도 측정
    }