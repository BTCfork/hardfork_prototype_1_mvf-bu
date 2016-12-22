// Copyright (c) 2012-2015 The Bitcoin Core developers
// Copyright (c) 2015-2016 The Bitcoin Unlimited developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <boost/test/unit_test.hpp>

#include "mvf-bu.h"
#include "test/test_bitcoin.h"
#ifdef ENABLE_WALLET
#include "wallet/wallet.h"
#endif

BOOST_FIXTURE_TEST_SUITE(mvfstandalone_tests, BasicTestingSetup)

// tests of the wallet backup filename construction
BOOST_AUTO_TEST_CASE(wallet_backup_path_expansion)
{
    boost::filesystem::path datadir = GetDataDir();
    std::string dds = datadir.string();
    static const boost::filesystem::path abspath = "/abs";
    static const boost::filesystem::path relpath = "rel";
    static const boost::filesystem::path fullpath = datadir / "w@.dat";

#ifdef ENABLE_WALLET
    // if first arg is empty, then datadir is prefixed
    BOOST_CHECK_EQUAL(MVFexpandWalletAutoBackupPath("", "w.dat", 0, false),
                      datadir / "w.dat.auto.0.bak");

    // if first arg is relative, then datadir is still prefixed
    BOOST_CHECK_EQUAL(MVFexpandWalletAutoBackupPath("dir", "w.dat", 1, false),
                      datadir / "dir" / "w.dat.auto.1.bak");

    // if first arg is absolute, then datadir is not prefixed
    BOOST_CHECK_EQUAL(MVFexpandWalletAutoBackupPath(abspath.string(), "w.dat", 2, false),
                      abspath / "w.dat.auto.2.bak");

    // if path contains @ it is replaced by height
    BOOST_CHECK_EQUAL(MVFexpandWalletAutoBackupPath("@@@", "w@.dat", 7, false),
                      datadir / "777" / "w7.dat.auto.7.bak");

    // if first contains filename, then appending of filename is skipped
    BOOST_CHECK_EQUAL(MVFexpandWalletAutoBackupPath(fullpath.string(), "w.dat", 6, false),
                      datadir / "w6.dat");
#endif
}

BOOST_AUTO_TEST_SUITE_END()
