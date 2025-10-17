#!/usr/bin/env python3
"""
새로운 가설: Strip 데이터에 Y offset이 포함됨
- Byte[0-3]: 헤더 (0x13 0x00 0x00 0x00)
- Byte[4]: Y offset 또는 skip count
- Byte[5-]: 실제 RLE 데이터
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

def drawStripWithOffset(src, height):
    """
    Strip decoding with Y offset in header
    """
    if len(src) < 5:
        return None

    # Parse header
    header_flag = src[0]
    y_offset = src[4]  # Y offset or skip count

    print(f"Header: flag=0x{header_flag:02x}, y_offset={y_offset}")

    # Decode from byte 5 onwards
    rle_data = src[5:]

    # Create 8×height buffer (1D)
    dst = [0] * (8 * height)
    dstPitch = 8

    color = 0
    run = 0
    x = 0
    y = y_offset  # Start from Y offset!
    src_idx = 0

    print(f"Starting RLE decode from y={y}")

    step = 0
    while x < 8:
        if src_idx >= len(rle_data):
            break

        color = rle_data[src_idx]
        src_idx += 1
        step += 1

        if step <= 20:
            print(f"[{step}] byte=0x{color:02x}, x={x}, y={y}")

        if color & 0x80:  # RLE mode
            run = color & 0x3F

            if color & 0x40:  # Two-color dithering
                if src_idx >= len(rle_data):
                    break
                color = rle_data[src_idx]
                src_idx += 1

                if run == 0:
                    if src_idx >= len(rle_data):
                        break
                    run = rle_data[src_idx]
                    src_idx += 1

                for z in range(run):
                    if y < height:  # Bounds check
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        dst[y * dstPitch + x] = pixel_color

                    y += 1
                    if y >= height:
                        y = y_offset  # Reset to offset, not 0!
                        x += 1

            else:  # Repeat previous
                if run == 0:
                    if src_idx >= len(rle_data):
                        break
                    run = rle_data[src_idx]
                    src_idx += 1

                for z in range(run):
                    if y < height:
                        if x > 0:
                            dst[y * dstPitch + x] = dst[y * dstPitch + (x - 1)]
                        else:
                            dst[y * dstPitch + x] = 0

                    y += 1
                    if y >= height:
                        y = y_offset
                        x += 1

        else:  # Single color
            run = color >> 4
            if run == 0:
                if src_idx >= len(rle_data):
                    break
                run = rle_data[src_idx]
                src_idx += 1

            pixel_color = color & 0xF

            for z in range(run):
                if y < height:
                    dst[y * dstPitch + x] = pixel_color

                y += 1
                if y >= height:
                    y = y_offset
                    x += 1

    print(f"✅ Decode complete: x={x}, y={y}, consumed={src_idx}/{len(rle_data)} bytes\n")

    # Convert to 2D
    pixels = [[0 for _ in range(8)] for _ in range(height)]
    for row in range(height):
        for col in range(8):
            pixels[row][col] = dst[row * dstPitch + col]

    return pixels


# Read LFL
data = Path('01.LFL').read_bytes()
decrypted = bytes([b ^ 0xFF for b in data])

# Test first 3 strips
strip_offsets = [0x438b, 0x439e, 0x43b1]

for i, strip_offset in enumerate(strip_offsets):
    print(f"\n{'='*60}")
    print(f"Strip {i} (offset=0x{strip_offset:04x})")
    print('='*60)

    strip_data = decrypted[strip_offset:strip_offset+19]

    # Show hex
    hex_str = ' '.join(f'{b:02x}' for b in strip_data)
    print(f"Data: {hex_str}\n")

    # Decode
    height = 144
    strip_pixels = drawStripWithOffset(strip_data, height)

    if strip_pixels:
        # Save as PNG
        img = Image.new('RGB', (8, height))
        for y in range(height):
            for x in range(8):
                color_idx = strip_pixels[y][x]
                rgb = EGA_PALETTE[color_idx]
                img.putpixel((x, y), rgb)

        img.save(f'test_strip_{i}_offset.png')
        print(f"💾 Saved: test_strip_{i}_offset.png")

        # Show non-zero pixels
        print(f"\nNon-zero pixels:")
        for y in range(height):
            for x in range(8):
                if strip_pixels[y][x] != 0:
                    print(f"  ({x},{y}): color {strip_pixels[y][x]}")

print(f"\n{'='*60}")
print("Analysis complete")
print('='*60)
