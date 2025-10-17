# LOOM SCUMM v3 그래픽 디코더 개발 진행 상황

## 현재 상태 (2025-10-17)

### ✅ 완료된 작업

#### 1. LFL 파일 구조 정확히 분석
- **실제 구조 확인**:
  ```
  0x00-0x03: 헤더 (룸 번호 등)
  0x04-0x05: Width (16-bit LE)  → 320px
  0x06-0x07: Height (16-bit LE) → 144px
  0x08-0x09: 0x0000 (패딩)
  0x0A+:     리소스 offset table (16-bit LE 배열)
  ```

- **배경 이미지 리소스 위치**:
  - Room 01: offset 0x009b에 40개 strip의 배경 이미지
  - Strip offset table: 각 strip의 절대 파일 위치
  - 평균 strip 크기: 약 19 bytes

#### 2. 서버 API 구현 (tools/server.ts)
- ✅ XOR 0xFF 복호화
- ✅ LFL 파일에서 배경 이미지 리소스 자동 탐지
- ✅ Strip offset table 재구성 (절대 주소 → 상대 주소)
- ✅ `/room/01/image` API 엔드포인트 구현
- **출력 형식**:
  ```
  [0x00-0x4F]: Strip offset table (40 strips × 2 bytes, 상대 주소)
  [0x50-...]:  Strip 데이터들 (연속 배치)
  ```

#### 3. TypeScript 디코더 업데이트 (tools/src/engine/ScummV3Decoder.ts)
- ✅ Format B (서버 재구성 데이터) 처리 추가
- ✅ Offset table 시작 위치: Format B는 offset+0, Format A는 offset+2
- ✅ Offset 검증 로직: Format B는 상대 주소이므로 minOffset=0
- ✅ 40개 strip (320x144) 파싱 성공

### ❌ 미해결 문제

#### 핵심 문제: Strip 디코딩 알고리즘 불일치

**현상**:
- 40개 strip을 모두 파싱하지만 이미지가 세로 줄무늬로 나옴
- 한 strip 테스트: 19바이트로 8x144 픽셀 중 첫 column만 118픽셀까지만 채움

**원인 분석**:
```python
# 현재 구현: 단순 RLE (ScummVM drawStripEGA로 추정)
Strip 0 (19 bytes):
  0x13 → run=1, color=3  → 1 pixel
  0x00 → run=0           → 다음 바이트가 run length
  0x00 → run=0           → 다음 바이트가 run length
  0x6e → run=110         → 110 pixels
  ...
  결과: 첫 column만 118픽셀, 나머지 7 columns는 비어있음
```

**가설**: SCUMM v3 EGA는 **4-bitplane planar 형식**을 사용
- 각 strip이 4개 bitplane으로 나뉘어져 있음
- 각 bitplane이 개별적으로 RLE 압축됨
- 19바이트 = 4 planes × ~4.75 bytes (144 pixels ÷ 8 bits = 18 bytes raw → RLE 압축)

### 📋 다음 작업 (중요!)

#### 1단계: ScummVM 소스코드 정확한 분석
**반드시 확인해야 할 파일**:
- `engines/scumm/gfx.cpp` - drawStripEGA() 함수
- `engines/scumm/gdi.cpp` - Gdi 클래스의 그래픽 처리
- `engines/scumm/charset.cpp` - EGA 관련 코드
- `engines/scumm/resource.cpp` - 리소스 로딩

**찾아야 할 정보**:
1. EGA planar bitplane 형식:
   - 4 planes (각 plane은 8x144 bits)
   - 각 plane의 RLE 압축 방식
   - Plane 데이터 배치 순서

2. RLE 압축 알고리즘:
   ```c
   // 예상 구조
   for (int plane = 0; plane < 4; plane++) {
     for (int col = 0; col < 8; col++) {
       // Vertical RLE stream for 144 pixels
       decompress_rle_vertical(data, dst, plane, col);
     }
   }
   ```

3. Pixel 재구성:
   ```
   pixel_color = plane0[y][x] | (plane1[y][x] << 1) |
                 (plane2[y][x] << 2) | (plane3[y][x] << 3)
   ```

#### 2단계: 디코더 재구현
**수정 대상**:
- `tools/src/engine/ScummV3Decoder.ts` - decodeStripV3() 함수
- `decode_room_correct.py` - decode_strip_v3() 함수

**구현 내용**:
1. 4-bitplane planar 형식으로 변경
2. 각 plane별 vertical RLE decompression
3. 4개 plane을 16색 픽셀로 재구성

#### 3단계: 테스트 및 검증
```bash
python3 decode_room_correct.py
# 예상 결과: 제대로 된 게임 배경 이미지 (320x144)
```

## 개발 환경

### 서버 실행
```bash
cd tools
bun run serve
# http://localhost:3000
```

### 빌드
```bash
cd tools
bun run build
```

### 테스트
```bash
# Python 디코더 테스트
python3 decode_room_correct.py

# 단일 strip 테스트
python3 test_single_strip.py

# LFL 구조 분석
python3 analyze_lfl_structure.py
```

## 참고 자료

### 문서
- `SCUMM_V3_FORMATS.md` - 그래픽 포맷 분석
- `scummvm.md` - LFL 파일 구조
- `README.md` - 프로젝트 개요

### 핵심 파일
- `tools/server.ts` - 서버 (Room 이미지 API)
- `tools/src/engine/ScummV3Decoder.ts` - TypeScript 디코더
- `tools/src/engine/GameEngine.ts` - 게임 엔진
- `decode_room_correct.py` - Python 디코더 (검증용)

### ScummVM 소스
- GitHub: https://github.com/scummvm/scummvm
- 주요 경로: `engines/scumm/`
- **핵심**: `gfx.cpp`의 `drawStripEGA()` 함수 찾기

## 문제 해결 전략

1. **ScummVM 소스 직접 확인**
   - drawStripEGA() 함수의 정확한 구현
   - Planar bitplane RLE 압축 알고리즘
   - 4-bit color 재구성 방식

2. **기존 SCUMM 툴 참조**
   - scummvm-tools의 이미지 인코더/디코더
   - 커뮤니티 구현체 검색

3. **실험적 접근**
   - Strip 데이터를 planar 형식으로 해석
   - 각 plane별로 RLE decompression 시도
   - 픽셀 재구성 알고리즘 테스트

## 예상 해결 시간
- ScummVM 소스 분석: 30분
- 디코더 재구현: 1시간
- 테스트 및 디버깅: 30분
- **총 예상 시간**: 2시간

---

**마지막 업데이트**: 2025-10-17
**다음 작업자에게**: 위의 "다음 작업" 섹션을 반드시 확인하고 ScummVM 소스코드 분석부터 시작하세요!
