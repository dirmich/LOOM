/**
 * SCUMM v3 그래픽 디코더
 * 8픽셀 스트립 기반 planar 포맷을 디코딩합니다.
 */

export class ScummV3Decoder {
  /**
   * SCUMM v3 Room Image 디코딩 (서버가 재구성한 포맷)
   *
   * 서버 재구성 포맷:
   * [0x00-0x01]: width (little-endian)
   * [0x02-0x03]: height (little-endian)
   * [0x04-...]:  strip offset table (상대 주소, offset 4 기준)
   * [...]:       strip 데이터 (RLE 압축)
   */
  static decodeObjectImage(data: Uint8Array): { width: number; height: number; pixels: Uint8Array } | null {
    if (data.length < 8) {
      console.warn('데이터가 너무 작습니다.');
      return null;
    }

    try {
      // Read width & height from header
      const width = data[0] | (data[1] << 8);
      const height = data[2] | (data[3] << 8);

      console.log(`  📐 Room size: ${width}×${height}`);

      // Validate dimensions
      if (width <= 0 || height <= 0 || width > 2000 || height > 300) {
        console.warn(`  ⚠️ Invalid dimensions: ${width}×${height}`);
        return null;
      }

      // Strip offset table starts at offset 4
      const tableStart = 4;
      const maxStrips = Math.ceil(width / 8);
      const offsets: number[] = [];

      // Read strip offset table
      for (let i = 0; i < maxStrips; i++) {
        const offsetPos = tableStart + i * 2;
        if (offsetPos + 1 >= data.length) {
          console.log(`  🛑 [${i}] offsetPos ${offsetPos} >= length`);
          break;
        }

        const stripOffset = data[offsetPos] | (data[offsetPos + 1] << 8);

        // Validate offset
        if (stripOffset === 0) {
          console.log(`  ⏭️  [${i}] stripOffset = 0`);
          if (i > 0) break;
          continue;
        }

        if (stripOffset >= data.length) {
          console.log(`  ❌ [${i}] Invalid stripOffset ${stripOffset}`);
          break;
        }

        // Check monotonic increase
        if (offsets.length > 0 && stripOffset <= offsets[offsets.length - 1]) {
          console.log(`  ❌ [${i}] Not monotonic: ${stripOffset} <= ${offsets[offsets.length - 1]}`);
          break;
        }

        offsets.push(stripOffset);
      }

      const numStrips = offsets.length;

      if (numStrips === 0) {
        console.warn('⚠️  No valid strips found');
        return null;
      }

      console.log(`  ✅ Found ${numStrips} strips`);
      console.log(`  📊 First 3 offsets: ${offsets.slice(0, 3).map(o => '0x' + o.toString(16)).join(', ')}`);

      // Decode each strip
      const pixels = new Uint8Array(width * height);
      pixels.fill(0);

      for (let strip = 0; strip < Math.min(numStrips, Math.floor(width / 8)); strip++) {
        const stripOffset = offsets[strip];
        const nextOffset = strip < numStrips - 1 ? offsets[strip + 1] : data.length;

        if (stripOffset >= data.length) continue;

        const stripData = data.slice(stripOffset, nextOffset);
        this.decodeStripEGA(stripData, pixels, strip * 8, width, height);
      }

      // Count non-zero pixels
      let nonZero = 0;
      for (let i = 0; i < pixels.length; i++) {
        if (pixels[i] !== 0) nonZero++;
      }
      const pct = ((nonZero * 100) / pixels.length).toFixed(2);
      console.log(`  🎨 Non-zero pixels: ${nonZero}/${pixels.length} (${pct}%)`);

      return { width, height, pixels };
    } catch (error) {
      console.error('❌ 디코딩 실패:', error);
      return null;
    }
  }

  /**
   * Format C: 오프셋 테이블 없이 raw 데이터를 직접 디코딩
   */
  private static decodeRawFormat(data: Uint8Array): { width: number; height: number; pixels: Uint8Array } | null {
    console.log(`  📊 Raw format 디코딩: ${data.length} bytes`);

    // Estimate dimensions
    const width = 320; // Standard SCUMM width
    const height = 200;

    const pixels = new Uint8Array(width * height);
    pixels.fill(0);

    // Try to decode as continuous vertical RLE stream
    // Process as 40 strips (320px / 8)
    const numStrips = 40;
    let offset = 0;

    for (let strip = 0; strip < numStrips && offset < data.length; strip++) {
      // Find strip size (heuristic: ~150-200 bytes per strip for 200px height)
      const estimatedStripSize = Math.min(300, Math.floor((data.length - offset) / (numStrips - strip)));
      const stripData = data.slice(offset, offset + estimatedStripSize);

      const consumed = this.decodeStripV3Safe(stripData, pixels, strip * 8, width, height);
      if (consumed > 0) {
        offset += consumed;
      } else {
        // Failed - try next strip position
        offset += 10; // Small skip
      }
    }

    console.log(`  ✅ Raw format 완료: ${width}x${height}, ${offset}/${data.length} bytes 사용`);
    return { width, height, pixels };
  }

  /**
   * Safe strip decoder that returns bytes consumed
   * Same structure as decodeStripV3: plane → col → RLE
   */
  private static decodeStripV3Safe(
    data: Uint8Array,
    pixels: Uint8Array,
    x: number,
    width: number,
    height: number
  ): number {
    if (data.length === 0) return 0;

    const planes: Uint8Array[] = [
      new Uint8Array(height * 8),
      new Uint8Array(height * 8),
      new Uint8Array(height * 8),
      new Uint8Array(height * 8)
    ];

    let offset = 0;
    const startOffset = offset;

    try {
      // Decode 4 bitplanes
      for (let plane = 0; plane < 4 && offset < data.length; plane++) {
        // Each plane has 8 vertical columns
        for (let col = 0; col < 8 && offset < data.length; col++) {
          let y = 0;

          // Decode one vertical RLE stream
          while (y < height && offset < data.length) {
            const code = data[offset++];

            if (code & 0x80) {
              // RLE: repeat
              const runLength = (code & 0x7F) + 1;
              if (offset >= data.length) break;
              const value = data[offset++];

              const bit = (value >> (7 - col)) & 1;

              for (let i = 0; i < runLength && y < height; i++, y++) {
                const planeIndex = y * 8 + col;
                if (planeIndex < planes[plane].length) {
                  planes[plane][planeIndex] = bit;
                }
              }
            } else {
              // Literal data
              const literalLength = (code & 0x7F) + 1;

              for (let i = 0; i < literalLength && y < height && offset < data.length; i++, y++) {
                const value = data[offset++];
                const bit = (value >> (7 - col)) & 1;

                const planeIndex = y * 8 + col;
                if (planeIndex < planes[plane].length) {
                  planes[plane][planeIndex] = bit;
                }
              }
            }
          }
        }
      }

      // Combine bitplanes into final pixels
      for (let y = 0; y < height; y++) {
        for (let col = 0; col < 8; col++) {
          const planeIndex = y * 8 + col;
          const pixelIndex = y * width + (x + col);

          if (pixelIndex < pixels.length) {
            const bit0 = planes[0][planeIndex];
            const bit1 = planes[1][planeIndex];
            const bit2 = planes[2][planeIndex];
            const bit3 = planes[3][planeIndex];

            const colorIndex = bit0 | (bit1 << 1) | (bit2 << 2) | (bit3 << 3);
            pixels[pixelIndex] = colorIndex;
          }
        }
      }

      return offset - startOffset;
    } catch (error) {
      console.warn(`  ⚠️  Strip decode error at offset ${offset}:`, error);
      return 0;
    }
  }

  /**
   * SCUMM v3 EGA 스트립 디코딩 (ScummVM drawStripEGA 정확한 구현)
   *
   * ScummVM의 3-mode RLE 시스템:
   * - 0x00-0x7F: Single color run (상위 4비트=길이, 하위 4비트=색상)
   * - 0x80-0xBF: Repeat previous pixel
   * - 0xC0-0xFF: Two-color dithering (두 색상을 교대로)
   */
  private static decodeStripEGA(
    data: Uint8Array,
    pixels: Uint8Array,
    stripX: number,
    width: number,
    height: number
  ): void {
    if (data.length === 0) return;

    // 8×height 픽셀 스트립 버퍼
    const dst: number[][] = [];
    for (let i = 0; i < height; i++) {
      dst[i] = new Array(8).fill(0);
    }

    let color = 0;
    let run = 0;
    let x = 0;
    let y = 0;
    let offset = 0;

    while (x < 8 && offset < data.length) {
      color = data[offset];
      offset++;

      if (color & 0x80) {  // RLE mode (0x80-0xFF)
        run = color & 0x3F;

        if (color & 0x40) {  // 0xC0-0xFF: Two-color dithering
          if (offset >= data.length) break;
          color = data[offset];
          offset++;

          if (run === 0) {
            if (offset >= data.length) break;
            run = data[offset];
            offset++;
          }

          for (let z = 0; z < run; z++) {
            if (x >= 8) break;  // Strip 경계 체크!
            if (y < height) {
              // Alternate between high and low nibble
              const pixelColor = (z & 1) ? (color & 0xF) : (color >> 4);
              dst[y][x] = pixelColor;
            }

            y++;
            if (y >= height) {
              y = 0;
              x++;
            }
          }
        } else {  // 0x80-0xBF: Repeat previous pixel
          if (run === 0) {
            if (offset >= data.length) break;
            run = data[offset];
            offset++;
          }

          for (let z = 0; z < run; z++) {
            if (x >= 8) break;  // Strip 경계 체크!
            if (y < height) {
              // Copy from previous column
              if (x > 0) {
                dst[y][x] = dst[y][x - 1];
              } else {
                dst[y][x] = 0;
              }
            }

            y++;
            if (y >= height) {
              y = 0;
              x++;
            }
          }
        }
      } else {  // 0x00-0x7F: Single color run
        run = color >> 4;
        if (run === 0) {
          if (offset >= data.length) break;
          run = data[offset];
          offset++;
        }

        const pixelColor = color & 0xF;
        for (let z = 0; z < run; z++) {
          if (x >= 8) break;  // Strip 경계 체크!
          if (y < height) {
            dst[y][x] = pixelColor;
          }

          y++;
          if (y >= height) {
            y = 0;
            x++;
          }
        }
      }
    }

    // Copy strip to main pixel buffer
    for (let row = 0; row < height; row++) {
      for (let col = 0; col < 8; col++) {
        const pixelX = stripX + col;
        const pixelIndex = row * width + pixelX;

        if (pixelIndex < pixels.length) {
          pixels[pixelIndex] = dst[row][col];
        }
      }
    }
  }

  /**
   * 높이 추정
   */
  private static estimateHeight(dataSize: number, numStrips: number): number {
    // LOOM은 대부분 144 픽셀 높이
    // 데이터 크기로 높이 추정
    const bytesPerStrip = dataSize / numStrips;

    if (bytesPerStrip < 80) return 64;
    if (bytesPerStrip < 150) return 88;
    if (bytesPerStrip < 250) return 128;

    // LOOM 기본 높이
    return 144;
  }

  /**
   * 폴백 디코딩 (Planar 포맷 추정)
   */
  private static decodeFallback(data: Uint8Array): { width: number; height: number; pixels: Uint8Array } {
    // 파일 크기로 추정
    let width = 320;
    let height = 200;

    if (data.length < 5000) {
      width = 160;
      height = 64;
    } else if (data.length < 15000) {
      width = 160;
      height = 128;
    } else if (data.length < 25000) {
      width = 160;
      height = 144;
    } else {
      width = 320;
      height = 200;
    }

    const pixels = new Uint8Array(width * height);

    // 4-plane planar 포맷으로 가정
    const planeSize = Math.floor(data.length / 4);
    const bytesPerLine = Math.ceil(width / 8);

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const lineOffset = y * bytesPerLine;
        const byteIndex = lineOffset + Math.floor(x / 8);
        const bitIndex = 7 - (x % 8);

        if (byteIndex < planeSize) {
          let colorIndex = 0;

          // 4개 플레인에서 비트 읽기
          for (let plane = 0; plane < 4; plane++) {
            const planeOffset = plane * planeSize;
            if (planeOffset + byteIndex < data.length) {
              const bit = (data[planeOffset + byteIndex] >> bitIndex) & 1;
              colorIndex |= (bit << plane);
            }
          }

          const pixelIndex = y * width + x;
          if (pixelIndex < pixels.length) {
            pixels[pixelIndex] = colorIndex;
          }
        }
      }
    }

    console.log(`  폴백 디코딩 (planar ${width}x${height}): ${data.length} bytes, ${planeSize} per plane`);
    return { width, height, pixels };
  }

  /**
   * SCUMM v3 RLE 압축 해제
   */
  private static decompressRLE(data: Uint8Array, maxSize: number): Uint8Array {
    const result: number[] = [];
    let offset = 0;

    while (offset < data.length && result.length < maxSize) {
      const code = data[offset++];

      if (code & 0x80) {
        // 반복
        const count = (code & 0x7F) + 1;
        const value = offset < data.length ? data[offset++] : 0;
        for (let i = 0; i < count; i++) {
          result.push(value);
        }
      } else {
        // 리터럴
        const count = code + 1;
        for (let i = 0; i < count && offset < data.length; i++) {
          result.push(data[offset++]);
        }
      }
    }

    return new Uint8Array(result);
  }

  /**
   * Planar to Chunky 변환 (4비트플레인 → 팔레트 인덱스)
   */
  private static planarToChunky(
    plane0: Uint8Array,
    plane1: Uint8Array,
    plane2: Uint8Array,
    plane3: Uint8Array,
    width: number,
    height: number
  ): Uint8Array {
    const pixels = new Uint8Array(width * height);
    const bytesPerLine = width / 8;

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const byteIndex = y * bytesPerLine + Math.floor(x / 8);
        const bitIndex = 7 - (x % 8);

        const bit0 = (plane0[byteIndex] >> bitIndex) & 1;
        const bit1 = (plane1[byteIndex] >> bitIndex) & 1;
        const bit2 = (plane2[byteIndex] >> bitIndex) & 1;
        const bit3 = (plane3[byteIndex] >> bitIndex) & 1;

        const colorIndex = bit0 | (bit1 << 1) | (bit2 << 2) | (bit3 << 3);
        pixels[y * width + x] = colorIndex;
      }
    }

    return pixels;
  }
}
