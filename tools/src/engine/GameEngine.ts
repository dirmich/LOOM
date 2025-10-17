/**
 * SCUMM 게임 엔진
 * 모든 컴포넌트를 통합하여 게임을 실행합니다.
 */

import type { Summary, RoomMetadata, ResourceMetadata } from '../types/resources';
import { PaletteManager } from './PaletteManager';
import { GraphicsRenderer } from './GraphicsRenderer';
import { SoundPlayer } from './SoundPlayer';
import { ScriptInterpreter } from './ScriptInterpreter';

export class GameEngine {
  private paletteManager: PaletteManager;
  private renderer: GraphicsRenderer;
  private soundPlayer: SoundPlayer;
  private scriptInterpreter: ScriptInterpreter;

  private summary: Summary | null = null;
  private currentRoom: number = 1;
  private resourceBasePath: string = '../out';

  constructor(canvas: HTMLCanvasElement, resourceBasePath: string = '../out') {
    this.resourceBasePath = resourceBasePath;

    this.paletteManager = new PaletteManager();
    this.renderer = new GraphicsRenderer(canvas, this.paletteManager);
    this.soundPlayer = new SoundPlayer();
    this.scriptInterpreter = new ScriptInterpreter();

    console.log('🎮 SCUMM 게임 엔진 초기화 완료');
  }

  /**
   * 게임 데이터 로드
   */
  async loadGameData(): Promise<void> {
    try {
      const response = await fetch(`${this.resourceBasePath}/_summary.json`);
      this.summary = await response.json();
      console.log(`📊 게임 데이터 로드 완료: ${this.summary.total_resources}개 리소스`);
    } catch (error) {
      console.error('게임 데이터 로드 실패:', error);
      throw error;
    }
  }

  /**
   * 룸 로드
   */
  async loadRoom(roomNumber: number): Promise<void> {
    if (!this.summary) {
      throw new Error('게임 데이터가 로드되지 않았습니다.');
    }

    // 룸 메타데이터 찾기
    const roomFile = this.summary.files.find(f => f.file === roomNumber.toString().padStart(2, '0'));
    if (!roomFile) {
      console.warn(`룸 ${roomNumber}을(를) 찾을 수 없습니다.`);
      return;
    }

    console.log(`🚪 룸 ${roomNumber} 로딩 중...`);
    this.currentRoom = roomNumber;

    // 화면 초기화
    this.renderer.clear();

    // 리소스 로드 및 렌더링
    await this.loadRoomResources(roomFile);

    console.log(`✅ 룸 ${roomNumber} 로딩 완료`);
  }

  /**
   * 룸 리소스 로드
   */
  private async loadRoomResources(roomFile: RoomMetadata): Promise<void> {
    console.log(`📦 리소스 요약: ${roomFile.total}개 총 리소스`);
    console.log(`   🖼️  그래픽: ${roomFile.graphics}개`);
    console.log(`   🔊 사운드: ${roomFile.sounds}개`);
    console.log(`   📜 스크립트: ${roomFile.scripts}개`);
    console.log(`   🎨 팔레트: ${roomFile.palettes}개`);
    console.log(`   ❓ 미분류: ${roomFile.unknown}개`);

    // 1. 팔레트 로드
    const paletteResources = roomFile.resources.filter(r => r.type === 'palettes');
    if (paletteResources.length > 0) {
      for (const res of paletteResources) {
        await this.loadPalette(res);
      }
    } else {
      console.log('🎨 팔레트 없음 - 기본 EGA 팔레트 사용');
    }

    // 2. 그래픽 로드 및 렌더링
    const graphicsResources = roomFile.resources.filter(r => r.type === 'graphics');
    console.log(`🖼️  그래픽 리소스 목록:`);
    graphicsResources.slice(0, 5).forEach((res, idx) => {
      console.log(`   [${idx}] ${res.filename} - ${res.size} bytes (entropy: ${res.entropy})`);
    });

    // 첫 번째 큰 그래픽 렌더링 (배경)
    if (graphicsResources.length > 0) {
      // 가장 큰 그래픽 찾기 (보통 배경)
      const largestGraphic = graphicsResources.reduce((prev, curr) =>
        curr.size > prev.size ? curr : prev
      );
      console.log(`🖼️  배경 이미지 렌더링: ${largestGraphic.filename}`);
      await this.loadGraphics(largestGraphic, 0, 0);
    }

    // 3. 스크립트 로드 (첫 번째만)
    const scriptResources = roomFile.resources.filter(r => r.type === 'scripts');
    if (scriptResources.length > 0) {
      await this.loadScript(scriptResources[0]);
      console.log(`📜 스크립트 정보:`);
      scriptResources.forEach((res, idx) => {
        console.log(`   [${idx}] ${res.filename} - ${res.size} bytes`);
      });
    }

    // 4. 사운드 정보
    const soundResources = roomFile.resources.filter(r => r.type === 'sounds');
    if (soundResources.length > 0) {
      console.log(`🔊 사운드 리소스 목록:`);
      soundResources.forEach((res, idx) => {
        console.log(`   [${idx}] ${res.filename} - ${res.size} bytes`);
      });
    }

    // 5. 리소스 정보 오버레이 (선택적)
    // this.drawResourceInfo(roomFile);
  }

  /**
   * 팔레트 로드
   */
  private async loadPalette(resource: ResourceMetadata): Promise<void> {
    try {
      const response = await fetch(`${this.resourceBasePath}/${resource.path}`);
      const buffer = await response.arrayBuffer();
      const data = new Uint8Array(buffer);

      await this.paletteManager.loadPalette(data);
      console.log(`🎨 팔레트 로드: ${resource.filename}`);
    } catch (error) {
      console.error('팔레트 로드 실패:', error);
    }
  }

  /**
   * 그래픽 로드
   */
  private async loadGraphics(resource: ResourceMetadata, x: number, y: number): Promise<void> {
    try {
      const response = await fetch(`${this.resourceBasePath}/${resource.path}`);
      const buffer = await response.arrayBuffer();
      const data = new Uint8Array(buffer);

      await this.renderer.renderBitmap(data, x, y);
      console.log(`🖼️  그래픽 렌더링: ${resource.filename} at (${x}, ${y})`);
    } catch (error) {
      console.error('그래픽 로드 실패:', error);
    }
  }

  /**
   * 스크립트 로드
   */
  private async loadScript(resource: ResourceMetadata): Promise<void> {
    try {
      const response = await fetch(`${this.resourceBasePath}/${resource.path}`);
      const buffer = await response.arrayBuffer();
      const data = new Uint8Array(buffer);

      this.scriptInterpreter.loadScript(data);
      console.log(`📜 스크립트 로드: ${resource.filename}`);

      // 스크립트 실행 (디버깅용)
      // await this.scriptInterpreter.run(100);
    } catch (error) {
      console.error('스크립트 로드 실패:', error);
    }
  }

  /**
   * 사운드 재생
   */
  async playSound(resourceId: number): Promise<void> {
    if (!this.summary) return;

    const roomFile = this.summary.files.find(f => f.file === this.currentRoom.toString().padStart(2, '0'));
    if (!roomFile) return;

    const soundResource = roomFile.resources.find(r => r.type === 'sounds' && r.id === resourceId);
    if (!soundResource) {
      console.warn(`사운드 리소스 ${resourceId}를 찾을 수 없습니다.`);
      return;
    }

    try {
      const response = await fetch(`${this.resourceBasePath}/${soundResource.path}`);
      const buffer = await response.arrayBuffer();
      const data = new Uint8Array(buffer);

      await this.soundPlayer.playSound(data);
      console.log(`🔊 사운드 재생: ${soundResource.filename}`);
    } catch (error) {
      console.error('사운드 재생 실패:', error);
    }
  }

  /**
   * 비프음 재생 (테스트용)
   */
  async playBeep(): Promise<void> {
    await this.soundPlayer.playBeep(800, 0.2);
  }

  /**
   * 게임 상태 가져오기
   */
  getGameState() {
    return {
      currentRoom: this.currentRoom,
      scriptState: this.scriptInterpreter.getGameState(),
      totalResources: this.summary?.total_resources || 0,
    };
  }

  /**
   * 렌더러 가져오기
   */
  getRenderer(): GraphicsRenderer {
    return this.renderer;
  }

  /**
   * 사운드 플레이어 가져오기
   */
  getSoundPlayer(): SoundPlayer {
    return this.soundPlayer;
  }

  /**
   * 스크립트 인터프리터 가져오기
   */
  getScriptInterpreter(): ScriptInterpreter {
    return this.scriptInterpreter;
  }

  /**
   * 리소스 정보를 Canvas에 표시
   */
  private drawResourceInfo(roomFile: RoomMetadata): void {
    const ctx = this.renderer.ctx;

    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, 640, 400);

    ctx.fillStyle = '#0f0';
    ctx.font = 'bold 20px monospace';
    ctx.fillText(`ROOM ${roomFile.file}`, 20, 40);

    ctx.font = '14px monospace';
    let y = 80;

    ctx.fillText(`📦 총 리소스: ${roomFile.total}개`, 20, y);
    y += 30;

    ctx.fillText(`🖼️  그래픽: ${roomFile.graphics}개`, 20, y);
    y += 25;
    ctx.fillText(`🔊 사운드: ${roomFile.sounds}개`, 20, y);
    y += 25;
    ctx.fillText(`📜 스크립트: ${roomFile.scripts}개`, 20, y);
    y += 25;
    ctx.fillText(`🎨 팔레트: ${roomFile.palettes}개`, 20, y);
    y += 25;
    ctx.fillText(`❓ 미분류: ${roomFile.unknown}개`, 20, y);
    y += 40;

    // 리소스 목록
    ctx.font = '12px monospace';
    ctx.fillStyle = '#0ff';
    ctx.fillText('리소스 목록 (처음 10개):', 20, y);
    y += 25;

    ctx.fillStyle = '#0a0';
    ctx.font = '11px monospace';
    roomFile.resources.slice(0, 10).forEach((res, idx) => {
      const typeIcon = res.type === 'graphics' ? '🖼️' :
                       res.type === 'sounds' ? '🔊' :
                       res.type === 'scripts' ? '📜' :
                       res.type === 'palettes' ? '🎨' : '❓';
      const sizeKB = (res.size / 1024).toFixed(1);
      ctx.fillText(`${typeIcon} ${res.filename} (${sizeKB} KB)`, 20, y);
      y += 18;
    });

    // 도움말
    y = 370;
    ctx.fillStyle = '#ff0';
    ctx.font = '10px monospace';
    ctx.fillText('⚠️ SCUMM v3 그래픽 디코더 구현 필요 - 현재는 리소스 정보만 표시', 20, y);
  }

  /**
   * 정리
   */
  async dispose(): Promise<void> {
    await this.soundPlayer.dispose();
    console.log('🛑 게임 엔진 종료');
  }
}
