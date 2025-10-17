#!/usr/bin/env python3
"""
SCUMM v3 스크립트 디스어셈블
descumm 도구를 사용하여 모든 스크립트를 읽을 수 있는 형태로 변환
"""
import json
import subprocess
from pathlib import Path


DESCUMM_PATH = '/tmp/scummvm-tools/descumm'


def disassemble_script(input_path, output_path):
    """descumm으로 스크립트 디스어셈블"""
    try:
        result = subprocess.run(
            [DESCUMM_PATH, '-3', '-u', str(input_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return False, f'Error: {result.stderr}'

        # 출력 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f'// Disassembled from: {input_path.name}\n')
            f.write(f'// SCUMM v3 script\n')
            f.write('=' * 70 + '\n\n')
            f.write(result.stdout)

        return True, None

    except subprocess.TimeoutExpired:
        return False, 'Timeout'
    except Exception as e:
        return False, str(e)


def disassemble_all():
    """모든 스크립트 디스어셈블"""
    decoded_dir = Path('decoded2')
    output_dir = Path('disassembled')
    output_dir.mkdir(exist_ok=True)

    # descumm 도구 확인
    if not Path(DESCUMM_PATH).exists():
        print(f'❌ descumm 도구를 찾을 수 없습니다: {DESCUMM_PATH}')
        print('   /tmp/scummvm-tools/descumm이 빌드되어 있어야 합니다.')
        return

    print('📜 SCUMM v3 스크립트 디스어셈블 시작')
    print('=' * 70)

    # resources.json 읽기
    with open(decoded_dir / 'resources.json', 'r') as f:
        resources_data = json.load(f)

    total = 0
    success = 0
    failed = 0

    for room in resources_data['rooms']:
        room_num = room['room']
        room_num_int = int(room_num) if isinstance(room_num, str) else room_num
        room_dir = decoded_dir / f'room_{room_num}'
        output_room_dir = output_dir / f'room_{room_num}'

        scripts = [r for r in room['resources'] if r['type'] == 'scripts']

        if not scripts:
            continue

        output_room_dir.mkdir(exist_ok=True)

        print(f'\n📂 Room {room_num_int:02d} ({len(scripts)}개 스크립트)')

        for res in scripts:
            total += 1
            script_path = room_dir / res['path'].replace(f'room_{room_num}/', '')

            if not script_path.exists():
                print(f'   ⚠️  {res["filename"]} - 파일 없음')
                failed += 1
                continue

            output_path = output_room_dir / res['filename'].replace('.bin', '.txt')

            ok, error = disassemble_script(script_path, output_path)

            if ok:
                print(f'   ✅ {res["filename"]} → {output_path.name}')
                success += 1
            else:
                print(f'   ❌ {res["filename"]} - {error}')
                failed += 1

    print('\n' + '=' * 70)
    print(f'✅ 완료: {total}개 스크립트')
    print(f'   성공: {success}개')
    print(f'   실패: {failed}개')
    print(f'\n📁 출력: {output_dir.absolute()}')


if __name__ == '__main__':
    disassemble_all()
