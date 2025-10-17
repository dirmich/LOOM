/**
 * 그래픽 렌더러
 * SCUMM EGA 비트맵을 Canvas에 렌더링합니다.
 */

import type { Bitmap } from '../types/resources';
import { PaletteManager } from './PaletteManager';
import { ScummV3Decoder } from './ScummV3Decoder';

export class GraphicsRenderer {
  private canvas: HTMLCanvasElement;
  public ctx: CanvasRenderingContext2D; // public으로 변경
  private paletteManager: PaletteManager;
  private scale: number = 2;

  constructor(canvas: HTMLCanvasElement, paletteManager: PaletteManager) {
    this.canvas = canvas;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      throw new Error('Canvas 2D context를 가져올 수 없습니다.');
    }
    this.ctx = ctx;
    this.paletteManager = paletteManager;

    // 픽셀 아트를 위한 설정
    this.ctx.imageSmoothingEnabled = false;
  }

  /**
   * 비트맵 데이터 렌더링
   */
  async renderBitmap(data: Uint8Array, x: number = 0, y: number = 0): Promise<void> {
    try {
      console.log(`🎨 그래픽 디코딩 시작 (${data.length} bytes)`);

      // SCUMM v3 디코더 사용
      const decoded = ScummV3Decoder.decodeObjectImage(data);

      if (decoded) {
        const bitmap: Bitmap = {
          width: decoded.width,
          height: decoded.height,
          data: decoded.pixels
        };
        this.drawBitmap(bitmap, x, y);
        console.log(`✅ 디코딩 성공: ${decoded.width}x${decoded.height}`);
      } else {
        console.warn('디코딩 실패 - Hex dump 표시');
        this.drawHexDump(data, x, y);
      }
    } catch (error) {
      console.error('비트맵 렌더링 실패:', error);
      this.drawHexDump(data, x, y);
    }
  }

  /**
   * 비트맵 데이터 파싱 (SCUMM v3 형식)
   */
  private parseBitmap(data: Uint8Array): Bitmap {
    // SCUMM v3는 복잡한 스트립 기반 압축 포맷 사용
    // 완전한 디코딩은 복잡하므로 기본 헤더만 파싱

    let width = 320;
    let height = 200;

    // 헤더에서 정보 추출 시도
    if (data.length >= 4) {
      // SCUMM v3 Object Image 헤더 구조
      // 처음 바이트들이 스트립 오프셋 테이블
      const numStrips = data[0];

      if (numStrips > 0 && numStrips <= 40) {
        // 스트립 개수로 너비 추정 (각 스트립은 8픽셀)
        width = numStrips * 8;
      }

      // 파일 크기로 높이 추정
      if (data.length < 1000) {
        height = 64;
      } else if (data.length < 5000) {
        height = 128;
      } else if (data.length < 20000) {
        height = 144;
      } else {
        height = 200;
      }
    }

    console.log(`  📐 추정 크기: ${width}x${height}, 데이터: ${data.length} bytes, 첫 바이트: 0x${data[0].toString(16)}`);
    return { width, height, data };
  }

  /**
   * 비트맵을 Canvas에 그리기
   */
  private drawBitmap(bitmap: Bitmap, x: number, y: number): void {
    const { width, height, data } = bitmap;

    // ImageData 생성
    const imageData = this.ctx.createImageData(width, height);
    const pixels = imageData.data;

    // EGA 평면(planar) 포맷 디코딩
    // 간단한 버전: 각 바이트를 팔레트 인덱스로 직접 사용
    for (let i = 0; i < Math.min(data.length, width * height); i++) {
      const paletteIndex = data[i] & 0x0F; // 4비트 컬러
      const [r, g, b, a] = this.paletteManager.getColorRGBA(paletteIndex);

      const pixelIndex = i * 4;
      pixels[pixelIndex] = r;
      pixels[pixelIndex + 1] = g;
      pixels[pixelIndex + 2] = b;
      pixels[pixelIndex + 3] = a;
    }

    // 스케일 적용하여 그리기
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = width;
    tempCanvas.height = height;
    const tempCtx = tempCanvas.getContext('2d')!;
    tempCtx.putImageData(imageData, 0, 0);

    this.ctx.drawImage(
      tempCanvas,
      x, y,
      width * this.scale,
      height * this.scale
    );
  }

  /**
   * Hex dump 표시 (디버깅용)
   */
  private drawHexDump(data: Uint8Array, x: number, y: number): void {
    this.ctx.fillStyle = '#000';
    this.ctx.fillRect(x, y, 600, 350);

    this.ctx.fillStyle = '#0f0';
    this.ctx.font = '9px monospace';

    // 헤더 정보
    this.ctx.fillText(`SCUMM 그래픽 데이터 (${data.length} bytes)`, x + 10, y + 15);
    this.ctx.fillText(`첫 바이트 (스트립 수?): ${data[0]} (0x${data[0].toString(16)})`, x + 10, y + 30);

    // Hex dump
    const lines = Math.min(25, Math.floor(data.length / 16));
    for (let i = 0; i < lines; i++) {
      const offset = i * 16;
      const bytes = Array.from(data.slice(offset, offset + 16))
        .map(b => b.toString(16).padStart(2, '0'))
        .join(' ');

      this.ctx.fillText(
        `${offset.toString(16).padStart(4, '0')}: ${bytes}`,
        x + 10,
        y + 50 + i * 12
      );
    }

    // 경고 메시지
    this.ctx.fillStyle = '#ff0';
    this.ctx.fillText('⚠️ SCUMM v3 압축 포맷 - 완전한 디코더 필요', x + 10, y + 340);
  }

  /**
   * 화면 지우기
   */
  clear(): void {
    this.ctx.fillStyle = '#000';
    this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
  }

  /**
   * 스케일 설정
   */
  setScale(scale: number): void {
    this.scale = scale;
  }

  /**
   * Canvas 크기 조정
   */
  resize(width: number, height: number): void {
    this.canvas.width = width;
    this.canvas.height = height;
  }
}
