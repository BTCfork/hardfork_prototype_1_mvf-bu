// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2015 The Bitcoin Core developers
// Copyright (c) 2015-2016 The Bitcoin Unlimited developers
// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef BITCOIN_CONSENSUS_PARAMS_H
#define BITCOIN_CONSENSUS_PARAMS_H

#include "uint256.h"
#include <map>
#include <string>
#include <math.h>    // MVF-BU added
#include "mvf-bu.h"  // MVF-BU added

namespace Consensus {

enum DeploymentPos
{
    DEPLOYMENT_TESTDUMMY,
    DEPLOYMENT_CSV, // Deployment of BIP68, BIP112, and BIP113.
    DEPLOYMENT_SEGWIT, // MVF-BU added for trigger on SegWit (BIP141/143/147) activation
    MAX_VERSION_BITS_DEPLOYMENTS
};

/**
 * Struct for each individual consensus rule change using BIP9.
 */
struct BIP9Deployment {
    /** Bit position to select the particular bit in nVersion. */
    int bit;
    /** Start MedianTime for version bits miner confirmation. Can be a date in the past */
    int64_t nStartTime;
    /** Timeout/expiry MedianTime for the deployment attempt. */
    int64_t nTimeout;
};

/**
 * Parameters that influence chain consensus.
 */
struct Params {
    uint256 hashGenesisBlock;
    int nSubsidyHalvingInterval;
    /** Used to check majorities for block version upgrade */
    int nMajorityEnforceBlockUpgrade;
    int nMajorityRejectBlockOutdated;
    int nMajorityWindow;
    /** Block height and hash at which BIP34 becomes active */
    int BIP34Height;
    uint256 BIP34Hash;
    /**
     * Minimum blocks including miner confirmation of the total of 2016 blocks in a retargetting period,
     * (nPowTargetTimespan / nPowTargetSpacing) which is also used for BIP9 deployments.
     * Examples: 1916 for 95%, 1512 for testchains.
     */
    uint32_t nRuleChangeActivationThreshold;
    uint32_t nMinerConfirmationWindow;
    BIP9Deployment vDeployments[MAX_VERSION_BITS_DEPLOYMENTS];
    /** Proof of work parameters */
    uint256 powLimit;
    bool fPowAllowMinDifficultyBlocks;
    bool fPowNoRetargeting;
    int64_t nPowTargetSpacing;
    int64_t nPowTargetTimespan;

    int MVFRetargetPeriodEnd() const { return FinalActivateForkHeight + HARDFORK_RETARGET_BLOCKS; }

    // return height-dependent target time span used to compute retargeting interval (MVHF-BU-DES-DIAD-4)
    int64_t MVFPowTargetTimespan(int Height) const
    {
        if (MVFisWithinRetargetPeriod(Height))
        {
            int MVFHeight = Height - FinalActivateForkHeight;

            switch (MVFHeight)
            {
                case    0 ... 7         : return nPowTargetSpacing;          // 10 minutes

                case    8 ... 46        : return nPowTargetSpacing * 6;      // 1 hour

                case    47 ... 153      : return nPowTargetSpacing * 36;     // 6 hours

                case    154 ... 299     : return nPowTargetSpacing * 72;    // 12 hours

                case    300 ... 1299     : return nPowTargetSpacing * 144;   // 24 hours - 1 day

                case    1300 ... 4999   : return nPowTargetSpacing * 288;   // 48 hours - 2 days

                case    5000 ... 9999   : return nPowTargetSpacing * 432;   // 72 hours - 3 days

                case    10000 ... 14999 : return nPowTargetSpacing * 576;   // 96 hours - 4 days

                case    15000 ... HARDFORK_RETARGET_BLOCKS : return nPowTargetSpacing * 1152;  // 192 hours - 8 days

                default : return nPowTargetTimespan;    // original 14 days
            }
        }
        else return nPowTargetTimespan;
    }

    bool MVFisWithinRetargetPeriod(int Height) const
    {
        if (Height >= FinalActivateForkHeight)
            return true;
        else
            return false;
    }
    int64_t DifficultyAdjustmentInterval() const { return nPowTargetTimespan / nPowTargetSpacing; }
    int64_t DifficultyAdjustmentInterval(int Height) const
    {
        // MVF-BU:
        // if outside the MVFRetargetPeriod then use the original values
        // otherwise use a height-dependent window size
        if (MVFisWithinRetargetPeriod(Height)) {
           // re-target MVF
            int MVFHeight = Height - FinalActivateForkHeight;
            switch (MVFHeight)
            {
                case    0 ... 2016:         return 1;           // every block (abrupt retargeting permitted)

                case    2017 ... 3999:      return 10;         // every 10 blocks

                case    4000 ... 9999:      return 40;        // every 40 blocks

                case    10000 ... 14999:    return 100;     // every 100 blocks

                case    15000 ... 19999:    return 400;    // every 400 blocks

                case    20000 ... HARDFORK_RETARGET_BLOCKS:    return 1000;  // every 1000 blocks

                default : return 2016;                      // every 2016 blocks
            }
        }
        else {
           // re-target original (MVHF-BU-DES-DIAD-4)
           return nPowTargetTimespan / nPowTargetSpacing;
        }
    }
    // MVF-BU end

    int64_t SizeForkExpiration() const { return 1514764800; } // BU (classic compatibility) 2018-01-01 00:00:00 GMT

};
} // namespace Consensus

#endif // BITCOIN_CONSENSUS_PARAMS_H
