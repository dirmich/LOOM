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

1. **extract_resources.py** - LFL 파일 리소스 추출
2. **decode_all_resources_fixed.py** - 배경 이미지 재구성
3. **decode_to_real_files.py** - PNG/WAV 변환
4. **disassemble_scripts.py** - 스크립트 디스어셈블
5. **analyze_resources.py** - 리소스 포맷 분석

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
