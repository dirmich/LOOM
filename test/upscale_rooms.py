#!/usr/bin/env python3
"""
디코딩된 Room 이미지를 4배 확대
"""
from PIL import Image
from pathlib import Path

room_files = [
    'room_01_decoded.png',
    'room_02_decoded.png',
    'room_04_decoded.png',
    'room_08_decoded.png',
    'room_10_decoded.png'
]

print("🔍 Room 이미지 4배 확대 중...\n")

for room_file in room_files:
    if not Path(room_file).exists():
        continue

    img = Image.open(room_file)
    width, height = img.size

    # Nearest neighbor (pixel-perfect upscaling)
    upscaled = img.resize((width * 4, height * 4), Image.NEAREST)

    output = room_file.replace('_decoded.png', '_upscaled_4x.png')
    upscaled.save(output)

    print(f"✅ {room_file} ({width}×{height}) → {output} ({width*4}×{height*4})")

print("\n완료!")
