#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.

#
# Test MVF fork triggering functionality (TRIG)
#

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *

TEST_FORKHEIGHT = 100


class MVF_TRIG_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 1)

    def setup_network(self):
        self.nodes = []
        self.is_network_split = False
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=%s" % TEST_FORKHEIGHT, ]))

    def is_fork_triggered(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-BU TODO: extend to check using RPC info about forks
        hf_active = search_file(self.options.tmpdir + "/node%s/regtest/debug.log" % node, "isMVFHardForkActive=1")
        fork_actions_performed = search_file(self.options.tmpdir + "/node%s/regtest/debug.log" % node, "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        print "Generating %s pre-fork blocks" % (TEST_FORKHEIGHT-1)
        self.nodes[0].generate(TEST_FORKHEIGHT-1)

        # check that fork has not triggered before the height
        assert_equal(False, self.is_fork_triggered())
        print "Fork did not trigger prematurely"

        # check that fork triggers at designated height
        self.nodes[0].generate(TEST_FORKHEIGHT-1)
        assert_equal(True, self.is_fork_triggered())
        print "Fork triggered successfully"

if __name__ == '__main__':
    MVF_TRIG_Test().main()
