// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common objects and functions

#include "mvf-bu.h"
#include "init.h"
#include "util.h"
#include "chainparams.h"

#include <iostream>
#include <fstream>
#include <boost/filesystem.hpp>

using namespace std;

// actual fork height, taking into account user configuration parameters (MVHF-BU-DES-TRIG-4)
int FinalActivateForkHeight = 0;

// actual fork id, taking into account user configuration parameters (MVHF-BU-DES-CSIG-1)
int FinalForkId = 0;

// track whether HF has been activated before in previous run (MVHF-BU-DES-TRIG-5)
// is set at startup based on btcfork.conf presence
bool wasMVFHardForkPreviouslyActivated = false;

// track whether HF is active (MVHF-BU-DES-TRIG-5)
bool isMVFHardForkActive = false;

// track whether auto wallet backup might still need to be done
// this is set to true at startup if client detects fork already triggered
// otherwise when the backup is made. (MVHF-BU-DES-WABU-1)
bool fAutoBackupDone = false;

// default suffix to append to wallet filename for auto backup (MVHF-BU-DES-WABU-1)
std::string autoWalletBackupSuffix = "auto.@.bak";


/** Add MVF-specific command line options (MVHF-BU-DES-TRIG-8) */
std::string ForkCmdLineHelp()
{
    std::string strUsage;
    strUsage += HelpMessageGroup(_("Bitcoin MVF-BU Options:"));

    // automatic wallet backup parameters (MVHF-BU-DES-WABU-1)
    strUsage += HelpMessageOpt("-autobackupwalletpath=<path>", _("Automatically backup the wallet to the autobackupwalletfile path after the block specified becomes the best block (-autobackupblock). Default: Enabled"));
    strUsage += HelpMessageOpt("-autobackupblock=<n>", _("Specify the block number that triggers the automatic wallet backup. Default: forkheight-1"));

    // fork height parameter (MVHF-BU-DES-TRIG-1)
    strUsage += HelpMessageOpt("-forkheight=<n>", strprintf(_("Block height at which to fork on active network (integer). Defaults (also minimums): mainnet:%u,testnet=%u,nolnet=%u,regtest=%u"), (unsigned)HARDFORK_HEIGHT_MAINNET, (unsigned)HARDFORK_HEIGHT_TESTNET, (unsigned)HARDFORK_HEIGHT_NOLNET, (unsigned)HARDFORK_HEIGHT_REGTEST));

    // fork id (MVHF-BU-DES-CSIG-1)
    strUsage += HelpMessageOpt("-forkid=<n>", strprintf(_("Fork id to use for signature change. Value must be between 0 and %d. Default is 0x%06x (%u)"), (unsigned)MAX_HARDFORK_SIGHASH_ID, (unsigned)HARDFORK_SIGHASH_ID, (unsigned)HARDFORK_SIGHASH_ID));

    return strUsage;
}


/** Performs fork-related setup / validation actions when the program starts */
void ForkSetup(const CChainParams& chainparams)
{
    int minForkHeightForNetwork = 0;
    std:string activeNetworkID = chainparams.NetworkIDString();

    LogPrintf("%s: MVF: doing setup\n", __func__);
    LogPrintf("%s: MVF: active network = %s\n", __func__, activeNetworkID);

    // determine minimum fork height according to network
    // (these are set to the same as the default fork heights for now, but could be made different)
    if (activeNetworkID == CBaseChainParams::MAIN)
        minForkHeightForNetwork = HARDFORK_HEIGHT_MAINNET;
    else if (activeNetworkID == CBaseChainParams::TESTNET)
        minForkHeightForNetwork = HARDFORK_HEIGHT_TESTNET;
    else if (activeNetworkID == CBaseChainParams::REGTEST)
        minForkHeightForNetwork = HARDFORK_HEIGHT_REGTEST;
    else if (activeNetworkID == CBaseChainParams::UNL)
        minForkHeightForNetwork = HARDFORK_HEIGHT_NOLNET;
    else
        throw std::runtime_error(strprintf("%s: Unknown chain %s.", __func__, activeNetworkID));

    FinalActivateForkHeight = GetArg("-forkheight", minForkHeightForNetwork);

    // shut down immediately if specified fork height is invalid
    if (FinalActivateForkHeight < minForkHeightForNetwork)
    {
        LogPrintf("MVF: Error: specified fork height (%d) is less than minimum for '%s' network (%d)\n", FinalActivateForkHeight, activeNetworkID, minForkHeightForNetwork);
        StartShutdown();
    }

    FinalForkId = GetArg("-forkid", HARDFORK_SIGHASH_ID);
    // check fork id for validity (MVHF-BU-DES-CSIG-2)
    if (FinalForkId == 0) {
        LogPrintf("MVF: Warning: fork id = 0 will result in vulnerability to replay attacks\n");
    }
    else {
        if (FinalForkId < 0 || FinalForkId > MAX_HARDFORK_SIGHASH_ID) {
            LogPrintf("MVF: Error: specified fork id (%d) is not in range 0..%u\n", FinalForkId, (unsigned)MAX_HARDFORK_SIGHASH_ID);
            StartShutdown();
        }
    }

    LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
    LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);
    LogPrintf("%s: MVF: auto backup block = %d\n", __func__, GetArg("-autobackupblock", FinalForkId - 1));

    // check if btcfork.conf exists (MVHF-BU-DES-TRIG-10)
    boost::filesystem::path pathBTCforkConfigFile(BTCFORK_CONF_FILENAME);
    if (!pathBTCforkConfigFile.is_complete())
        pathBTCforkConfigFile = GetDataDir(false) / pathBTCforkConfigFile;
    if (boost::filesystem::exists(pathBTCforkConfigFile)) {
        LogPrintf("%s: MVF: found marker config file at %s - client has already forked before\n", __func__, pathBTCforkConfigFile.string().c_str());
        wasMVFHardForkPreviouslyActivated = true;
    }
    else {
        LogPrintf("%s: MVF: no marker config file at %s - client has not forked yet\n", __func__, pathBTCforkConfigFile.string().c_str());
        wasMVFHardForkPreviouslyActivated = false;
    }

    // we should always set the activation flag to false during setup
    isMVFHardForkActive = false;
}


/** Actions when the fork triggers (MVHF-BU-DES-TRIG-6) */
void ActivateFork(void)
{
    LogPrintf("%s: MVF: checking whether to perform fork activation\n", __func__);
    if (!isMVFHardForkActive && !wasMVFHardForkPreviouslyActivated)  // sanity check to protect the one-off actions
    {
        LogPrintf("%s: MVF: performing fork activation actions\n", __func__);

        boost::filesystem::path pathBTCforkConfigFile(BTCFORK_CONF_FILENAME);
        if (!pathBTCforkConfigFile.is_complete())
            pathBTCforkConfigFile = GetDataDir(false) / pathBTCforkConfigFile;

        LogPrintf("%s: MVF: checking for existence of %s\n", __func__, pathBTCforkConfigFile.string().c_str());

        // remove btcfork.conf if it already exists - it shall be overwritten
        if (boost::filesystem::exists(pathBTCforkConfigFile)) {
            LogPrintf("%s: MVF: removing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
            try {
                boost::filesystem::remove(pathBTCforkConfigFile);
            } catch (const boost::filesystem::filesystem_error& e) {
                LogPrintf("%s: Unable to remove pidfile: %s\n", __func__, e.what());
            }
        }
        // try to write the btcfork.conf (MVHF-BU-DES-TRIG-10)
        LogPrintf("%s: MVF: writing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
        std::ofstream  btcforkfile(pathBTCforkConfigFile.string().c_str(), std::ios::out);
        btcforkfile << "forkheight=" << FinalActivateForkHeight << "\n";
        btcforkfile << "forkid=" << FinalForkId << "\n";
        btcforkfile << "autobackupblock=" << GetArg("-autobackupblock", FinalActivateForkHeight - 1) << "\n";
        btcforkfile.close();

        LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
        LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);
        LogPrintf("%s: MVF: auto backup block = %d\n", __func__, GetArg("-autobackupblock", FinalForkId - 1));
    }
    // set the flag so that other code knows HF is active
    LogPrintf("%s: MVF: enabling isMVFHardForkActive\n", __func__);
    isMVFHardForkActive = true;
}


/** Actions when the fork is deactivated in reorg (MVHF-BU-DES-TRIG-7) */
void DeactivateFork(void)
{
    LogPrintf("%s: MVF: checking whether to perform fork deactivation\n", __func__);
    if (isMVFHardForkActive)
    {
        LogPrintf("%s: MVF: performing fork deactivation actions\n", __func__);
    }
    LogPrintf("%s: MVF: disabling isMVFHardForkActive\n", __func__);
    isMVFHardForkActive = false;
}
