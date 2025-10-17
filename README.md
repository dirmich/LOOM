# LOOM LFL 파일 분석 도구

SCUMM v3 (LOOM) LFL 파일을 분석하고 정보를 추출하는 Python 도구입니다.

## 파일 목록

- **scummvm.md** - LFL 파일 포맷 상세 문서
- **lfl_analyzer.py** - Python 분석 도구
- **\*.LFL** - LOOM 게임 리소스 파일

## 빠른 시작

### 1. 단일 파일 분석

```bash
python3 lfl_analyzer.py 01.LFL
```

**출력 예시**:
```
======================================================================
📄 파일: 01.LFL
======================================================================

📊 기본 정보
   타입: room
   크기: 55,213 bytes
   룸 크기: 19866x48128 pixels
   설명: 룸 리소스 파일

📍 리소스 오프셋 테이블
   발견된 오프셋: 20개
   # 1: 위치 0x0004 → 오프셋 0x0140 (   320 bytes)
   # 2: 위치 0x0006 → 오프셋 0x0090 (   144 bytes)
   ...
```

### 2. 전체 디렉토리 분석

```bash
python3 lfl_analyzer.py --all .
```

**출력 예시**:
```
🔍 총 75개 LFL 파일 발견

======================================================================
📊 전체 통계
======================================================================
   총 파일 수: 75개
   총 크기: 1,984,680 bytes (1.89 MB)
   평균 크기: 26,462 bytes
   룸 파일: 74개
```

### 3. 복호화된 파일 저장

```bash
python3 lfl_analyzer.py 01.LFL --export-decrypted
```

생성되는 파일: `01.decrypted` (0xFF XOR 복호화된 원본 데이터)

### 4. 헤더 정보 저장

```bash
python3 lfl_analyzer.py 01.LFL --export-header
```

생성되는 파일: `01.info.txt` (헤더 및 오프셋 정보)

### 5. 모든 정보 추출

```bash
python3 lfl_analyzer.py 01.LFL --export-decrypted --export-header --output ./output
```

## 사용법

```
usage: lfl_analyzer.py [-h] [--all DIR] [--export-decrypted]
                       [--export-header] [--output DIR] [file]

SCUMM LFL 파일 분석 도구 (LOOM)

positional arguments:
  file                  분석할 LFL 파일

optional arguments:
  -h, --help            도움말 표시
  --all DIR             디렉토리 내 모든 LFL 파일 분석
  --export-decrypted    복호화된 데이터를 파일로 저장
  --export-header       헤더 정보를 텍스트 파일로 저장
  --output DIR, -o DIR  출력 디렉토리 (기본: 현재 디렉토리)
```

## 기능

### 분석 기능

- ✅ 0xFF XOR 복호화
- ✅ 룸 헤더 파싱 (너비, 높이)
- ✅ 리소스 오프셋 테이블 추출
- ✅ 데이터 섹션 자동 탐지
- ✅ 엔트로피 기반 데이터 타입 추정
- ✅ 00.LFL 인덱스 파일 분석

### 추출 기능

- ✅ 복호화된 데이터 저장
- ✅ 헤더 및 오프셋 정보 저장
- ✅ 디렉토리 일괄 처리

### 데이터 타입 추정

| 엔트로피 | 추정 타입 |
|---------|----------|
| < 10% | 패딩/단순 데이터 |
| 10-30% | 스크립트/코드 |
| 30-60% | 압축 데이터 |
| > 60% | 그래픽/사운드 |

## 출력 형식

### 기본 정보
- 파일 타입 (index/room)
- 파일 크기
- 룸 크기 (width × height)

### 리소스 오프셋 테이블
- 오프셋 위치
- 리소스 시작 주소
- 리소스 크기

### 데이터 섹션
- 섹션 범위 (시작-끝)
- 섹션 크기
- 헥스 미리보기
- 추정 데이터 타입

### 엔트로피 분석
- 파일을 4개 섹션으로 나누어 분석
- 각 섹션의 엔트로피 퍼센트
- 데이터 타입 추정

## 예제

### 예제 1: 특정 룸 분석

```bash
python3 lfl_analyzer.py 10.LFL
```

### 예제 2: 모든 파일 분석 및 통계

```bash
python3 lfl_analyzer.py --all . > analysis_report.txt
```

### 예제 3: 여러 파일 배치 처리

```bash
for file in 01.LFL 02.LFL 03.LFL; do
    python3 lfl_analyzer.py "$file" --export-decrypted --output ./decrypted
done
```

### 예제 4: 인덱스 파일 분석

```bash
python3 lfl_analyzer.py 00.LFL
```

## Python 코드 예제

### 기본 사용

```python
from lfl_analyzer import LFLAnalyzer

# 파일 분석
analyzer = LFLAnalyzer('01.LFL')
analyzer.analyze()
analyzer.print_report()

# 헤더 정보 접근
print(f"룸 크기: {analyzer.header['width']}x{analyzer.header['height']}")

# 오프셋 접근
for pos, offset in analyzer.offsets:
    print(f"리소스 오프셋: 0x{offset:04x}")
```

### 직접 복호화

```python
# 파일 읽기
with open('01.LFL', 'rb') as f:
    encrypted = f.read()

# 0xFF XOR 복호화
decrypted = bytes([b ^ 0xFF for b in encrypted])

# 헤더 파싱
import struct
width = struct.unpack('<H', decrypted[0:2])[0]
height = struct.unpack('<H', decrypted[2:4])[0]

print(f"룸 크기: {width}x{height}")
```

## 기술 정보

### LFL 파일 구조

```
00.LFL (인덱스)
├─ 매직 헤더: FF FE 17 FC
└─ 리소스 비트맵 테이블

XX.LFL (룸 파일)
├─ [암호화: 0xFF XOR]
├─ 헤더
│  ├─ 룸 너비 (16비트)
│  ├─ 룸 높이 (16비트)
│  └─ 오프셋 테이블 (16비트 배열)
└─ 리소스 데이터
   ├─ 그래픽 (EGA 비트맵)
   ├─ 스크립트 (SCUMM 바이트코드)
   ├─ 사운드
   ├─ 애니메이션
   └─ 팔레트
```

### SCUMM v3 특징

- 청크 태그 없음 (old-style)
- 16비트 주소 체계
- 리틀 엔디안 바이트 순서
- 0xFF XOR 암호화
- 고정 오프셋 기반 구조

## 문서

상세한 파일 포맷 정보는 **scummvm.md** 문서를 참고하세요.

## 요구사항

- Python 3.6 이상
- 표준 라이브러리만 사용 (외부 의존성 없음)

## 라이센스

분석 도구는 교육 및 연구 목적으로 자유롭게 사용할 수 있습니다.

## 참고

- LOOM 게임은 LucasArts의 저작물입니다
- ScummVM: https://www.scummvm.org/
- SCUMM 위키: https://wiki.scummvm.org/

## 개발 정보

- **작성일**: 2025년
- **분석 대상**: LOOM (DOS EGA 버전)
- **SCUMM 버전**: v3
- **도구**: Python 3

---

**분석 완료!** LOOM의 비밀을 탐험하세요! 🎮✨
