#!/usr/bin/env python3
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF post fork retargeting
#
# on node 0, test pure block height trigger at height FORK_BLOCK
#
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.arith import *
from random import randint

# period (in blocks) from fork activation until retargeting returns to normal
# MVF-BU TODO: Revert to 180*144
HARDFORK_RETARGET_BLOCKS = 180*144    # the period when retargeting returns to original
FORK_BLOCK = 2020                    # needs to be >= 2018 to test fork difficulty reset
POW_LIMIT = 0x207fffff
PREFORK_BLOCKTIME = 800              # the seconds for a block during the regtest prefork
ORIGINAL_DIFFADJINTERVAL = 2016      # the original difficulty adjustment interval
STANDARD_BLOCKTIME = 600             # the standard target seconds for a block

def CalculateMVFNextWorkRequired(bits, actualBlockTimeSecs, targetBlockTimeSecs):
    """
    Returns difficulty (as integer representing bit string)
    using the fork reset formula in pow.cpp:CalculateMVFNextWorkRequired()

    >>> CalculateMVFNextWorkRequired(b'1d00d86a', 600, 600)
    486594665
    >>> CalculateMVFNextWorkRequired(b'207fffff', 600, 600)
    545259518
    """

    bnPowLimit = bits2target_int(hex2bin(int2hex(POW_LIMIT))) # MVF-BU moved here

    # Limit adjustment step
    nActualTimespan = actualBlockTimeSecs

    # Target by interval
    nTargetTimespan = targetBlockTimeSecs

    # permit 10x retargetchanges for a few blocks after the fork i.e. when nTargetTimespan is < 30 minutes (MVHF-BU-DES-DIAD-5)
    if (nTargetTimespan >= STANDARD_BLOCKTIME * 3) :
        retargetLimit = 4
    else :
        retargetLimit = 10
    # prevent abrupt changes to target
    if (nActualTimespan < nTargetTimespan/retargetLimit) :
        nActualTimespan = nTargetTimespan/retargetLimit
    if (nActualTimespan > nTargetTimespan*retargetLimit) :
        nActualTimespan = nTargetTimespan*retargetLimit

    # compare with debug.log
    #print "nTargetTimespan=%d nActualTimespan=%d" % (nTargetTimespan,nActualTimespan)

    # Retarget
    bnOld = bits2target_int(hex2bin(bits))     # SetCompact
    # MVF-BU begin: move division before multiplication
    # at regtest difficulty, the multiplication is prone to overflowing
    bnNew1 = bnOld // nTargetTimespan
    bnNew2 = bnNew1 * nActualTimespan

    # Test for overflow
    if (bnNew2 // nActualTimespan != bnNew1 or bnNew2 > bnPowLimit):
        bnNew = bnPowLimit
    else :
        bnNew = bnNew2

    newBits = "0x%s" % bin2hex(target_int2bits(int(bnNew))) # GetCompact
    nBitsReset = int(newBits,0)
    return nBitsReset


def CalculateMVFResetWorkRequired(bits):
    # Returns difficulty using the fork reset formula in pow.cpp:CalculateMVFResetWorkRequired()

    bnPowLimit = bits2target_int(hex2bin(int2hex(POW_LIMIT)))
    # drop difficulty via factor
    nDropFactor = HARDFORK_DROPFACTOR_REGTEST_DEFAULT
    # total blocktimes prefork during run_test
    nActualTimespan = ORIGINAL_DIFFADJINTERVAL * PREFORK_BLOCKTIME
    # used reduced target time span while within the re-target period
    nTargetTimespan = nActualTimespan / nDropFactor

    # compare with debug.log
    #print "nTargetTimespan=%d nActualTimespan=%d" % (nTargetTimespan,nActualTimespan)

    bnOld = bits2target_int(hex2bin(bits))     # SetCompact
    bnNew1 = bnOld / nTargetTimespan
    bnNew2 = bnNew1 * nActualTimespan

    # check for overflow or overlimit
    if (bnNew2 / nActualTimespan != bnNew1 or bnNew2 > bnPowLimit):
        bnNew = bnPowLimit
    else:
        bnNew = bnNew2

    nBitsReset = int("0x%s" % bin2hex(target_int2bits(bnNew)),0) # GetCompact
    return nBitsReset


class MVF_RETARGET_BlockHeight_Test(BitcoinTestFramework):

    def add_options(self, parser):
        parser.add_option("--quick", dest="quick", default=False, action="store_true",
        help="Run shortened version of test")

    def setup_chain(self):
        # random seed is initialized and output by the test framework
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 1)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir
            ,["-forkheight=%s"%FORK_BLOCK, "-rpcthreads=100","-blockversion=%d" % 0x20000000 ]
            ))

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-BU TODO: extend to check using RPC info about forks
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        hf_active = search_file(nodelog, "isMVFHardForkActive=1")
        fork_actions_performed = search_file(nodelog, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not trigger before the forkheight
        print("Generating %s pre-fork blocks" % (FORK_BLOCK - 1))

        #block0 already exists
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        preblocktime = best_block['time']
        for n in range(FORK_BLOCK - 1):
            # Change block times so that difficulty develops
            preblocktime = preblocktime + PREFORK_BLOCKTIME
            self.nodes[0].setmocktime(preblocktime)
            self.nodes[0].generate(1)

        print("Done generating %s pre-fork blocks" % (FORK_BLOCK - 1))
        print("Stopping node 0")
        stop_node(self.nodes[0],0)
        print("Restarting node 0 with -force-retarget")
        self.nodes[0] = start_node(0, self.options.tmpdir
            ,["-forkheight=%s"%FORK_BLOCK, "-force-retarget", "-rpcthreads=100","-blockversion=%d" % 0x20000000 ]
            )

        # Read difficulty before the fork
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        print("Pre-fork difficulty: %.10f %s " % (best_block['difficulty'], best_block['bits']))
        nBits = CalculateMVFResetWorkRequired(best_block['bits'])
        reset_bits = int2hex(nBits)
        reset_diff_expected = bits2difficulty(nBits)
        assert_greater_than(reset_diff_expected, 0)

        # Test fork did not trigger prematurely
        assert_equal(False, self.is_fork_triggered_on_node(0))
        print("Fork did not trigger prematurely")

        # Generate fork block
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        self.nodes[0].setmocktime(best_block['time'] + STANDARD_BLOCKTIME)
        self.nodes[0].generate(1)
        assert_equal(True,   self.is_fork_triggered_on_node(0))

        print("Fork triggered successfully (block height %s)" % best_block['height'])

        # Test fork difficulty reset
        best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
        assert_equal(best_block['bits'],reset_bits)
        #assert_equal(best_block['bits'], "207eeeee") # fixed reset
        print("Post-fork difficulty reset success: %.10f %s " % (best_block['difficulty'], best_block['bits']))

        # use to track how many times the same bits are used in a row
        prev_block = 0
        diffadjinterval = 0
        # the first nexttimeblock test phase is cyclical increases of 50 seconds starting from here
        # if the starting number is too low it may cause timeout errors too often
        next_block_time = 300
        count_bits_used = 0

        # print column titles
        print(">> Bits change log <<")
        print("Time,Block,Delta(secs),Bits,Used,DiffAdjInterval,TimespanBlocks,Difficulty,NextBits")

        # start generating MVF blocks with varying time stamps
        oneRetargetPeriodAfterMVFRetargetPeriod = HARDFORK_RETARGET_BLOCKS+ORIGINAL_DIFFADJINTERVAL+1
        if self.options.quick:
            # used for CI - just test one day after fork
            # this is basically just to test reset and initial response
            number_of_blocks_to_test_after_fork = 144
        else:
            # full range
            number_of_blocks_to_test_after_fork = oneRetargetPeriodAfterMVFRetargetPeriod = HARDFORK_RETARGET_BLOCKS+ORIGINAL_DIFFADJINTERVAL+1

        for n in range(number_of_blocks_to_test_after_fork):
            best_block = self.nodes[0].getblock(self.nodes[0].getbestblockhash(), True)
            prev_block = self.nodes[0].getblock(best_block['previousblockhash'], True)

            # track bits used
            if (prev_block['bits'] == best_block['bits'] or best_block['height'] == FORK_BLOCK) and n < oneRetargetPeriodAfterMVFRetargetPeriod -1 :
                count_bits_used += 1
            else:
                # when the bits change then output the retargeting metrics
                # for the previous group of bits
                print_block = self.nodes[0].getblock(self.nodes[0].getblockhash(prev_block['height'] - count_bits_used))
                avgDeltaBlockTime = (prev_block['time'] - print_block['time']) / count_bits_used

                if n == oneRetargetPeriodAfterMVFRetargetPeriod -1 :
                    nextBits = "end"
                else :
                    # Test difficulty during MVF retarget period
                    first_block = self.nodes[0].getblock(self.nodes[0].getblockhash(int(prev_block['height']) - int(timespanblocks)))
                    actualBlockTimeSecs = prev_block['time'] - first_block['time']
                    #print("actualBlockTimeSecs = %s" % actualBlockTimeSecs)
                    nBits = CalculateMVFNextWorkRequired(prev_block['bits'], actualBlockTimeSecs, difficultytimespan)
                    nextBits = int2hex(nBits)
                    ## begin debug
                    #best_diff_expected = bits2difficulty(nBits)
                    #print("%s %.10f : %s " % (nextBits, best_diff_expected, best_block['bits']))
                    #
                    #if best_block['bits'] != nextBits : #debug
                    #    print("err bits %s %s %s " % (best_block['bits'], nextBits, diffadjinterval))
                    #    input()
                    ## end debug
                    assert_equal(best_block['bits'], nextBits)

                print("%s,%d,%d,%s,%d,%d,%d,%.10f,%s " %(
                    time.strftime("%Y-%m-%d %H:%M",time.gmtime(prev_block['time'])),
                    prev_block['height'],
                    avgDeltaBlockTime,
                    prev_block['bits'],
                    count_bits_used,
                    diffadjinterval,
                    timespanblocks,
                    prev_block['difficulty'],
                    nextBits
                    ))

                # reset bits tracking variables
                count_bits_used = 1
                #input()
            #### end if prev_block['bits'] == best_block['bits']

            # Get difficulty time span
            difficultytimespan = self.nodes[0].getblockchaininfo()['difficultytimespan']
            timespanblocks = difficultytimespan / STANDARD_BLOCKTIME
            #print "%s : %s" % (best_block['height'],timespanblocks)

            # Get difficulty adjustment interval
            diffadjinterval = self.nodes[0].getblockchaininfo()['difficultyadjinterval']

            # Test processed bits are used within the expected difficulty interval
            # except when the bits is at the bits limit: 207fffff
            #
            # In some cases the retarget causes the same bits to be returned
            # so this test has been disabled.
            #
            #if int("0x%s"%prev_block['bits'],0) <> POW_LIMIT :
                #if count_bits_used > diffadjinterval : #debug
                    #print "err count_bits_used %s : %s " % (prev_block['bits'], nextBits)
                    #input()
                #assert_less_than_equal(count_bits_used, diffadjinterval)

            # Setup various block time interval tests
            if n in range(0,11) :
                next_block_time = next_block_time + 50
            elif n in range(11,22) :
                # this may cause bits to hit the limit POW_LIMIT
                next_block_time = 1200
            elif n in range(22,26) :
                # this may cause timeout errors
                next_block_time = 300
            elif n in range(26,500) :
                # exactly standard block times
                next_block_time = STANDARD_BLOCKTIME
            elif n in range(500,525) :
                # simulate faster blocks
                # this may cause timeout errors
                next_block_time = randint(100,300)
            elif n in range(525,550) :
                # simulate slow blocks
                # this may cause bits to hit the limit POW_LIMIT
                next_block_time = randint(1000,3000)
            elif n >= HARDFORK_RETARGET_BLOCKS :
                # exactly standard block times so when the original retargeting
                # begins again the difficulty will stay about the same
                next_block_time = STANDARD_BLOCKTIME
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                next_block_time = randint(500,700)

            self.nodes[0].setmocktime(best_block['time'] + next_block_time)

            # Test the interval matches the interval defined in params.DifficultyAdjustmentInterval()
            # notice the range() high setting is plus one versus c++ switch
            if n in range(0,2017) :
                diff_interval_expected = 1     # retarget every block
            elif n in range(2017,4000) :
                diff_interval_expected = 10
            elif n in range(4000,10000) :
                diff_interval_expected = 40
            elif n in range(10000,15000) :
                diff_interval_expected = 100
            elif n in range(15000,20000) :
                diff_interval_expected = 400
            elif n in range(20000,HARDFORK_RETARGET_BLOCKS+1) :
                diff_interval_expected = 1000
            else:
                diff_interval_expected = ORIGINAL_DIFFADJINTERVAL  # every 14 days original

            #if diff_interval_expected <> diffadjinterval :
                #print "err diffadjinterval %d %d %d" % (n, diff_interval_expected, diffadjinterval)
                #input()
            assert_equal(diff_interval_expected, diffadjinterval)

            # print info for every block
            #if best_block['height'] >= 16127 :
                #first_block = self.nodes[0].getblock(self.nodes[0].getblockhash(prev_block['height'] - timespanblocks))
                #print "%s :: %s :: %d :: %s :: %.10f :: %d :: %d" %(
                    #best_block['height'],
                    #time.strftime("%H:%M",time.gmtime(best_block['time'])),
                    #best_block['time'] - prev_block['time'],
                    #best_block['bits'],
                    #best_block['difficulty'],
                    #count_bits_used,
                    #first_block['height'])
                #input()

            # generate the next block
            self.nodes[0].generate(1)

        #### end for n in range

        print("Done.")

if __name__ == '__main__':
    import doctest
    (failure_count, test_count) = doctest.testmod()
    if failure_count:
        sys.exit(1)
    MVF_RETARGET_BlockHeight_Test().main()
