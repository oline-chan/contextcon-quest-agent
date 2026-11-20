"""Pure-Python Keccak-256 and secp256k1 helpers (stdlib only).

Ethereum uses Keccak-256 (NOT the NIST SHA3-256 padding), so we cannot use
``hashlib.sha3_256`` here. This module implements Keccak-f[1600] directly and
is verified against known test vectors in tests/test_wallet.py:

* keccak256(b"")      == c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470
* keccak256(b"abc")   == 4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45
* privkey 1 (secp256k1) -> address 0x7E5F4552091A69125d5DfCb7b8C2659029395Bdf
"""

MASK64 = (1 << 64) - 1

# Keccak-f[1600] round constants.
_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089,
    0x8000000000008003, 0x8000000000008002, 0x8000000000000080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_R = [
    [0, 36, 3, 41, 18],
    [1, 44, 10, 45, 2],
    [62, 6, 43, 15, 61],
    [28, 55, 25, 21, 56],
    [27, 20, 39, 8, 14],
]

_PILN = [10, 7, 11, 17, 18, 3, 5, 16, 8, 21, 24, 4, 15, 23, 19, 13, 12, 2, 20, 14, 22, 9, 6, 1]


def _rotl(x, n):
    return ((x << n) | (x >> (64 - n))) & MASK64 if n else x


def _keccak_f1600(state):
    for rnd in range(24):
        # Theta
        c = [state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20]
             for x in range(5)]
        d = [c[(x - 1) % 5] ^ _rotl(c[(x + 1) % 5], 1) for x in range(5)]
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] ^= d[x]
        # Rho + Pi
        b = [0] * 25
        for x in range(5):
            for y in range(5):
                b[y + 5 * ((2 * x + 3 * y) % 5)] = _rotl(state[x + 5 * y], _R[x][y])
        # Chi
        for x in range(5):
            for y in range(5):
                state[x + 5 * y] = b[x + 5 * y] ^ ((~b[(x + 1) % 5 + 5 * y]) & b[(x + 2) % 5 + 5 * y])
        # Iota
        state[0] ^= _RC[rnd]
    return state


def keccak256(data: bytes) -> bytes:
    """Keccak-256 digest of ``data`` (Ethereum flavour, pad10*1 with 0x01)."""
    rate = 136  # bytes per block for Keccak-256
    state = [0] * 25
    # Absorb full blocks
    offset = 0
    while offset + rate <= len(data):
        block = data[offset:offset + rate]
        for i in range(rate // 8):
            state[i] ^= int.from_bytes(block[i * 8:(i + 1) * 8], "little")
        _keccak_f1600(state)
        offset += rate
    # Final block with pad10*1, domain byte 0x01
    tail = bytearray(data[offset:])
    tail.append(0x01)
    while len(tail) < rate:
        tail.append(0x00)
    tail[-1] |= 0x80
    for i in range(rate // 8):
        state[i] ^= int.from_bytes(tail[i * 8:(i + 1) * 8], "little")
    _keccak_f1600(state)
    return b"".join(state[i].to_bytes(8, "little") for i in range(4))


# --- secp256k1 (for deriving an EVM address from a burner private key) ---
_P = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_GX = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_GY = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


def _ec_add(p, q):
    if p is None:
        return q
    if q is None:
        return p
    x1, y1 = p
    x2, y2 = q
    if x1 == x2 and (y1 + y2) % _P == 0:
        return None
    if p == q:
        lam = (3 * x1 * x1) * pow(2 * y1, -1, _P) % _P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, _P) % _P
    x3 = (lam * lam - x1 - x2) % _P
    y3 = (lam * (x1 - x3) - y1) % _P
    return (x3, y3)


def _ec_mul(k, point=(_GX, _GY)):
    result = None
    addend = point
    while k:
        if k & 1:
            result = _ec_add(result, addend)
        addend = _ec_add(addend, addend)
        k >>= 1
    return result


def private_key_to_address(private_key: bytes) -> str:
    """Derive the checksummed EVM address for a 32-byte private key."""
    if len(private_key) != 32:
        raise ValueError("private key must be 32 bytes")
    k = int.from_bytes(private_key, "big")
    if not 1 <= k < _N:
        raise ValueError("private key out of range")
    x, y = _ec_mul(k)
    pub = x.to_bytes(32, "big") + y.to_bytes(32, "big")
    digest = keccak256(pub)
    raw = digest[-20:].hex()
    # EIP-55 checksum
    h = keccak256(raw.encode()).hex()
    checksummed = "".join(
        ch.upper() if int(h[i], 16) >= 8 else ch for i, ch in enumerate(raw)
    )
    return "0x" + checksummed
