# LOOM SCUMM v3 리소스 추출 도구

LOOM (1990) 게임의 SCUMM v3 리소스를 추출하고 실제 파일 포맷으로 변환하는 도구입니다.

## ✅ 완료된 기능

- 🖼️ **배경 이미지**: PNG로 완벽 변환 (73개)
- 📜 **스크립트**: 읽을 수 있는 어셈블리로 디스어셈블 (21개 중 17개)
- 🔊 **사운드**: 포맷 분석 (MIDI 기반, ScummVM 권장)
- 📦 **오브젝트**: 원본 데이터 추출

## 🚀 빠른 시작

### 1. 리소스 추출 및 변환

```bash
# 1단계: LFL 파일에서 리소스 추출
python3 extract_resources.py

# 2단계: 리소스 디코딩 (배경 이미지 재구성)
python3 decode_all_resources_fixed.py

# 3단계: 실제 파일 포맷으로 변환 (PNG, WAV, TXT)
python3 decode_to_real_files.py

# 4단계: 스크립트 디스어셈블 (ScummVM descumm 필요)
python3 disassemble_scripts.py
```

### 2. 결과 확인

```bash
# 배경 이미지 (PNG)
open converted2/room_01/background.png

# 디스어셈블된 스크립트
cat disassembled/room_00/00_res001.txt
```

## 📁 출력 구조

```
out/                      # 1단계: 추출된 원본 리소스
├── _summary.json         # 리소스 메타데이터
├── graphics/
├── sounds/
└── scripts/

decoded2/                 # 2단계: 디코딩된 리소스
├── resources.json
└── room_XX/
    ├── background/
    ├── graphics/
    ├── sounds/
    └── scripts/

converted2/               # 3단계: 실제 파일 포맷
└── room_XX/
    ├── background.png    # 🖼️ PNG 이미지
    ├── sounds/*.wav      # 🔊 WAV (MIDI 데이터, 재생 불가)
    └── graphics/*.bin

disassembled/             # 4단계: 디스어셈블된 스크립트
└── room_XX/
    └── *.txt             # 읽을 수 있는 어셈블리
```

## 🔊 사운드 & 스크립트 한계

### 사운드
- **문제**: MIDI 기반 악기 데이터 (PC Speaker/AdLib)
- **현재**: WAV 생성되지만 재생 불가
- **해결**: ScummVM 사용 권장

### 스크립트
- **문제**: SCUMM v3 바이트코드
- **해결**: descumm 도구로 디스어셈블 (17/21 성공)

## 🎮 게임 플레이

완벽한 사운드와 그래픽으로 플레이하려면:

```bash
# ScummVM 다운로드
# https://www.scummvm.org/

# LOOM 폴더를 ScummVM에 추가
# → 완벽한 재생
```

## 📊 통계

| 타입 | 개수 | 변환 | 비고 |
|------|------|------|------|
| 배경 이미지 | 73 | ✅ PNG | 완벽 |
| 사운드 | 385 | ⚠️ WAV | MIDI 데이터, 재생 불가 |
| 스크립트 | 21 | ✅ TXT | 17개 성공 |
| 오브젝트 | 2931 | 📦 BIN | 원본 유지 |

## 🛠️ 주요 스크립트

### 1. extract_resources.py
**목적**: LFL 파일에서 리소스 추출 및 분류

**기능**:
- XOR 0xFF 암호화 해제
- 엔트로피 기반 리소스 타입 자동 분류
  - graphics (엔트로피 > 0.7, 크기 > 1KB)
  - sounds (엔트로피 > 0.6, 크기 < 2KB)
  - scripts (엔트로피 < 0.3)
  - palettes (크기 16-48 바이트)

**입력**: 현재 디렉토리의 `*.LFL` 파일

**출력**:
- `out/` 디렉토리 (타입별 분류된 리소스)
- `out/_summary.json` (리소스 메타데이터)

**사용법**:
```bash
python3 extract_resources.py
# 대화형 프롬프트: 기존 out/ 디렉토리 삭제 여부 선택
```

---

### 2. decode_all_resources_fixed.py
**목적**: 배경 이미지 재구성 및 리소스 디코딩

**기능**:
- SMAP 기반 배경 이미지 재구성
  - Width/Height 헤더 + Strip offset table + Strip data
  - ScummVM 호환 포맷으로 변환
- 나머지 리소스는 out/에서 복사

**입력**:
- `*.LFL` 파일
- `out/_summary.json` (extract_resources.py 실행 필요)

**출력**:
- `decoded2/` 디렉토리 (Room별 분류)
- `decoded2/resources.json` (전체 리소스 맵)

**사용법**:
```bash
python3 decode_all_resources_fixed.py
# 출력: 73개 배경 이미지 재구성
```

---

### 3. decode_to_real_files.py
**목적**: 실제 파일 포맷으로 변환 (PNG/WAV)

**기능**:
- 배경 이미지 → PNG (EGA 16색 팔레트)
- 사운드 → WAV (⚠️ MIDI 데이터, 재생 불가)
- 스크립트 → TXT (Hex dump, ⚠️ 완전한 디스어셈블 아님)

**요구사항**:
- `pip3 install Pillow` (PNG 생성용)

**입력**: `decoded2/resources.json`

**출력**:
- `converted2/room_XX/background.png` (🖼️ 73개)
- `converted2/room_XX/sounds/*.wav` (⚠️ 재생 불가)

**사용법**:
```bash
python3 decode_to_real_files.py
```

**한계**:
- 사운드: MIDI 기반 데이터, WAV 생성되지만 재생 안됨
- 스크립트: Hex dump만 표시, 완전한 디스어셈블 아님

---

### 4. disassemble_scripts.py
**목적**: SCUMM v3 스크립트를 읽을 수 있는 어셈블리로 변환

**기능**:
- ScummVM descumm 도구 사용
- SCUMM v3 바이트코드 → 읽을 수 있는 어셈블리

**요구사항**:
```bash
# descumm 도구 빌드 필요
cd /tmp
git clone --depth 1 https://github.com/scummvm/scummvm-tools.git
cd scummvm-tools
./configure
make descumm
```

**입력**: `decoded2/resources.json`

**출력**:
- `disassembled/room_XX/*.txt` (17개 성공, 81%)

**사용법**:
```bash
python3 disassemble_scripts.py
```

**결과 예시**:
```
[0000] (0F) if (getState(1) == 0) {
[0006] (00)   stopObjectCode();
[0007] (80)   breakHere();
```

---

### 5. analyze_resources.py
**목적**: 리소스 포맷 분석 및 식별

**기능**:
- 사운드 포맷 식별 (PC Speaker, AdLib, Roland)
- 스크립트 opcode 빈도 분석
- 권장 사항 제공

**입력**: `decoded2/resources.json`

**출력**: 콘솔 리포트 (파일 생성 없음)

**사용법**:
```bash
python3 analyze_resources.py
```

**분석 내용**:
- 사운드: 포맷별 개수 및 예시
- 스크립트: opcode 통계
- 권장: ScummVM 사용, descumm 도구

## 📚 문서

### 분석 문서 (analyze/)
- [SCUMM_V3_포맷_분석.md](./analyze/SCUMM_V3_포맷_분석.md) - 포맷 상세 설명
- [SMAP_이미지_추출_가이드.md](./analyze/SMAP_이미지_추출_가이드.md) - 이미지 추출 가이드
- [리소스_변환_가이드.md](./analyze/리소스_변환_가이드.md) - 변환 가이드
- [최종성공_20251018.md](./analyze/최종성공_20251018.md) - 완성 보고서
- 작업 로그: `analyze/작업로그_*.md`

### 오래된 문서 (docs/)
- SCUMM v3 초기 연구 자료

## 🎨 브라우저 뷰어

```bash
cd tools
bun install
bun run build
bun run serve

# http://localhost:3000
```

## 📝 참고

- **ScummVM**: https://www.scummvm.org/
- **ScummVM-tools**: https://github.com/scummvm/scummvm-tools
- **descumm**: ScummVM-tools의 스크립트 디스어셈블러

## 📅 최종 업데이트

2025-10-18: 스크립트 디스어셈블 완료 및 프로젝트 정리
