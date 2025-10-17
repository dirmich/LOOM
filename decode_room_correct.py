#!/usr/bin/env python3
"""
서버의 Room API 데이터를 정확히 디코딩
브라우저 TypeScript 로직과 동일하게 구현
"""
import urllib.request
from PIL import Image

# EGA 16-color palette
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

def decode_strip_v3(data, height):
    """ScummVM drawStripEGA - 정확한 구현"""
    dst = [[0 for _ in range(8)] for _ in range(height)]

    color = 0
    run = 0
    x = 0
    y = 0
    offset = 0

    while x < 8:
        if offset >= len(data):
            break

        color = data[offset]
        offset += 1

        if color & 0x80:
            run = color & 0x3F

            if color & 0x40:  # 0xC0-0xFF: Two-color dithering
                if offset >= len(data):
                    break
                color = data[offset]
                offset += 1

                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                for z in range(run):
                    if y < height and x < 8:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        dst[y][x] = pixel_color
                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

            else:  # 0x80-0xBF: Repeat previous pixel
                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                for z in range(run):
                    if y < height and x < 8:
                        dst[y][x] = dst[y][x - 1] if x > 0 else 0
                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

        else:  # 0x00-0x7F: Single color run
            run = color >> 4
            if run == 0:
                if offset >= len(data):
                    break
                run = data[offset]
                offset += 1

            for z in range(run):
                if y < height and x < 8:
                    dst[y][x] = color & 0xF
                y += 1
                if y >= height:
                    y = 0
                    x += 1

    return dst

def decode_object_image(data, height=144):
    """
    ScummV3Decoder.decodeObjectImage()와 동일한 로직
    """
    if len(data) < 8:
        return None, None, None

    # Skip 0x00 padding
    offset = 0
    while offset < len(data) and data[offset] == 0x00:
        offset += 1

    print(f"헤더 패딩: {offset} bytes")

    if offset + 1 >= len(data):
        return None, None, None

    # Read first word
    first_word = data[offset] | (data[offset + 1] << 8)
    file_size = len(data) - offset

    print(f"첫 번째 word: 0x{first_word:04x} ({first_word})")
    print(f"파일 크기: {file_size} bytes")

    # Format detection (TypeScript와 동일)
    is_format_a = abs(first_word - file_size) < file_size * 0.1
    is_format_b = first_word < 1000 and first_word < file_size
    is_format_c = first_word > file_size

    print(f"포맷 감지: A={is_format_a}, B={is_format_b}, C={is_format_c}")

    if is_format_c:
        print("Format C: Raw 포맷 - 지원하지 않음")
        return None, None, None

    # Format B (서버 재구성 데이터): offset table이 offset+0부터 시작
    # Format A (원본 LFL): offset table이 offset+2부터 시작
    table_start = offset if is_format_b else (offset + 2)
    offsets = []

    # Read offset table (max 40 strips)
    for i in range(40):
        offset_pos = table_start + i * 2
        if offset_pos + 1 >= len(data):
            print(f"[{i}] offsetPos {offset_pos} >= length")
            break

        strip_offset = data[offset_pos] | (data[offset_pos + 1] << 8)

        # Validate offset
        if strip_offset == 0:
            if i > 0:
                break
            continue

        # Format B: stripOffset는 상대 주소 (그대로 사용)
        # Format A: stripOffset는 절대 주소 (그대로 사용)
        real_offset = strip_offset

        # Format B는 상대 주소이므로 table_start 체크 불필요
        min_offset = 0 if is_format_b else table_start
        if real_offset >= len(data) or real_offset < min_offset:
            print(f"[{i}] Invalid realOffset {real_offset}")
            break

        # Check monotonic increase
        if len(offsets) > 0 and real_offset <= offsets[-1]:
            print(f"[{i}] Not monotonic: {real_offset} <= {offsets[-1]}")
            break

        offsets.append(real_offset)

    num_strips = len(offsets)
    width = num_strips * 8

    print(f"✅ 디코딩: {num_strips}개 스트립, {width}x{height}")
    print(f"첫 3개 오프셋: {', '.join([f'0x{o:x}' for o in offsets[:3]])}")

    if num_strips == 0:
        return None, None, None

    # Decode each strip
    pixels = [[0 for _ in range(width)] for _ in range(height)]

    for strip in range(num_strips):
        strip_offset = offsets[strip]
        next_offset = offsets[strip + 1] if strip < num_strips - 1 else len(data)

        if strip_offset >= len(data):
            continue

        strip_data = data[strip_offset:next_offset]
        strip_pixels = decode_strip_v3(strip_data, height)

        # Copy strip to main buffer
        strip_x = strip * 8
        for row in range(height):
            for col in range(8):
                pixel_x = strip_x + col
                if pixel_x < width:
                    pixels[row][pixel_x] = strip_pixels[row][col]

    return pixels, width, height

def save_png(pixels, width, height, output_path):
    """PNG로 저장"""
    img = Image.new('RGB', (width, height))

    for y in range(height):
        for x in range(width):
            color_idx = pixels[y][x]
            rgb = EGA_PALETTE[color_idx]
            img.putpixel((x, y), rgb)

    img.save(output_path)
    print(f"✅ 저장: {output_path}")

# Main
url = 'http://localhost:3000/room/01/image'
print(f"📂 {url} 로드 중...\n")

try:
    with urllib.request.urlopen(url) as response:
        data = response.read()

    print(f"✅ 로드 완료: {len(data):,} bytes\n")

    # Decode
    pixels, width, height = decode_object_image(data)

    if pixels:
        # Save PNG
        output_file = 'room_01_correct.png'
        save_png(pixels, width, height, output_file)

        print(f"\n🎮 이미지: {width}x{height}")
        print(f"📁 출력: {output_file}")
    else:
        print("❌ 디코딩 실패")

except Exception as e:
    print(f"❌ 오류: {e}")
