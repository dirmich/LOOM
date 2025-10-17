#!/usr/bin/env python3
"""
SCUMM v3 정확한 디코딩 - SMAP 방식
"""
from PIL import Image

EGA_PALETTE = [
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00), (0x00, 0xAA, 0xAA),
    (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA), (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA),
    (0x55, 0x55, 0x55), (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
    (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55), (0xFF, 0xFF, 0xFF),
]

def drawStripEGA(src, height):
    """ScummVM drawStripEGA"""
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
                    if x >= 8: break  # Stop at strip boundary
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
                    if x >= 8: break  # Stop at strip boundary
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
                if x >= 8: break  # Stop at strip boundary
                if y < height:
                    pixels[y][x] = pixel_color
                y += 1
                if y >= height: y, x = 0, x + 1

    return pixels

# XOR decrypt
with open('01.LFL', 'rb') as f:
    encrypted = f.read()
decrypted = bytes([b ^ 0xFF for b in encrypted])

# Room dimensions
width = decrypted[4] | (decrypted[5] << 8)
height = decrypted[6] | (decrypted[7] << 8)

print(f"🎮 Room 01 디코딩")
print(f"  크기: {width}×{height}")

# Resource 0 = SMAP
smap_ptr = 0x0135  # Resource 0 offset

# Read strip offsets (16-color: smap_ptr + 2 + stripnr * 2)
strip_offsets = []
for strip_idx in range(100):
    offset_pos = smap_ptr + 2 + strip_idx * 2
    if offset_pos + 1 >= len(decrypted):
        break

    strip_offset = decrypted[offset_pos] | (decrypted[offset_pos + 1] << 8)
    if strip_offset == 0 or smap_ptr + strip_offset >= len(decrypted):
        break

    strip_offsets.append(smap_ptr + strip_offset)

num_strips = len(strip_offsets)
print(f"  Strips: {num_strips}")

# Use declared width, not strip count
print(f"  디코딩 너비: {width}×{height} (strip {num_strips}개)")

# Decode all strips
full_pixels = [[0 for _ in range(width)] for _ in range(height)]

for strip_idx in range(min(num_strips, width // 8)):
    strip_offset = strip_offsets[strip_idx]
    next_offset = strip_offsets[strip_idx + 1] if strip_idx < num_strips - 1 else len(decrypted)
    strip_data = decrypted[strip_offset:next_offset]

    strip_pixels = drawStripEGA(strip_data, height)

    if strip_pixels:
        strip_x = strip_idx * 8
        for y in range(height):
            for x in range(8):
                pixel_x = strip_x + x
                if pixel_x < width and y < len(strip_pixels):
                    full_pixels[y][pixel_x] = strip_pixels[y][x]

# Count non-zero pixels
non_zero = sum(1 for y in range(height) for x in range(width) if full_pixels[y][x] != 0)
pct = non_zero * 100 / (width * height)
print(f"  Non-zero: {non_zero}/{width * height} ({pct:.2f}%)")

# Save PNG
img = Image.new('RGB', (width, height))
for y in range(height):
    for x in range(width):
        color_idx = full_pixels[y][x]
        rgb = EGA_PALETTE[color_idx]
        img.putpixel((x, y), rgb)

img.save('room_01_correct.png')
print(f"  ✅ Saved: room_01_correct.png")

# 4x upscale
upscaled = img.resize((width * 4, height * 4), Image.NEAREST)
upscaled.save('room_01_correct_4x.png')
print(f"  ✅ Saved: room_01_correct_4x.png")
