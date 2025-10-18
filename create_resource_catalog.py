#!/usr/bin/env python3
"""
LOOM 리소스 카탈로그 생성
모든 추출된 리소스를 HTML로 정리
"""
import json
from pathlib import Path


def load_resources_json():
    """resources.json 읽기"""
    with open('decoded2/resources.json', 'r') as f:
        return json.load(f)


def count_resources():
    """리소스 개수 집계"""
    resources = load_resources_json()

    counts = {
        'backgrounds': 0,
        'objects': 0,
        'scripts': 0,
        'sounds': 0,
    }

    for room in resources['rooms']:
        for res in room['resources']:
            res_type = res['type']
            if res_type == 'backgrounds':
                counts['backgrounds'] += 1
            elif res_type == 'objects':
                counts['objects'] += 1
            elif res_type == 'scripts':
                counts['scripts'] += 1
            elif res_type == 'sounds':
                counts['sounds'] += 1

    return counts


def create_html_catalog():
    """HTML 카탈로그 생성"""
    counts = count_resources()

    # CSS 스타일
    style = """
        body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
        .container { max-width: 1400px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }
        h1 { color: #333; text-align: center; margin-bottom: 30px; }
        .stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-number { font-size: 2.5em; font-weight: bold; }
        .stat-label { font-size: 0.9em; margin-top: 5px; }
        .section { margin-bottom: 50px; }
        .section h2 { color: #667eea; border-bottom: 3px solid #667eea; padding-bottom: 10px; margin-bottom: 20px; }
        .grid { display: grid; gap: 15px; }
        .grid-2 { grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); }
        .grid-3 { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
        .grid-4 { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); }
        .card { border: 1px solid #ddd; border-radius: 8px; overflow: hidden; background: white; transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .card-image { width: 100%; height: 180px; object-fit: contain; background: #f8f8f8; padding: 10px; }
        .card-body { padding: 15px; }
        .card-title { font-weight: bold; color: #333; margin-bottom: 5px; font-size: 0.9em; }
        .card-meta { color: #666; font-size: 0.8em; }
        .list-item { background: white; border: 1px solid #ddd; border-radius: 8px; padding: 15px; display: flex; align-items: center; gap: 10px; }
        .list-item:hover { border-color: #667eea; }
        .badge { background: #d4edda; color: #155724; padding: 3px 10px; border-radius: 10px; font-size: 0.75em; margin-left: 10px; }
    """

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOOM 리소스 카탈로그</title>
    <style>{style}</style>
</head>
<body>
    <div class="container">
        <h1>🎮 LOOM 리소스 카탈로그</h1>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{counts['backgrounds']}</div>
                <div class="stat-label">배경 이미지</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{counts['objects']}</div>
                <div class="stat-label">오브젝트</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{counts['scripts']}</div>
                <div class="stat-label">스크립트</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{counts['sounds']}</div>
                <div class="stat-label">사운드</div>
            </div>
        </div>
"""

    # 배경 이미지 섹션
    html += f"""
        <div class="section">
            <h2>🖼️ 배경 이미지 (Backgrounds) - {counts['backgrounds']}개</h2>
            <div class="grid grid-3">
"""

    backgrounds_dir = Path('backgrounds')
    if backgrounds_dir.exists():
        bg_files = sorted(backgrounds_dir.glob('*.png'))
        for bg_file in bg_files:
            room_num = bg_file.stem.replace('room_', '')
            html += f"""
                <div class="card">
                    <img class="card-image" src="backgrounds/{bg_file.name}" alt="Room {room_num}">
                    <div class="card-body">
                        <div class="card-title">Room {room_num}</div>
                        <div class="card-meta">320×144 EGA 16색</div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
"""

    # 오브젝트 그래픽 섹션
    html += """
        <div class="section">
            <h2>🎨 오브젝트 그래픽 (Objects) - 111개</h2>
            <div class="grid grid-4">
"""

    objects_dir = Path('objects_png_v3')
    if objects_dir.exists():
        obj_files = sorted(objects_dir.glob('*.png'))[:111]
        for obj_file in obj_files:
            parts = obj_file.stem.split('_')
            room_num = parts[0]
            obj_num = parts[1]
            html += f"""
                <div class="card">
                    <img class="card-image" src="objects_png_v3/{obj_file.name}" alt="Object {obj_num}">
                    <div class="card-body">
                        <div class="card-title">Obj {obj_num}</div>
                        <div class="card-meta">Room {room_num}</div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
"""

    # 스크립트 섹션
    html += """
        <div class="section">
            <h2>📜 스크립트 (Scripts) - 17개</h2>
            <div class="grid grid-2">
"""

    disasm_dir = Path('disassembled')
    if disasm_dir.exists():
        script_files = []
        for room_dir in sorted(disasm_dir.glob('room_*')):
            for script_file in sorted(room_dir.glob('*.txt')):
                script_files.append(script_file)

        for script_file in script_files:
            room_num = script_file.parent.name.replace('room_', '')
            script_name = script_file.stem
            size = script_file.stat().st_size
            size_str = f'{size:,} bytes'

            html += f"""
                <div class="list-item">
                    <div style="font-size: 2em;">📝</div>
                    <div style="flex: 1;">
                        <div class="card-title">{script_name}<span class="badge">디스어셈블됨</span></div>
                        <div class="card-meta">Room {room_num} • {size_str}</div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>
"""

    # 사운드 섹션
    html += f"""
        <div class="section">
            <h2>🎵 사운드 (Sounds) - {counts['sounds']}개</h2>
            <p style="margin-bottom: 20px; color: #666;">Roland MT-32 MIDI 파일 • 표준 MIDI 포맷(.mid)으로 변환됨</p>
            <div class="grid grid-3">
"""

    sounds_dir = Path('sounds_standard_midi')
    if sounds_dir.exists():
        sound_files = sorted(sounds_dir.glob('*.mid'))

        # 처음 50개만 표시
        for sound_file in sound_files[:50]:
            parts = sound_file.stem.split('_')
            room_num = parts[0]
            res_id = parts[1]
            size = sound_file.stat().st_size
            size_str = f'{size:,} bytes'

            html += f"""
                <div class="list-item">
                    <div style="font-size: 1.8em;">🎼</div>
                    <div style="flex: 1;">
                        <div class="card-title">{sound_file.stem}</div>
                        <div class="card-meta">Room {room_num} • {size_str}</div>
                    </div>
                </div>
"""

        remaining = len(sound_files) - 50
        if remaining > 0:
            html += f"""
                <div class="list-item" style="border: 2px dashed #ddd; background: #f8f8f8;">
                    <div style="flex: 1; text-align: center; padding: 20px;">
                        <div class="card-title" style="color: #666;">+ {remaining}개 더...</div>
                        <div class="card-meta">sounds_standard_midi/ 폴더에서 확인하세요</div>
                    </div>
                </div>
"""

    html += """
            </div>
        </div>

        <div style="text-align: center; padding: 30px; color: #666; border-top: 2px solid #f0f0f0;">
            <p><strong>LOOM 리소스 추출 프로젝트</strong></p>
            <p>ScummVM SCUMM v3 엔진 분석을 통한 완전한 리소스 추출</p>
            <p style="margin-top: 15px;">🎮 LucasArts LOOM (1990) • 🔧 ScummVM 소스 분석 • 🚀 100% 완료</p>
        </div>
    </div>
</body>
</html>
"""

    # HTML 파일 저장
    output_path = Path('resource_catalog.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return output_path


def main():
    """메인 함수"""
    print('📚 LOOM 리소스 카탈로그 생성')
    print('=' * 70)

    output_path = create_html_catalog()

    print(f'\n✅ HTML 카탈로그 생성 완료!')
    print(f'   파일: {output_path.absolute()}')
    print(f'\n   웹 브라우저로 열어서 확인하세요:')
    print(f'   open {output_path.absolute()}')
    print('\n' + '=' * 70)


if __name__ == '__main__':
    main()
