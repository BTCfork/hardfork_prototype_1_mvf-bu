#!/usr/bin/env python2
# Copyright (c) 2014-2015 The Bitcoin Core developers
# Copyright (c) 2015-2016 The Bitcoin Unlimited developers
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
# MVF-BU
"""
See https://github.com/BTCfork/hardfork_prototype_1_mvf-bu/blob/master/doc/mvf-bu-test-design.md#411

Exercise the auto backup wallet code.  Ported from walletbackup.sh.

Test case is:
5 nodes. 1 2 and 3 send transactions between each other, fourth node is a miner.
The 5th node does no transactions and only tests for the -disablewallet conflict.
.
1 2 3 each mine a block to start, then
Miner creates 100 blocks so 1 2 3 each have 50 mature coins to spend.
Then 5 iterations of 1/2/3 sending coins amongst
themselves to get transactions in the wallets,
and the miner mining one block.

Then 5 more iterations of transactions and mining a block.

The node config sets wallets to automatically back up
as defined in the backupblock constant 114.

Balances are saved for sanity check:
  Sum(1,2,3,4 balances) == 114*50

1/2/3/4 are shutdown, and their wallets erased.
Then restored using the auto backup wallets eg wallet.dat.auto.114.bak.
Sanity check to confirm 1/2/3/4 balances match the 114 block balances.
Sanity check to confirm 5th node does NOT perform the auto backup
and that the debug.log contains a conflict message

Node 2 is rewinded to before the backup height, and a check is made that
an existing backup is copied to a .old file with identical contents if the
existing backup is overwritten.

Finally, node 1 is stopped, its wallet backup is deleted, and the node is
restarted. A post-fork block is generated to check that the wallet backup
is not re-performed once the node has already forked.
"""

import os
import fnmatch
import hashlib
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from random import randint
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

# backup block must be > 113 as these blocks are used for context setup
backupblock = 114

class WalletBackupTest(BitcoinTestFramework):

    def setup_chain(self):
        logging.info("Initializing test directory "+self.options.tmpdir)
        initialize_chain_clean(self.options.tmpdir, 5)

    # This mirrors how the network was setup in the bash test
    def setup_network(self, split=False):
        logging.info("Starting nodes")

        # nodes 1, 2,3 are spenders, let's give them a keypool=100
        # and configure option autobackupwalletpath
        # testing each file path variant
        # as per the test design at sw-req-10-1
        self.extra_args = [
            ["-keypool=100",
                "-autobackupwalletpath=%s"%(os.path.join(self.options.tmpdir,"node0","newabsdir","pathandfile.@.bak")),
                "-forkheight=%s"%(backupblock+1),
                "-autobackupblock=%s"%(backupblock)],
            ["-keypool=100",
                "-autobackupwalletpath=filenameonly.@.bak",
                "-forkheight=%s"%(backupblock+1),
                "-autobackupblock=%s"%(backupblock)],
            ["-keypool=100",
                "-autobackupwalletpath=" + os.path.join(".","newreldir"),
                "-forkheight=%s"%(backupblock+1),
                "-autobackupblock=%s"%(backupblock)],
            ["-autobackupblock=%s"%(backupblock),
                "-forkheight=%s"%(backupblock+1)],
            ["-disablewallet",
                "-autobackupwalletpath="+ os.path.join(self.options.tmpdir,"node4"),
                "-forkheight=%s"%(backupblock+1),
                "-autobackupblock=%s"%(backupblock)]]

        self.nodes = start_nodes(5, self.options.tmpdir, self.extra_args)
        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)
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
    def start_four(self):
        for i in range(4):
            self.nodes[i] = start_node(i, self.options.tmpdir, self.extra_args[i])

        connect_nodes(self.nodes[0], 3)
        connect_nodes(self.nodes[1], 3)
        connect_nodes(self.nodes[2], 3)


    def stop_four(self):
        stop_node(self.nodes[0], 0)
        stop_node(self.nodes[1], 1)
        stop_node(self.nodes[2], 2)
        stop_node(self.nodes[3], 3)

    def erase_hot_wallets(self):
        for node in xrange(4):
            os.remove(os.path.join(self.options.tmpdir,"node%s" % node,"regtest","wallet.dat"))

    def run_test(self):
        logging.info("Automatic backup configured for block %s"%(backupblock))
        assert_greater_than(backupblock, 113)

        # target backup files
        node0backupfile = os.path.join(self.options.tmpdir,"node0","newabsdir","pathandfile.%s.bak"%(backupblock))
        node1backupfile = os.path.join(self.options.tmpdir,"node1","regtest","filenameonly.%s.bak"%(backupblock))
        node2backupfile = os.path.join(self.options.tmpdir,"node2","regtest","newreldir","wallet.dat.auto.%s.bak"%(backupblock))
        node3backupfile = os.path.join(self.options.tmpdir,"node3","regtest","wallet.dat.auto.%s.bak"%(backupblock))

        logging.info("Generating initial blockchain")
        self.nodes[0].generate(1)
        sync_blocks(self.nodes)
        self.nodes[1].generate(1)
        sync_blocks(self.nodes)
        self.nodes[2].generate(1)
        sync_blocks(self.nodes)
        self.nodes[3].generate(100)

        sync_blocks(self.nodes)
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

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

        # At this point should be 113 blocks
        self.sync_all()
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

        # Generate any further blocks to reach the backup block
        blocks_remaining = backupblock - self.nodes[0].getblockcount() - 1
        if (blocks_remaining) > 0:
            self.nodes[3].generate(blocks_remaining)

        self.sync_all()
        logging.info("Generated %s blocks"%(self.nodes[0].getblockcount()))

        # Only 1 more block until the auto backup is triggered
        # Test the auto backup files do NOT exist yet
        node0backupexists = 0
        node1backupexists = 0
        node2backupexists = 0
        node3backupexists = 0

        if os.path.isfile(node0backupfile):
            node0backupexists = 1
            logging.info("Error backup exists too early: %s"%(node0backupfile))

        if os.path.isfile(node1backupfile):
            node1backupexists = 1
            logging.info("Error backup exists too early: %s"%(node1backupfile))

        if os.path.isfile(node2backupfile):
            node2backupexists = 1
            logging.info("Error backup exists too early: %s"%(node2backupfile))

        if os.path.isfile(node3backupfile):
            node3backupexists = 1
            logging.info("Error backup exists too early: %s"%(node3backupfile))

        assert_equal(0, node0backupexists)
        assert_equal(0, node1backupexists)
        assert_equal(0, node2backupexists)
        assert_equal(0, node3backupexists)

        # Generate the block that should trigger the auto backup
        self.nodes[3].generate(1)
        self.sync_all()
        assert_equal(self.nodes[0].getblockcount(),backupblock)

        logging.info("Reached backup block %s automatic backup triggered"%(self.nodes[0].getblockcount()))

        # Test if the backup files exist
        if os.path.isfile(node0backupfile): node0backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node0backupfile))

        if os.path.isfile(node1backupfile): node1backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node1backupfile))

        if os.path.isfile(node2backupfile):
            node2backupexists = 1
            # take MD5 for comparison to .old file in later test
            node2backupfile_orig_md5 = hashlib.md5(open(node2backupfile, 'rb').read()).hexdigest()
        else: logging.info("Error backup does not exist: %s"%(node2backupfile))

        if os.path.isfile(node3backupfile): node3backupexists = 1
        else: logging.info("Error backup does not exist: %s"%(node3backupfile))

        assert_equal(1, node0backupexists)
        assert_equal(1, node1backupexists)
        assert_equal(1, node2backupexists)
        assert_equal(1, node3backupexists)

        # generate one more block to trigger the fork
        self.nodes[3].generate(1)
        self.sync_all()
        assert_equal(self.nodes[0].getblockcount(),backupblock+1)

        ##
        # Calculate wallet balances for comparison after restore
        ##

        # Balance of each wallet
        balance0 = self.nodes[0].getbalance()
        balance1 = self.nodes[1].getbalance()
        balance2 = self.nodes[2].getbalance()
        balance3 = self.nodes[3].getbalance()

        total = balance0 + balance1 + balance2 + balance3

        logging.info("Node0 balance:" + str(balance0))
        logging.info("Node1 balance:" + str(balance1))
        logging.info("Node2 balance:" + str(balance2))
        logging.info("Node3 balance:" + str(balance3))

        logging.info("Original Wallet Total: " + str(total))

        ##
        # Test restoring spender wallets from backups
        ##
        logging.info("Switching wallets. Restoring using automatic wallet backups...")
        self.stop_four()
        self.erase_hot_wallets()

        # Restore wallets from backup
        shutil.copyfile(node0backupfile, os.path.join(tmpdir,"node0","regtest","wallet.dat"))
        shutil.copyfile(node1backupfile, os.path.join(tmpdir,"node1","regtest","wallet.dat"))
        shutil.copyfile(node2backupfile, os.path.join(tmpdir,"node2","regtest","wallet.dat"))
        shutil.copyfile(node3backupfile, os.path.join(tmpdir,"node3","regtest","wallet.dat"))

        logging.info("Re-starting nodes")
        self.start_four()
        self.sync_all()

        total2 = self.nodes[0].getbalance() + self.nodes[1].getbalance() + self.nodes[2].getbalance() + self.nodes[3].getbalance()
        logging.info("Node0 balance:" + str(self.nodes[0].getbalance()))
        logging.info("Node1 balance:" + str(self.nodes[1].getbalance()))
        logging.info("Node2 balance:" + str(self.nodes[2].getbalance()))
        logging.info("Node3.balance:" + str(self.nodes[3].getbalance()))

        logging.info("Backup Wallet Total: " + str(total2))

        # balances should equal the auto backup balances
        assert_equal(self.nodes[0].getbalance(), balance0)
        assert_equal(self.nodes[1].getbalance(), balance1)
        assert_equal(self.nodes[2].getbalance(), balance2)
        assert_equal(self.nodes[3].getbalance(), balance3)
        assert_equal(total,total2)

        # Test Node4 auto backup wallet does NOT exist: tmpdir + "/node4/wallet.dat.auto.114.bak"
        # when -disablewallet is enabled then no backup file should be created and graceful exit happens
        # without causing a runtime error
        node4backupexists = 0
        if os.path.isfile(os.path.join(tmpdir,"node4","regtest","wallet.dat.auto.%s.bak"%(backupblock))):
            node4backupexists = 1
            logging.info("Error: Auto backup performed on node4 with -disablewallet!")

        # Test Node4 debug.log contains a conflict message - length test should be > 0
        debugmsg_list = search_file(os.path.join(tmpdir,"node4","regtest","debug.log"),"-disablewallet and -autobackupwalletpath conflict")

        assert_equal(0,node4backupexists)
        assert_greater_than(len(debugmsg_list),0)

        # test that existing wallet backup is preserved
        # rewind node 2's chain to before backupblock
        logging.info("Stopping all nodes")
        self.stop_four()
        for n in xrange(4):
            os.unlink(os.path.join(tmpdir,"node%s" % n,"btcfork.conf"))
        logging.info("Erasing blockchain on node 2 while keeping backup file")
        shutil.rmtree(self.options.tmpdir + "/node2/regtest/blocks")
        shutil.rmtree(self.options.tmpdir + "/node2/regtest/chainstate")
        logging.info("Restarting node 2")
        self.nodes[2] = start_node(2, self.options.tmpdir,["-keypool=100",
                                                           "-autobackupwalletpath="+ os.path.join(".","newreldir"),
                                                           "-forkheight=%s"%(backupblock+1),
                                                           "-autobackupblock=%s"%(backupblock) ])

        # check that there is no .old yet (node 2 needs to generate a block to hit the height)
        old_files_found=[]
        for file in os.listdir(os.path.join(tmpdir,"node2","regtest","newreldir")):
            if fnmatch.fnmatch(file, "wallet.dat.auto.%s.bak.*.old" % (backupblock)):
                logging.info("old file found: %s" % file)
                old_files_found.append(file)
        assert_equal(0, len(old_files_found))
        # generate enough blocks to hit the backup block height
        # this should cause the existing backup to be saved to a timestamped .old copy
        self.nodes[2].generate(backupblock)
        for file in os.listdir(os.path.join(tmpdir,"node2","regtest","newreldir")):
            if fnmatch.fnmatch(file, "*.old"):
                old_files_found.append(file)
        assert_equal(1, len(old_files_found))
        # check that the contents of the .old match what we recorded earlier for node 2's backup
        # (the file should just have been renamed)
        logging.info("Checking .old file %s" % old_files_found[0])
        assert_equal(node2backupfile_orig_md5,hashlib.md5(open(os.path.join(tmpdir,"node2","regtest","newreldir",old_files_found[0]), 'rb').read()).hexdigest())
        # generate the fork block
        self.nodes[2].generate(backupblock+1)
        logging.info("Checksum ok - shutting down")
        stop_node(self.nodes[2], 2)
        os.unlink(os.path.join(tmpdir,"node2","btcfork.conf"))
        self.start_four()

        # test that wallet backup is not performed again if fork has already
        # triggered and wallet exists
        # (otherwise it would backup a later-state wallet)
        logging.info("stopping node 1")
        stop_node(self.nodes[1], 1)
        logging.info("checking that wallet backup file exists: %s" % node1backupfile)
        assert(os.path.isfile(node1backupfile))
        logging.info("removing wallet backup file %s" % node1backupfile)
        os.remove(node1backupfile)
        # check that no wallet backup file created
        logging.info("restarting node 1")
        os.unlink(os.path.join(tmpdir,"node1","btcfork.conf"))
        self.nodes[1] = start_node(1, self.options.tmpdir, ["-keypool=100",
                                                            "-autobackupwalletpath=filenameonly.@.bak",
                                                            "-forkheight=%s"%(backupblock+1),
                                                            "-autobackupblock=%s"%(backupblock)])
        logging.info("generating another block on node 1")
        self.nodes[1].generate(1)
        logging.info("checking that backup file has not been created again...")
        node1backupexists = 0
        if os.path.isfile(node1backupfile):
            node1backupexists = 1
            logging.info("Error: Auto backup created again on node1 after fork has already activated!")
        assert_equal(0, node1backupexists)


if __name__ == '__main__':
    WalletBackupTest().main()
