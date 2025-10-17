#!/usr/bin/env python3
"""
모든 Room 디코딩
"""
import struct
from PIL import Image
from pathlib import Path

EGA_PALETTE = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00), (0x00, 0xAA, 0xAA),
    (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA), (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA),
    (0x55, 0x55, 0x55), (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
    (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55), (0xFF, 0xFF, 0xFF),
]

def drawStripEGA(src, height):
    """ScummVM drawStripEGA - 정확한 구현"""
    pixels = [[0 for _ in range(8)] for _ in range(height)]
    color, run, x, y, src_idx = 0, 0, 0, 0, 0

    while x < 8 and src_idx < len(src):
        color = src[src_idx]
        src_idx += 1

        if color & 0x80:
            run = color & 0x3F
            if color & 0x40:  # Two-color dithering
                if src_idx >= len(src): break
                color = src[src_idx]
                src_idx += 1
                if run == 0:
                    if src_idx >= len(src): break
                    run = src[src_idx]
                    src_idx += 1
                for z in range(run):
                    if y < height:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        pixels[y][x] = pixel_color
                    y += 1
                    if y >= height: y, x = 0, x + 1
            else:  # Repeat previous
                if run == 0:
                    if src_idx >= len(src): break
                    run = src[src_idx]
                    src_idx += 1
                for z in range(run):
                    if y < height:
                        pixels[y][x] = pixels[y][x - 1] if x > 0 else 0
                    y += 1
                    if y >= height: y, x = 0, x + 1
        else:  # Single color
            run = color >> 4
            if run == 0:
                if src_idx >= len(src): break
                run = src[src_idx]
                src_idx += 1
            pixel_color = color & 0xF
            for z in range(run):
                if y < height:
                    pixels[y][x] = pixel_color
                y += 1
                if y >= height: y, x = 0, x + 1

    return pixels

def decode_room(lfl_file, output_png):
    """Room 디코딩"""
    with open(lfl_file, 'rb') as f:
        encrypted = f.read()
    decrypted = bytes([b ^ 0xFF for b in encrypted])

    # Room dimensions
    room_width = decrypted[4] | (decrypted[5] << 8)
    room_height = decrypted[6] | (decrypted[7] << 8)

    # Find strip offsets
    resourceTableStart = 0x0A
    resourceOffsets = []
    for i in range(20):
        pos = resourceTableStart + i * 2
        if pos + 1 >= len(decrypted): break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        if offset == 0 or offset >= len(decrypted): break
        resourceOffsets.append(offset)

    # Find background image resource (strip table)
    stripOffsets = []
    for resourceOffset in resourceOffsets:
        potentialStrips = []
        for i in range(200):  # Max 200 strips
            pos = resourceOffset + i * 2
            if pos + 1 >= len(decrypted): break
            offset = decrypted[pos] | (decrypted[pos + 1] << 8)
            if offset == 0 or offset >= len(decrypted): break
            potentialStrips.append(offset)

        if len(potentialStrips) >= 3:
            gaps = [potentialStrips[i + 1] - potentialStrips[i] for i in range(min(5, len(potentialStrips) - 1))]
            avgGap = sum(gaps) / len(gaps)
            if avgGap > 10 and avgGap < 5000:
                stripOffsets = potentialStrips
                break

    num_strips = len(stripOffsets)

    if num_strips == 0:
        print(f"{lfl_file}: No strips found")
        return False

    # Use actual strip count for width
    actual_width = num_strips * 8
    height = room_height

    print(f"{lfl_file}:")
    print(f"  Room size: {room_width}×{room_height}")
    print(f"  Strips: {num_strips} → actual width: {actual_width}×{height}")

    # Decode strips
    full_pixels = [[0 for _ in range(actual_width)] for _ in range(height)]

    for strip_idx in range(num_strips):
        try:
            strip_offset = stripOffsets[strip_idx]
            next_offset = stripOffsets[strip_idx + 1] if strip_idx < num_strips - 1 else len(decrypted)
            strip_data = decrypted[strip_offset:next_offset]

            strip_pixels = drawStripEGA(strip_data, height)

            if strip_pixels:
                strip_x = strip_idx * 8
                for y in range(height):
                    for x in range(8):
                        pixel_x = strip_x + x
                        if pixel_x < actual_width and y < len(strip_pixels) and x < len(strip_pixels[0]):
                            full_pixels[y][pixel_x] = strip_pixels[y][x]
        except Exception as e:
            print(f"  ⚠️ Strip {strip_idx} error: {e}")
            continue

    # Count non-zero pixels
    non_zero = sum(1 for y in range(height) for x in range(actual_width) if full_pixels[y][x] != 0)
    pct = non_zero * 100 / (actual_width * height) if actual_width * height > 0 else 0
    print(f"  Non-zero pixels: {non_zero}/{actual_width * height} ({pct:.2f}%)")

    # Save PNG
    img = Image.new('RGB', (actual_width, height))
    for y in range(height):
        for x in range(actual_width):
            color_idx = full_pixels[y][x]
            rgb = EGA_PALETTE[color_idx]
            img.putpixel((x, y), rgb)

    img.save(output_png)
    print(f"  ✅ Saved: {output_png}\n")
    return True

# Decode rooms 01-10
print("🎮 LOOM Room 디코더\n" + "="*60 + "\n")

success_count = 0
for i in range(1, 11):
    lfl = f'{i:02d}.LFL'
    png = f'room_{i:02d}_decoded.png'

    if not Path(lfl).exists():
        continue

    try:
        if decode_room(lfl, png):
            success_count += 1
    except Exception as e:
        print(f"{lfl}: ❌ Error - {e}\n")

print("="*60)
print(f"✅ 성공: {success_count}개 Room")
