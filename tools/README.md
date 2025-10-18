# LOOM 리소스 추출 도구 모음

SCUMM v3 게임 리소스 추출 및 변환 도구들

## 📋 주요 도구

### 1. 리소스 추출 (Extract)

**`extract_resources.py`**
- LOOM LFL 파일에서 리소스 추출 (기본)
- XOR 0xFF 복호화 및 리소스 파싱

**`extract_objects_v3.py`**
- 오브젝트 리소스 위치 및 정보 추출
- 248개 오브젝트 분석 및 분류

### 2. 오브젝트 디코딩 (Objects)

**`decode_objects_v3.py`** ⭐
- 오브젝트 그래픽을 PNG로 변환 (최종 버전)
- 4가지 OBIM 포맷 지원
- 111개 이미지 100% 성공

### 3. 스크립트 디스어셈블 (Scripts)

**`disassemble_scripts.py`**
- SCUMM 스크립트를 descumm으로 디스어셈블
- 17개 스크립트 처리

**`check_scripts_status.py`**
- 스크립트 디스어셈블 상태 확인
- 성공/실패 분석

### 4. 코스튬 분석 (Costumes)

**`find_costumes.py`**
- 00.LFL 리소스 인덱스 분석
- 코스튬 리소스 검색 (LOOM: 0개)

### 5. 사운드 변환 (Sounds)

**`convert_sounds_to_midi.py`**
- Roland MT-32 데이터에 RO 태그 추가
- 385개 .ro 파일 생성 (ScummVM 호환)

**`convert_to_standard_midi.py`** ⭐
- Roland 데이터를 표준 MIDI(.mid)로 변환
- 385개 .mid 파일 생성 (일반 플레이어 호환)

### 6. 카탈로그 생성 (Catalog)

**`create_resource_catalog.py`** ⭐
- 모든 리소스를 HTML 카탈로그로 생성
- 배경, 오브젝트, 스크립트, 사운드 통합 뷰

## 🗂️ 사용 방법

### 기본 추출 워크플로우

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

### 개별 도구 실행

```bash
# 오브젝트 분석
python3 tools/extract_objects_v3.py

# 스크립트 상태 확인
python3 tools/check_scripts_status.py

# 코스튬 찾기
python3 tools/find_costumes.py

# ScummVM용 사운드 변환
python3 tools/convert_sounds_to_midi.py
```

## 📁 출력 디렉토리

| 도구 | 출력 위치 | 파일 수 |
|------|----------|---------|
| extract_resources.py | `decoded2/` | 전체 리소스 |
| decode_objects_v3.py | `objects_png_v3/` | 111개 PNG |
| disassemble_scripts.py | `disassembled/` | 17개 TXT |
| convert_sounds_to_midi.py | `sounds_midi/` | 385개 RO |
| convert_to_standard_midi.py | `sounds_standard_midi/` | 385개 MID |
| create_resource_catalog.py | `resource_catalog.html` | 1개 HTML |

## 🔧 의존성

### 필수
- Python 3.8+
- PIL (Pillow)

### 선택
- descumm (ScummVM 도구) - 스크립트 디스어셈블용

### 설치

```bash
pip install Pillow
```

## 📚 Archive 폴더

`tools/archive/` 폴더에는 개발 과정의 구버전 및 분석 도구들이 보관되어 있습니다:

- 이전 버전 디코더들 (v1, v2)
- 테스트 스크립트
- 분석 도구들
- 실패 분석 스크립트

참고용으로 보관하지만 일반적으로 사용하지 않습니다.

## ✨ 최종 결과

**100% 리소스 추출 완료!**

- ✅ 배경: 73/73 (100%)
- ✅ 오브젝트: 111/111 (100%)
- ✅ 스크립트: 17/17 (100%)
- ✅ 코스튬: 0 (LOOM 특성)
- ✅ 사운드: 385/385 (100%)

**총 971개 출력 파일**
