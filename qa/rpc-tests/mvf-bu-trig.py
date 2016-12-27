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

import os

from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *


class MVF_TRIG_Test(BitcoinTestFramework):

    def setup_chain(self):
        print("Initializing test directory " + self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)
        self.nodelog = {}
        self.btcfork_conf = {}
        for n in range(0,4):
            self.nodelog[n] = os.path.join(self.options.tmpdir,"node%d" % n,"regtest","debug.log")
            self.btcfork_conf[n] = os.path.join(self.options.tmpdir,"node%d" % n,"btcfork.conf")

    def start_all_nodes(self):
        self.nodes = []
        self.is_network_split = False
        self.expected_fork_entries = {}
        self.nodes.append(start_node(0, self.options.tmpdir,
                            ["-forkheight=100", ]))
        self.nodes.append(start_node(1, self.options.tmpdir,
                            ["-forkheight=200", ]))
        self.nodes.append(start_node(2, self.options.tmpdir,
                            ["-forkheight=999999",
                             "-blockversion=%s" % 0x20000002])) # signal SegWit
        self.nodes.append(start_node(3, self.options.tmpdir,
                            ["-forkheight=300",
                             "-blockversion=%s" % 0x20000002])) # signal SegWit, but forkheight should pre-empt
        self.expected_fork_entries[0] = { "forkheight": "100", "forkid": "7827456", "autobackupblock": "99"}
        self.expected_fork_entries[1] = { "forkheight": "200", "forkid": "7827456", "autobackupblock": "199"}
        self.expected_fork_entries[2] = { "forkheight": "431", "forkid": "7827456", "autobackupblock": "431"}
        self.expected_fork_entries[3] = { "forkheight": "300", "forkid": "7827456", "autobackupblock": "299"}

    def setup_network(self):
        self.start_all_nodes()

    def prior_fork_detected_on_node(self, node=0):
        """ check in log file if prior fork has been detected and return true/false """
        marker_found = search_file(self.nodelog[node], "MVF: found marker config file")
        return (len(marker_found) > 0)

    def is_config_file_consistent(self, node=0, entry_map={}):
        """ check whether btcfork.conf file matches expectations,
        and return true/false. One of the assumptions is that the
        config file should exist. Do not call this function otherwise."""
        config_file_written = search_file(self.nodelog[node], "MVF: writing")
        if len(config_file_written) == 0:
            # absence of config file is unexpected
            print "is_config_file_consistent: config file not found for node %d" % node
            return False
        verify_btcfork_conf = config_file_written[0].split(" ")[-1:][0].strip()
        if verify_btcfork_conf != self.btcfork_conf[node]:
            # check that filename matches what is expected
            print "is_config_file_consistent: config filename %s mismatch %s for node %d" % (verify_btcfork_conf, self.btcfork_conf[node], node)
            return False
        for key in entry_map.keys():
            key_found = search_file(self.btcfork_conf[node], "%s=" % key)
            if (len(key_found) != 1):
                print "is_config_file_consistent: key %s not found for node %d" % (key, node)
                return False
            val_found=key_found[0].split("=")[1].strip()
            if (val_found != entry_map[key]):
                print "is_config_file_consistent: unexpected value '%s' for key %s found for node %d" % (val_found, key, node)
                return False
        return True

    def is_fork_triggered_on_node(self, node=0):
        """ check in log file if fork has triggered and return true/false """
        # MVF-BU TODO: extend to check using RPC info about forks
        hf_active = (search_file(self.nodelog[node], "isMVFHardForkActive=1") and
                     search_file(self.nodelog[node], "enabling isMVFHardForkActive"))
        fork_actions_performed = search_file(self.nodelog[node], "MVF: performing fork activation actions")
        return (len(hf_active) > 0 and len(fork_actions_performed) == 1)

    def run_test(self):
        # check that fork does not triggered before the height
        print "Generating 99 pre-fork blocks"
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(99)
            assert_equal(False, self.is_fork_triggered_on_node(n)
                                or self.prior_fork_detected_on_node(n))
        print "Fork did not trigger prematurely"

        # check that fork triggers for nodes 0 and 1 at designated height
        # move all nodes to height 100
        for n in xrange(len(self.nodes)):
            self.nodes[n].generate(1)
        assert_equal(True,  self.is_fork_triggered_on_node(0))
        assert_equal(True,  self.is_config_file_consistent(0, self.expected_fork_entries[0]))
        assert_equal(False, self.prior_fork_detected_on_node(0))
        for n in [1,2,3]:
            assert_equal(False, self.is_fork_triggered_on_node(n))
            assert_equal(False, self.prior_fork_detected_on_node(n))

        print "Fork triggered successfully on node 0 (block height 100)"

        # check node 1 triggering around height 200
        self.nodes[1].generate(99)
        assert_equal(False, self.is_fork_triggered_on_node(1))
        self.nodes[1].generate(1)
        assert_equal(True,  self.is_fork_triggered_on_node(1))
        assert_equal(True,  self.is_config_file_consistent(1, self.expected_fork_entries[1]))
        print "Fork triggered successfully on node 1 (block height 200)"

        # check node 2 triggering around height 431
        # it starts at 100
        self.nodes[2].generate(330)
        assert_equal(False, self.is_fork_triggered_on_node(2)
                            or self.prior_fork_detected_on_node(2))
        self.nodes[2].generate(1)
        assert_equal(True,  self.is_fork_triggered_on_node(2))
        assert_equal(True,  self.is_config_file_consistent(2, self.expected_fork_entries[2]))
        assert_equal(False, self.prior_fork_detected_on_node(2))
        # block 431 is when fork activation is performed.
        # block 432 is first block where new consensus rules are in effect.
        print "Fork triggered successfully on node 2 (segwit, height 431)"

        # check node 3 triggering around height 300
        # move to 299
        self.nodes[3].generate(199)
        assert_equal(False, self.is_fork_triggered_on_node(3)
                            or self.prior_fork_detected_on_node(3))
        self.nodes[3].generate(1)
        assert_equal(True,  self.is_fork_triggered_on_node(3))
        assert_equal(True,  self.is_config_file_consistent(3, self.expected_fork_entries[3]))
        assert_equal(False, self.prior_fork_detected_on_node(3))
        print "Fork triggered successfully on node 3 (block height 300 ahead of SegWit)"

        # test startup detection of prior fork activation.
        # by now, all 4 nodes have triggered.
        print "Stopping all nodes"
        for n in xrange(4):
            assert_equal(False, self.prior_fork_detected_on_node(n))
            stop_node(self.nodes[n], n)
            # get rid of debug.log files so we can better check retrigger
            os.unlink(os.path.join(self.options.tmpdir,"node%d" % n,"regtest","debug.log"))

        # restart them all, check that they detected having forked on prior run
        print "Restarting all nodes"
        self.start_all_nodes()
        for n in xrange(4):
            assert_equal(True, self.prior_fork_detected_on_node(n))
            assert(len(search_file(self.nodelog[n], "enabling isMVFHardForkActive")) == 1)
            assert(len(search_file(self.nodelog[n], "found marker config file")) == 1)
        print "Prior fork activation detected on all nodes"

if __name__ == '__main__':
    MVF_TRIG_Test().main()
