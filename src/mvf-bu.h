// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common declarations

#pragma once
#ifndef BITCOIN_MVF_BU_H
#define BITCOIN_MVF_BU_H

#include <boost/filesystem.hpp>

#include "mvf-bu-globals.h"

class CChainParams;

//extern std::string ForkCmdLineHelp();  // fork-specific command line option help (MVHF-BU-DES-TRIG-8)
extern boost::filesystem::path MVFGetConfigFile();  // get the full path to the btcfork.conf file
extern bool ForkSetup(const CChainParams& chainparams);  // actions to perform at program setup (parameter validation etc.)
extern void ActivateFork(int actualForkHeight, bool doBackup=true);  // actions to perform at fork triggering (MVHF-BU-DES-TRIG-6)
extern void DeactivateFork(void);  // actions to revert if reorg deactivates fork (MVHF-BU-DES-TRIG-7)
extern std::string MVFexpandWalletAutoBackupPath(const std::string& strDest, const std::string& strWalletFile, int BackupBlock, bool createDirs=true); // returns the finalized path of the auto wallet backup file (MVHF-BU-DES-WABU-2)
extern std::string MVFGetArg(const std::string& strArg, const std::string& strDefault);
extern int64_t MVFGetArg(const std::string& strArg, int64_t nDefault);
extern bool MVFGetBoolArg(const std::string& strArg, bool fDefault);
extern bool MFVSoftSetArg(const std::string& strArg, const std::string& strValue);
extern bool MFVSoftSetBoolArg(const std::string& strArg, bool fValue);

#endif
