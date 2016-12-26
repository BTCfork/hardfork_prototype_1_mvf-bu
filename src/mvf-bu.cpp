// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common objects and functions

#include "mvf-bu.h"
#include "mvf-btcfork_conf_parser.h"
#include "init.h"
#include "util.h"
#include "utilstrencodings.h"   // for atoi64
#include "chainparams.h"
#include "validationinterface.h"

#include <iostream>
#include <fstream>
#include <boost/filesystem.hpp>
#include <boost/algorithm/string/replace.hpp>
#include <boost/exception/to_string_stub.hpp>

using namespace std;

// key-value maps for btcfork.conf configuration items
map<string, string> btcforkMapArgs;
map<string, vector<string> > btcforkMapMultiArgs;

// version string identifying the consensus-relevant algorithmic changes
// so that a user can quickly see if MVF fork clients are compatible
// for test purposes (since they may diverge during development/testing).
// A new value must be chosen whenever there are changes to consensus
// relevant functionality (excepting things which are parameterized).
// Values are surnames chosen from the name list of space travelers at
// https://en.wikipedia.org/wiki/List_of_space_travelers_by_name
std::string post_fork_consensus_id = "YAMAZAKI";

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

    // first, set initial values from built-in defaults
    FinalForkId = GetArg("-forkid", HARDFORK_SIGHASH_ID);

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
    if (mapArgs.count("-autobackupblock") == 0) {
        // default value for backup block is 1 block prior to fixed fork trigger
        mapArgs["-autobackupblock"] = FinalActivateForkHeight - 1;
    }

    // check if btcfork.conf exists (MVHF-BU-DES-TRIG-10)
    boost::filesystem::path pathBTCforkConfigFile(BTCFORK_CONF_FILENAME);
    if (!pathBTCforkConfigFile.is_complete())
        pathBTCforkConfigFile = GetDataDir(false) / pathBTCforkConfigFile;
    if (boost::filesystem::exists(pathBTCforkConfigFile)) {
        LogPrintf("%s: MVF: found marker config file at %s - client has already forked before\n", __func__, pathBTCforkConfigFile.string().c_str());
        // read the btcfork.conf file if it exists, override standard config values using its configuration
        try
        {
            MVFReadConfigFile(btcforkMapArgs, btcforkMapMultiArgs);
            if (btcforkMapArgs.count("-forkheight")) {
                FinalActivateForkHeight = atoi(btcforkMapArgs["-forkheight"]);
                mapArgs["-forkheight"] = FinalActivateForkHeight;
            }
            if (btcforkMapArgs.count("-autobackupblock")) {
                mapArgs["-autobackupblock"] = btcforkMapArgs["-autobackupblock"];
            }
            if (btcforkMapArgs.count("-forkid")) {
                FinalForkId = atoi(btcforkMapArgs["-forkid"]);
                mapArgs["-forkid"] = btcforkMapArgs["-forkid"];
            }
        } catch (const std::exception& e) {
            LogPrintf("MVF: Error reading %s configuration file: %s\n", BTCFORK_CONF_FILENAME, e.what());
            fprintf(stderr,"MVF: Error reading %s configuration file: %s\n", BTCFORK_CONF_FILENAME, e.what());
        }
        wasMVFHardForkPreviouslyActivated = true;
    }
    else {
        LogPrintf("%s: MVF: no marker config file at %s - client has not forked yet\n", __func__, pathBTCforkConfigFile.string().c_str());
        wasMVFHardForkPreviouslyActivated = false;
    }

    // validation

    // shut down immediately if specified fork height is invalid
    if (FinalActivateForkHeight <= 0)
    {
        LogPrintf("MVF: Error: specified fork height (%d) is less than minimum for '%s' network (%d)\n", FinalActivateForkHeight, activeNetworkID, minForkHeightForNetwork);
        StartShutdown();
    }

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

    // debug traces of final values
    LogPrintf("%s: MVF: fork consensus code = %s\n", __func__, post_fork_consensus_id);
    LogPrintf("%s: MVF: active network = %s\n", __func__, activeNetworkID);
    LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);
    LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
    if (GetBoolArg("-segwitfork", DEFAULT_TRIGGER_ON_SEGWIT))
        LogPrintf("%s: MVF: Segregated Witness trigger is ENABLED\n", __func__);
    else
        LogPrintf("%s: MVF: Segregated Witness trigger is DISABLED\n", __func__);
    LogPrintf("%s: MVF: auto backup block = %d\n", __func__, atoi(mapArgs["-autobackupblock"]));

    if (GetBoolArg("-force-retarget", DEFAULT_FORCE_RETARGET))
        LogPrintf("%s: MVF: force-retarget is ENABLED\n", __func__);
    else
        LogPrintf("%s: MVF: force-retarget is DISABLED\n", __func__);

    // we should always set the activation flag to false during setup
    isMVFHardForkActive = false;
}

boost::filesystem::path MVFGetConfigFile()
{
    boost::filesystem::path pathConfigFile(BTCFORK_CONF_FILENAME);
    if (!pathConfigFile.is_complete())
        pathConfigFile = GetDataDir(false) / pathConfigFile;

    return pathConfigFile;
}

/** Actions when the fork triggers (MVHF-BU-DES-TRIG-6) */
// doBackup parameter default is true
void ActivateFork(int actualForkHeight, bool doBackup)
{
    LogPrintf("%s: MVF: checking whether to perform fork activation\n", __func__);
    if (!isMVFHardForkActive && !wasMVFHardForkPreviouslyActivated)  // sanity check to protect the one-off actions
    {
        LogPrintf("%s: MVF: performing fork activation actions\n", __func__);

        // set so that we capture the actual height at which it forked
        // because this can be different from user-specified configuration
        // (e.g. soft-fork activated)
        FinalActivateForkHeight = actualForkHeight;

        boost::filesystem::path pathBTCforkConfigFile(MVFGetConfigFile());
        LogPrintf("%s: MVF: checking for existence of %s\n", __func__, pathBTCforkConfigFile.string().c_str());

        // remove btcfork.conf if it already exists - it shall be overwritten
        if (boost::filesystem::exists(pathBTCforkConfigFile)) {
            LogPrintf("%s: MVF: removing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
            try {
                boost::filesystem::remove(pathBTCforkConfigFile);
            } catch (const boost::filesystem::filesystem_error& e) {
                LogPrintf("%s: MVF: Unable to remove %s config file: %s\n", __func__, pathBTCforkConfigFile.string().c_str(), e.what());
            }
        }
        // try to write the btcfork.conf (MVHF-BU-DES-TRIG-10)
        LogPrintf("%s: MVF: writing %s\n", __func__, pathBTCforkConfigFile.string().c_str());
        std::ofstream  btcforkfile(pathBTCforkConfigFile.string().c_str(), std::ios::out);
        btcforkfile << "forkheight=" << FinalActivateForkHeight << "\n";
        btcforkfile << "forkid=" << FinalForkId << "\n";

        LogPrintf("%s: MVF: active fork height = %d\n", __func__, FinalActivateForkHeight);
        LogPrintf("%s: MVF: active fork id = 0x%06x (%d)\n", __func__, FinalForkId, FinalForkId);

        // MVF-BU begin MVHF-BU-DES-WABU-3
        // check if we need to do wallet auto backup at fork block
        // this is in case of soft-fork triggered activation
        // MVF-BU TODO: reduce code duplication between this block and main.cpp:UpdateTip()
        if (doBackup && !fAutoBackupDone)
        {
            std::string strWalletBackupFile = GetArg("-autobackupwalletpath", "");
            int BackupBlock = actualForkHeight;

            //LogPrintf("MVF DEBUG: autobackupwalletpath=%s\n",strWalletBackupFile);
            //LogPrintf("MVF DEBUG: autobackupblock=%d\n",BackupBlock);

            if (GetBoolArg("-disablewallet", false))
            {
                LogPrintf("MVF: -disablewallet and -autobackupwalletpath conflict so automatic backup disabled.");
                fAutoBackupDone = true;
            }
            else {
                // Auto Backup defined, but no need to check block height since
                // this is fork activation time and we still have not backed up
                // so just get on with it
                if (GetMainSignals().BackupWalletAuto(strWalletBackupFile, BackupBlock))
                    fAutoBackupDone = true;
                else {
                    // shutdown in case of wallet backup failure (MVHF-BU-DES-WABU-5)
                    // MVF-BU TODO: investigate if this is safe in terms of wallet flushing/closing or if more needs to be done
                    btcforkfile << "error: unable to perform automatic backup - exiting" << "\n";
                    btcforkfile.close();
                    throw std::runtime_error("CWallet::BackupWalletAuto() : Auto wallet backup failed!");
                }
            }
            btcforkfile << "autobackupblock=" << FinalActivateForkHeight << "\n";
            LogPrintf("%s: MVF: soft-forked auto backup block = %d\n", __func__, FinalActivateForkHeight);

        }
        else {
            // auto backup was already made pre-fork - emit parameters
            btcforkfile << "autobackupblock=" << GetArg("-autobackupblock", FinalActivateForkHeight - 1) << "\n";
            LogPrintf("%s: MVF: height-based auto backup block = %d\n", __func__, GetArg("-autobackupblock", FinalActivateForkHeight - 1));
        }

        // close fork parameter file
        btcforkfile.close();
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


/** returns the finalized path of the auto wallet backup file (MVHF-BU-DES-WABU-2) */
std::string MVFexpandWalletAutoBackupPath(const std::string& strDest, const std::string& strWalletFile, int BackupBlock, bool createDirs)
{
    boost::filesystem::path pathBackupWallet = strDest;

    //if the backup destination is blank
    if (strDest == "")
    {
        // then prefix it with the existing data dir and wallet filename
        pathBackupWallet = GetDataDir() / strprintf("%s.%s",strWalletFile, autoWalletBackupSuffix);
    }
    else {
        if (pathBackupWallet.is_relative())
            // prefix existing data dir
            pathBackupWallet = GetDataDir() / pathBackupWallet;

        // if pathBackupWallet is a folder or symlink, or if it does end
        // on a filename with an extension...
        if (!pathBackupWallet.has_extension() || (boost::filesystem::is_directory(pathBackupWallet) && boost::filesystem::is_symlink(pathBackupWallet)))
            // ... we assume no custom filename so append the default filename
            pathBackupWallet /= strprintf("%s.%s",strWalletFile, autoWalletBackupSuffix);

        if (pathBackupWallet.branch_path() != "" && createDirs)
            // create directories if they don't exist
            // MVF-BU TODO: this directory creation should be factored out
            // so that we do not need to pass a Boolean arg and this function
            // should not have the side effect. Marked for cleanup.
            boost::filesystem::create_directories(pathBackupWallet.branch_path());
    }

    std::string strBackupFile = pathBackupWallet.string();

    // replace # with BackupBlock number
    boost::replace_all(strBackupFile,"@", boost::to_string_stub(BackupBlock));
    //LogPrintf("DEBUG: strBackupFile=%s\n",strBackupFile);

    return strBackupFile;
}

// get / set functions for btcforkMapArgs
std::string MVFGetArg(const std::string& strArg, const std::string& strDefault)
{
    if (btcforkMapArgs.count(strArg))
        return btcforkMapArgs[strArg];
    return strDefault;
}

int64_t MVFGetArg(const std::string& strArg, int64_t nDefault)
{
    if (btcforkMapArgs.count(strArg))
        return atoi64(btcforkMapArgs[strArg]);
    return nDefault;
}

bool MVFGetBoolArg(const std::string& strArg, bool fDefault)
{
    if (btcforkMapArgs.count(strArg))
        return InterpretBool(btcforkMapArgs[strArg]);
    return fDefault;
}

bool MFVSoftSetArg(const std::string& strArg, const std::string& strValue)
{
    if (btcforkMapArgs.count(strArg))
        return false;
    btcforkMapArgs[strArg] = strValue;
    return true;
}

bool MFVSoftSetBoolArg(const std::string& strArg, bool fValue)
{
    if (fValue)
        return SoftSetArg(strArg, std::string("1"));
    else
        return SoftSetArg(strArg, std::string("0"));
}
