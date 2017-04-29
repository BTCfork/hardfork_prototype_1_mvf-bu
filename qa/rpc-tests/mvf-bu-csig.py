#!/usr/bin/env python3
# Copyright (c) 2014-2015 The Bitcoin Core developers
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
# MVF-BU
"""
Exercise the signature change (replay protection) code.
Derived from walletbackupauto.py.

Test case is:
4 nodes - 2 forking and 2 non-forking, sending transactions between each other.
Prior to the fork, anything goes.
Post fork, the nodes of the same kind can still send between each other,
but not to the nodes of the other kind (2 way check).
"""

import os
import fnmatch
import hashlib
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import logging
import time

#logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

FORKHEIGHT = 120

class ReplayProtectionTest(BitcoinTestFramework):

    def setup_chain(self):
        #logging.info("Initializing test directory "+self.options.tmpdir)
        print("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 4)

    def setup_network(self, split=False):
        #logging.info("Starting nodes")
        print("Starting nodes")

        # all nodes are spenders, let's give them a keypool=100
        self.extra_args = [
            ['-debug', '-whitelist=127.0.0.1', "-keypool=100"],
            ['-debug', '-whitelist=127.0.0.1', "-keypool=100"],
            ['-debug', '-whitelist=127.0.0.1', "-keypool=100", "-forkheight=%s"%FORKHEIGHT],
            ['-debug', '-whitelist=127.0.0.1', "-keypool=100", "-forkheight=%s"%FORKHEIGHT]]

        self.nodes = start_nodes(4, self.options.tmpdir, self.extra_args)
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[0], 2)
        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 2)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[3], 2)
        self.is_network_split=False
        self.sync_all()

    def send_and_check(self, from_node, to_node, expect_to_succeed=True, force_sync=True, check=True, check_for_fail=False):
        ''' try sending 0.1 BTC from one node to another,
            and optionally check if successful '''
        to_addr = self.nodes[to_node].getnewaddress()
        amount = Decimal(1) / Decimal(10)
        txid = self.nodes[from_node].sendtoaddress(to_addr, amount)
        if force_sync:
            sync_mempools([self.nodes[from_node], self.nodes[to_node]])
        else:
            time.sleep(1)
        if check:
            if check_for_fail:
                assert_equal(txid in self.nodes[from_node].getrawmempool(), True)
                assert_equal(txid in self.nodes[to_node].getrawmempool(), False)
            else:
                assert_equal(txid in self.nodes[from_node].getrawmempool() and (txid in self.nodes[to_node].getrawmempool() or not expect_to_succeed), True)
        return txid

    def run_test(self):
        #logging.info("Fork height configured for block %s"%(FORKHEIGHT))
        print("Fork height configured for block %s"%(FORKHEIGHT))

        #logging.info("Generating initial 104 blocks")
        print("Generating initial 104 blocks")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        self.nodes[1].generate(1)
        sync_blocks(self.nodes)
        self.nodes[2].generate(1)
        sync_blocks(self.nodes)
        self.nodes[3].generate(101)

        sync_blocks(self.nodes)
        #logging.info("Current height %s blocks"%(self.nodes[0].getblockcount()))
        print("Current height %s blocks"%(self.nodes[0].getblockcount()))

        assert_equal(self.nodes[0].getbalance(), 50)
        assert_equal(self.nodes[1].getbalance(), 50)
        assert_equal(self.nodes[2].getbalance(), 50)
        assert_equal(self.nodes[3].getbalance(), 50)

        assert_equal(self.nodes[0].getblockcount(), 104)

        #logging.info("Check all sending works after setup")
        print("Check all sending works after setup")
        # from any node to the others should be ok now
        # this should generate 4*3 = 12 more blocks
        for src_node in range(4):
            for dst_node in range(4):
                if src_node != dst_node:
                    #logging.info("... from %d to %d" %(src_node, dst_node))
                    print("... from %d to %d" %(src_node, dst_node))
                    self.send_and_check(src_node, dst_node, True)
                    self.nodes[dst_node].generate(1)
                    sync_blocks(self.nodes)

        current_height = self.nodes[0].getblockcount()
        assert_equal(current_height, 116)

        # generate blocks, one on each node in turn, until we reach pre-fork block height
        blocks_to_fork = FORKHEIGHT - current_height - 1
        self.nodes[0].generate(blocks_to_fork)

        # not sure why this loop didn't work reliably...
        # maybe it was the round-robin generation
        while False: #blocks_to_fork > 0:
            #logging.info("blocks left to fork height: %d" % blocks_to_fork)
            print("blocks left to fork height: %d" % blocks_to_fork)
            self.nodes[blocks_to_fork % 4].generate(1)
            blocks_to_fork -= 1

        sync_blocks(self.nodes)
        assert_equal(self.nodes[0].getblockcount(), FORKHEIGHT - 1)

        #logging.info("Current height %s blocks (pre-fork block)"%(self.nodes[0].getblockcount()))
        print("Current height %s blocks (pre-fork block)"%(self.nodes[0].getblockcount()))

        # check that we can still send to all other nodes for the pre-fork block

        # collect a bunch of tx's sent by the nodes to each other
        #logging.info("sending tx's between all nodes at pre-fork")
        print("sending tx's between all nodes at pre-fork")
        should_be_fine_txs = []
        for src_node in range(4):
            for dst_node in range(4):
                if src_node != dst_node:
                    #logging.info("... from %d to %d" %(src_node, dst_node))
                    print("... from %d to %d" %(src_node, dst_node))
                    should_be_fine_txs.append(self.send_and_check(src_node, dst_node, True))

        #logging.info("Verifying tx's were still accepted by all nodes")
        print("Verifying tx's were still accepted by all nodes")
        sync_mempools(self.nodes)
        mempools = [self.nodes[i].getrawmempool() for i in range(4)]
        for tx in should_be_fine_txs:
            for n in range(4):
                assert_equal(tx in mempools[n], True)

        # generate the fork block
        #logging.info("Generate fork block at height %s" % FORKHEIGHT)
        print("Generate fork block at height %s" % FORKHEIGHT)
        self.nodes[0].generate(1)

        # check the previous round of tx's not in mempool anymore
        self.sync_all()
        assert_equal(self.nodes[0].getblockcount(), FORKHEIGHT)

        #logging.info("Verifying tx's no longer in any mempool")
        print("Verifying tx's no longer in any mempool")
        mempools = [self.nodes[i].getrawmempool() for i in range(4)]
        for tx in should_be_fine_txs:
            for n in range(4):
                assert_equal(tx in mempools[n], False)

        # check that now, only nodes of the same kind can transact
        # these pairs should work fine
        #logging.info("Checking transactions between same-kind nodes")
        print("Checking transactions between same-kind nodes")
        for pair in ((0,1), (1,0), (2,3), (3,2)):
            #logging.info("... from %d to %d" %(pair[0], pair[1]))
            print("... from %d to %d" %(pair[0], pair[1]))
            self.send_and_check(pair[0], pair[1], True)

        # re-connect the nodes which have been disconnected due to the
        # above post-fork transactions, so we can test them separately
        #logging.info("Re-connecting nodes which disconnected due to prior step")
        print("Re-connecting nodes which disconnected due to prior step")
        connect_nodes_bi(self.nodes,0,2)
        connect_nodes_bi(self.nodes,0,3)
        connect_nodes_bi(self.nodes,1,2)
        connect_nodes_bi(self.nodes,1,3)
        #logging.info("Checking transactions between forked/unforked nodes")
        print("Checking transactions between forked/unforked nodes")
        # these should not work anymore


        # MVF-BU TODO: decide whether to accept old-style signatures post-fork (maybe limited-time only?)
        # if you only want to deny new->old, then use the commented out code
        #for pair in ((2,0), (2,1), (3,0), (3,1)):

        # check both forked->unforked and vice versa are blocked now
        for pair in ((0,2), (0,3), (1,2), (1,3), (2,0), (2,1), (3,0), (3,1)):
            #logging.info("... from %d to %d" %(pair[0], pair[1]))
            print("... from %d to %d" %(pair[0], pair[1]))
            self.send_and_check(pair[0], pair[1], expect_to_succeed=False, force_sync=False, check=True, check_for_fail=True)

if __name__ == '__main__':
    ReplayProtectionTest().main()
