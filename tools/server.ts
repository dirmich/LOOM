/**
 * 간단한 개발 서버 (Bun)
 * LFL 파일 서빙 및 XOR 복호화 지원
 */

/**
 * XOR 0xFF 복호화
 */
function xorDecrypt(data: Uint8Array): Uint8Array {
  const result = new Uint8Array(data.length);
  for (let i = 0; i < data.length; i++) {
    result[i] = data[i] ^ 0xFF;
  }
  return result;
}

/**
 * SCUMM v3 Room에서 배경 이미지 데이터 추출 및 재구성
 */
function extractRoomImage(roomData: Uint8Array): Uint8Array | null {
  if (roomData.length < 10) return null;

  // Room 헤더 파싱
  // [04-05] Width (pixels)
  // [06-07] Height (pixels)
  const width = roomData[4] | (roomData[5] << 8);
  const height = roomData[6] | (roomData[7] << 8);

  console.log(`  Room: ${width}x${height}px`);

  // 리소스 오프셋 테이블은 0x0A부터 시작
  const resourceTableStart = 0x0A;
  const resourceOffsets: number[] = [];

  // 리소스 오프셋 읽기
  for (let i = 0; i < 20; i++) {
    const pos = resourceTableStart + i * 2;
    if (pos + 1 >= roomData.length) break;

    const offset = roomData[pos] | (roomData[pos + 1] << 8);
    if (offset === 0) break;
    if (offset >= roomData.length) break;

    resourceOffsets.push(offset);
  }

  if (resourceOffsets.length === 0) return null;

  // 배경 이미지 리소스 찾기 (strip offset table을 포함하는 리소스)
  let bgImageResourceOffset = 0;
  let stripOffsets: number[] = [];

  for (const resourceOffset of resourceOffsets) {
    // 이 리소스가 strip offset table인지 확인
    const potentialStrips: number[] = [];

    for (let i = 0; i < 40; i++) {
      const pos = resourceOffset + i * 2;
      if (pos + 1 >= roomData.length) break;

      const offset = roomData[pos] | (roomData[pos + 1] << 8);
      if (offset === 0) break;
      if (offset >= roomData.length) break;

      potentialStrips.push(offset);
    }

    // Strip table인지 확인 (일정 간격으로 증가하는 offset)
    if (potentialStrips.length >= 3) {
      const gaps = [];
      for (let i = 0; i < Math.min(5, potentialStrips.length - 1); i++) {
        gaps.push(potentialStrips[i + 1] - potentialStrips[i]);
      }
      const avgGap = gaps.reduce((a, b) => a + b, 0) / gaps.length;

      // 평균 간격이 10~5000 사이면 strip table
      if (avgGap > 10 && avgGap < 5000) {
        bgImageResourceOffset = resourceOffset;
        stripOffsets = potentialStrips;
        break;
      }
    }
  }

  if (stripOffsets.length === 0) {
    console.log('  ❌ Background image resource not found');
    return null;
  }

  console.log(`  ✅ Found ${stripOffsets.length} strips at resource offset 0x${bgImageResourceOffset.toString(16)}`);

  // 새로운 이미지 데이터 재구성
  // [0x00-0x4F]: 새 strip offset table (상대 주소)
  // [0x50-...]:  Strip 데이터들

  const newTableSize = stripOffsets.length * 2;
  let totalStripDataSize = 0;

  // 각 strip 크기 계산
  const stripSizes: number[] = [];
  for (let i = 0; i < stripOffsets.length; i++) {
    const stripStart = stripOffsets[i];
    const stripEnd = i < stripOffsets.length - 1 ? stripOffsets[i + 1] : roomData.length;
    const stripSize = stripEnd - stripStart;
    stripSizes.push(stripSize);
    totalStripDataSize += stripSize;
  }

  // 새 데이터 버퍼 생성
  const newData = new Uint8Array(newTableSize + totalStripDataSize);

  // 새 offset table 작성 (상대 주소)
  let currentOffset = newTableSize;
  for (let i = 0; i < stripOffsets.length; i++) {
    newData[i * 2] = currentOffset & 0xFF;
    newData[i * 2 + 1] = (currentOffset >> 8) & 0xFF;
    currentOffset += stripSizes[i];
  }

  // Strip 데이터 복사
  let writePos = newTableSize;
  for (let i = 0; i < stripOffsets.length; i++) {
    const stripStart = stripOffsets[i];
    const stripSize = stripSizes[i];
    const stripData = roomData.slice(stripStart, stripStart + stripSize);
    newData.set(stripData, writePos);
    writePos += stripSize;
  }

  console.log(`  📦 Reconstructed image: ${newData.length} bytes (${stripOffsets.length} strips)`);
  console.log(`  📊 First 3 strip offsets: ${stripOffsets.slice(0, 3).map(o => `0x${o.toString(16)}`).join(', ')}`);

  return newData;
}

const server = Bun.serve({
  port: 3000,
  async fetch(req) {
    const url = new URL(req.url);
    let filePath = url.pathname;

    // 루트 경로는 index.html로
    if (filePath === '/') {
      filePath = '/index.html';
    }

    // Room 이미지 추출 API: /room/01/image
    const roomImageMatch = filePath.match(/^\/room\/(\d{2})\/image$/);
    if (roomImageMatch) {
      const roomNum = roomImageMatch[1];
      const lflFile = Bun.file(`../${roomNum}.LFL`);

      if (await lflFile.exists()) {
        console.log(`📂 Loading ${roomNum}.LFL for image extraction...`);
        const encrypted = new Uint8Array(await lflFile.arrayBuffer());
        const decrypted = xorDecrypt(encrypted);

        const imageData = extractRoomImage(decrypted);
        if (imageData) {
          return new Response(imageData, {
            headers: {
              'Content-Type': 'application/octet-stream',
              'Content-Length': imageData.length.toString(),
            },
          });
        }
      }
      return new Response('Room image not found', { status: 404 });
    }

    // LFL 파일 요청 처리 (XOR 복호화)
    if (filePath.match(/\/\d{2}\.LFL$/i)) {
      const lflFile = Bun.file(`..${filePath}`);
      if (await lflFile.exists()) {
        const encrypted = new Uint8Array(await lflFile.arrayBuffer());
        const decrypted = xorDecrypt(encrypted);
        return new Response(decrypted, {
          headers: {
            'Content-Type': 'application/octet-stream',
            'Content-Length': decrypted.length.toString(),
          },
        });
      }
    }

    // 파일 경로 결정
    const file = Bun.file(`.${filePath}`);

    // 파일이 존재하면 반환
    if (await file.exists()) {
      return new Response(file);
    }

    // out 디렉토리에서 찾기 (리소스 파일)
    const outFile = Bun.file(`..${filePath}`);
    if (await outFile.exists()) {
      return new Response(outFile);
    }

    // 404
    return new Response('Not Found', { status: 404 });
  },
});

console.log(`🚀 서버 시작: http://localhost:${server.port}`);
console.log(`📁 LFL 파일: ../*.LFL (XOR 복호화 지원)`);
console.log(`🎮 브라우저에서 http://localhost:3000 을 열어주세요!`);
