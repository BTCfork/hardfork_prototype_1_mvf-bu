#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
'''
>>> max_diff_bits = target_int2bits(MAX_DIFF_1)
>>> bin2hex(max_diff_bits)
'1d00ffff'
>>> pool_diff_bits = target_int2bits(POOL_DIFF_1)
>>> bin2hex(pool_diff_bits)
'1d00ffff'
>>> bits_bytes = target_int2bits(22791193517536179595645637622052884930882401463536451358196587084939)
>>> bin2hex(bits_bytes)
'1d00d86a'
>>> bits2target_int(bits_bytes)
22791060871177364286867400663010583169263383106957897897309909286912L
'''

import binascii

############################################################################
# begin code from from http://bitcoin.stackexchange.com/a/30458

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

# end code from from http://bitcoin.stackexchange.com/a/30458
############################################################################


# Bitcoin difficulty 1 target - used for computing difficulty
MAX_DIFF_1  = 0x00000000FFFF0000000000000000000000000000000000000000000000000000

# not really using POOL_DIFF_1, I believe
POOL_DIFF_1 = 0x00000000FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF


def bits2difficulty(bits):
    '''
    Python implementation of rpcblockchain.cpp:GetDifficulty()
    Returns floating point number that represents the difficulty.
    Minimum difficulty = 1.0 corresponds to the maximum target (MAX_DIFF_1)
    Returned difficulty can be below this minimum for testnets.
    >>> bits2difficulty(0x1d00ffff)
    1.0
    >>> bits2difficulty(0x207fffff)
    4.6565423739069247e-10
    >>> bits2difficulty(0xffffffff)
    0.0
    >>> bits2difficulty(0)
    Traceback (most recent call last):
    ...
    ZeroDivisionError: float division by zero
    '''
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


def bin2int(bytestring):
    '''
    Return integer representation of byte string.
    >>> bin2int(hex2bin('00'))
    0
    >>> bin2int(hex2bin('fe'))
    254
    >>> bin2int(hex2bin('1d00ffff'))
    486604799
    >>> bin2int(hex2bin('207fffff'))
    545259519
    '''
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
