#!/usr/bin/env python3
"""
LOOM 리소스 포맷 분석
- 사운드 포맷 식별 (PC Speaker, AdLib, Roland)
- 스크립트 간단 분석
"""
import json
from pathlib import Path


def identify_sound_format(data):
    """사운드 포맷 식별"""
    if len(data) < 8:
        return 'unknown', 'Too small'

    # SCUMM v5+ 포맷 확인 (블록 헤더)
    try:
        header = data[:4].decode('ascii', errors='ignore').strip()
        if header in ['SPK', 'ADL', 'ROL']:
            formats = {
                'SPK': ('PC Speaker', 'PC Speaker beeps (MIDI-based)'),
                'ADL': ('AdLib', 'FM synthesis (OPL2 chip, MIDI-based)'),
                'ROL': ('Roland MT-32', 'MIDI data for external device')
            }
            return formats[header]
    except:
        pass

    # SCUMM v3 포맷 분석 (휴리스틱)
    # 0xBD = AdLib register command
    if 0xBD in data[:20]:
        return 'AdLib (v3)', 'FM synthesis data (no header)'

    # 반복 패턴 확인 (PC Speaker일 가능성)
    if len(set(data[:20])) < 5:
        return 'PC Speaker (v3)', 'Simple beep data (no header)'

    return 'Unknown', 'Cannot identify format'


def analyze_script_header(data):
    """스크립트 헤더 간단 분석"""
    if len(data) < 16:
        return {}

    info = {
        'size': len(data),
        'first_opcode': f'0x{data[0]:02X}',
        'common_opcodes': []
    }

    # 처음 50바이트의 opcode 빈도 분석
    opcodes = {}
    for i in range(0, min(50, len(data)), 4):  # 4바이트 단위 (opcode + params)
        if i < len(data):
            opcode = data[i]
            opcodes[opcode] = opcodes.get(opcode, 0) + 1

    # 가장 많이 나온 opcode 3개
    info['common_opcodes'] = sorted(opcodes.items(), key=lambda x: x[1], reverse=True)[:3]

    return info


def analyze_all_resources():
    """모든 리소스 분석"""
    decoded_dir = Path('decoded2')

    if not decoded_dir.exists():
        print('❌ decoded2/ 디렉토리가 없습니다.')
        return

    with open(decoded_dir / 'resources.json', 'r') as f:
        resources_data = json.load(f)

    print('🔍 LOOM 리소스 포맷 분석')
    print('=' * 70)

    sound_formats = {}
    total_sounds = 0
    total_scripts = 0

    for room in resources_data['rooms']:
        room_num = room['room']
        room_dir = decoded_dir / f'room_{room_num}'

        for res in room['resources']:
            res_path = room_dir / res['path'].replace(f'room_{room_num}/', '')

            if not res_path.exists():
                continue

            data = res_path.read_bytes()

            # 사운드 분석
            if res['type'] == 'sounds':
                total_sounds += 1
                format_name, description = identify_sound_format(data)

                if format_name not in sound_formats:
                    sound_formats[format_name] = {
                        'count': 0,
                        'description': description,
                        'examples': []
                    }

                sound_formats[format_name]['count'] += 1

                if len(sound_formats[format_name]['examples']) < 3:
                    sound_formats[format_name]['examples'].append(
                        f'room_{room_num}/{res["filename"]}'
                    )

            # 스크립트 분석
            elif res['type'] == 'scripts':
                total_scripts += 1

    # 결과 출력
    print(f'\n📊 사운드 포맷 분석 (총 {total_sounds}개)')
    print('-' * 70)

    for format_name, info in sorted(sound_formats.items()):
        print(f'\n🔊 {format_name}: {info["count"]}개')
        print(f'   설명: {info["description"]}')
        print(f'   예시:')
        for example in info['examples']:
            print(f'      - {example}')

    print(f'\n\n📜 스크립트 분석 (총 {total_scripts}개)')
    print('-' * 70)
    print('   ⚠️  SCUMM v3 바이트코드 (opcode + 파라미터)')
    print('   해결: ScummVM descumm 도구 필요')
    print('   참고: SCUMM_V3_포맷_분석.md')

    # 권장사항
    print('\n\n💡 권장 사항')
    print('=' * 70)
    print('1. 🎮 게임 플레이: ScummVM 사용 (완전한 사운드 재생)')
    print('2. 🔊 사운드 추출: MIDI 변환 구현 필요 (고급)')
    print('3. 📜 스크립트 읽기: descumm 도구 사용')
    print('   https://github.com/scummvm/scummvm-tools')


if __name__ == '__main__':
    analyze_all_resources()
