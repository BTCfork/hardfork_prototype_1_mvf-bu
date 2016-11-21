#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF post fork retargeting
#
# on node 0, test pure block height trigger at height 100
#

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import decimal

class MVF_RETARGET_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 1)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir
            ,["-forkheight=100", "-force-retarget","-rpcthreads=100" ]
            ))

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-BU TODO: extend to check using RPC info about forks
        nodelog = self.options.tmpdir + "/node%s/regtest/debug.log" % node
        hf_active = search_file(nodelog, "isMVFHardForkActive=1")
        fork_actions_performed = search_file(nodelog, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not triggered before the height
        print "Generating 99 pre-fork blocks"
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(99)
            assert_equal(False, self.is_fork_triggered_on_node(n))
        print "Fork did not trigger prematurely"

        # check that fork triggers for nodes at designated height
        # move all nodes to height 100
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(1)
        assert_equal(True,   self.is_fork_triggered_on_node(0))

        print "Fork triggered successfully on node 0 (block height 100)"

        # use to track how many times the same bits are used in a row
        prev_block = 0
        count_bits_used = decimal.Decimal(-1)
        diffadjinterval = 0
        next_block_time = 0
        prev_block_delta = decimal.Decimal(0)
        best_diff_expected = decimal.Decimal(0)
        prev_blocks_delta_avg = decimal.Decimal(0)
        diff_factor = decimal.Decimal(0)

        # start generating MVF blocks with varying time stamps
        print "nBits changed @ Time,Block,Delta(secs),nBits,Used,Difficulty"
        for n in xrange(200 * 24 * 60 * 60 / 600): #26640
            best_block_hash = self.nodes[0].getbestblockhash()
            best_block = self.nodes[0].getblock(best_block_hash, True)

            prev_block = self.nodes[0].getblock(best_block['previousblockhash'], True)

            if prev_block['bits'] == best_block['bits']:
                count_bits_used += 1
            else:
                prev_blocks_delta_avg = decimal.Decimal(prev_block_delta / count_bits_used)
                diff_factor = decimal.Decimal(600 / prev_blocks_delta_avg)
                best_diff_expected = decimal.Decimal(prev_block['difficulty']) * diff_factor

                print "%s,%d,%d,%s,%d,%s " %(
                    time.strftime("%Y-%m-%d %H:%M",time.gmtime(prev_block['time'])),
                    prev_block['height'],
                    prev_blocks_delta_avg,
                    prev_block['bits'],
                    count_bits_used,
                    prev_block['difficulty'],
                    #best_diff_expected,
                    #diff_factor
                    )

                if prev_block['bits'] <> "207fffff":
                    assert_less_than_equal(count_bits_used, diffadjinterval)

                if n <= 500 :
                    assert_equal(round(best_block['difficulty'],4), round(best_diff_expected,4))

                count_bits_used = 1
                prev_block_delta = 0
            #### end if prev_block['bits'] == best_block['bits']

            # determine block time interval
            if n in range(0,11) :
                next_block_time = next_block_time + 50
            elif n in range(12,18) :
                next_block_time = 300
            elif n in range(19,26) :
                next_block_time = 1200
            elif n in range(27,500) :
                next_block_time = 600
            elif n in range(501,2500) :
                 # simulate slow blocks just after the fork i.e. low hash power/high difficulty
                # this will cause bits to hit the limit 207fffff
                next_block_time = randint(4000,6000)
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                next_block_time = randint(500,700)


            self.nodes[0].setmocktime(best_block['time'] + next_block_time)

            prev_block_delta = prev_block_delta + (best_block['time'] - prev_block['time'])
            diffadjinterval = self.nodes[0].getblockchaininfo()['difficultyadjinterval']

            # print info for every block
            #print "%s :: %s :: %d :: %f :: %f" %(
                #best_block['height'],
                #time.strftime("%H:%M",time.gmtime(best_block['time'])),
                #prev_block_delta,
                #best_block['difficulty'],
                #best_diff_expected)

            #print "%d,%d,%f,%f,%f,%f" % (
                #n, next_block_time,
                #prev_block_delta / count_bits_used,
                #prev_block_delta / count_bits_used / 600,
                #best_diff_expected,
                #best_block['difficulty'])

            self.nodes[0].generate(1)

        #### end for n in xrange


        print "Done."
        #raw_input()

if __name__ == '__main__':
    MVF_RETARGET_Test().main()
