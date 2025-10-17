#!/usr/bin/env python3
"""
전체 Room 이미지 디코딩 (Y offset 버전)
"""
import struct
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

def decodeStripWithOffset(src, height):
    """Decode strip with Y offset"""
    if len(src) < 5:
        return None

    y_offset = src[4]
    rle_data = src[5:]

    # 8×height buffer
    pixels = [[0 for _ in range(8)] for _ in range(height)]

    color = 0
    run = 0
    x = 0
    y = y_offset
    src_idx = 0

    while x < 8:
        if src_idx >= len(rle_data):
            break

        color = rle_data[src_idx]
        src_idx += 1

        if color & 0x80:
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
                    if y < height:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        pixels[y][x] = pixel_color

                    y += 1
                    if y >= height:
                        y = 0  # Reset to 0, not y_offset!
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
                            pixels[y][x] = pixels[y][x - 1]
                        else:
                            pixels[y][x] = 0

                    y += 1
                    if y >= height:
                        y = 0  # Reset to 0, not y_offset!
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
                    pixels[y][x] = pixel_color

                y += 1
                if y >= height:
                    y = y_offset
                    x += 1

    return pixels


# Read and decrypt LFL
with open('01.LFL', 'rb') as f:
    encrypted = f.read()
decrypted = bytes([b ^ 0xFF for b in encrypted])

# Room dimensions
width = decrypted[4] | (decrypted[5] << 8)
height = decrypted[6] | (decrypted[7] << 8)

print(f"Room size: {width}×{height}")

# Find strip offsets
resourceTableStart = 0x0A
resourceOffsets = []
for i in range(20):
    pos = resourceTableStart + i * 2
    if pos + 1 >= len(decrypted):
        break
    offset = decrypted[pos] | (decrypted[pos + 1] << 8)
    if offset == 0:
        break
    if offset >= len(decrypted):
        break
    resourceOffsets.append(offset)

# Find background image strips
stripOffsets = []
for resourceOffset in resourceOffsets:
    potentialStrips = []
    for i in range(40):
        pos = resourceOffset + i * 2
        if pos + 1 >= len(decrypted):
            break
        offset = decrypted[pos] | (decrypted[pos + 1] << 8)
        if offset == 0:
            break
        if offset >= len(decrypted):
            break
        potentialStrips.append(offset)

    if len(potentialStrips) >= 3:
        gaps = [potentialStrips[i + 1] - potentialStrips[i] for i in range(min(5, len(potentialStrips) - 1))]
        avgGap = sum(gaps) / len(gaps)
        if avgGap > 10 and avgGap < 5000:
            stripOffsets = potentialStrips
            break

num_strips = len(stripOffsets)
print(f"Found {num_strips} strips")
print()

# Create full image buffer
full_pixels = [[0 for _ in range(width)] for _ in range(height)]

# Decode each strip
for strip_idx in range(min(num_strips, 40)):  # Limit to 40 strips
    strip_offset = stripOffsets[strip_idx]
    next_offset = stripOffsets[strip_idx + 1] if strip_idx < num_strips - 1 else len(decrypted)
    strip_size = next_offset - strip_offset

    strip_data = decrypted[strip_offset:strip_offset+strip_size]

    # Decode strip
    strip_pixels = decodeStripWithOffset(strip_data, height)

    if strip_pixels:
        # Copy to full image buffer
        strip_x = strip_idx * 8  # Each strip is 8 pixels wide

        for y in range(height):
            for x in range(8):
                pixel_x = strip_x + x
                if pixel_x < width:
                    full_pixels[y][pixel_x] = strip_pixels[y][x]

        # Show non-zero pixels for first 5 strips
        if strip_idx < 5:
            non_zero_count = sum(1 for y in range(height) for x in range(8) if strip_pixels[y][x] != 0)
            print(f"Strip {strip_idx}: size={strip_size}, y_offset={strip_data[4]}, non_zero_pixels={non_zero_count}")

print()

# Save as PNG
img = Image.new('RGB', (width, height))
for y in range(height):
    for x in range(width):
        color_idx = full_pixels[y][x]
        rgb = EGA_PALETTE[color_idx]
        img.putpixel((x, y), rgb)

output_file = 'room_01_with_offset.png'
img.save(output_file)
print(f"✅ Saved: {output_file} ({width}×{height})")

# Count non-zero pixels in full image
non_zero_total = sum(1 for y in range(height) for x in range(width) if full_pixels[y][x] != 0)
print(f"📊 Non-zero pixels in full image: {non_zero_total}/{width*height} ({non_zero_total*100/(width*height):.2f}%)")
