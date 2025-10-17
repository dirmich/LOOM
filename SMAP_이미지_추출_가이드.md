# SCUMM v3 SMAP 이미지 추출 완벽 가이드

**대상**: LOOM (1990) 및 SCUMM v3 게임
**포맷**: Small Header, 16-color EGA
**작성일**: 2025-10-18

---

## 📋 목차

1. [LFL 파일 구조](#lfl-파일-구조)
2. [XOR 복호화](#xor-복호화)
3. [SMAP 리소스 찾기](#smap-리소스-찾기)
4. [Strip Offset 테이블](#strip-offset-테이블)
5. [RLE 디코딩](#rle-디코딩)
6. [전체 이미지 합성](#전체-이미지-합성)
7. [트러블슈팅](#트러블슈팅)

---

## LFL 파일 구조

### 전체 레이아웃
```
Offset    크기    내용
------    ----    ----
0x00      2       파일 크기 (little-endian)
0x02      2       알 수 없음
0x04      2       Room 너비 (pixels)
0x06      2       Room 높이 (pixels)
0x08      2       알 수 없음
0x0A      ?       리소스 테이블 (2-byte offset 배열)
...       ...     리소스 데이터들
```

### 리소스 테이블
```python
# 0x0A부터 2바이트씩 리소스 offset
resourceTableStart = 0x0A
offsets = []
for i in range(20):  # 최대 20개
    pos = resourceTableStart + i * 2
    offset = data[pos] | (data[pos + 1] << 8)
    if offset == 0:
        break  # 0이면 테이블 끝
    offsets.append(offset)
```

**중요**:
- 리소스 0번이 **SMAP** (배경 이미지)
- SCUMM v3는 **small header** - chunk tag 없음!

---

## XOR 복호화

### 암호화 방식
LOOM LFL 파일은 **XOR 0xFF**로 암호화:

```python
with open('01.LFL', 'rb') as f:
    encrypted = f.read()

# XOR 0xFF로 복호화
decrypted = bytes([b ^ 0xFF for b in encrypted])
```

**검증 방법**:
- 복호화 후 offset 값들이 파일 크기 내에 있어야 함
- ASCII 문자열 패턴 확인

---

## SMAP 리소스 찾기

### Small Header 방식
```python
# Resource 0 = SMAP (리소스 테이블 첫 번째)
smap_ptr = decrypted[0x0A] | (decrypted[0x0B] << 8)

print(f"SMAP offset: 0x{smap_ptr:04X}")
```

**주의**:
- `SMAP` chunk tag 찾으면 **안 됨** (small header는 tag 없음)
- 리소스 0번이 **직접 SMAP 데이터**

### 구조
```
SMAP Offset   내용
-----------   ----
+0x00         Strip 개수 (암시적, 0이 나올 때까지)
+0x02         Strip 0 offset (SMAP 기준 상대)
+0x04         Strip 1 offset
+0x06         Strip 2 offset
...           ...
```

---

## Strip Offset 테이블

### 16-Color 게임 (LOOM)
```python
# ScummVM 코드: offset = READ_LE_UINT16(smap_ptr + stripnr * 2 + 2)
strip_offsets = []
for strip_idx in range(200):  # 충분히 큰 숫자
    offset_pos = smap_ptr + 2 + strip_idx * 2

    # 2바이트 little-endian 읽기
    strip_offset = decrypted[offset_pos] | (decrypted[offset_pos + 1] << 8)

    # 0이거나 범위 초과면 끝
    if strip_offset == 0 or smap_ptr + strip_offset >= len(decrypted):
        break

    # SMAP 기준 상대 offset → 절대 offset
    abs_offset = smap_ptr + strip_offset
    strip_offsets.append(abs_offset)

num_strips = len(strip_offsets)
print(f"Strip 개수: {num_strips}")
```

**핵심**:
- Strip offset은 **SMAP 시작점 기준 상대 주소**
- 절대 offset = `smap_ptr + strip_offset`

### 다른 SCUMM 버전
```python
# Small header 또는 16-color:
offset = READ_LE_UINT16(smap_ptr + stripnr * 2 + 2)

# 일반 버전:
offset = READ_LE_UINT16(smap_ptr + stripnr * 2 + 8)

# Version 8:
offset = READ_LE_UINT32(smap_ptr + stripnr * 4 + 8)
```

---

## RLE 디코딩

### drawStripEGA 알고리즘

**3가지 RLE 모드**:

#### Mode 1: Single Color (0x00-0x7F)
```
Byte Format: 0RRRCCCC
  RRR = run length (0이면 다음 byte에서 읽기)
  CCCC = color (0-15)

예시:
  0x13 = run=1, color=3 → 1픽셀을 color 3으로
  0x05 0x20 = run=0 → 0x20(32픽셀)을 color 5로
```

#### Mode 2: Repeat Previous (0x80-0xBF)
```
Byte Format: 10RRRRRR
  RRRRRR = run length (0이면 다음 byte에서 읽기)

동작: 이전 x 위치의 픽셀 반복

예시:
  0x85 = run=5 → 이전 픽셀을 5번 반복
  0x80 0x10 = run=0 → 0x10(16번) 반복
```

#### Mode 3: Two-Color Dithering (0xC0-0xFF)
```
Byte Format: 11RRRRRR [HHHHLLLL]
  RRRRRR = run length (0이면 다음 byte에서 읽기)
  다음 byte: HHHH = high color, LLLL = low color

동작: 두 색상을 교대로 칠함 (체스판 패턴)

예시:
  0xC5 0x3A = run=5, colors 3와 A
    픽셀 0: color 3
    픽셀 1: color A
    픽셀 2: color 3
    픽셀 3: color A
    픽셀 4: color 3
```

### Python 구현
```python
def drawStripEGA(src, height):
    """ScummVM drawStripEGA 정확한 포팅"""
    pixels = [[0 for _ in range(8)] for _ in range(height)]
    color, run, x, y, src_idx = 0, 0, 0, 0, 0

    while x < 8 and src_idx < len(src):
        color = src[src_idx]
        src_idx += 1

        if color & 0x80:  # Mode 2 또는 3
            run = color & 0x3F

            if color & 0x40:  # Mode 3: Two-color dithering
                if src_idx >= len(src): break
                color = src[src_idx]
                src_idx += 1

                if run == 0:  # Extended run length
                    if src_idx >= len(src): break
                    run = src[src_idx]
                    src_idx += 1

                for z in range(run):
                    if x >= 8: break  # Strip 경계
                    if y < height:
                        # 홀수/짝수 픽셀에 다른 색
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        pixels[y][x] = pixel_color
                    y += 1
                    if y >= height:
                        y, x = 0, x + 1

            else:  # Mode 2: Repeat previous
                if run == 0:  # Extended run length
                    if src_idx >= len(src): break
                    run = src[src_idx]
                    src_idx += 1

                for z in range(run):
                    if x >= 8: break  # Strip 경계
                    if y < height:
                        pixels[y][x] = pixels[y][x - 1] if x > 0 else 0
                    y += 1
                    if y >= height:
                        y, x = 0, x + 1

        else:  # Mode 1: Single color
            run = color >> 4
            if run == 0:  # Extended run length
                if src_idx >= len(src): break
                run = src[src_idx]
                src_idx += 1

            pixel_color = color & 0xF
            for z in range(run):
                if x >= 8: break  # Strip 경계
                if y < height:
                    pixels[y][x] = pixel_color
                y += 1
                if y >= height:
                    y, x = 0, x + 1

    return pixels
```

**중요 포인트**:
- Strip은 **8×height** 픽셀
- **세로로** 채움 (column-major)
- `x >= 8`일 때 **즉시 중단** (strip 경계)

---

## 전체 이미지 합성

### 1. 너비 결정
```python
# LFL 헤더의 선언 너비 사용
width = decrypted[4] | (decrypted[5] << 8)
height = decrypted[6] | (decrypted[7] << 8)

# Strip count는 참고용 (width와 다를 수 있음)
max_strips = width // 8
```

### 2. Strip 디코딩 및 합성
```python
full_pixels = [[0 for _ in range(width)] for _ in range(height)]

for strip_idx in range(min(num_strips, max_strips)):
    # Strip 데이터 추출
    strip_offset = strip_offsets[strip_idx]
    next_offset = strip_offsets[strip_idx + 1] if strip_idx < num_strips - 1 else len(decrypted)
    strip_data = decrypted[strip_offset:next_offset]

    # RLE 디코딩
    strip_pixels = drawStripEGA(strip_data, height)

    # 전체 이미지에 복사
    if strip_pixels:
        strip_x = strip_idx * 8
        for y in range(height):
            for x in range(8):
                pixel_x = strip_x + x
                if pixel_x < width and y < len(strip_pixels):
                    full_pixels[y][pixel_x] = strip_pixels[y][x]
```

### 3. PNG 저장
```python
from PIL import Image

# EGA 16-color 팔레트
EGA_PALETTE = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00), (0x00, 0xAA, 0xAA),
    (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA), (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA),
    (0x55, 0x55, 0x55), (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
    (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55), (0xFF, 0xFF, 0xFF),
]

img = Image.new('RGB', (width, height))
for y in range(height):
    for x in range(width):
        color_idx = full_pixels[y][x]
        rgb = EGA_PALETTE[color_idx]
        img.putpixel((x, y), rgb)

img.save('output.png')
```

---

## 트러블슈팅

### 문제 1: IndexError - list assignment index out of range
**증상**: RLE 디코딩 중 배열 범위 초과

**원인**:
- Run length가 strip 경계(8픽셀) 넘어감
- Height 초과

**해결**:
```python
for z in range(run):
    if x >= 8: break  # 추가!
    if y < height:
        pixels[y][x] = pixel_color
    y += 1
    if y >= height: y, x = 0, x + 1
```

### 문제 2: 세로 줄무늬만 나옴
**증상**: 깨진 이미지, 세로 줄무늬 패턴

**원인**:
- 잘못된 strip offset 사용
- SMAP 위치를 잘못 찾음

**해결**:
```python
# ❌ 잘못된 방법
for resourceOffset in resourceOffsets:
    # gap 휴리스틱으로 추측...

# ✅ 올바른 방법
smap_ptr = decrypted[0x0A] | (decrypted[0x0B] << 8)
strip_offset = smap_ptr + (decrypted[smap_ptr + 2 + stripnr * 2] | ...)
```

### 문제 3: 픽셀 비율이 너무 낮음 (<10%)
**증상**: 대부분 검은색, 일부 픽셀만 표시

**원인**:
- 올바른 위치지만 Y offset 가설 적용
- Strip offset이 상대 주소임을 몰랐음

**해결**:
```python
# ❌ 잘못: Y offset으로 해석
y_offset = strip_data[4]
rle_data = strip_data[5:]

# ✅ 올바름: 전체 데이터가 RLE
rle_data = strip_data
```

### 문제 4: 너비가 맞지 않음
**증상**: 이미지가 늘어나거나 잘림

**원인**:
- Strip count × 8을 너비로 사용
- 선언 너비 무시

**해결**:
```python
# ✅ LFL 헤더의 선언 너비 사용
width = decrypted[4] | (decrypted[5] << 8)

# Strip은 width // 8개만 사용
for strip_idx in range(min(num_strips, width // 8)):
    # ...
```

---

## 완성 코드

전체 코드는 `decode_all_rooms_correct.py` 참조.

**핵심 단계**:
1. XOR 0xFF 복호화
2. SMAP = Resource 0
3. Strip offset 읽기 (SMAP+2부터)
4. 각 strip RLE 디코딩
5. 8픽셀씩 가로로 배치
6. PNG 저장

---

## 참고 자료

- **ScummVM 소스코드**:
  - `engines/scumm/gfx.cpp` - drawStripEGA()
  - `engines/scumm/resource.cpp` - findResource()

- **SCUMM 위키**:
  - http://wiki.scummvm.org/index.php/SCUMM/Technical_Reference

- **본 프로젝트**:
  - `decode_all_rooms_correct.py` - 작동하는 디코더
  - `최종성공_20251018.md` - 개발 과정

---

**작성일**: 2025-10-18
**버전**: 1.0
**작성자**: Claude AI Agent
