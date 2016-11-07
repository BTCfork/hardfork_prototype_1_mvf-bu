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
#include <math.h>  //MVF-BU
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

    // MVF-BU begin (MVHF-BU-DES-TRIG-3)
    int nMVFDefaultActivateForkHeight;     // trigger block height

    int MVFDefaultActivateForkHeight() const { return nMVFDefaultActivateForkHeight; };

    int MVFRetargetPeriodEnd() const { return  FinalActivateForkHeight + (180 * 24 * 60 * 60 / nPowTargetSpacing); }

    int64_t MVFPowTargetTimespan(int Height) const
    {
    	int MVFHeight = Height - FinalActivateForkHeight;

    	switch (MVFHeight)
    	{
    		case 	1 ...
					10: return nPowTargetSpacing;			// 10 minutes (abrupt retargeting permitted)

    		case 	11 ...
					40: return nPowTargetSpacing * 3;		// 30 minutes

    		case	41 ...
					101: return nPowTargetSpacing * 6; 		// 1 hour

    		case	102 ...
					2000: return nPowTargetSpacing * 6 * 3; // 3 hours

    		default : return nPowTargetSpacing * 6 * 12; 	// 12 hours
    	}

    }

    bool MVFisWithinRetargetPeriod(int Height) const
    {
 	   if (Height >= FinalActivateForkHeight && Height < MVFRetargetPeriodEnd() )
 		   return true;
 	   else
 		   return false;
    }

    int64_t DifficultyAdjustmentInterval(int Height) const
   {
	   // mvhf-bu - if outside the MVFRetargetPeriod then use the original values
	   if (MVFisWithinRetargetPeriod(Height))
		   // re-target MVF
		   return MVFPowTargetTimespan(Height) / nPowTargetSpacing;
	   else // re-target original
		   return nPowTargetTimespan / nPowTargetSpacing;
   }

    // MVF-BU end

    int64_t SizeForkExpiration() const { return 1514764800; } // BU (classic compatibility) 2018-01-01 00:00:00 GMT


};
} // namespace Consensus

#endif // BITCOIN_CONSENSUS_PARAMS_H
