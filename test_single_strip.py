#!/usr/bin/env python3
"""
첫 번째 strip 하나만 수동 디코딩해서 테스트
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

def decode_strip_debug(data, height):
    """디버그 정보와 함께 strip 디코딩"""
    dst = [[0 for _ in range(8)] for _ in range(height)]

    color = 0
    run = 0
    x = 0
    y = 0
    offset = 0

    print(f"\n=== Strip 디코딩 시작 (height={height}) ===")

    step = 0
    while x < 8 and offset < len(data):
        color = data[offset]
        offset += 1
        step += 1

        if step <= 20:  # 처음 20 단계만 출력
            print(f"\nStep {step}: offset={offset-1}, byte=0x{color:02x}")

        if color & 0x80:  # RLE mode
            run = color & 0x3F

            if color & 0x40:  # Two-color dithering
                if offset >= len(data):
                    break
                color = data[offset]
                offset += 1

                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                if step <= 20:
                    print(f"  → Two-color dither: run={run}, colors={color>>4}/{color&0xF}")
                    print(f"  → Fill ({y},{x}) for {run} pixels")

                for z in range(run):
                    if y < height and x < 8:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        dst[y][x] = pixel_color
                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

            else:  # Repeat previous
                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                if step <= 20:
                    print(f"  → Repeat previous: run={run}")
                    print(f"  → Fill ({y},{x}) for {run} pixels")

                for z in range(run):
                    if y < height and x < 8:
                        dst[y][x] = dst[y][x - 1] if x > 0 else 0
                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

        else:  # Single color
            run = color >> 4
            if run == 0:
                if offset >= len(data):
                    break
                run = data[offset]
                offset += 1

            pixel_color = color & 0xF

            if step <= 20:
                print(f"  → Single color: run={run}, color={pixel_color}")
                print(f"  → Fill ({y},{x}) for {run} pixels")

            for z in range(run):
                if y < height and x < 8:
                    dst[y][x] = pixel_color
                y += 1
                if y >= height:
                    y = 0
                    x += 1

    print(f"\n✅ 디코딩 완료: x={x}, y={y}, offset={offset}/{len(data)}")
    return dst


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
strip_pixels = decode_strip_debug(strip_data, height)

# Save as 8x144 PNG
img = Image.new('RGB', (8, height))
for y in range(height):
    for x in range(8):
        color_idx = strip_pixels[y][x]
        rgb = EGA_PALETTE[color_idx]
        img.putpixel((x, y), rgb)

img.save('test_strip_0.png')
print(f"\n💾 저장: test_strip_0.png (8x{height})")

# Show first/last 10 rows
print(f"\n첫 10행의 픽셀 값:")
for y in range(10):
    row_str = ' '.join(f'{strip_pixels[y][x]:x}' for x in range(8))
    print(f"  Row {y:3d}: {row_str}")

print(f"\n마지막 10행의 픽셀 값:")
for y in range(height - 10, height):
    row_str = ' '.join(f'{strip_pixels[y][x]:x}' for x in range(8))
    print(f"  Row {y:3d}: {row_str}")
