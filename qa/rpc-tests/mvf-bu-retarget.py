#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF fork triggering functionality (TRIG)
#
# on node 0, test pure block height trigger at height 100
# on node 1, test pure block height trigger at height 200
# on node 2, test SegWit trigger at height 431 (432 blocks = 3 periods of 144 blocks)
# on node 3, test block height trigger pre-empts SegWit trigger at 300
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
        self.nodes.append(start_node(1, self.options.tmpdir,
                            ["-forkheight=200", ]))
        self.nodes.append(start_node(2, self.options.tmpdir,
                            ["-forkheight=999999",
                             "-blockversion=%s" % 0x20000002])) # signal SegWit
        self.nodes.append(start_node(3, self.options.tmpdir,
                            ["-forkheight=300",
                             "-blockversion=%s" % 0x20000002])) # signal SegWit, but forkheight should pre-empt

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
        assert_equal(False,  self.is_fork_triggered_on_node(1))
        assert_equal(False,  self.is_fork_triggered_on_node(2))
        assert_equal(False,  self.is_fork_triggered_on_node(3))
        print "Fork triggered successfully on node 0 (block height 100)"

        # start generating blocks with time stamps 600 apart
        for n in xrange(144):
            best_block_hash = self.nodes[0].getbestblockhash()
            best_block = self.nodes[0].getblock(best_block_hash, True)

            print "%s :: %s :: %d :: %s" %(
                best_block['height'],
                time.strftime("%H:%M",time.gmtime(best_block['time'])),
                best_block['difficulty'],
                best_block['bits'])

            self.nodes[0].setmocktime(best_block['time'] + randint(300,900))
            self.nodes[0].generate(1)

        print "Done. Check the logs now or press enter to shutdown test."
        raw_input()

if __name__ == '__main__':
    MVF_RETARGET_Test().main()
