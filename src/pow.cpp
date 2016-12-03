// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2015 The Bitcoin Core developers
// Copyright (c) 2015-2016 The Bitcoin Unlimited developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "pow.h"

#include "arith_uint256.h"
#include "chain.h"
#include "primitives/block.h"
#include "uint256.h"
#include "util.h"
#include "mvf-bu.h"  // MVF-BU added

unsigned int GetNextWorkRequired(const CBlockIndex* pindexLast, const CBlockHeader *pblock, const Consensus::Params& params)
{
    // MVF-BU begin difficulty re-targeting
    if (params.MVFisWithinRetargetPeriod(pindexLast->nHeight+1))
        return GetMVFNextWorkRequired(pindexLast, pblock, params);
    // MVF-BU end

    unsigned int nProofOfWorkLimit = UintToArith256(params.powLimit).GetCompact();

    // Genesis block
    if (pindexLast == NULL)
        return nProofOfWorkLimit;

    // Only change once per difficulty adjustment interval
    if ((pindexLast->nHeight+1) % params.DifficultyAdjustmentInterval() != 0)
    {
        // MVF-BU: added force-retarget parameter to enable adjusting difficulty for regtest tests
        if (params.fPowAllowMinDifficultyBlocks && !GetBoolArg("-force-retarget", DEFAULT_FORCE_RETARGET))
        {
            // Special difficulty rule for testnet:
            // If the new block's timestamp is more than 2* 10 minutes
            // then allow mining of a min-difficulty block.
            if (pblock->GetBlockTime() > pindexLast->GetBlockTime() + params.nPowTargetSpacing*2)
                return nProofOfWorkLimit;
            else
            {
                // Return the last non-special-min-difficulty-rules-block
                const CBlockIndex* pindex = pindexLast;
                while (pindex->pprev && pindex->nHeight % params.DifficultyAdjustmentInterval() != 0 && pindex->nBits == nProofOfWorkLimit)
                    pindex = pindex->pprev;
                return pindex->nBits;
            }
        }
        return pindexLast->nBits;
    }

    // Go back by what we want to be 14 days worth of blocks
    int nHeightFirst = pindexLast->nHeight - (params.DifficultyAdjustmentInterval()-1);
    assert(nHeightFirst >= 0);
    const CBlockIndex* pindexFirst = pindexLast->GetAncestor(nHeightFirst);
    assert(pindexFirst);

    return CalculateNextWorkRequired(pindexLast, pindexFirst->GetBlockTime(), params);
}

unsigned int CalculateNextWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    // MVF-BU: added force-retarget parameter to enable adjusting difficulty for regtest tests
    if (params.fPowNoRetargeting && !GetBoolArg("-force-retarget", DEFAULT_FORCE_RETARGET))
        return pindexLast->nBits;

    // Limit adjustment step
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;
    LogPrintf("  nActualTimespan = %d  before bounds\n", nActualTimespan);
    if (nActualTimespan < params.nPowTargetTimespan/4)
        nActualTimespan = params.nPowTargetTimespan/4;
    if (nActualTimespan > params.nPowTargetTimespan*4)
        nActualTimespan = params.nPowTargetTimespan*4;

    // Retarget
    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit);
    arith_uint256 bnNew;
    arith_uint256 bnOld;
    bnNew.SetCompact(pindexLast->nBits);
    bnOld = bnNew;
    bnNew *= nActualTimespan;
    if (bnNew / nActualTimespan != bnOld) bnNew = bnPowLimit; else //MVF-BU Add overflow handle
    bnNew /= params.nPowTargetTimespan;

    if (bnNew > bnPowLimit)
        bnNew = bnPowLimit;

    /// debug print
    LogPrintf("GetNextWorkRequired RETARGET\n");
    LogPrintf("params.nPowTargetTimespan = %d    nActualTimespan = %d\n", params.nPowTargetTimespan, nActualTimespan);
    LogPrintf("Before: %08x  %s\n", pindexLast->nBits, bnOld.ToString());
    LogPrintf("After:  %08x  %s\n", bnNew.GetCompact(), bnNew.ToString());

    return bnNew.GetCompact();
}

// MVF-BU begin: difficulty functions
// TODO: Move these functions into mvf-bu.cpp
unsigned int GetMVFNextWorkRequired(const CBlockIndex* pindexLast, const CBlockHeader *pblock, const Consensus::Params& params)
{
    unsigned int nProofOfWorkLimit = UintToArith256(params.powLimit).GetCompact();

    LogPrintf("MVF NEXT WORK DifficultyAdjInterval = %d , TargetTimeSpan = %d \n",
            params.DifficultyAdjustmentInterval(pindexLast->nHeight),
            params.MVFPowTargetTimespan(pindexLast->nHeight));

    // Genesis block
    if (pindexLast == NULL) return nProofOfWorkLimit;

    int nHeightFirst = pindexLast->nHeight - (params.MVFPowTargetTimespan(pindexLast->nHeight) / params.nPowTargetSpacing);
    if (nHeightFirst < 0) nHeightFirst = 0;
    const CBlockIndex* pindexFirst = pindexLast->GetAncestor(nHeightFirst);
    assert(pindexFirst);

    if (pindexLast->nHeight == FinalActivateForkHeight - 1)
    {
        // MVF-BU difficulty re-targeting reset (MVHF-BU-DES-DIAD-2)
        return CalculateMVFResetWorkRequired(pindexLast, pindexFirst->GetBlockTime(), params);
    }
    else
    {
        // Only change once per difficulty adjustment interval
        if ((pindexLast->nHeight+1) % params.DifficultyAdjustmentInterval(pindexLast->nHeight) != 0)  // MVF-BU: use height-dependent interval
        {
            // MVF-BU: added force parameter to enable adjusting difficulty for regtest tests
            if (params.fPowAllowMinDifficultyBlocks && !GetBoolArg("-force-retarget", false))
            {
                // TODO: CAUTION THIS CODE IS OUTSIDE REGTEST FRAMEWORK
                // Special difficulty rule for testnet:
                // If the new block's timestamp is more than 2* 10 minutes
                // then allow mining of a min-difficulty block.
                if (pblock->GetBlockTime() > pindexLast->GetBlockTime() + params.nPowTargetSpacing*2)
                    return nProofOfWorkLimit;
                else
                {
                    // Return the last non-special-min-difficulty-rules-block
                    const CBlockIndex* pindex = pindexLast;
                    // MVF-BU: use height-dependent interval
                    while (pindex->pprev && pindex->nHeight % params.DifficultyAdjustmentInterval(pindex->nHeight) != 0 && pindex->nBits == nProofOfWorkLimit)
                        pindex = pindex->pprev;
                    return pindex->nBits;
                }
            }
            return pindexLast->nBits;
        }
        LogPrintf("MVF RETARGET");
        return CalculateMVFNextWorkRequired(pindexLast, pindexFirst->GetBlockTime(), params);

    } // end fork reset
}

unsigned int CalculateMVFNextWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    bool force_retarget=GetBoolArg("-force-retarget", DEFAULT_FORCE_RETARGET);  // MVF-BU added for retargeting tests on regtestnet (MVHF-BU-DES-DIAD-6)
    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit); // MVF-BU moved here

    if (params.fPowNoRetargeting && !force_retarget)
        return pindexLast->nBits;

    // Limit adjustment step
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;
    // MVF-BU begin check for abnormal condition
    // This actually occurred during testing, resulting in new target == 0
    // which could never be met
    if (nActualTimespan == 0) {
        LogPrintf("  MVF: nActualTimespan == 0, returning bnPowLimit\n");
         return bnPowLimit.GetCompact();
    }
    // MVF-BU end
    LogPrintf("  MVF: nActualTimespan = %d  before bounds\n", nActualTimespan);

    // MVF-BU begin
    // Since in MVF fork recovery period, use faster retarget time span dependent on height (MVHF-BU-DES-DIAD-3)
    int nTargetTimespan = params.MVFPowTargetTimespan(pindexLast->nHeight);

    // permit x10 retarget changes for a few blocks after the fork i.e. when nTargetTimespan is < 30 minutes (MVHF-BU-DES-DIAD-5)
    int retargetLimit;
    if (nTargetTimespan >= params.nPowTargetSpacing * 3)
        retargetLimit = 4; else retargetLimit = 10;

    // prevent abrupt changes to target
    if (nActualTimespan < nTargetTimespan/retargetLimit)
        nActualTimespan = nTargetTimespan/retargetLimit;
    if (nActualTimespan > nTargetTimespan*retargetLimit)
        nActualTimespan = nTargetTimespan*retargetLimit;
    // MVF-BU end

    // Retarget
    arith_uint256 bnNew, bnNew1, bnNew2, bnOld;
    bnOld.SetCompact(pindexLast->nBits);
    // MVF-BU begin: move division before multiplication
    // at regtest difficulty, the multiplication is prone to overflowing
    bnNew1 = bnOld / nTargetTimespan;
    bnNew2 = bnNew1 * nActualTimespan;

    // Test for overflow
    if (bnNew2 / nActualTimespan != bnNew1)
    {
        bnNew = bnPowLimit;
        LogPrintf("MVF GetNextWorkRequired OVERFLOW\n");
    }
    else if (bnNew2 > bnPowLimit)
    {
        bnNew = bnPowLimit;
        LogPrintf("MVF GetNextWorkRequired OVERLIMIT\n");
    }
    else
        bnNew = bnNew2;
    // MVF-BU end

    /// debug print
    LogPrintf("GetNextWorkRequired RETARGET\n");
    LogPrintf("nTargetTimespan = %d    nActualTimespan = %d\n", nTargetTimespan, nActualTimespan);
    LogPrintf("Before: %08x  %s\n", pindexLast->nBits, bnOld.ToString());
    LogPrintf("After:  %08x  %s\n", bnNew.GetCompact(), bnNew.ToString());

    return bnNew.GetCompact();
}

/** Perform the fork difficulty reset */
unsigned int CalculateMVFResetWorkRequired(const CBlockIndex* pindexLast, int64_t nFirstBlockTime, const Consensus::Params& params)
{
    const arith_uint256 bnPowLimit = UintToArith256(params.powLimit); // MVF-BU moved here

    arith_uint256 bnNew, bnNew1, bnNew2, bnOld;

    // TODO : Determine best reset formula
    // drop difficulty via factor
    int nDropFactor = 4;
    // use same formula as standard
    int64_t nActualTimespan = pindexLast->GetBlockTime() - nFirstBlockTime;
    // used reduced target time span
    int64_t nTargetTimespan = nActualTimespan / nDropFactor;

    bnOld.SetCompact(pindexLast->nBits);
    bnNew1 = bnOld / nTargetTimespan;
    bnNew2 = bnNew1 * nActualTimespan;

    // check for overflow or overlimit
    if (bnNew2 / nActualTimespan != bnNew1 || bnNew2 > bnPowLimit)
        bnNew = bnPowLimit;
    else bnNew = bnNew2;

    // ignore formula above and override with fixed difficulty
    //bnNew.SetCompact(0x207eeeee);

    /// debug print
    LogPrintf("GetNextWorkRequired RETARGET\n");
    LogPrintf("nTargetTimespan = %d    nActualTimespan = %d\n", nTargetTimespan, nActualTimespan);
    LogPrintf("Before: %08x  %s\n", pindexLast->nBits, bnOld.ToString());
    LogPrintf("After MVF FORK BLOCK DIFFICULTY RESET  %08x  %s\n", bnNew.GetCompact(),bnNew.ToString());
    return bnNew.GetCompact();
}
// MVF-BU end: difficulty functions

bool CheckProofOfWork(uint256 hash, unsigned int nBits, const Consensus::Params& params)
{
    bool fNegative;
    bool fOverflow;
    arith_uint256 bnTarget;
    static bool force_retarget=GetBoolArg("-force-retarget", DEFAULT_FORCE_RETARGET);  // MVF-BU (MVHF-BU-DES-DIAD-6)

    bnTarget.SetCompact(nBits, &fNegative, &fOverflow);

    // Check range
    // MVF-BU begin
    // --force-retarget is used to suppress output for regtest tests (MVHF-BU-DES-DIAD-6)
    if (fNegative || bnTarget == 0 || fOverflow || bnTarget > UintToArith256(params.powLimit))
    {
        // do not output verbose error msgs if force-retarget
        // this is to prevent log file flooding when regtests with actual
        // retargeting are done
        if (!force_retarget)
            return error("CheckProofOfWork(): nBits below minimum work");
        else
            return false;
    }
    // Check proof of work matches claimed amount
    if (UintToArith256(hash) > bnTarget)
    {
        if (!force_retarget)
            return error("CheckProofOfWork(): hash %s doesn't match nBits 0x%x",hash.ToString(),nBits);
        else
            return false;
    }
    // MVF-BU end


    return true;
}

arith_uint256 GetBlockProof(const CBlockIndex& block)
{
    arith_uint256 bnTarget;
    bool fNegative;
    bool fOverflow;
    bnTarget.SetCompact(block.nBits, &fNegative, &fOverflow);
    if (fNegative || fOverflow || bnTarget == 0)
        return 0;
    // We need to compute 2**256 / (bnTarget+1), but we can't represent 2**256
    // as it's too large for a arith_uint256. However, as 2**256 is at least as large
    // as bnTarget+1, it is equal to ((2**256 - bnTarget - 1) / (bnTarget+1)) + 1,
    // or ~bnTarget / (nTarget+1) + 1.
    return (~bnTarget / (bnTarget + 1)) + 1;
}

int64_t GetBlockProofEquivalentTime(const CBlockIndex& to, const CBlockIndex& from, const CBlockIndex& tip, const Consensus::Params& params)
{
    arith_uint256 r;
    int sign = 1;
    if (to.nChainWork > from.nChainWork) {
        r = to.nChainWork - from.nChainWork;
    } else {
        r = from.nChainWork - to.nChainWork;
        sign = -1;
    }
    r = r * arith_uint256(params.nPowTargetSpacing) / GetBlockProof(tip);
    if (r.bits() > 63) {
        return sign * std::numeric_limits<int64_t>::max();
    }
    return sign * r.GetLow64();
}
