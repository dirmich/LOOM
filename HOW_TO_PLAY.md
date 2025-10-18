# LOOM 게임 플레이 가이드

## 🎮 게임 실행 방법

### 1. ScummVM 설치

**macOS (Homebrew 사용):**
```bash
brew install scummvm
```

**또는 직접 다운로드:**
- https://www.scummvm.org/downloads/
- macOS용 DMG 파일 다운로드 및 설치

### 2. LOOM 게임 추가

**방법 1: GUI 사용**
1. ScummVM 실행
2. "Add Game..." 버튼 클릭
3. 이 폴더(`/Users/dirmich/work/0.game/LOOM`) 선택
4. "Choose" 클릭

**방법 2: 커맨드라인**
```bash
# ScummVM 실행 (현재 디렉토리에서)
scummvm --path=/Users/dirmich/work/0.game/LOOM loom

# 또는 간단히
cd /Users/dirmich/work/0.game/LOOM
scummvm loom
```

### 3. 게임 설정

**그래픽 모드:**
- EGA (16색) - 원본 버전
- VGA (256색) - 향상된 그래픽 (파일이 있는 경우)

**사운드:**
- Roland MT-32 (최고 음질) - 에뮬레이션 지원
- AdLib
- PC Speaker

**자막:**
- 영어 자막 활성화 권장

### 4. 게임 플레이

**기본 조작:**
- 마우스로 화면 클릭하여 상호작용
- 드래프트(마법) 시스템 사용
- 인벤토리 관리

**세이브/로드:**
- F5: 세이브/로드 메뉴
- F1: 도움말
- ESC: 메인 메뉴

## 🎵 사운드 설정

### Roland MT-32 사운드 사용 (권장)

ScummVM은 Roland MT-32를 자동으로 에뮬레이션합니다:

1. ScummVM 설정에서 "Music Device" → "MT-32 Emulator" 선택
2. 또는 `~/.scummvmrc` 파일에 추가:
```ini
[loom]
music_driver=mt32
```

### 우리가 추출한 MIDI 파일은?

추출한 MIDI 파일(`sounds_standard_midi/`)은 분석/보관용입니다:
- 게임은 원본 LFL 파일의 사운드를 직접 사용
- ScummVM이 자동으로 Roland MT-32 데이터를 처리
- 추출된 MIDI는 별도 플레이어로 들을 수 있음

## 📁 필요한 파일

게임 실행에 필요한 파일들 (모두 현재 디렉토리에 있음):
```
00.LFL - 리소스 인덱스
01.LFL ~ 99.LFL - 게임 데이터
DISK01.LEC - 레코드 파일 (선택)
```

## 🎯 빠른 시작

**한 줄로 설치 + 실행:**
```bash
brew install scummvm && scummvm --path=/Users/dirmich/work/0.game/LOOM loom
```

## 🔧 문제 해결

### "Game not found" 오류
- 00.LFL 파일이 있는 디렉토리에서 실행
- Game ID는 `loom` 사용

### 사운드가 안 들림
- ScummVM 설정에서 "Audio" 확인
- Roland MT-32 에뮬레이션 활성화

### 화면이 이상함
- 그래픽 필터 설정 확인
- Aspect ratio correction 활성화

## 📚 참고

**ScummVM 공식 문서:**
- https://docs.scummvm.org/

**LOOM Wiki:**
- https://scummvm.org/games/#games:loom

**우리 프로젝트:**
- 리소스 추출: 100% 완료
- 카탈로그: `resource_catalog.html`
- 도구: `tools/` 디렉토리

## 🎮 즐거운 게임 되세요!

LOOM은 1990년 LucasArts의 걸작 어드벤처 게임입니다.
드래프트(음악 기반 마법) 시스템으로 퍼즐을 풀어나가세요!
