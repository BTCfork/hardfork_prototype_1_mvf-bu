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

class MVF_RETARGET_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=100", "-force-retarget" ]))
        #self.nodes.append(start_node(1, self.options.tmpdir,
                            #["-forkheight=200", ]))
        #self.nodes.append(start_node(2, self.options.tmpdir,
                            #["-forkheight=999999",
                             #"-blockversion=%s" % 0x20000002])) # signal SegWit
        #self.nodes.append(start_node(3, self.options.tmpdir,
                            #["-forkheight=300",
                             #"-blockversion=%s" % 0x20000002])) # signal SegWit, but forkheight should pre-empt

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

        # check that fork triggers for nodes 0 and 1 at designated height
        # move all nodes to height 100
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(1)
        assert_equal(True,   self.is_fork_triggered_on_node(0))

        print "Fork triggered successfully on node 0 (block height 100)"

        # use to track how many times the same bits are used in a row
        prev_block = 0
        count_bits_used = 1

        # start generating MVF blocks with varying time stamps
        for n in xrange(4032):
            best_block_hash = self.nodes[0].getbestblockhash()
            best_block = self.nodes[0].getblock(best_block_hash, True)

            if prev_block <> 0 :
                if prev_block['bits'] == best_block['bits']:
                    count_bits_used += 1
                else:
                    print "nBits changed @ Height:nBits:Diff:Used %s : %s : %f : %d" %(
                        prev_block['height'],
                        prev_block['bits'],
                        prev_block['difficulty'],
                        count_bits_used)

                    count_bits_used = 1

            #print "%s :: %s :: %f :: %s" %(
                #best_block['height'],
                #time.strftime("%H:%M",time.gmtime(best_block['time'])),
                #best_block['difficulty'],
                #best_block['bits'])

            if n <= 36 :
                # simulate slow blocks just after the fork i.e. low hash power/high difficulty
                self.nodes[0].setmocktime(best_block['time'] + randint(4000,8000))
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                self.nodes[0].setmocktime(best_block['time'] + randint(300,900))

            self.nodes[0].generate(1)

            prev_block = best_block
        #end for n in xrange

        print "Done. Check the logs now or press enter to shutdown test."
        raw_input()

if __name__ == '__main__':
    MVF_RETARGET_Test().main()
