// Copyright (c) 2016 The Bitcoin developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.
// MVF-BU common declarations
#pragma once
#ifndef BITCOIN_MVF_BTCFORK_CONF_PARSER_H
#define BITCOIN_MVF_BTCFORK_CONF_PARSER_H

#include "mvf-bu.h"

// read btcfork.conf file
extern void MVFReadConfigFile(std::map<std::string, std::string>& mapSettingsRet, std::map<std::string, std::vector<std::string> >& mapMultiSettingsRet);

#endif

