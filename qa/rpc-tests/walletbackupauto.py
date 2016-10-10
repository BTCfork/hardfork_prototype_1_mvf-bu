#!/usr/bin/env python2
# Copyright (c) 2014-2015 The Bitcoin Core developers
# Copyright (c) 2015-2016 The Bitcoin Unlimited developers
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
# MVHF-BU
"""
Exercise the auto backup wallet code.  Ported from walletbackup.sh.

Test case is:
4 nodes. 1 2 and 3 send transactions between each other, fourth node is a miner
5th node does no transactions and only tests the -disablewallet
.
1 2 3 each mine a block to start, then
Miner creates 100 blocks so 1 2 3 each have 50 mature coins to spend.
Then 5 iterations of 1/2/3 sending coins amongst
themselves to get transactions in the wallets,
and the miner mining one block.

Then 5 more iterations of transactions and mining a block.

Miner then generates 101 more blocks, so any
transaction fees paid mature.

The node config sets wallets to automatically back up at block 114.

Balances are saved for sanity check:
  Sum(1,2,3,4 balances) == 114*50

Then 5 more iterations of transactions and mining a block.

Miner then generates 101 more blocks, so any
transaction fees paid mature.

1/2/3 are shutdown, and their wallets erased.
Then restored using wallet.dat.auto.114.bak backup.
Sanity check to confirm 1/2/3 balances match the 114 block balances.
Sanity check to confirm 5th node does NOT perform the auto backup
and that the debug.log contains a conflict message
"""

import os
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

class WalletBackupTest(BitcoinTestFramework):

    def setup_chain(self):
        logging.info("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 5)

    # This mirrors how the network was setup in the bash test
    def setup_network(self, split=False):
        # nodes 1, 2,3 are spenders, let's give them a keypool=100
        # and configure option autobackupwalletpath enabled for block 114

        logging.info("Starting nodes")

        extra_args = [
            ["-keypool=100",
                "-autobackupwalletpath="+self.options.tmpdir+"/node0",
                "-autobackupblock=114"],
            ["-keypool=100",
                "-autobackupwalletpath="+self.options.tmpdir+"/node1",
                "-autobackupblock=114"],
            ["-keypool=100",
                "-autobackupwalletpath="+self.options.tmpdir+"/node2",
                "-autobackupblock=114"],
            [],
            ["-disablewallet",
                "-autobackupwalletpath="+self.options.tmpdir+"/node4",
                "-autobackupblock=114"]]

        self.nodes = start_nodes(5, self.options.tmpdir, extra_args)
        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)
        connect_nodes(self.nodes[2], 0)
        connect_nodes(self.nodes[4], 3)
        self.is_network_split=False
        self.sync_all()

    def one_send(self, from_node, to_address):
        if (randint(1,2) == 1):
            amount = Decimal(randint(1,10)) / Decimal(10)
            self.nodes[from_node].sendtoaddress(to_address, amount)

    def do_one_round(self):
        a0 = self.nodes[0].getnewaddress()
        a1 = self.nodes[1].getnewaddress()
        a2 = self.nodes[2].getnewaddress()

        self.one_send(0, a1)
        self.one_send(0, a2)
        self.one_send(1, a0)
        self.one_send(1, a2)
        self.one_send(2, a0)
        self.one_send(2, a1)

        # Have the miner (node3) mine a block.
        # Must sync mempools before mining.
        sync_mempools(self.nodes)
        self.nodes[3].generate(1)

    # As above, this mirrors the original bash test.
    def start_three(self):

        self.nodes[0] = start_node(0, self.options.tmpdir)
        self.nodes[1] = start_node(1, self.options.tmpdir)
        self.nodes[2] = start_node(2, self.options.tmpdir)

        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)
        connect_nodes(self.nodes[2], 0)

    def stop_three(self):
        stop_node(self.nodes[0], 0)
        stop_node(self.nodes[1], 1)
        stop_node(self.nodes[2], 2)

    def erase_three(self):
        os.remove(self.options.tmpdir + "/node0/regtest/wallet.dat")
        os.remove(self.options.tmpdir + "/node1/regtest/wallet.dat")
        os.remove(self.options.tmpdir + "/node2/regtest/wallet.dat")

    def run_test(self):
        logging.info("Generating initial blockchain")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        self.nodes[1].generate(1)
        sync_blocks(self.nodes)
        self.nodes[2].generate(1)
        sync_blocks(self.nodes)
        self.nodes[3].generate(100)
        sync_blocks(self.nodes)

        assert_equal(self.nodes[0].getbalance(), 50)
        assert_equal(self.nodes[1].getbalance(), 50)
        assert_equal(self.nodes[2].getbalance(), 50)
        assert_equal(self.nodes[3].getbalance(), 0)

        tmpdir = self.options.tmpdir

        logging.info("Creating transactions")
        # Five rounds of sending each other transactions.
        for i in range(5):
            self.do_one_round()


        logging.info("More transactions")
        for i in range(5):
            self.do_one_round()

        # Generate 101 more blocks, so any fees paid mature
        self.nodes[3].generate(101)
        self.sync_all()

        logging.info("Reached block 114. Auto backup triggered.")

        balance0 = self.nodes[0].getbalance()
        balance1 = self.nodes[1].getbalance()
        balance2 = self.nodes[2].getbalance()
        balance3 = self.nodes[3].getbalance()

        total = balance0 + balance1 + balance2 + balance3

        logging.info("Node0 balance:" + str(balance0))
        logging.info("Node1 balance:" + str(balance1))
        logging.info("Node2 balance:" + str(balance2))
        logging.info("Node3 balance:" + str(balance3))

        logging.info("Total: " + str(total))

        # At this point, there are 214 blocks (103 for setup, then 10 rounds, then 101.)
        # 114 are mature, so the sum of all wallets should be 114 * 50 = 5700.
        assert_equal(total, 5700)

        ##
        # Test restoring spender wallets from backups
        ##
        logging.info("Restoring using wallet.dat.auto.114.bak")
        self.stop_three()
        self.erase_three()

        # Start node2 with no chain
        shutil.rmtree(self.options.tmpdir + "/node2/regtest/blocks")
        shutil.rmtree(self.options.tmpdir + "/node2/regtest/chainstate")

        # Restore wallets from backup
        shutil.copyfile(tmpdir + "/node0/wallet.dat.auto.114.bak", tmpdir + "/node0/regtest/wallet.dat")
        shutil.copyfile(tmpdir + "/node1/wallet.dat.auto.114.bak", tmpdir + "/node1/regtest/wallet.dat")
        shutil.copyfile(tmpdir + "/node2/wallet.dat.auto.114.bak", tmpdir + "/node2/regtest/wallet.dat")

        logging.info("Re-starting nodes")
        self.start_three()
        sync_blocks(self.nodes, 10)

        total2 = total = self.nodes[0].getbalance() + self.nodes[1].getbalance() + self.nodes[2].getbalance() + self.nodes[3].getbalance()
        logging.info("Node0 balance:" + str(self.nodes[0].getbalance()))
        logging.info("Node1 balance:" + str(self.nodes[1].getbalance()))
        logging.info("Node2 balance:" + str(self.nodes[2].getbalance()))
        logging.info("Node3.balance:" + str(self.nodes[3].getbalance()))

        logging.info("Total: " + str(total2))



        # Test Node4 auto backup wallet does NOT exist: tmpdir + "/node3/wallet.dat.auto.114.bak"
        # when -disablewallet is enabled then no backup file should be created and graceful exit happens
        # without causing a runtime error
        node4backupexists = 0
        if os.path.isfile(tmpdir + "/node4/wallet.dat.auto.114.bak"):
            node4backupexists = 1
            logging.info("Error: Auto backup performed on node4 with -disablewallet!")


        # Test Node4 debug.log contains a conflict message - length test should be > 0
        debugmsg_list = search_file(tmpdir + "/node4/regtest/debug.log","-disablewallet and -autobackupwalletpath conflict")

        # balances should equal the 114 block auto backup balances
        assert_equal(self.nodes[0].getbalance(), balance0)
        assert_equal(self.nodes[1].getbalance(), balance1)
        assert_equal(self.nodes[2].getbalance(), balance2)
        assert_equal(0,node4backupexists)
        assert_greater_than(len(debugmsg_list),0)

if __name__ == '__main__':
    WalletBackupTest().main()
