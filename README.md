# LOOM SCUMM v3 브라우저 뷰어

LOOM (1990) 게임의 SCUMM v3 엔진 데이터를 브라우저에서 볼 수 있는 도구입니다.

## 📋 프로젝트 구조

```
LOOM/
├── *.LFL           # LOOM 게임 데이터 파일 (LucasFilm Library)
├── LOOM.EXE        # 원본 실행 파일
├── tools/          # 브라우저 뷰어
│   ├── src/
│   │   ├── engine/
│   │   │   ├── ScummV3Decoder.ts    # SCUMM v3 EGA 그래픽 디코더
│   │   │   ├── GameEngine.ts        # 게임 엔진 코어
│   │   │   ├── GraphicsRenderer.ts  # 그래픽 렌더러
│   │   │   ├── PaletteManager.ts    # EGA 팔레트 관리
│   │   │   ├── ScriptInterpreter.ts # 스크립트 인터프리터
│   │   │   └── SoundPlayer.ts       # 사운드 플레이어
│   │   ├── types/
│   │   │   └── resources.ts         # 타입 정의
│   │   └── main.ts                  # 메인 진입점
│   ├── index.html   # 브라우저 UI
│   ├── server.ts    # 개발 서버
│   └── package.json # 의존성 설정
├── out/            # 추출된 리소스 파일 (자동 생성)
└── README.md       # 이 파일
```

## 🚀 시작하기

### 1. 필수 요구사항

- **Python 3**: 리소스 추출용
  ```bash
  python3 --version  # 3.6 이상
  ```

- **Bun**: JavaScript 런타임 및 빌드 도구
  ```bash
  curl -fsSL https://bun.sh/install | bash
  ```

- **LOOM 게임 파일**: `*.LFL` 파일들과 `LOOM.EXE`가 프로젝트 루트에 있어야 합니다
  - 00.LFL ~ 99.LFL (일부 번호는 없을 수 있음)
  - LOOM.EXE

### 2. 리소스 추출

LFL 파일에서 게임 리소스를 추출합니다:

```bash
python3 extract_resources.py
```

이 스크립트는:
- *.LFL 파일을 XOR 복호화 (0xFF)
- 각 리소스 블록 추출
- 엔트로피 기반 타입 분류 (graphics, sounds, scripts, palettes, unknown)
- `out/` 디렉토리에 타입별로 정리
- `out/_summary.json` 생성 (메타데이터)

출력 구조:
```
out/
├── _summary.json
├── graphics/
│   ├── 01_res001.bin
│   ├── 01_res002.bin
│   └── ...
├── sounds/
├── scripts/
├── palettes/
└── unknown/
```

### 3. 의존성 설치

```bash
cd tools
bun install
```

### 3. 빌드

TypeScript 코드를 브라우저용 JavaScript로 컴파일합니다:

```bash
bun run build
```

이 명령은:
- `src/` 폴더의 TypeScript 코드를 컴파일
- `dist/main.js` 파일 생성 (브라우저에서 실행 가능)

### 4. 개발 서버 실행

```bash
bun run serve
```

서버가 시작되면:
```
🚀 서버 시작: http://localhost:3000
📁 게임 데이터: ../out/
🎮 브라우저에서 http://localhost:3000 을 열어주세요!
```

### 5. 브라우저에서 보기

1. 브라우저에서 http://localhost:3000 열기
2. 콘솔 로그에서 디코딩 과정 확인 가능 (F12 → Console)
3. 좌우 화살표 키로 룸(Room) 전환

## 🎮 사용법

### 키보드 단축키

- **← (왼쪽 화살표)**: 이전 룸
- **→ (오른쪽 화살표)**: 다음 룸
- **1-9**: 특정 룸으로 이동

### 콘솔 명령

브라우저 개발자 도구 콘솔(F12)에서 사용 가능:

```javascript
// 특정 룸 로드
gameEngine.loadRoom(5)

// 현재 룸 정보
gameEngine.currentRoom

// 리소스 정보
gameEngine.resourceIndex
```

## 🔧 개발

### 코드 수정 후 재빌드

1. TypeScript 코드 수정
2. 재빌드:
   ```bash
   bun run build
   ```
3. 브라우저에서 **Cmd+Shift+R** (Mac) 또는 **Ctrl+F5** (Windows)로 하드 리프레시

### 빠른 개발 사이클

```bash
# 파일 변경 감지 + 자동 재빌드 (watch 모드는 직접 설정 필요)
bun run build && bun run serve
```

## 📊 기술 상세

### SCUMM v3 EGA 그래픽 포맷

SCUMM v3는 8픽셀 너비의 세로 스트립(strip) 단위로 그래픽을 저장합니다:

#### 3-Mode RLE 압축 (ScummVM drawStripEGA)

1. **Mode 1 (0x00-0x7F)**: 단색 런
   - 상위 4비트: 길이 (0이면 다음 바이트에서 읽음)
   - 하위 4비트: 색상 (0-15, EGA 16색)

2. **Mode 2 (0x80-0xBF)**: 이전 픽셀 반복
   - 하위 6비트: 길이 (0이면 다음 바이트에서 읽음)
   - 왼쪽 열의 같은 y 좌표 픽셀 복사

3. **Mode 3 (0xC0-0xFF)**: 2색 디더링
   - 하위 6비트: 길이 (0이면 다음 바이트에서 읽음)
   - 다음 바이트: 2개 색상 (상위/하위 4비트)
   - 홀수 픽셀은 상위, 짝수 픽셀은 하위 색상

#### 스트립 디코딩 과정

1. 8픽셀 × 높이 버퍼 생성
2. y=0, x=0부터 시작
3. RLE 코드 읽어서 픽셀 채우기
4. y가 높이 도달하면 y=0, x++ (다음 열로)
5. x가 8 도달하면 스트립 완료

### LFL 파일 구조

```
LFL File (LucasFilm Library)
├── Index Section (0x00 ~ ...)
│   └── Room offset table
├── Room 1
│   ├── Header (크기, 높이, 너비 등)
│   ├── Image Data (오프셋 테이블 + 압축된 스트립 데이터)
│   ├── Object Data
│   ├── Script Data
│   └── Sound Data
├── Room 2
├── ...
```

#### 암호화

- 모든 LFL 파일은 **XOR 0xFF**로 암호화
- 서버가 파일 읽을 때 자동으로 복호화

### 높이 추정 알고리즘

파일 크기와 스트립 개수로 높이 추정:

```typescript
bytesPerStrip = fileSize / numStrips

if bytesPerStrip < 100  → height = 64
if bytesPerStrip < 200  → height = 88
if bytesPerStrip < 400  → height = 128
if bytesPerStrip < 800  → height = 144  (LOOM 대부분 룸)
else                    → height = 200
```

## 🐛 트러블슈팅

### 그래픽이 세로 줄무늬로 나타남

- **원인**: 오프셋 테이블 파싱 실패
- **해결**: 콘솔 로그 확인 → 어느 단계에서 break되는지 확인
- **디버그**: `ScummV3Decoder.ts`의 오프셋 파싱 로그 참고

### 빌드 후에도 변경사항이 반영 안 됨

1. 브라우저 캐시 문제:
   ```
   Cmd+Shift+R (Mac) 또는 Ctrl+F5 (Windows)
   ```

2. 서버 재시작:
   ```bash
   # 기존 서버 종료 (Ctrl+C)
   bun run serve
   ```

3. dist/ 폴더 완전 삭제 후 재빌드:
   ```bash
   rm -rf dist && bun run build
   ```

### 서버가 시작 안 됨 (포트 이미 사용 중)

```bash
# 포트 3000 사용 중인 프로세스 찾기
lsof -ti:3000

# 종료
kill $(lsof -ti:3000)

# 또는 다른 포트 사용 (server.ts 수정)
```

## 📚 참고 자료

- [ScummVM Source Code](https://github.com/scummvm/scummvm) - SCUMM 엔진 레퍼런스 구현
- [SCUMM v3 Formats](./SCUMM_V3_FORMATS.md) - 상세 포맷 문서
- [ScummVM Wiki](./scummvm.md) - ScummVM 관련 정보

## 📝 라이선스

이 프로젝트는 LOOM 게임 데이터를 분석하고 표시하기 위한 교육 목적 도구입니다.
LOOM 게임의 저작권은 LucasArts/Disney에 있습니다.

## 🔄 업데이트 히스토리

### 2025-10-17
- ✅ ScummVM의 정확한 `drawStripEGA` 알고리즘 구현
- ✅ 3-mode RLE 압축 지원 (단색/반복/디더링)
- ✅ 오프셋 계산 버그 수정
- ✅ 높이 추정 개선 (144px 지원)
- ✅ 디버그 로깅 강화
