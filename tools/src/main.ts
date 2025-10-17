/**
 * SCUMM 게임 엔진 메인 엔트리 포인트
 */

import { GameEngine } from './engine/GameEngine';

// 전역 변수로 엔진 인스턴스 저장
let gameEngine: GameEngine | null = null;

/**
 * 게임 초기화
 */
async function initGame(): Promise<void> {
  console.log('🎮 LOOM SCUMM 엔진 시작...');

  const canvas = document.getElementById('gameCanvas') as HTMLCanvasElement;
  if (!canvas) {
    console.error('Canvas 요소를 찾을 수 없습니다!');
    return;
  }

  try {
    // 게임 엔진 생성
    gameEngine = new GameEngine(canvas);

    // 게임 데이터 로드
    await gameEngine.loadGameData();

    // 첫 번째 룸 로드
    await gameEngine.loadRoom(1);

    // 전역 객체로 노출 (디버깅용)
    (window as any).gameEngine = gameEngine;

    console.log('✅ 게임 초기화 완료!');
    console.log('💡 콘솔에서 gameEngine 객체를 사용할 수 있습니다.');

    // 상태 표시 업데이트
    updateStatus();
  } catch (error) {
    console.error('게임 초기화 실패:', error);
    showError('게임 초기화에 실패했습니다. 콘솔을 확인하세요.');
  }
}

/**
 * 상태 표시 업데이트
 */
function updateStatus(): void {
  if (!gameEngine) return;

  const statusElement = document.getElementById('status');
  if (statusElement) {
    const state = gameEngine.getGameState();
    statusElement.textContent = `Room: ${state.currentRoom} | Resources: ${state.totalResources}`;
  }
}

/**
 * 에러 표시
 */
function showError(message: string): void {
  const statusElement = document.getElementById('status');
  if (statusElement) {
    statusElement.textContent = `❌ ${message}`;
    statusElement.style.color = 'red';
  }
}

/**
 * 룸 변경
 */
async function changeRoom(roomNumber: number): Promise<void> {
  if (!gameEngine) return;

  try {
    await gameEngine.loadRoom(roomNumber);
    updateStatus();
  } catch (error) {
    console.error('룸 로드 실패:', error);
  }
}

/**
 * 비프음 재생 (테스트)
 */
async function testBeep(): Promise<void> {
  if (!gameEngine) return;
  await gameEngine.playBeep();
}

// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', () => {
  // 초기화 버튼
  const initButton = document.getElementById('initButton');
  if (initButton) {
    initButton.addEventListener('click', initGame);
  }

  // 룸 선택
  const roomSelect = document.getElementById('roomSelect') as HTMLSelectElement;
  if (roomSelect) {
    roomSelect.addEventListener('change', (e) => {
      const roomNumber = parseInt((e.target as HTMLSelectElement).value);
      changeRoom(roomNumber);
    });
  }

  // 테스트 버튼
  const beepButton = document.getElementById('beepButton');
  if (beepButton) {
    beepButton.addEventListener('click', testBeep);
  }

  console.log('📱 UI 이벤트 리스너 등록 완료');
});

// 전역 함수 노출 (디버깅용)
(window as any).changeRoom = changeRoom;
(window as any).testBeep = testBeep;
(window as any).initGame = initGame;
