/**
 * 사운드 플레이어
 * SCUMM 사운드 리소스를 Web Audio API로 재생합니다.
 */

import type { Sound } from '../types/resources';

export class SoundPlayer {
  private audioContext: AudioContext | null = null;
  private masterVolume: number = 0.5;
  private isInitialized: boolean = false;

  constructor() {
    // AudioContext는 사용자 인터랙션 후 초기화
  }

  /**
   * AudioContext 초기화
   */
  private async initAudioContext(): Promise<void> {
    if (this.isInitialized) return;

    try {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      this.isInitialized = true;
      console.log('AudioContext 초기화 완료');
    } catch (error) {
      console.error('AudioContext 초기화 실패:', error);
    }
  }

  /**
   * 사운드 데이터 재생
   */
  async playSound(data: Uint8Array): Promise<void> {
    await this.initAudioContext();

    if (!this.audioContext) {
      console.warn('AudioContext가 초기화되지 않았습니다.');
      return;
    }

    try {
      const sound = this.parseSound(data);
      await this.playParsedSound(sound);
    } catch (error) {
      console.error('사운드 재생 실패:', error);
    }
  }

  /**
   * 사운드 데이터 파싱
   */
  private parseSound(data: Uint8Array): Sound {
    // SCUMM v3 사운드 포맷 간단 파싱
    // PC 스피커 또는 AdLib 데이터

    // 기본값
    let frequency = 440; // A4
    let duration = 1.0;

    // 간단한 휴리스틱: 데이터 패턴으로 주파수 추정
    if (data.length >= 4) {
      // 첫 2바이트로 주파수 추정
      const freqValue = (data[0] | (data[1] << 8)) & 0xFFFF;
      if (freqValue > 100 && freqValue < 20000) {
        frequency = freqValue;
      }

      // 길이로 재생 시간 추정
      duration = Math.min(5.0, data.length / 1000);
    }

    return { frequency, duration, data };
  }

  /**
   * 파싱된 사운드 재생
   */
  private async playParsedSound(sound: Sound): Promise<void> {
    if (!this.audioContext) return;

    const { frequency, duration } = sound;
    const now = this.audioContext.currentTime;

    // 오실레이터 생성
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.type = 'square'; // PC 스피커 스타일
    oscillator.frequency.setValueAtTime(frequency, now);

    // 볼륨 엔벨로프 (ADSR)
    gainNode.gain.setValueAtTime(0, now);
    gainNode.gain.linearRampToValueAtTime(this.masterVolume, now + 0.01); // Attack
    gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.7, now + 0.1); // Decay
    gainNode.gain.linearRampToValueAtTime(this.masterVolume * 0.7, now + duration - 0.1); // Sustain
    gainNode.gain.linearRampToValueAtTime(0, now + duration); // Release

    // 연결
    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    // 재생
    oscillator.start(now);
    oscillator.stop(now + duration);
  }

  /**
   * PC 스피커 비프음 재생 (테스트용)
   */
  async playBeep(frequency: number = 440, duration: number = 0.2): Promise<void> {
    await this.initAudioContext();

    if (!this.audioContext) return;

    const now = this.audioContext.currentTime;
    const oscillator = this.audioContext.createOscillator();
    const gainNode = this.audioContext.createGain();

    oscillator.type = 'square';
    oscillator.frequency.setValueAtTime(frequency, now);

    gainNode.gain.setValueAtTime(this.masterVolume, now);
    gainNode.gain.linearRampToValueAtTime(0, now + duration);

    oscillator.connect(gainNode);
    gainNode.connect(this.audioContext.destination);

    oscillator.start(now);
    oscillator.stop(now + duration);
  }

  /**
   * 볼륨 설정
   */
  setVolume(volume: number): void {
    this.masterVolume = Math.max(0, Math.min(1, volume));
  }

  /**
   * 볼륨 가져오기
   */
  getVolume(): number {
    return this.masterVolume;
  }

  /**
   * 정리
   */
  async dispose(): Promise<void> {
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
      this.isInitialized = false;
    }
  }
}
