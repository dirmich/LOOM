/**
 * SCUMM 스크립트 인터프리터
 * SCUMM v3 바이트코드를 실행합니다.
 */

import type { Script } from '../types/resources';

interface GameState {
  variables: number[];
  flags: boolean[];
  currentRoom: number;
  actorPositions: Map<number, { x: number; y: number }>;
}

export class ScriptInterpreter {
  private script: Script | null = null;
  private pc: number = 0; // Program Counter
  private stack: number[] = [];
  private gameState: GameState;
  private isRunning: boolean = false;

  // SCUMM v3 명령어 정의 (부분)
  private static readonly OPCODES = {
    // 기본 명령어
    STOP_SCRIPT: 0x00,
    WAIT_FOR_ACTOR: 0x01,
    WAIT_FOR_MESSAGE: 0x02,
    WAIT_FOR_CAMERA: 0x03,
    WAIT_FOR_SENTENCE: 0x04,

    // 제어 흐름
    JUMP: 0x18,
    JUMP_IF_NOT_ZERO: 0x19,
    JUMP_IF_ZERO: 0x1A,

    // 변수 조작
    SET_VAR: 0x40,
    GET_VAR: 0x41,
    INC_VAR: 0x42,
    DEC_VAR: 0x43,

    // 액터 제어
    ACTOR_OPS: 0x13,

    // 룸 제어
    LOAD_ROOM: 0x72,

    // 그래픽
    DRAW_OBJECT: 0x05,

    // 사운드
    START_SOUND: 0x1C,
    STOP_SOUND: 0x1D,
  } as const;

  constructor() {
    this.gameState = {
      variables: new Array(256).fill(0),
      flags: new Array(256).fill(false),
      currentRoom: 1,
      actorPositions: new Map(),
    };
  }

  /**
   * 스크립트 로드
   */
  loadScript(data: Uint8Array): void {
    this.script = {
      code: data,
      offset: 0
    };
    this.pc = 0;
    this.stack = [];
  }

  /**
   * 스크립트 실행 (단계별)
   */
  async step(): Promise<boolean> {
    if (!this.script || this.pc >= this.script.code.length) {
      return false;
    }

    const opcode = this.readByte();
    await this.executeOpcode(opcode);

    return this.isRunning;
  }

  /**
   * 스크립트 실행 (전체)
   */
  async run(maxSteps: number = 1000): Promise<void> {
    this.isRunning = true;
    let steps = 0;

    while (this.isRunning && steps < maxSteps) {
      const canContinue = await this.step();
      if (!canContinue) break;
      steps++;
    }

    console.log(`스크립트 실행 완료: ${steps} 단계`);
  }

  /**
   * 명령어 실행
   */
  private async executeOpcode(opcode: number): Promise<void> {
    console.log(`[0x${this.pc.toString(16)}] Opcode: 0x${opcode.toString(16)}`);

    switch (opcode) {
      case ScriptInterpreter.OPCODES.STOP_SCRIPT:
        this.isRunning = false;
        break;

      case ScriptInterpreter.OPCODES.SET_VAR: {
        const varNum = this.readByte();
        const value = this.readWord();
        this.gameState.variables[varNum] = value;
        console.log(`  SET_VAR: var[${varNum}] = ${value}`);
        break;
      }

      case ScriptInterpreter.OPCODES.GET_VAR: {
        const varNum = this.readByte();
        const value = this.gameState.variables[varNum];
        this.stack.push(value);
        console.log(`  GET_VAR: var[${varNum}] => ${value}`);
        break;
      }

      case ScriptInterpreter.OPCODES.JUMP: {
        const offset = this.readWord();
        this.pc = offset;
        console.log(`  JUMP: -> 0x${offset.toString(16)}`);
        break;
      }

      case ScriptInterpreter.OPCODES.LOAD_ROOM: {
        const roomNum = this.readByte();
        this.gameState.currentRoom = roomNum;
        console.log(`  LOAD_ROOM: ${roomNum}`);
        break;
      }

      case ScriptInterpreter.OPCODES.START_SOUND: {
        const soundNum = this.readByte();
        console.log(`  START_SOUND: ${soundNum}`);
        // 사운드 재생 로직 (GameEngine과 연동)
        break;
      }

      default:
        console.log(`  Unknown opcode: 0x${opcode.toString(16)}`);
        // 알 수 없는 명령어는 건너뛰기
        break;
    }
  }

  /**
   * 1바이트 읽기
   */
  private readByte(): number {
    if (!this.script || this.pc >= this.script.code.length) {
      return 0;
    }
    return this.script.code[this.pc++];
  }

  /**
   * 2바이트 읽기 (리틀 엔디안)
   */
  private readWord(): number {
    const low = this.readByte();
    const high = this.readByte();
    return low | (high << 8);
  }

  /**
   * 게임 상태 가져오기
   */
  getGameState(): GameState {
    return {
      ...this.gameState,
      variables: [...this.gameState.variables],
      flags: [...this.gameState.flags],
      actorPositions: new Map(this.gameState.actorPositions),
    };
  }

  /**
   * 변수 설정
   */
  setVariable(index: number, value: number): void {
    this.gameState.variables[index] = value;
  }

  /**
   * 변수 가져오기
   */
  getVariable(index: number): number {
    return this.gameState.variables[index];
  }

  /**
   * 스크립트 중지
   */
  stop(): void {
    this.isRunning = false;
  }

  /**
   * 스크립트 리셋
   */
  reset(): void {
    this.pc = 0;
    this.stack = [];
    this.isRunning = false;
  }
}
