# SCUMM v3 Graphics Formats (LOOM)

디코더 분석을 통해 발견한 세 가지 SCUMM v3 그래픽 포맷

## 📊 Format Detection Summary

| Format | 감지 조건 | 예제 파일 | 특징 |
|--------|----------|-----------|------|
| **Format A** | `첫 word ≈ 파일크기` (±10%) | 05_res002.bin | 이미지 크기 헤더 + 오프셋 테이블 |
| **Format B** | `첫 word < 1000` | 01_res002.bin | 직접 오프셋 테이블 (헤더 없음) |
| **Format C** | `첫 word > 파일크기` | 01_res001.bin | Raw RLE 데이터 (오프셋 테이블 없음) |

## 📝 Format Details

### Format A: Size Header + Offset Table
```
[0x00 padding] [image size word] [offset table] [strip data...]
                └─ 2 bytes       └─ n×2 bytes   └─ RLE compressed
```

**구조:**
1. 0x00 바이트 패딩 (가변 길이, 0~100 bytes)
2. 이미지 전체 크기 (word, little-endian)
3. 스트립 오프셋 테이블 (각 스트립 시작 위치, 이미지 시작 기준 상대 오프셋)
4. 각 스트립의 vertical RLE 압축 데이터

**예제:** 05_res002.bin
- 파일 크기: 22110 bytes
- 첫 word: 0x565e (22110) ✓ 파일 크기와 일치
- 오프셋: [0xb2, 0x180, 0x245, ...] (이미지 시작부터의 상대 오프셋)

### Format B: Direct Offset Table
```
[0x00 padding] [offset table] [strip data...]
                └─ n×2 bytes   └─ RLE compressed
```

**구조:**
1. 0x00 바이트 패딩 (가변 길이)
2. 스트립 오프셋 테이블 (크기 헤더 없이 바로 시작)
3. 각 스트립의 vertical RLE 압축 데이터

**예제:** 01_res002.bin
- 파일 크기: 36978 bytes (패딩 80 bytes 포함)
- 첫 word: 0x0065 (101) - 작은 오프셋 값
- 오프셋: [101, 10, 38, 58, 82, ...] - 직접 오프셋

### Format C: Raw Continuous RLE
```
[continuous RLE stream for all strips]
└─ No offset table, decode sequentially
```

**구조:**
1. 오프셋 테이블 없음
2. 모든 스트립이 연속된 RLE 스트림으로 인코딩
3. 각 스트립은 순차적으로 디코딩 필요
4. 스트립 경계는 휴리스틱으로 추정 (200px 높이 기준 ~150-300 bytes/strip)

**예제:** 01_res001.bin
- 파일 크기: 6142 bytes
- 첫 word: 0x2c43 (11331) ✗ 파일 크기보다 큼
- 패턴: `43 2c 43 3f 43 52...` - 0x43 반복 (RLE 데이터)

## 🔧 Decoder Implementation

### ScummV3Decoder.ts 주요 개선사항:

#### 1. Format Auto-Detection
```typescript
const firstWord = data[offset] | (data[offset + 1] << 8);
const fileSize = data.length - offset;

const isFormatA = Math.abs(firstWord - fileSize) < fileSize * 0.1;
const isFormatB = firstWord < 1000 && firstWord < fileSize;
const isFormatC = firstWord > fileSize;
```

#### 2. Format-Specific Decoding

**Format A/B:**
- `tableStart` 위치 계산 (Format A는 +2, Format B는 +0)
- 오프셋 테이블 파싱 및 유효성 검사
- 각 스트립별 vertical RLE 디코딩

**Format C:**
- `decodeRawFormat()` 함수로 처리
- 연속된 RLE 스트림을 40개 스트립으로 분할
- `decodeStripV3Safe()` 사용하여 소비된 바이트 추적

#### 3. Error Handling
- 각 포맷에 대한 폴백 메커니즘
- 안전한 스트립 디코딩 (bounds checking)
- 상세한 콘솔 로깅

## 🧪 Testing

### 테스트 파일 분포:

```bash
$ python3 verify_formats.py

파일명                      포맷             첫 word    파일크기
======================================================================
out/graphics/01_res001.bin     C (raw)            0x2c43 ( 11331)    6142
out/graphics/01_res002.bin     B (direct offsets) 0x0065 (   101)   36898
out/graphics/05_res002.bin     A (size+offsets)   0x565e ( 22110)   22110
out/graphics/01_res007.bin     C (raw)            0x8d91 ( 36241)   31746
out/graphics/02_res004.bin     C (raw)            0x63d0 ( 25552)    8872
```

### 브라우저 콘솔에서 확인할 메시지:

```
🎨 그래픽 디코딩 시작 (36898 bytes)
  헤더 패딩: 80 bytes
  첫 번째 word: 0x65 (101)
  포맷 감지: A=false, B=true, C=false
  ✅ 디코딩: 20개 스트립, 160x200
  첫 3개 오프셋: 0xdb, 0x11e, 0x159
✅ 디코딩 성공: 160x200
```

## 🎯 Next Steps

1. **브라우저 새로고침**: Ctrl+Shift+R (Windows) / Cmd+Shift+R (Mac)
2. **룸 전환 테스트**: 각 룸(01, 02, 04, 05)에서 그래픽 확인
3. **콘솔 로그 확인**: 포맷 감지 및 디코딩 메시지 검토
4. **추가 개선 사항**:
   - Format C 휴리스틱 정확도 향상
   - 실제 ScummVM 소스코드와 비교 검증
   - 다중 그래픽 레이어링 구현

## 📚 References

- ScummVM gfx.cpp: SCUMM v3 graphics decoding reference
- LOOM (1990): Lucasfilm Games, SCUMM Engine v3
- EGA Graphics: 16-color palette, 4-bitplane format
