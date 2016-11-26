# This file was copied from Slush's stratum-mining project
# with some modifications


'''Various helper methods. It probably needs some cleanup.'''

import struct
import StringIO
import binascii
from hashlib import sha256

def to_hex(s):
    assert type(s) ==  str # fixme: handle other types
    assert len(s) == 32
    return binascii.hexlify(s[::-1])

def deser_varint(f):
    nit = struct.unpack("<B", f.read(1))[0]
    if nit == 253:
        nit = struct.unpack("<H", f.read(2))[0]
    elif nit == 254:
        nit = struct.unpack("<I", f.read(4))[0]
    elif nit == 255:
        nit = struct.unpack("<Q", f.read(8))[0]
    return nit

def ser_varint(i):
    if i < 253:
        return chr(i)
    elif i < 0x10000:
        return chr(253) + struct.pack("<H", i)
    elif i < 0x100000000L:
        return chr(254) + struct.pack("<I", i)
    return chr(255) + struct.pack("<Q", i)

def deser_string(f):
    nit = struct.unpack("<B", f.read(1))[0]
    if nit == 253:
        nit = struct.unpack("<H", f.read(2))[0]
    elif nit == 254:
        nit = struct.unpack("<I", f.read(4))[0]
    elif nit == 255:
        nit = struct.unpack("<Q", f.read(8))[0]
    return f.read(nit)

def ser_string(s):
    if len(s) < 253:
        return chr(len(s)) + s
    elif len(s) < 0x10000:
        return chr(253) + struct.pack("<H", len(s)) + s
    elif len(s) < 0x100000000L:
        return chr(254) + struct.pack("<I", len(s)) + s
    return chr(255) + struct.pack("<Q", len(s)) + s

def deser_uint256(f):
    r = 0L
    for i in xrange(8):
        t = struct.unpack("<I", f.read(4))[0]
        r += t << (i * 32)
    return r

def ser_uint256(u):
    rs = ""
    for i in xrange(8):
        rs += struct.pack("<I", u & 0xFFFFFFFFL)
        u >>= 32
    return rs

def uint256_from_str(s):
    r = 0L
    t = struct.unpack("<IIIIIIII", s[:32])
    for i in xrange(8):
        r += t[i] << (i * 32)
    return r

def uint256_from_str_be(s):
    r = 0L
    t = struct.unpack(">IIIIIIII", s[:32])
    for i in xrange(8):
        r += t[i] << (i * 32)
    return r

def uint256_from_compact(c):
    nbytes = (c >> 24) & 0xFF
    v = (c & 0xFFFFFFL) << (8 * (nbytes - 3))
    return v

def deser_vector(f, c):
    nit = struct.unpack("<B", f.read(1))[0]
    if nit == 253:
        nit = struct.unpack("<H", f.read(2))[0]
    elif nit == 254:
        nit = struct.unpack("<I", f.read(4))[0]
    elif nit == 255:
        nit = struct.unpack("<Q", f.read(8))[0]
    r = []
    for i in xrange(nit):
        t = c()
        t.deserialize(f)
        r.append(t)
    return r

def ser_vector(l):
    r = ""
    if len(l) < 253:
        r = chr(len(l))
    elif len(l) < 0x10000:
        r = chr(253) + struct.pack("<H", len(l))
    elif len(l) < 0x100000000L:
        r = chr(254) + struct.pack("<I", len(l))
    else:
        r = chr(255) + struct.pack("<Q", len(l))
    for i in l:
        r += i.serialize()
    return r

def deser_uint256_vector(f):
    nit = struct.unpack("<B", f.read(1))[0]
    if nit == 253:
        nit = struct.unpack("<H", f.read(2))[0]
    elif nit == 254:
        nit = struct.unpack("<I", f.read(4))[0]
    elif nit == 255:
        nit = struct.unpack("<Q", f.read(8))[0]
    r = []
    for i in xrange(nit):
        t = deser_uint256(f)
        r.append(t)
    return r

def ser_uint256_vector(l):
    r = ""
    if len(l) < 253:
        r = chr(len(l))
    elif len(l) < 0x10000:
        r = chr(253) + struct.pack("<H", len(l))
    elif len(l) < 0x100000000L:
        r = chr(254) + struct.pack("<I", len(l))
    else:
        r = chr(255) + struct.pack("<Q", len(l))
    for i in l:
        r += ser_uint256(i)
    return r

__b58chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
__b58base = len(__b58chars)

def b58decode(v, length):
    """ decode v into a string of len bytes
    """
    long_value = 0L
    for (i, c) in enumerate(v[::-1]):
        long_value += __b58chars.find(c) * (__b58base**i)

    result = ''
    while long_value >= 256:
        div, mod = divmod(long_value, 256)
        result = chr(mod) + result
        long_value = div
    result = chr(long_value) + result

    nPad = 0
    for c in v:
        if c == __b58chars[0]: nPad += 1
        else: break

    result = chr(0)*nPad + result
    if length is not None and len(result) != length:
        return None

    return result

def reverse_hash(h):
    # This only revert byte order, nothing more
    if len(h) != 64:
        raise Exception('hash must have 64 hexa chars')

    return ''.join([ h[56-i:64-i] for i in range(0, 64, 8) ])

def doublesha(b):
    return sha256(sha256(b).digest()).digest()

def bits_to_target(bits):
    return struct.unpack('<L', bits[:3] + b'\0')[0] * 2**(8*(int(bits[3], 16) - 3))

def address_to_pubkeyhash(addr):
    try:
        addr = b58decode(addr, 25)
    except:
        return None

    if addr is None:
        return None

    ver = addr[0]
    cksumA = addr[-4:]
    cksumB = doublesha(addr[:-4])[:4]

    if cksumA != cksumB:
        return None

    return (ver, addr[1:-4])

def ser_uint256_be(u):
    '''ser_uint256 to big endian'''
    rs = ""
    for i in xrange(8):
        rs += struct.pack(">I", u & 0xFFFFFFFFL)
        u >>= 32
    return rs

def deser_uint256_be(f):
    r = 0L
    for i in xrange(8):
        t = struct.unpack(">I", f.read(4))[0]
        r += t << (i * 32)
    return r

def ser_number(n):
    # For encoding nHeight into coinbase
    s = bytearray(b'\1')
    while n > 127:
        s[0] += 1
        s.append(n % 256)
        n //= 256
    s.append(n)
    return bytes(s)

def script_to_address(addr):
    d = address_to_pubkeyhash(addr)
    if not d:
        raise ValueError('invalid address')
    (ver, pubkeyhash) = d
    return b'\x76\xa9\x14' + pubkeyhash + b'\x88\xac'



def long_hex(bytes):
  return bytes.encode('hex_codec')

def short_hex(bytes):
  t = bytes.encode('hex_codec')
  if len(t) < 11:
    return t
  return t[0:4]+"..."+t[-4:]

#################################################################################

# from http://bitcoin.stackexchange.com/a/30458

def target_int2bits(target):
    # comprehensive explanation here: bitcoin.stackexchange.com/a/2926/2116

    # get in base 256 as a hex string
    target_hex = int2hex(target)

    bits = "00" if (hex2int(target_hex[: 2]) > 127) else ""
    bits += target_hex # append
    bits = hex2bin(bits)
    length = int2bin(len(bits), 1)

    # the bits value could be zero (0x00) so make sure it is at least 3 bytes
    bits += hex2bin("0000")

    # the bits value could be bigger than 3 bytes, so cut it down to size
    bits = bits[: 3]

    return length + bits

def bits2target_int(bits_bytes):
    exp = bin2int(bits_bytes[: 1]) # exponent is the first byte
    mult = bin2int(bits_bytes[1:]) # multiplier is all but the first byte
    return mult * (2 ** (8 * (exp - 3)))

def int2hex(intval):
    hex_str = hex(intval)[2:]
    if hex_str[-1] == "L":
        hex_str = hex_str[: -1]
    if len(hex_str) % 2:
        hex_str = "0" + hex_str
    return hex_str

def hex2int(hex_str):
    return int(hex_str, 16)

def hex2bin(hex_str):
    return binascii.a2b_hex(hex_str)

def int2bin(val, pad_length = False):
    hexval = int2hex(val)
    if pad_length: # specified in bytes
        hexval = hexval.zfill(2 * pad_length)
    return hex2bin(hexval)

def bin2hex(binary):
    # convert raw binary data to a hex string. also accepts ascii chars (0 - 255)
    return binascii.b2a_hex(binary)

#>>> bits_bytes = target_int2bits(22791193517536179595645637622052884930882401463536451358196587084939)
#>>> bin2hex(bits_bytes)
#'1d00d86a'
#>>> # this ^^ is the value in blockexplorer.com in brackets.
#>>> # display the "bits" as an integer:
#>>> bits2target_int(bits_bytes)
#22791060871177364286867400663010583169263383106957897897309909286912L
#>>> # this ^^ is the value at the end of your answer.

#################################################################################


# own code:

# Bitcoin difficulty 1 target - used for computing difficulty
MAX_DIFF_1  = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

# not really using POOL_DIFF_1, I believe
POOL_DIFF_1 = 0x00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF

def compute_difficulty_from_uint256(target):
    # ref. https://en.bitcoin.it/wiki/Difficulty#What_is_the_formula_for_difficulty.3F
    return MAX_DIFF_1 / float(target)

def compute_target_from_difficulty(difficulty):
    return int(MAX_DIFF_1 / float(difficulty))

#def bits2difficulty(bits):
#    target = uint256_from_compact(bits)
#    return compute_difficulty_from_uint256(target)

def bits2difficulty(bits):
    # Floating point number that is a multiple of the minimum difficulty,
    # minimum difficulty = 1.0.

    nShift = (bits >> 24) & 0xff

    dDiff = float(0x0000ffff) / float(bits & 0x00ffffff)

    while nShift < 29:
        dDiff *= 256.0
        nShift += 1
    while nShift > 29:
        dDiff /= 256.0
        nShift -= 1

    # not supposed to return diff < 1.0 
    # but it seems this is possible indeed, despite the above comment in CPP function
    #assert dDiff >= 1.0, "diff M 1.0: %s" % dDiff

    return dDiff


def diff2bits(diff, maxdiff=MAX_DIFF_1):
    target = int(maxdiff / float(diff))
    return target_int2bits(target)

def bin2int(bytestring):
    result = 0
    remainder = bytestring
    while len(remainder) > 0:
        if len(remainder) == 1:
            first_byte = int(ord(remainder[0]))
            remainder = ''
        else:
            first_byte, remainder = int(ord(remainder[0])), remainder[1:] 
        result = (result << 8) + first_byte
    return result

def diffstr2target(hexstr):
    """ returns the target for a difficulty in compact hex (bdiff)
        such as is output by command line clients"""
    int_diff = int('0x' + hexstr, 16)
    return int_diff
