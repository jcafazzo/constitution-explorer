// Pure binary STL scaling, shared by the browser exporter and the local checks.
export function scaleBinarySTL(buffer, lengthMM) {
  if (!Number.isFinite(lengthMM) || lengthMM < 100 || lengthMM > 200) {
    throw new Error('Model length must be between 100 and 200 mm');
  }
  if (buffer.byteLength < 84) throw new Error('Truncated STL');
  const result = buffer.slice(0);
  const view = new DataView(result);
  const faces = view.getUint32(80, true);
  if (!faces || 84 + faces * 50 !== result.byteLength) throw new Error('Invalid binary STL');
  const factor = lengthMM / 100;
  for (let i = 0; i < faces; i++) {
    for (let j = 0; j < 9; j++) {
      const offset = 84 + i * 50 + 12 + j * 4;
      const coordinate = view.getFloat32(offset, true);
      if (!Number.isFinite(coordinate)) throw new Error('Invalid vertex coordinate');
      view.setFloat32(offset, coordinate * factor, true);
    }
  }
  return result;
}
