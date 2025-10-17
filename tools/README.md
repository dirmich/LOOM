# LOOM SCUMM v3 게임 엔진

Bun.sh + TypeScript로 구현한 SCUMM v3 게임 엔진입니다.

## 🎮 기능

### 구현 완료
- ✅ **LFL 파일 파싱** - 리소스 추출 및 분류
- ✅ **EGA 팔레트 관리** - 16색 팔레트 지원
- ✅ **그래픽 렌더링** - Canvas API로 비트맵 렌더링
- ✅ **사운드 재생** - Web Audio API로 PC 스피커 에뮬레이션
- ✅ **스크립트 인터프리터** - SCUMM 바이트코드 기본 실행
- ✅ **게임 엔진** - 통합 엔진 및 룸 관리

### 진행 중
- ⚠️ **스크립트 실행** - 전체 SCUMM 명령어 구현
- ⚠️ **입력 처리** - 마우스/키보드 입력

### 예정
- ❌ **완전한 게임 플레이** - 전체 게임 로직
- ❌ **세이브/로드** - 게임 상태 저장
- ❌ **최적화** - 성능 개선

## 📁 프로젝트 구조

```
tools/
├── package.json              # 프로젝트 설정
├── tsconfig.json             # TypeScript 설정
├── server.ts                 # 개발 서버
├── index.html                # 메인 HTML
├── src/
│   ├── main.ts              # 엔트리 포인트
│   ├── types/
│   │   └── resources.ts     # 타입 정의
│   └── engine/
│       ├── GameEngine.ts    # 메인 게임 엔진
│       ├── PaletteManager.ts # 팔레트 관리
│       ├── GraphicsRenderer.ts # 그래픽 렌더링
│       ├── SoundPlayer.ts   # 사운드 재생
│       └── ScriptInterpreter.ts # 스크립트 실행
└── README.md
```

## 🚀 시작하기

### 1. 의존성 설치

```bash
bun install
```

### 2. 개발 서버 실행

```bash
bun run serve
```

서버가 시작되면 브라우저에서 http://localhost:3000 을 엽니다.

### 3. 게임 시작

1. "게임 시작" 버튼 클릭
2. 룸 선택 드롭다운으로 다른 룸 탐험
3. 브라우저 콘솔에서 `gameEngine` 객체로 직접 제어

## 🔧 개발

### 빌드

```bash
bun run build
```

빌드된 파일은 `dist/` 디렉토리에 생성됩니다.

### 개발 모드 (watch)

```bash
bun run dev
```

파일 변경 시 자동으로 재실행됩니다.

## 🎯 사용 예시

### 브라우저 콘솔에서

```javascript
// 룸 변경
await gameEngine.loadRoom(5);

// 비프음 재생
await gameEngine.playBeep();

// 게임 상태 확인
const state = gameEngine.getGameState();
console.log(state);

// 렌더러 접근
const renderer = gameEngine.getRenderer();
renderer.setScale(3);

// 사운드 볼륨 조절
const soundPlayer = gameEngine.getSoundPlayer();
soundPlayer.setVolume(0.8);

// 스크립트 인터프리터 접근
const interpreter = gameEngine.getScriptInterpreter();
console.log(interpreter.getVariable(0));
```

## 📊 리소스 데이터

게임 엔진은 `../out/` 디렉토리의 추출된 리소스를 사용합니다:

```
out/
├── _summary.json          # 전체 리소스 요약
├── XX_metadata.json       # 각 룸별 메타데이터
├── graphics/              # 그래픽 리소스
├── sounds/                # 사운드 리소스
├── scripts/               # 스크립트 리소스
├── palettes/              # 팔레트 리소스
└── unknown/               # 미분류 리소스
```

## 🏗️ 아키텍처

### 컴포넌트

1. **PaletteManager**
   - EGA 16색 팔레트 관리
   - RGB 변환 (0-63 → 0-255)

2. **GraphicsRenderer**
   - Canvas 2D API 사용
   - EGA 비트맵 렌더링
   - 픽셀 아트 스타일 유지

3. **SoundPlayer**
   - Web Audio API 사용
   - PC 스피커 에뮬레이션
   - ADSR 엔벨로프

4. **ScriptInterpreter**
   - SCUMM v3 바이트코드 실행
   - 변수 및 플래그 관리
   - 게임 상태 추적

5. **GameEngine**
   - 모든 컴포넌트 통합
   - 리소스 로딩 관리
   - 룸 전환 처리

## 🔍 디버깅

### 콘솔 로그

모든 컴포넌트는 콘솔에 상세한 로그를 출력합니다:

```
🎮 SCUMM 게임 엔진 초기화 완료
📊 게임 데이터 로드 완료: 543개 리소스
🚪 룸 1 로딩 중...
🎨 팔레트 로드: 01_res001.bin
🖼️  그래픽 렌더링: 01_res002.bin at (0, 0)
📜 스크립트 로드: 01_res003.bin
✅ 룸 1 로딩 완료
```

### 브라우저 개발자 도구

1. F12로 개발자 도구 열기
2. Console 탭에서 로그 확인
3. `gameEngine` 객체로 직접 제어
4. Network 탭에서 리소스 로딩 확인

## 📚 참고 자료

- [ScummVM 공식 사이트](https://www.scummvm.org/)
- [SCUMM 위키](https://wiki.scummvm.org/index.php/SCUMM)
- [SCUMM Technical Reference](https://wiki.scummvm.org/index.php/SCUMM/Technical_Reference)
- [Bun 공식 문서](https://bun.sh/docs)
- [Canvas API](https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)

## 🤝 기여

이 프로젝트는 학습 목적으로 만들어졌습니다. 개선 사항이나 버그를 발견하시면 이슈를 남겨주세요!

## 📝 라이센스

이 프로젝트는 교육 및 연구 목적으로 자유롭게 사용할 수 있습니다.
LOOM 게임은 LucasArts의 저작물입니다.

## 🎯 다음 단계

1. **전체 SCUMM 명령어 구현**
   - 현재: 기본 명령어만 구현
   - 목표: 모든 SCUMM v3 명령어 지원

2. **입력 처리**
   - 마우스 클릭 감지
   - 키보드 입력 처리
   - 게임 인터랙션

3. **게임 로직**
   - 액터 이동
   - 대화 시스템
   - 인벤토리 관리

4. **최적화**
   - 리소스 캐싱
   - 렌더링 성능 개선
   - 메모리 관리

---

**만든 날짜**: 2025년
**버전**: 0.1.0
**엔진**: SCUMM v3
**게임**: LOOM (1990)
