# LOOM LFL 파일 포맷 분석 문서

## 개요

LFL (LucasArts File) 포맷은 SCUMM 엔진의 리소스 컨테이너 파일 형식입니다.
LOOM (1990)은 SCUMM v3를 사용하며, 오래된 스타일의 바이너리 구조를 가지고 있습니다.

- **게임**: Loom (1990)
- **엔진**: SCUMM v3 (Script Creation Utility for Maniac Mansion)
- **개발사**: Lucasfilm Games (LucasArts)
- **버전**: Interpreter 3.5.37, 3.5.40
- **플랫폼**: DOS (EGA/VGA)
- **배포**: 3×720KB 플로피 또는 6×360KB 플로피

---

## 암호화/인코딩

### 0xFF XOR 암호화

모든 LFL 파일(00.LFL 제외)은 0xFF XOR 암호화가 적용되어 있습니다.

- **방식**: 각 바이트에 0xFF를 XOR 연산
- **목적**: 간단한 데이터 보호 및 난독화
- **복호화**: `decrypted_byte = encrypted_byte ^ 0xFF`

**예시**:
```
원본:  0x65 XOR 0xFF = 0x9A
복호화: 0x9A XOR 0xFF = 0x65
```

---

## 파일 구조

### 1. 00.LFL - 마스터 인덱스 파일

**기본 정보**:
- 크기: 5,748 bytes
- 용도: 리소스 디렉토리 및 매핑 테이블
- 암호화: 없음 (일반 바이너리)

**구조**:
```
[0x0000-0x0003] 매직 헤더: FF FE 17 FC
[0x0004-EOF   ] 리소스 비트맵 테이블
```

**비트맵 인코딩**:
| 값 | 의미 |
|----|------|
| 0xFF | 리소스 없음 |
| 0xF0 | 특수 마커 |
| 0x7F | 부분 리소스 |
| 0xFD/0xFE | 특정 리소스 타입 |
| 기타 | 리소스 플래그 및 위치 정보 |

---

### 2. XX.LFL - 룸 리소스 파일 (01-99)

**기본 정보**:
- 크기: 14KB ~ 58KB (룸마다 다름)
- 용도: 특정 룸의 모든 리소스 포함
- 암호화: 0xFF XOR

**복호화 후 구조**:

#### 헤더 섹션 (32-64 bytes)

```
오프셋 0x00-0x01: [16비트] 룸 너비 (예: 0x0140 = 320px)
오프셋 0x02-0x03: [16비트] 룸 높이
오프셋 0x04+:     [16비트 배열] 리소스 오프셋 테이블
```

#### 리소스 데이터 블록

- 스크립트 코드 (SCUMM 바이트코드)
- 그래픽 데이터 (EGA/VGA 비트맵)
- 오브젝트 정의
- 사운드 샘플
- 팔레트 정보
- 코스튬 애니메이션 데이터

---

## 리소스 오프셋 테이블

### 구조

- **위치**: 헤더 섹션 (오프셋 0x04부터 시작)
- **형식**: 16비트 리틀 엔디안 정수 배열
- **목적**: 각 리소스의 파일 내 위치 지정

### 예시 (01.LFL)

```
오프셋 0x0004 → 리소스 위치 0x0140 (320 bytes)
오프셋 0x0006 → 리소스 위치 0x0090 (144 bytes)
오프셋 0x000c → 리소스 위치 0x188e (6286 bytes)
```

---

## 리소스 타입

### 1. 그래픽 리소스 (엔트로피: 80-96%)

- EGA 16색 비트맵
- 평면(planar) 포맷
- RLE 압축 가능
- 룸 배경, 오브젝트 스프라이트

### 2. 스크립트 (엔트로피: 30-60%)

- SCUMM 바이트코드
- 조건문, 루프, 이벤트 처리
- 대화 로직

### 3. 코스튬 (애니메이션)

- 캐릭터 애니메이션 프레임
- 프레임 순서 정의
- 타이밍 정보

### 4. 사운드 (엔트로피: 70-95%)

- 효과음, 음악
- PC 스피커 또는 AdLib/Roland

### 5. 팔레트

- 16색 EGA 팔레트 매핑
- RGB 값 정의

---

## 데이터 블록 구조

### 01.LFL 예시

```
섹션 #1: 0x000000-0x00188d (6,285 bytes)  [메인 헤더 + 그래픽]
섹션 #2: 0x0018de-0x001942 (  100 bytes)  [오브젝트 정의]
섹션 #3: 0x00194b-0x0019ba (  111 bytes)  [오브젝트 정의]
섹션 #4: 0x0019c3-0x001a73 (  176 bytes)  [스크립트]
섹션 #5: 0x001a7c-0x001b46 (  202 bytes)  [스크립트]
...
섹션 #8: 0x001c98-0x002cb3 (4,123 bytes)  [대용량 그래픽]
```

**구분자**: 연속된 0x00 바이트 (8+ bytes)

---

## SCUMM v3 특징

### 핵심 특성

- ❌ 청크 태그 없음 (나중 버전의 'RO', 'SC' 등 없음)
- ✅ 고정 오프셋 기반 구조
- ✅ 16비트 주소 체계
- ✅ 간단한 0xFF XOR 암호화
- ✅ 리틀 엔디안 바이트 순서
- ✅ Old-style 룸 포맷

### 후기 버전과의 차이

| 특징 | SCUMM v3 (LOOM) | SCUMM v5+ |
|------|-----------------|-----------|
| 청크 태그 | 없음 | 있음 (RO, SC, CO 등) |
| 주소 체계 | 16비트 | 32비트 |
| 암호화 | 0xFF XOR | 0x69 XOR 또는 없음 |
| 구조 | 고정 오프셋 | 청크 기반 |

---

## 코드 예제

### Python으로 LFL 파일 읽기

```python
import struct

def read_lfl_file(filename):
    """LFL 파일을 읽고 복호화합니다."""
    with open(filename, 'rb') as f:
        encrypted = f.read()

    # 0xFF XOR 복호화
    decrypted = bytes([b ^ 0xFF for b in encrypted])

    return decrypted

def parse_room_header(data):
    """룸 헤더를 파싱합니다."""
    if len(data) < 4:
        return None

    width = struct.unpack('<H', data[0:2])[0]
    height = struct.unpack('<H', data[2:4])[0]

    return {
        'width': width,
        'height': height
    }

def extract_offsets(data, start=4, count=10):
    """리소스 오프셋 테이블을 추출합니다."""
    offsets = []

    for i in range(start, min(start + count * 2, len(data)), 2):
        offset = struct.unpack('<H', data[i:i+2])[0]
        if 32 < offset < len(data):
            offsets.append(offset)

    return offsets

# 사용 예시
data = read_lfl_file('01.LFL')
header = parse_room_header(data)
print(f"Room size: {header['width']}x{header['height']}")

offsets = extract_offsets(data)
print(f"Resource offsets: {offsets}")
```

### C로 LFL 파일 읽기

```c
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    unsigned short width;
    unsigned short height;
} RoomHeader;

void decrypt_xor(unsigned char *data, size_t size) {
    for (size_t i = 0; i < size; i++) {
        data[i] ^= 0xFF;
    }
}

RoomHeader parse_header(unsigned char *data) {
    RoomHeader header;
    header.width = data[0] | (data[1] << 8);   // Little-endian
    header.height = data[2] | (data[3] << 8);
    return header;
}

int main() {
    FILE *fp = fopen("01.LFL", "rb");
    if (!fp) return 1;

    fseek(fp, 0, SEEK_END);
    size_t size = ftell(fp);
    fseek(fp, 0, SEEK_SET);

    unsigned char *data = malloc(size);
    fread(data, 1, size, fp);
    fclose(fp);

    decrypt_xor(data, size);

    RoomHeader header = parse_header(data);
    printf("Room size: %dx%d\n", header.width, header.height);

    free(data);
    return 0;
}
```

---

## 분석 도구

### 권장 도구

- **ScummVM**: 게임 실행 및 디버깅
- **Scumm Revisited 2/5**: 리소스 추출/편집
- **ScummVM Tools**: 리소스 변환
- **HxD / 010 Editor**: 헥스 에디터

### 커맨드라인 분석

```bash
# 헥스 덤프
hexdump -C 01.LFL | head -20

# 파일 타입 확인
file *.LFL

# 문자열 추출
strings 01.LFL

# XOR 복호화 (xxd 사용)
xxd -p 01.LFL | xxd -r -p | tr '\000-\377' '\377-\000' > 01.decrypted

# Python으로 빠른 분석
python3 -c "
import sys
data = open('01.LFL', 'rb').read()
dec = bytes([b^0xFF for b in data])
print(f'Width: {int.from_bytes(dec[0:2], \"little\")}')
print(f'Height: {int.from_bytes(dec[2:4], \"little\")}')
"
```

---

## 파일 목록 및 통계

### LOOM 디렉토리 구성

```
00.LFL - 5.6KB   (인덱스)
01.LFL - 54KB    (룸 1)
02.LFL - 57KB    (룸 2)
03.LFL - 14KB    (룸 3)
04.LFL - 33KB    (룸 4)
...
99.LFL - 크기가변 (룸 99)
```

### 통계

- **총 파일 수**: 74개
- **총 크기**: 약 2.2MB
- **파일 크기 범위**: 5.6KB ~ 58KB
- **평균 파일 크기**: 약 30KB

---

## 엔트로피 분석

### 데이터 타입별 엔트로피

| 데이터 타입 | 엔트로피 범위 | 특징 |
|------------|--------------|------|
| 그래픽 | 80-96% | 높은 엔트로피, 다양한 픽셀 값 |
| 사운드 | 70-95% | 중상 엔트로피, 샘플 데이터 |
| 스크립트 | 30-60% | 낮은 엔트로피, 반복되는 명령 |
| 팔레트 | 20-40% | 낮은 엔트로피, 제한된 값 |

### 파일 섹션별 분석 (01.LFL)

```
섹션 1 (0x000000-0x0035eb): 96.09% 엔트로피 → 그래픽/사운드
섹션 2 (0x0035eb-0x006bd6): 95.31% 엔트로피 → 그래픽/사운드
섹션 3 (0x006bd6-0x00a1c1): 78.91% 엔트로피 → 그래픽/사운드
섹션 4 (0x00a1c1-0x00d7ac): 82.81% 엔트로피 → 그래픽/사운드
```

---

## 참고 자료

### 공식 문서

- [ScummVM 공식 사이트](https://www.scummvm.org/)
- [SCUMM 위키](https://wiki.scummvm.org/index.php/SCUMM)

### 기술 문서

- ScummVM 소스 코드: `engines/scumm/resource.cpp`
- LFL 추출 도구: `scummvm-tools/engines/scumm/`

### 커뮤니티

- [ScummVM 포럼](https://forums.scummvm.org/)
- [SCUMM 개발자 메일링 리스트](https://www.scummvm.org/contact/)

---

## 요약

LFL 파일은 SCUMM 게임의 리소스 아카이브 파일입니다:

1. **00.LFL** = 마스터 인덱스 (비트맵 기반 리소스 맵)
2. **XX.LFL** = 룸별 리소스 컨테이너 (0xFF XOR 암호화)
3. **헤더** = 룸 크기 + 리소스 오프셋 테이블 (16비트)
4. **데이터** = 그래픽, 스크립트, 사운드, 애니메이션
5. **구조** = 오래된 고정 오프셋 방식 (태그 없음)

ScummVM이 이 파일들을 읽어 게임을 실행하며, 직접 분석하거나 수정할 수 있습니다.

---

**작성일**: 2025년
**분석 대상**: LOOM (DOS EGA 버전)
**도구**: Python 3, hexdump, ScummVM
