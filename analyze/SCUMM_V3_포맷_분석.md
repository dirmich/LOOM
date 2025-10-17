# SCUMM v3 포맷 분석 및 개선 방향

## 🔊 사운드 포맷

### 현재 문제
- 모든 사운드를 raw PCM으로 가정하여 WAV 변환
- 실제로는 재생되지 않는 노이즈만 발생

### 실제 포맷
SCUMM v3 사운드는 다음 중 하나:

1. **SPK (PC Speaker)**
   - PC Speaker beeps
   - MIDI 기반 포맷으로 인코딩
   - 주파수와 지속시간 데이터

2. **ADL (AdLib)**
   - FM 합성 (OPL2 칩)
   - MIDI 기반 포맷
   - 레지스터 명령어 (`0xBD` 등)

3. **ROL (Roland MT-32)**
   - MIDI 데이터
   - 외부 MIDI 장치용

### 데이터 구조 (추정)
```
"SPK " or "ADL " or "ROL "  // 4 bytes - 블록 타입
[size]                       // 4 bytes - 데이터 크기
[MIDI-like data]             // variable - 실제 음악 데이터
```

### 해결 방법

#### 옵션 1: ScummVM으로 재생
LOOM을 ScummVM에서 실행하면 원본 사운드를 들을 수 있습니다.

#### 옵션 2: MIDI 변환 (고급)
1. 사운드 포맷 식별 (SPK/ADL/ROL)
2. MIDI 데이터 추출
3. 표준 MIDI 파일(.mid)로 변환
4. 적절한 소프트 신디사이저로 렌더링

#### 옵션 3: ScummVM 소스 활용
- `scummvm/engines/scumm/sound.cpp` 참고
- PC Speaker/AdLib 에뮬레이터 구현
- WAV로 렌더링

## 📜 스크립트 포맷

### 현재 문제
- Hex dump만 표시
- 읽을 수 없는 바이트 코드

### 실제 포맷
SCUMM v3 바이트코드:
- **Opcode** (1 byte): 명령어 타입
- **Parameters** (word/byte): 파라미터
- Opcode의 비트 패턴으로 파라미터 타입 결정
  - `opcode & 0x80`: 파라미터가 변수인지 상수인지
  - `opcode & 0x40`: 추가 플래그

### 예시
```
0F 00 00 80  → opcode 0x0F + 파라미터들
```

### 해결 방법

#### 옵션 1: ScummVM descumm 도구 사용 (권장)
```bash
# ScummVM-tools 설치
git clone https://github.com/scummvm/scummvm-tools.git
cd scummvm-tools
./configure
make

# SCUMM v3 스크립트 디스어셈블
./descumm -3 script.bin > script.txt
```

**장점**:
- 완전하고 검증된 도구
- 모든 SCUMM v3 opcode 지원
- 바로 사용 가능

#### 옵션 2: 자체 디스어셈블러 구현 (고급)
1. SCUMM v3 opcode 테이블 작성
2. Python 디스어셈블러 구현
3. 읽기 쉬운 어셈블리 출력

**참고 소스**:
- `scummvm-tools/engines/scumm/descumm.cpp`
- `scummvm/engines/scumm/script_v3.cpp`

## 🎯 권장 해결책

### 단기 (즉시 적용 가능)

#### 1. ScummVM descumm 사용
```python
import subprocess

def disassemble_script(script_path, output_path):
    """descumm 도구로 스크립트 디스어셈블"""
    result = subprocess.run(
        ['descumm', '-3', script_path],
        capture_output=True,
        text=True
    )

    with open(output_path, 'w') as f:
        f.write(result.stdout)
```

#### 2. 사운드 포맷 식별
```python
def identify_sound_format(data):
    """사운드 포맷 식별"""
    if len(data) < 8:
        return 'unknown'

    # 블록 헤더 확인
    header = data[:4].decode('ascii', errors='ignore')

    if header == 'SPK ':
        return 'pc_speaker'
    elif header == 'ADL ':
        return 'adlib'
    elif header == 'ROL ':
        return 'roland'
    else:
        # 구버전 포맷 (헤더 없음)
        # 휴리스틱 분석 필요
        return 'unknown'
```

### 장기 (고급 구현)

#### 1. SCUMM v3 디스어셈블러 구현
- Opcode 테이블 완성
- 파라미터 파싱 로직
- 읽기 쉬운 출력

#### 2. 사운드 변환기 구현
- PC Speaker → WAV (주파수 생성)
- AdLib → MIDI → WAV (OPL 에뮬레이션)
- 또는 표준 MIDI 파일 생성

## 📊 현실적 제안

### 즉시 개선 가능
1. **스크립트**: descumm 도구 통합
2. **사운드**: 포맷 식별 및 안내 메시지

### 완전한 해결 (시간 필요)
1. **스크립트**: Python 디스어셈블러 구현
2. **사운드**: OPL 에뮬레이터 + WAV 렌더링

## 🔗 참고 자료

- [ScummVM Wiki - Sound Resources](https://wiki.scummvm.org/index.php?title=SCUMM/Technical_Reference/Sound_resources)
- [ScummVM-tools descumm](https://github.com/scummvm/scummvm-tools/blob/master/engines/scumm/descumm.cpp)
- [SCUMM Bytecode Deep Dive](https://tonick.net/p/2021/03/a-deep-dive-into-the-scumm-bytecode/)
- [ScummVM Sound Source](https://github.com/scummvm/scummvm/blob/master/engines/scumm/sound.cpp)
