// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common objects and functions

#include "mvf-bu.h"
#include "init.h"
#include "util.h"
#include "chainparams.h"

using namespace std;

// actual fork height, taking into account user configuration parameters (MVHF-BU-DES-TRIG-4)
int FinalActivateForkHeight = 0;

// track whether HF is active (MVHF-BU-DES-TRIG-5)
bool isMVFHardForkActive = false;

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

    return strUsage;
}


/** Performs fork-related setup / validation actions when the program starts */
void ForkSetup(const CChainParams& chainparams)
{
    int minForkHeightForNetwork = 0;
    std:string activeNetworkID = chainparams.NetworkIDString();

    LogPrintf("%s: MVF: doing setup\n", __func__);
    LogPrintf("%s: MVF: active network = %s\n", __func__, activeNetworkID);
    FinalActivateForkHeight = GetArg("-forkheight", chainparams.GetConsensus().nMVFActivateForkHeight);

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

    // shut down immediately if specified fork height is invalid
    if (FinalActivateForkHeight < minForkHeightForNetwork)
    {
        LogPrintf("MVF: Error: specified fork height (%d) is less than minimum for '%s' network (%d)\n", FinalActivateForkHeight, activeNetworkID, minForkHeightForNetwork);
        StartShutdown();
        FinalActivateForkHeight = minForkHeightForNetwork;
    }

    // we should always set the activation flag to false during setup
    isMVFHardForkActive = false;

    LogPrintf("%s: MVF: ForkSetup() active fork height = %d\n", __func__, FinalActivateForkHeight);
}


/** Actions when the fork triggers (MVHF-BU-DES-TRIG-6) */
void ActivateFork(void)
{
    LogPrintf("%s: MVF: checking whether to perform fork activation\n", __func__);
    if (!isMVFHardForkActive)
    {
        LogPrintf("%s: MVF: performing fork activation actions\n", __func__);
        isMVFHardForkActive = true;
    }
}


/** Actions when the fork is deactivated in reorg (MVHF-BU-DES-TRIG-7) */
void DeactivateFork(void)
{
    LogPrintf("%s: MVF: checking whether to perform fork deactivation\n", __func__);
    if (isMVFHardForkActive)
    {
        LogPrintf("%s: MVF: performing fork deactivation actions\n", __func__);
        isMVFHardForkActive = false;
    }
}
