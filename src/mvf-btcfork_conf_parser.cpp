// Copyright (c) 2016-2017 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common objects and functions

#include <boost/filesystem/fstream.hpp>
#include <boost/program_options/detail/config_file.hpp>

#include "mvf-bu.h"
#include "mvf-btcfork_conf_parser.h"

using namespace std;

// copied from util.cpp:ReadConfigFile with minor simplifications.
// MVF-BU TOOD: would be good to refactor so we don't need separate procedures
void MVFReadConfigFile(boost::filesystem::path pathCfgFile,
                       map<string, string>& mapSettingsRet,
                       map<string, vector<string> >& mapMultiSettingsRet)
{
    boost::filesystem::ifstream streamConfig(pathCfgFile);
    if (!streamConfig.good())
        return; // No btcfork.conf file is OK

    set<string> setOptions;
    setOptions.insert("*");

    for (boost::program_options::detail::config_file_iterator it(streamConfig, setOptions), end; it != end; ++it)
    {
        // Don't overwrite existing settings so command line settings override bitcoin.conf
        string strKey = string("-") + it->string_key;
        string strValue = it->value[0];
        if (mapSettingsRet.count(strKey) == 0)
            mapSettingsRet[strKey] = strValue;
        mapMultiSettingsRet[strKey].push_back(strValue);
    }
}
