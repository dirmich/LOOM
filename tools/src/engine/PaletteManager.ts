/**
 * EGA 팔레트 관리자
 * 16색 EGA 팔레트를 관리하고 RGB 변환을 처리합니다.
 */

import type { EGAPalette } from '../types/resources';

export class PaletteManager {
  private currentPalette: EGAPalette;

  // EGA 기본 16색 팔레트 (0-63 범위)
  private static readonly DEFAULT_EGA_PALETTE: number[][] = [
    [0, 0, 0],       // 0: Black
    [0, 0, 42],      // 1: Blue
    [0, 42, 0],      // 2: Green
    [0, 42, 42],     // 3: Cyan
    [42, 0, 0],      // 4: Red
    [42, 0, 42],     // 5: Magenta
    [42, 21, 0],     // 6: Brown
    [42, 42, 42],    // 7: Light Gray
    [21, 21, 21],    // 8: Dark Gray
    [21, 21, 63],    // 9: Light Blue
    [21, 63, 21],    // 10: Light Green
    [21, 63, 63],    // 11: Light Cyan
    [63, 21, 21],    // 12: Light Red
    [63, 21, 63],    // 13: Light Magenta
    [63, 63, 21],    // 14: Yellow
    [63, 63, 63],    // 15: White
  ];

  constructor() {
    this.currentPalette = {
      colors: PaletteManager.DEFAULT_EGA_PALETTE.map(c => [...c])
    };
  }

  /**
   * 팔레트 데이터 로드
   */
  async loadPalette(data: Uint8Array): Promise<void> {
    const colors: number[][] = [];

    // 팔레트 데이터 파싱 (RGB 3바이트씩)
    if (data.length === 48) {
      // 16색 * 3 bytes (RGB)
      for (let i = 0; i < 16; i++) {
        const r = data[i * 3];
        const g = data[i * 3 + 1];
        const b = data[i * 3 + 2];
        colors.push([r, g, b]);
      }
      this.currentPalette = { colors };
    } else if (data.length === 16) {
      // 인덱스 테이블일 경우 기본 팔레트 재정렬
      for (let i = 0; i < 16; i++) {
        const idx = data[i] % 16;
        colors.push([...PaletteManager.DEFAULT_EGA_PALETTE[idx]]);
      }
      this.currentPalette = { colors };
    }
  }

  /**
   * EGA 색상을 RGB로 변환 (0-63 → 0-255)
   */
  egaToRgb(egaValue: number): number {
    return Math.floor((egaValue * 255) / 63);
  }

  /**
   * 팔레트 인덱스를 RGB 문자열로 변환
   */
  getColor(index: number): string {
    const color = this.currentPalette.colors[index % 16];
    const r = this.egaToRgb(color[0]);
    const g = this.egaToRgb(color[1]);
    const b = this.egaToRgb(color[2]);
    return `rgb(${r}, ${g}, ${b})`;
  }

  /**
   * 팔레트 인덱스를 RGBA 배열로 변환
   */
  getColorRGBA(index: number): [number, number, number, number] {
    const color = this.currentPalette.colors[index % 16];
    return [
      this.egaToRgb(color[0]),
      this.egaToRgb(color[1]),
      this.egaToRgb(color[2]),
      255
    ];
  }

  /**
   * 현재 팔레트 가져오기
   */
  getPalette(): EGAPalette {
    return {
      colors: this.currentPalette.colors.map(c => [...c])
    };
  }

  /**
   * 기본 팔레트로 리셋
   */
  reset(): void {
    this.currentPalette = {
      colors: PaletteManager.DEFAULT_EGA_PALETTE.map(c => [...c])
    };
  }
}
