#!/usr/bin/env python2
# Copyright (c) 2016 The Bitcoin developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
# Endurance test derived from mvf-core-retarget.py
# to check if "timed out" problem (httplib problem) occurs on
# other clients.
#
# The test just generates a block at a time and does a little RPC
# for a very long period.
# If it runs through, that's a good indication but not proof that the
# problem does not exist on a particular platforms. A couple of
# successful runs should be done (extremely unlikely to pass if the
# problem does exist).
import time
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from datetime import datetime
from random import randint

TEST_PERIOD=180*144          # ~180 days worth of blocks

class Endurance_Test(BitcoinTestFramework):

    def setup_chain(self):

        print("Initializing test directory " + self.options.tmpdir)

        initialize_chain_clean(self.options.tmpdir, 1)

    def setup_network(self):

        self.nodes = []

        self.is_network_split = False

        self.nodes.append(start_node(0, self.options.tmpdir, ["-force-retarget"]))

    def run_test(self):

        print "Generating 99 blocks"

        self.nodes[0].generate(99)

        self.nodes[0].generate(1)

        print "generating individual blocks"

        for n in xrange(TEST_PERIOD):

            self.nodes[0].generate(1)

            best_block_hash = self.nodes[0].getbestblockhash()

            best_block = self.nodes[0].getblock(best_block_hash, True)

            last_block_timestamp = best_block['time']

            assert_equal(101+n, self.nodes[0].getblockcount())

            timenow = time.time()

            diffadjinterval = self.nodes[0].getblockchaininfo()['difficultyadjinterval']

            print "%s height %s %s %d %s" % (
                time.strftime("%Y-%m-%d %H:%M",time.gmtime(timenow)),
                best_block['height'],
                time.strftime("%Y-%m-%d %H:%M",time.gmtime(last_block_timestamp)),
                diffadjinterval,
                best_block['bits'])

            if (n <= 36) :
                # simulate slow blocks i.e. low hash power/high difficulty
                next_block_time = randint(900,1800)
            else:
                # simulate ontime blocks i.e. hash power/difficult around 600 secs
                next_block_time = randint(500,700)

            self.nodes[0].setmocktime(last_block_timestamp + next_block_time )

        print "Done."

if __name__ == '__main__':

    Endurance_Test().main()