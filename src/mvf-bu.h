// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common declarations
#pragma once
#ifndef BITCOIN_MVF_BU_H
#define BITCOIN_MVF_BU_H

#include "protocol.h"

class CChainParams;

extern int FinalActivateForkHeight;         // MVHF-BU-DES-TRIG-4
extern bool isMVFHardForkActive;            // MVHF-BU-DES-TRIG-5
extern std::string autoWalletBackupSuffix;  // MVHF-BU-DES-WABU-1


// default values that can be easily put into an enum
enum {
// MVHF-BU-DES-TRIG-1 - trigger related parameter defaults
// MVF-BU TODO: choose values with some consideration instead of dummy values
HARDFORK_HEIGHT_MAINNET =  666666,   // operational network trigger height
HARDFORK_HEIGHT_TESTNET = 9999999,   // public test network trigger height
HARDFORK_HEIGHT_NOLNET  = 8888888,   // BU public no-limit test network  trigger height
HARDFORK_HEIGHT_REGTEST =     100,   // regression test network (local)  trigger height

// MVHF-BU-DES-NSEP-1 - network separation parameter defaults
// MVF-BU TODO: re-check that these port values could be used
HARDFORK_PORT_MAINNET = 9442,        // default post-fork port on operational network (mainnet)
HARDFORK_PORT_TESTNET = 9443,        // default post-fork port on public test network (testnet)
HARDFORK_PORT_NOLNET  = 9444,        // default post-fork port on BU public no-limit test network (nolnet)
HARDFORK_PORT_REGTEST = 19555,       // default post-fork port on local regression test network (regtestnet)

// MVHF-BU-DES-CSIG-1 - signature change parameter defaults
HARDFORK_SIGHASH_ID = 0x777000,      // 3 byte fork id that is left-shifted by 8 bits and then ORed with the SIGHASHes
MAX_HARDFORK_SIGHASH_ID = 0xFFFFFF,  // fork id may not exceed maximum representable in 3 bytes
};

// MVHF-BU-DES-NSEP-1 - network separation parameter defaults
// message start strings (network magic) after forking
// The message start string should be designed to be unlikely to occur in normal data.
// The characters are rarely used upper ASCII, not valid as UTF-8, and produce
// a large 32-bit integer with any alignment.
// MVF-BU TODO: Assign new netmagic values
// MVF-BU TODO: Clarify why it's ok for testnet to deviate from the above rationale.
//              One would expect regtestnet to be less important than a public network!
static const CMessageHeader::MessageStartChars pchMessageStart_HardForkMainnet  = { 0xf9, 0xbe, 0xb4, 0xd9 },
                                               pchMessageStart_HardForkNolnet   = { 0xfa, 0xce, 0xc4, 0xe9 },
                                               pchMessageStart_HardForkTestnet  = { 0x0b, 0x11, 0x09, 0x07 },
                                               pchMessageStart_HardForkRegtest  = { 0xf9, 0xbe, 0xb4, 0xd9 };

// MVHF-BU-DES-DIAD-1 - difficulty adjustment parameter defaults
// MVF-BU TODO: calibrate the values for public testnets according to estimated initial present hashpower
// values to which powLimit is reset at fork time on various networks:
static const uint256 HARDFORK_POWRESET_MAINNET = uint256S("00007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),  // mainnet
                     HARDFORK_POWRESET_TESTNET = uint256S("007fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),  // testnet
                     HARDFORK_POWRESET_NOLNET  = uint256S("3fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"),  // nolnet
                     HARDFORK_POWRESET_REGTEST = uint256S("7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");  // regtestnet


extern std::string ForkCmdLineHelp();  // fork-specific command line option help (MVHF-BU-DES-TRIG-8)
extern void ForkSetup(const CChainParams& chainparams);  // actions to perform at program setup (parameter validation etc.)
extern void ActivateFork(void);    // actions to perform at fork triggering (MVHF-BU-DES-TRIG-6)
extern void DeactivateFork(void);  // actions to revert if reorg deactivates fork (MVHF-BU-DES-TRIG-7)

#endif
