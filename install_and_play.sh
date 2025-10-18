#!/bin/bash
# LOOM 게임 설치 및 실행 스크립트

echo "🎮 LOOM 게임 플레이 준비"
echo "=" 

# ScummVM 설치 확인
if ! command -v scummvm &> /dev/null; then
    echo "📦 ScummVM이 설치되어 있지 않습니다."
    echo ""
    echo "설치 방법:"
    echo "  brew install scummvm"
    echo ""
    echo "또는 다운로드:"
    echo "  https://www.scummvm.org/downloads/"
    echo ""
    read -p "지금 Homebrew로 설치하시겠습니까? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 ScummVM 설치 중..."
        brew install scummvm
        
        if [ $? -eq 0 ]; then
            echo "✅ ScummVM 설치 완료!"
        else
            echo "❌ 설치 실패. 수동으로 설치해주세요."
            exit 1
        fi
    else
        echo "설치를 취소했습니다."
        exit 0
    fi
else
    echo "✅ ScummVM이 이미 설치되어 있습니다."
    scummvm --version
fi

echo ""
echo "🎮 LOOM 게임 실행..."
echo ""

# 현재 디렉토리에서 실행
GAME_PATH="$(cd "$(dirname "$0")" && pwd)"

echo "게임 경로: $GAME_PATH"
echo ""

# ScummVM 실행
scummvm --path="$GAME_PATH" loom

echo ""
echo "게임을 종료했습니다."
