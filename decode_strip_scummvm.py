#!/usr/bin/env python3
"""
ScummVM drawStripEGA() 함수 정확한 포팅
"""
from pathlib import Path
from PIL import Image

EGA_PALETTE = [
    (0x00, 0x00, 0x00),  # 0: Black
    (0x00, 0x00, 0xAA),  # 1: Blue
    (0x00, 0xAA, 0x00),  # 2: Green
    (0x00, 0xAA, 0xAA),  # 3: Cyan
    (0xAA, 0x00, 0x00),  # 4: Red
    (0xAA, 0x00, 0xAA),  # 5: Magenta
    (0xAA, 0x55, 0x00),  # 6: Brown
    (0xAA, 0xAA, 0xAA),  # 7: Light Gray
    (0x55, 0x55, 0x55),  # 8: Dark Gray
    (0x55, 0x55, 0xFF),  # 9: Light Blue
    (0x55, 0xFF, 0x55),  # 10: Light Green
    (0x55, 0xFF, 0xFF),  # 11: Light Cyan
    (0xFF, 0x55, 0x55),  # 12: Light Red
    (0xFF, 0x55, 0xFF),  # 13: Light Magenta
    (0xFF, 0xFF, 0x55),  # 14: Yellow
    (0xFF, 0xFF, 0xFF),  # 15: White
]

def drawStripEGA(src, height):
    """
    ScummVM drawStripEGA() 정확한 포팅

    void Gdi::drawStripEGA(byte *dst, int dstPitch, const byte *src, int height) const
    """
    # 8×height 크기의 버퍼 (1D array)
    dst = [0] * (8 * height)
    dstPitch = 8  # width of strip

    color = 0
    run = 0
    x = 0
    y = 0
    src_idx = 0

    print(f"\n=== drawStripEGA (height={height}) ===")
    print(f"Total bytes: {len(src)}")

    step = 0
    while x < 8:
        if src_idx >= len(src):
            print(f"[{step}] Reached end of data at x={x}, y={y}")
            break

        color = src[src_idx]
        src_idx += 1
        step += 1

        if step <= 30:
            print(f"\n[{step}] offset={src_idx-1}, byte=0x{color:02x}, x={x}, y={y}")

        if color & 0x80:  # RLE mode
            run = color & 0x3F

            if color & 0x40:  # 0xC0-0xFF: Two-color dithering
                if src_idx >= len(src):
                    break
                color = src[src_idx]
                src_idx += 1

                if run == 0:
                    if src_idx >= len(src):
                        break
                    run = src[src_idx]
                    src_idx += 1

                if step <= 30:
                    print(f"  Two-color dither: run={run}, colors={color>>4}/{color&0xF}")

                for z in range(run):
                    pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                    dst[y * dstPitch + x] = pixel_color

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

            else:  # 0x80-0xBF: Repeat previous
                if run == 0:
                    if src_idx >= len(src):
                        break
                    run = src[src_idx]
                    src_idx += 1

                if step <= 30:
                    print(f"  Repeat previous: run={run}")

                for z in range(run):
                    # Copy from previous pixel (x-1)
                    if x > 0:
                        dst[y * dstPitch + x] = dst[y * dstPitch + (x - 1)]
                    else:
                        dst[y * dstPitch + x] = 0

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

        else:  # 0x00-0x7F: Single color
            run = color >> 4
            if run == 0:
                if src_idx >= len(src):
                    break
                run = src[src_idx]
                src_idx += 1

            pixel_color = color & 0xF

            if step <= 30:
                print(f"  Single color: run={run}, color={pixel_color}")

            for z in range(run):
                dst[y * dstPitch + x] = pixel_color

                y += 1
                if y >= height:
                    y = 0
                    x += 1

    print(f"\n✅ Decoding complete: x={x}, y={y}, consumed={src_idx}/{len(src)} bytes")

    # Convert 1D array to 2D
    pixels = [[0 for _ in range(8)] for _ in range(height)]
    for row in range(height):
        for col in range(8):
            pixels[row][col] = dst[row * dstPitch + col]

    return pixels


# Read LFL
data = Path('01.LFL').read_bytes()
decrypted = bytes([b ^ 0xFF for b in data])

# Get first strip
strip_offset = 0x438b
strip_size = 19
strip_data = decrypted[strip_offset:strip_offset + strip_size]

print(f"Strip data ({strip_size} bytes):")
for i in range(0, strip_size, 16):
    hex_str = ' '.join(f'{b:02x}' for b in strip_data[i:i+16])
    print(f"  {i:04x}: {hex_str}")

# Decode
height = 144
strip_pixels = drawStripEGA(strip_data, height)

# Save as 8x144 PNG
img = Image.new('RGB', (8, height))
for y in range(height):
    for x in range(8):
        color_idx = strip_pixels[y][x]
        rgb = EGA_PALETTE[color_idx]
        img.putpixel((x, y), rgb)

img.save('test_strip_scummvm.png')
print(f"\n💾 저장: test_strip_scummvm.png (8x{height})")

# Show first/last 10 rows
print(f"\n첫 10행의 픽셀 값:")
for y in range(10):
    row_str = ' '.join(f'{strip_pixels[y][x]:x}' for x in range(8))
    print(f"  Row {y:3d}: {row_str}")

print(f"\n마지막 10행의 픽셀 값:")
for y in range(height - 10, height):
    row_str = ' '.join(f'{strip_pixels[y][x]:x}' for x in range(8))
    print(f"  Row {y:3d}: {row_str}")
