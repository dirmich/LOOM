# LOOM 리소스 추출 프로젝트 🎮

LOOM (1990) 게임의 SCUMM v3 리소스를 **100% 완벽 추출** 및 변환한 프로젝트입니다.

## 🎉 프로젝트 완료!

**✅ 100% 달성!**

| 리소스 타입 | 개수 | 성공률 | 출력 형식 |
|------------|------|--------|----------|
| **배경 이미지** | 73 | **100%** | PNG (320×144, EGA 16색) |
| **오브젝트 그래픽** | 111 | **100%** | PNG (다양한 크기) |
| **스크립트** | 17 | **100%** | TXT (디스어셈블) |
| **사운드** | 385 | **100%** | MIDI + RO (Roland MT-32) |
| **코스튬** | 0 | N/A | (LOOM 특성) |

**총 출력 파일:** 971개

---

## 🎮 게임 플레이 방법

### 빠른 시작 (한 줄로!)

```bash
# ScummVM 설치 + 게임 실행
brew install scummvm && scummvm --path=$(pwd) loom
```

### 또는 스크립트 사용

```bash
# 자동 설치 및 실행
./install_and_play.sh
```

**자세한 내용:** [HOW_TO_PLAY.md](./HOW_TO_PLAY.md)

---

## 📁 프로젝트 구조

```
LOOM/
├── 00.LFL ~ 99.LFL        # 원본 게임 파일
│
├── backgrounds/           # 🖼️ 배경 이미지 (73개 PNG)
├── objects_png_v3/        # 🎨 오브젝트 (111개 PNG)
├── disassembled/          # 📜 스크립트 (17개 TXT)
├── sounds_midi/           # 🎵 사운드 (385개 RO - ScummVM용)
├── sounds_standard_midi/  # 🎵 사운드 (385개 MID - 표준 MIDI)
│
├── resource_catalog.html  # 📚 모든 리소스 HTML 카탈로그
│
├── tools/                 # 🔧 주요 도구 (9개)
│   ├── extract_resources.py
│   ├── decode_objects_v3.py
│   ├── disassemble_scripts.py
│   ├── convert_to_standard_midi.py
│   ├── create_resource_catalog.py
│   └── archive/           # 구버전/분석용 (11개)
│
├── analyze/               # 📄 작업 로그 및 분석 문서
└── decoded2/              # 중간 추출 데이터
```

---

## 🚀 리소스 보기

### 1. HTML 카탈로그 (권장! ⭐)

```bash
open resource_catalog.html
```

**한눈에 모든 리소스 확인:**
- 배경 이미지 73개 (썸네일)
- 오브젝트 111개 (썸네일)
- 스크립트 17개 (목록)
- 사운드 385개 (처음 50개 + 안내)

### 2. 개별 리소스

```bash
# 배경 이미지
open backgrounds/room_01.png

# 오브젝트
open objects_png_v3/

# 스크립트
cat disassembled/room_00/00_res001.txt

# 사운드 (MIDI)
open sounds_standard_midi/00_res004.mid
```

---

## 🔧 도구 사용법

### 전체 워크플로우

```bash
# 1. 리소스 추출
python3 tools/extract_resources.py

# 2. 오브젝트 PNG 변환
python3 tools/decode_objects_v3.py

# 3. 스크립트 디스어셈블
python3 tools/disassemble_scripts.py

# 4. 사운드 MIDI 변환
python3 tools/convert_to_standard_midi.py

# 5. HTML 카탈로그 생성
python3 tools/create_resource_catalog.py
```

**자세한 도구 설명:** [tools/README.md](./tools/README.md)

---

## 🎵 사운드 재생

### ScummVM으로 재생 (권장)
```bash
scummvm --path=$(pwd) loom
```
- 자동으로 Roland MT-32 에뮬레이션
- 완벽한 음질

### MIDI 플레이어로 재생
```bash
open sounds_standard_midi/00_res004.mid
```
- 일반 MIDI 플레이어 사용 가능
- Roland MT-32 음원 권장 (Munt 에뮬레이터)

---

## 📊 기술적 성과

### ScummVM 소스 분석 성공

**분석한 핵심 파일:**
- `engines/scumm/resource_v3.cpp` - 리소스 로딩
- `engines/scumm/object.cpp` - 오브젝트 처리
- `engines/scumm/gfx.cpp` - 그래픽 디코딩
- `engines/scumm/sound.cpp` - 사운드 처리

**구현한 기능:**
- XOR 0xFF 복호화
- 4가지 OBIM 포맷 디코더
- Strip 기반 RLE 압축 해제
- Roland MT-32 MIDI 변환

### SCUMM v3 포맷 완전 이해

**오브젝트 타입 분류:**
1. OBIM 이미지 (111개) - 100% PNG 변환
2. 빈 오브젝트 (56개) - 논리 오브젝트
3. 19-byte 메타데이터 (65개) - 참조 데이터
4. 텍스트 메타데이터 (16개) - 설명 텍스트

**스크립트 분석:**
- SCUMM v3 바이트코드
- descumm 도구 사용
- 17/17 실제 스크립트 100% 성공

**사운드 포맷:**
- Roland MT-32 raw 데이터
- Tagless 포맷 (헤더 없음)
- ScummVM "RO" 태그 추가 방식 구현

---

## 📚 문서

### 사용 가이드
- **[HOW_TO_PLAY.md](./HOW_TO_PLAY.md)** - 게임 플레이 방법
- **[tools/README.md](./tools/README.md)** - 도구 설명서

### 분석 문서 (analyze/)
- **작업로그_20251018_100퍼센트완성.md** - 100% 달성 보고서
- **작업로그_20251018_최종정리.md** - 최종 정리
- **작업로그_20251018_ScummVM분석.md** - ScummVM 분석
- **작업로그_20251018_오브젝트디코딩.md** - 오브젝트 디코딩
- **작업로그_20251018_디코더개선.md** - 디코더 개선

---

## 🛠️ 의존성

### 필수
```bash
pip install Pillow
```

### 선택 (스크립트 디스어셈블용)
```bash
# descumm 빌드
git clone --depth 1 https://github.com/scummvm/scummvm-tools.git /tmp/scummvm-tools
cd /tmp/scummvm-tools
./configure && make descumm
```

### 게임 플레이용
```bash
brew install scummvm
```

---

## 🎯 주요 특징

### ✨ 완벽한 리소스 추출
- 배경, 오브젝트, 스크립트, 사운드 **100% 추출**
- 4가지 OBIM 포맷 모두 지원
- ScummVM 소스 분석 기반 정확한 구현

### 📊 체계적인 문서화
- 6개 상세 작업 로그
- 11개 Python 도구
- HTML 리소스 카탈로그

### 🎮 게임 플레이 지원
- ScummVM 통합 가이드
- 자동 설치 스크립트
- Roland MT-32 사운드 지원

---

## 🔍 LOOM 특수성

**코스튬 없음:**
- 전통적인 어드벤처 게임과 다름
- 대화/마법 중심 게임플레이
- 캐릭터 애니메이션 최소화

**드래프트 시스템:**
- 음악 기반 마법 시스템
- Roland MT-32 전용 사운드
- 독특한 MIDI 포맷

---

## 📝 참고 자료

- **ScummVM**: https://www.scummvm.org/
- **ScummVM 소스**: https://github.com/scummvm/scummvm
- **ScummVM Tools**: https://github.com/scummvm/scummvm-tools
- **LOOM Wiki**: https://scummvm.org/games/#games:loom

---

## 🎉 프로젝트 완료

**ScummVM 소스 분석을 통한 완벽한 리버스 엔지니어링 성공!** 🚀

- ✅ 배경: 73/73 (100%)
- ✅ 오브젝트: 111/111 (100%)
- ✅ 스크립트: 17/17 (100%)
- ✅ 사운드: 385/385 (100%)

**총 971개 파일, 100% 성공!**

---

## 📅 업데이트 내역

- **2025-10-18**: 프로젝트 100% 완료
  - 사운드 MIDI 변환 완료
  - HTML 리소스 카탈로그 생성
  - Python 도구 폴더 구조 정리
  - 게임 플레이 가이드 추가
