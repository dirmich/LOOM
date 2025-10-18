#!/usr/bin/env python3
"""
LOOM 리소스를 실제 파일 포맷으로 변환
- 이미지 → PNG
- 사운드 → WAV
- 스크립트 → TXT (hex dump + 디스어셈블)
"""
import os
import json
import struct
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️  PIL 없음 - 이미지는 raw 파일로만 저장됩니다")
    print("   설치: pip3 install Pillow")

try:
    import wave
    WAVE_AVAILABLE = True
except ImportError:
    WAVE_AVAILABLE = False


# EGA 16색 팔레트 (RGB)
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


def xor_decrypt(data):
    """XOR 0xFF 복호화"""
    return bytearray([b ^ 0xFF for b in data])


def decode_scumm_image(data):
    """재구성된 SCUMM 이미지 디코딩"""
    if len(data) < 8:
        return None, None, None

    # Read width & height
    width = data[0] | (data[1] << 8)
    height = data[2] | (data[3] << 8)

    if width <= 0 or height <= 0 or width > 2000 or height > 300:
        return None, None, None

    # Strip offset table
    table_start = 4
    max_strips = (width + 7) // 8
    offsets = []

    for i in range(max_strips):
        offset_pos = table_start + i * 2
        if offset_pos + 1 >= len(data):
            break
        strip_offset = data[offset_pos] | (data[offset_pos + 1] << 8)
        if strip_offset == 0 or strip_offset >= len(data):
            break
        offsets.append(strip_offset)

    if len(offsets) == 0:
        return None, None, None

    # Decode strips
    pixels = bytearray(width * height)

    for strip_idx in range(min(len(offsets), width // 8)):
        strip_offset = offsets[strip_idx]
        next_offset = offsets[strip_idx + 1] if strip_idx < len(offsets) - 1 else len(data)
        strip_data = data[strip_offset:next_offset]

        decode_strip_ega(strip_data, pixels, strip_idx * 8, width, height)

    return width, height, bytes(pixels)


def decode_strip_ega(data, pixels, strip_x, width, height):
    """ScummVM drawStripEGA 구현"""
    if len(data) == 0:
        return

    # 8×height 픽셀 스트립 버퍼
    dst = [[0 for _ in range(8)] for _ in range(height)]

    color = 0
    run = 0
    x = 0
    y = 0
    offset = 0

    while x < 8 and offset < len(data):
        color = data[offset]
        offset += 1

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

                for z in range(run):
                    if x >= 8:
                        break
                    if y < height:
                        pixel_color = (color & 0xF) if (z & 1) else (color >> 4)
                        dst[y][x] = pixel_color

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

            else:  # Repeat previous pixel
                if run == 0:
                    if offset >= len(data):
                        break
                    run = data[offset]
                    offset += 1

                for z in range(run):
                    if x >= 8:
                        break
                    if y < height:
                        if x > 0:
                            dst[y][x] = dst[y][x - 1]
                        else:
                            dst[y][x] = 0

                    y += 1
                    if y >= height:
                        y = 0
                        x += 1

        else:  # Single color run
            run = color >> 4
            if run == 0:
                if offset >= len(data):
                    break
                run = data[offset]
                offset += 1

            pixel_color = color & 0xF
            for z in range(run):
                if x >= 8:
                    break
                if y < height:
                    dst[y][x] = pixel_color

                y += 1
                if y >= height:
                    y = 0
                    x += 1

    # Copy to main buffer
    for row in range(height):
        for col in range(8):
            pixel_x = strip_x + col
            if pixel_x < width:
                pixel_index = row * width + pixel_x
                if pixel_index < len(pixels):
                    pixels[pixel_index] = dst[row][col]


def save_as_png(pixels, width, height, output_path):
    """PNG로 저장"""
    if not PIL_AVAILABLE:
        # Raw 파일로 저장
        with open(output_path.with_suffix('.raw'), 'wb') as f:
            f.write(pixels)
        return False

    # RGB 이미지 생성
    img = Image.new('RGB', (width, height))
    rgb_data = []

    for pixel in pixels:
        r, g, b = EGA_PALETTE[pixel & 0x0F]
        rgb_data.extend([r, g, b])

    img.putdata(list(zip(rgb_data[0::3], rgb_data[1::3], rgb_data[2::3])))
    img.save(output_path)
    return True


def convert_sound_to_wav(data, output_path):
    """사운드 데이터를 WAV로 변환 (추정)"""
    # SCUMM v3 사운드는 여러 포맷이 있음:
    # - PC Speaker beeps
    # - AdLib music
    # - Raw PCM samples

    # 간단한 PCM으로 가정 (8-bit unsigned, 11025 Hz)
    sample_rate = 11025

    with wave.open(str(output_path), 'wb') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(1)  # 8-bit
        wav.setframerate(sample_rate)
        wav.writeframes(data)

    return True


def disassemble_script(data, output_path):
    """스크립트 바이트코드 디스어셈블 (간단한 hex dump)"""
    with open(output_path, 'w') as f:
        f.write(f"SCUMM v3 Script - {len(data)} bytes\n")
        f.write("=" * 60 + "\n\n")

        # Hex dump
        for i in range(0, len(data), 16):
            chunk = data[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            f.write(f'{i:04X}  {hex_str:<48}  {ascii_str}\n')

        f.write("\n" + "=" * 60 + "\n")
        f.write("Note: Full SCUMM opcode disassembly not implemented yet\n")


def process_resources():
    """decoded2/ 디렉토리의 리소스들을 실제 파일로 변환"""
    decoded_dir = Path('decoded2')
    output_dir = Path('converted2')
    output_dir.mkdir(exist_ok=True)

    # resources.json 읽기
    with open(decoded_dir / 'resources.json', 'r') as f:
        resources_data = json.load(f)

    print('🎮 LOOM 리소스 변환 시작')
    print('=' * 70)

    stats = {
        'images': 0,
        'sounds': 0,
        'scripts': 0,
        'other': 0
    }

    for room in resources_data['rooms']:
        room_num = room['room']
        print(f'\n📂 Room {room_num} 처리 중...')

        room_output = output_dir / f'room_{room_num}'
        room_output.mkdir(exist_ok=True)

        for res in room['resources']:
            res_type = res['type']
            res_path = decoded_dir / res['path']

            if not res_path.exists():
                continue

            data = res_path.read_bytes()

            # 배경 이미지
            if res_type == 'background' and res.get('reconstructed'):
                width, height, pixels = decode_scumm_image(data)
                if pixels:
                    output_path = room_output / 'background.png'
                    if save_as_png(pixels, width, height, output_path):
                        print(f'   🖼️  {output_path.name} - {width}×{height}')
                        stats['images'] += 1

            # 그래픽 오브젝트
            elif res_type == 'graphics':
                # 원본 그래픽은 그대로 복사 (추후 디코딩 가능)
                output_path = room_output / 'graphics' / res['filename']
                output_path.parent.mkdir(exist_ok=True)
                output_path.write_bytes(data)
                stats['other'] += 1

            # 사운드
            elif res_type == 'sounds':
                output_path = room_output / 'sounds' / res['filename'].replace('.bin', '.wav')
                output_path.parent.mkdir(exist_ok=True)
                try:
                    convert_sound_to_wav(data, output_path)
                    print(f'   🔊 {output_path.name} - {len(data)} bytes')
                    stats['sounds'] += 1
                except Exception as e:
                    # 실패하면 원본 복사
                    output_path = output_path.with_suffix('.bin')
                    output_path.write_bytes(data)
                    stats['other'] += 1

            # 스크립트
            elif res_type == 'scripts':
                output_path = room_output / 'scripts' / res['filename'].replace('.bin', '.txt')
                output_path.parent.mkdir(exist_ok=True)
                disassemble_script(data, output_path)
                print(f'   📜 {output_path.name} - {len(data)} bytes')
                stats['scripts'] += 1

            # 기타
            else:
                output_path = room_output / res_type / res['filename']
                output_path.parent.mkdir(exist_ok=True)
                output_path.write_bytes(data)
                stats['other'] += 1

    # 결과 출력
    print('\n' + '=' * 70)
    print('✅ 변환 완료!')
    print(f'   🖼️  이미지: {stats["images"]}개 (PNG)')
    print(f'   🔊 사운드: {stats["sounds"]}개 (WAV)')
    print(f'   📜 스크립트: {stats["scripts"]}개 (TXT)')
    print(f'   📦 기타: {stats["other"]}개')
    print(f'\n   출력 디렉토리: {output_dir.absolute()}')


if __name__ == '__main__':
    process_resources()
