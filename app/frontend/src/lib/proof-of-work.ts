/**
 * Preuve de travail anti-robots (voir core/antispam.py) : retrouve le nombre `n`
 * compris entre 0 et `max` tel que SHA-256(`salt` + n) vaille `hash`.
 */
export interface Challenge {
  salt: string;
  hash: string;
  max: number;
}

const BATCH = 1000;

function hexToBytes(hex: string): Uint8Array {
  const bytes = new Uint8Array(hex.length / 2);
  for (let i = 0; i < bytes.length; i += 1) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  return bytes;
}

function sameBytes(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i += 1) if (a[i] !== b[i]) return false;
  return true;
}

export async function solve({ salt, hash, max }: Challenge): Promise<number | null> {
  if (!globalThis.crypto?.subtle || !/^[0-9a-f]{64}$/.test(hash)) return null;
  const encoder = new TextEncoder();
  const target = hexToBytes(hash);
  for (let start = 0; start <= max; start += BATCH) {
    const digests: Promise<ArrayBuffer>[] = [];
    for (let n = start; n <= Math.min(start + BATCH - 1, max); n += 1) {
      digests.push(crypto.subtle.digest("SHA-256", encoder.encode(`${salt}${n}`)));
    }
    const results = await Promise.all(digests);
    const found = results.findIndex((digest) => sameBytes(new Uint8Array(digest), target));
    if (found >= 0) return start + found;
  }
  return null;
}
