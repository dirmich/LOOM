/**
 * SCUMM 리소스 타입 정의
 */

export interface ResourceMetadata {
  id: number;
  offset: number;
  size: number;
  type: ResourceType;
  entropy: string;
  filename: string;
  path: string;
}

export interface RoomMetadata {
  file: string;
  total: number;
  graphics: number;
  sounds: number;
  scripts: number;
  palettes: number;
  unknown: number;
  resources: ResourceMetadata[];
}

export interface Summary {
  total_files: number;
  total_resources: number;
  graphics: number;
  sounds: number;
  scripts: number;
  palettes: number;
  unknown: number;
  files: RoomMetadata[];
}

export type ResourceType = 'graphics' | 'sounds' | 'scripts' | 'palettes' | 'unknown';

export interface EGAPalette {
  colors: number[][]; // RGB 값 배열 [[r,g,b], ...]
}

export interface Bitmap {
  width: number;
  height: number;
  data: Uint8Array;
}

export interface Sound {
  frequency: number;
  duration: number;
  data: Uint8Array;
}

export interface Script {
  code: Uint8Array;
  offset: number;
}
