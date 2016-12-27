// Copyright (c) 2012-2015 The Bitcoin Core developers
// Copyright (c) 2015-2016 The Bitcoin Unlimited developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <fstream>
#include <boost/test/unit_test.hpp>

#include "mvf-bu.h"
#include "mvf-btcfork_conf_parser.h"
#include "test/test_bitcoin.h"

#ifdef ENABLE_WALLET
#include "wallet/wallet.h"
#endif

BOOST_FIXTURE_TEST_SUITE(mvfstandalone_tests, BasicTestingSetup)

// tests of the wallet backup filename construction
BOOST_AUTO_TEST_CASE(wallet_backup_path_expansion)
{
    std::string platform(BOOST_PLATFORM);

    boost::filesystem::path datadir = GetDataDir();
    std::string dds = datadir.string();
    static const boost::filesystem::path abspath(GetDataDir());
    static const boost::filesystem::path relpath("rel");
    static const boost::filesystem::path fullpath = datadir / "w@.dat";
    static const boost::filesystem::path userpath("/home/user/.bitcoin");

    // sanity checks
    BOOST_CHECK(abspath.is_absolute());
    BOOST_CHECK(!abspath.is_relative());
    BOOST_CHECK(relpath.is_relative());
    BOOST_CHECK(!relpath.is_absolute());
    BOOST_CHECK(!relpath.has_root_directory());
    BOOST_CHECK(fullpath.has_filename());
    BOOST_CHECK(userpath.has_filename());
    BOOST_CHECK(userpath.has_extension());
    BOOST_CHECK_EQUAL(userpath.filename(), ".bitcoin");
    BOOST_CHECK_EQUAL(userpath.extension(), ".bitcoin");
    BOOST_CHECK_EQUAL(userpath.extension(), userpath.filename());

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


BOOST_AUTO_TEST_CASE(btcfork_conf_maps)
{
    btcforkMapArgs.clear();
    btcforkMapArgs["strtest1"] = "string...";
    // strtest2 undefined on purpose
    btcforkMapArgs["inttest1"] = "12345";
    btcforkMapArgs["inttest2"] = "81985529216486895";
    // inttest3 undefined on purpose
    btcforkMapArgs["booltest1"] = "";
    // booltest2 undefined on purpose
    btcforkMapArgs["booltest3"] = "0";
    btcforkMapArgs["booltest4"] = "1";

    BOOST_CHECK_EQUAL(MVFGetArg("strtest1", "default"), "string...");
    BOOST_CHECK_EQUAL(MVFGetArg("strtest2", "default"), "default");
    BOOST_CHECK_EQUAL(MVFGetArg("inttest1", -1), 12345);
    BOOST_CHECK_EQUAL(MVFGetArg("inttest2", -1), 81985529216486895LL);
    BOOST_CHECK_EQUAL(MVFGetArg("inttest3", -1), -1);
    BOOST_CHECK_EQUAL(MVFGetBoolArg("booltest1", false), true);
    BOOST_CHECK_EQUAL(MVFGetBoolArg("booltest2", false), false);
    BOOST_CHECK_EQUAL(MVFGetBoolArg("booltest3", false), false);
    BOOST_CHECK_EQUAL(MVFGetBoolArg("booltest4", false), true);
}

// test MVFGetConfigFile(), the MVF config (btcfork.conf) filename construction
BOOST_AUTO_TEST_CASE(mvfgetconfigfile)
{
    BOOST_CHECK_EQUAL(MVFGetConfigFile(), GetDataDir() / BTCFORK_CONF_FILENAME);
}

// test MVFReadConfigFile() which reads a config file into arg maps
BOOST_AUTO_TEST_CASE(mvfreadconfigfile)
{
    boost::filesystem::path pathBTCforkConfigFile = GetTempPath() / boost::filesystem::unique_path("btcfork.conf.%%%%.txt");
    //fprintf(stderr,"btcfork_conf_file: set config file %s\n", pathBTCforkConfigFile.string().c_str());
    BOOST_CHECK(!boost::filesystem::exists(pathBTCforkConfigFile));
    try
    {
        std::ofstream btcforkfile(pathBTCforkConfigFile.string().c_str(), std::ios::out);
        btcforkfile << "forkheight=" << HARDFORK_HEIGHT_REGTEST << "\n";
        btcforkfile << "forkid=" << HARDFORK_SIGHASH_ID << "\n";
        btcforkfile << "autobackupblock=" << (HARDFORK_HEIGHT_REGTEST - 1) << "\n";
        btcforkfile.close();
    } catch (const std::exception& e) {
        BOOST_ERROR("Cound not write config file " << pathBTCforkConfigFile << " : " << e.what());
    }
    BOOST_CHECK(boost::filesystem::exists(pathBTCforkConfigFile));
    // clear args map and read file
    btcforkMapArgs.clear();
    try
    {
        MVFReadConfigFile(pathBTCforkConfigFile, btcforkMapArgs, btcforkMapMultiArgs);
    } catch (const std::exception& e) {
        BOOST_ERROR("Cound not read config file " << pathBTCforkConfigFile << " : " << e.what());
    }
    // check map after reading
    BOOST_CHECK_EQUAL(atoi(btcforkMapArgs["-forkheight"]), (int)HARDFORK_HEIGHT_REGTEST);
    BOOST_CHECK_EQUAL(atoi(btcforkMapArgs["-forkid"]), (int)HARDFORK_SIGHASH_ID);
    BOOST_CHECK_EQUAL(atoi(btcforkMapArgs["-autobackupblock"]), (int)(HARDFORK_HEIGHT_REGTEST - 1));
    // cleanup
    boost::filesystem::remove(pathBTCforkConfigFile);
    BOOST_CHECK(!boost::filesystem::exists(pathBTCforkConfigFile));
}

BOOST_AUTO_TEST_SUITE_END()
