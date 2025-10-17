# SCUMM v3 EGA Graphics Format Research

## 핵심 발견사항 (2025-10-17)

### 1. Vertical Strip Encoding
- **Strip Width**: 8 pixels
- **Compression Direction**: Vertical (세로 방향)
- **이유**: 세로 방향이 같은 색상의 run이 더 길어서 압축률이 높음

### 2. RLE Compression Algorithm
**기본 원리**:
- Run count가 data 앞에 위치
- High bit (0x80) set: Repeat mode → 다음 data를 count만큼 반복
- High bit clear: Literal mode → count만큼의 bytes를 그대로 복사

**Run Count 범위**:
- Maximum: 127 (0x7F)
- 127보다 긴 run은 여러 개의 counter byte 필요

### 3. EGA Planar Format (4 Bitplanes)
- **Format**: 4 color planes, each 1-bit-per-pixel
- **Compression Code**: BMCOMP_PIX32
- **Function**: drawStripEGA()
- **Pixel Reconstruction**:
  ```
  pixel_color = plane0[y][x] | (plane1[y][x] << 1) |
                (plane2[y][x] << 2) | (plane3[y][x] << 3)
  ```

### 4. Strip Data Structure (추정)
19 bytes per strip for 8x144 pixels:
- Raw: 144 pixels ÷ 8 bits = 18 bytes per plane
- 4 planes × 18 bytes = 72 bytes raw
- RLE compressed: ~19 bytes (약 74% 압축률)

**가능한 구조**:
```
Strip Data = Plane0_RLE + Plane1_RLE + Plane2_RLE + Plane3_RLE

각 Plane_RLE:
  - Vertical column (144 pixels)
  - RLE compressed (high bit = repeat, low bit = literal)
  - 평균 ~4.75 bytes per plane (19 ÷ 4)
```

## ScummVM 소스 코드 참조

### 핵심 파일
1. **engines/scumm/gfx.cpp**
   - `drawStripEGA()` 함수 구현
   - URL: https://github.com/scummvm/scummvm/blob/master/engines/scumm/gfx.cpp

2. **engines/scumm/gfx.h**
   - Function declaration:
     ```cpp
     void drawStripEGA(byte *dst, int dstPitch, const byte *src, int height) const;
     ```

### 검색 키워드
- "SCUMM v3 EGA planar bitplane"
- "BMCOMP_PIX32"
- "drawStripEGA implementation"
- "SCUMM vertical RLE compression"

## 참고 자료

### ScummVM 공식
- **Main Repository**: https://github.com/scummvm/scummvm
- **Wiki - Technical Reference**: https://wiki.scummvm.org/index.php/SCUMM/Technical_Reference
- **Wiki - Image Resources**: https://wiki.scummvm.org/index.php/SCUMM/Technical_Reference/Image_resources
  (주의: v6+ 만 다룸, v3 정보 없음)

### 커뮤니티 리소스
- **SCUMM Revisited - Image Format**: http://jsg.id.au/scumm/scummrev/articles/image.html
- **SCUMM Image Encoder**: http://www.jestarjokin.net/apps/scummimg/
- **Scumm Image Formats Wiki**: https://github.com/jamesu/scummc/wiki/Scumm-Image-formats
- **ModdingWiki - PCX Format**: https://moddingwiki.shikadi.net/wiki/PCX_Format

### JavaScript/Dart 구현체
- **jsscummvm**: https://github.com/mutle/jsscummvm
- **SCUMM-Dart**: https://github.com/jcsirot/SCUMM-Dart
- **nutcracker**: https://github.com/BLooperZ/nutcracker

## 현재 구현 문제점

### 잘못된 가정
현재 `decodeStripV3()` 함수는:
- ❌ 단일 픽셀 스트림으로 처리
- ❌ 8×144 = 1152 pixels를 순차적으로 디코딩 시도
- ❌ 19 bytes로는 1152 pixels 표현 불가능

### 올바른 접근
구현해야 할 알고리즘:
1. **4 Bitplane 분리**:
   ```
   19 bytes = Plane0 (4-5 bytes) + Plane1 (4-5 bytes) +
              Plane2 (4-5 bytes) + Plane3 (4-5 bytes)
   ```

2. **각 Plane별 Vertical RLE Decompression**:
   ```
   for each plane (0-3):
     decompress_vertical_rle(src, height=144)
     → output: 144 bits (18 bytes when unpacked)
   ```

3. **4 Bitplane → 16-color Pixel 재구성**:
   ```
   for y in range(144):
     for x in range(8):
       bit0 = plane0[y*8 + x]
       bit1 = plane1[y*8 + x]
       bit2 = plane2[y*8 + x]
       bit3 = plane3[y*8 + x]
       pixel_color = bit0 | (bit1<<1) | (bit2<<2) | (bit3<<3)
   ```

## 다음 단계

### 1. ScummVM 소스 직접 분석 (필수)
- [ ] `engines/scumm/gfx.cpp` 파일 전체 다운로드
- [ ] `drawStripEGA()` 함수 정확한 구현 찾기
- [ ] Planar bitplane RLE 디코딩 알고리즘 추출
- [ ] 테스트 케이스 작성

### 2. 디코더 재구현
- [ ] TypeScript `decodeStripV3()` 재작성
- [ ] Python `decode_strip_v3()` 재작성
- [ ] 4-bitplane 분리 로직
- [ ] Vertical RLE decompression
- [ ] Pixel reconstruction

### 3. 테스트 및 검증
- [ ] 단일 strip 테스트 (8×144)
- [ ] 전체 40 strips 테스트 (320×144)
- [ ] 실제 게임 화면과 비교
- [ ] room_01_correct.png 업데이트

## 노트

### 테스트 데이터
- **Room 01 첫 번째 strip**:
  - Offset: 0x438b
  - Size: 19 bytes
  - Expected output: 8×144 pixels (첫 8 columns)

### 예상 결과
19 bytes가 4 planes로 나뉘면:
- Plane당 평균: 4.75 bytes
- 압축 전 (raw): 18 bytes per plane (144 bits)
- 압축률: ~74% (18 → 4.75)

이는 RLE 압축으로 충분히 달성 가능한 수준.

---

**마지막 업데이트**: 2025-10-17
**상태**: ScummVM 소스 분석 진행 중
**다음 작업자**: 위의 "다음 단계" 섹션을 따라 drawStripEGA() 구현 분석
