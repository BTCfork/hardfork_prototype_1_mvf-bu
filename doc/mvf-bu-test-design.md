# MVF-BU test design

##1. Contents <a id="1-contents"></a>

1. [Contents](#1-contents)
2. [Introduction](#2-introduction)
3. [System tests](#3-system-tests)
4. [Software tests](#4-software-tests)


##2. Introduction <a id="2-introduction"></a>

This document contains design information for system/software tests
added for the MVF-BU.

Its purpose is to let developers (and others) know what needs to be
tested for particular requirements, and how the test(s) written for
a particular requirement will accomplish that.


##3. System tests <a id="3-system-tests"></a>

In some cases, it may be desirable to create a separate high-level test
corresponding to a system requirement (SYS-REQ-*).

In most cases, the tests for software requirements derived from a system
requirement should suffice to cover the required functionality.


TODO: create system tests where needed (it is recommended that they
should be automatically executable 'qa tests' like the rest. although in
some cases the functionality may not be easily verifiable using the
current regression test framework. In that cases it will be acceptable
for the test to consist of a clear manual procedure which can be
followed by a tester to verify the requirement).


##4. Software tests <a id="4-software-tests"></a>

These correspond to the software requirements (SW-REQ-*) in requirements.md.

These should be realized as automated regression tests ("qa tests")
wherever possible.

Several SW requirements can be tested together in one actual test, however
the test script should clearly indicate which SW requirement is being tested
by which test (code) section, and altogether the test should cover the points
below.

If the functionality is complex, it is advisable to split up into
several automated tests along the lines of software requirements.


###4.1 Wallet backup tests

This section gives some notes on the testing of the wallet backup 
requirements (REQ-10-*).


###4.1.1 SW-REQ-10-1

The test should check that various backup location path options can be
exercised:

1. a backup path with a path+filename  (uses exactly that)
2. a backup path only filename (uses default path + specified filename)
3. a backup path only a path (uses default filename)
4. an empty backup path  ( --> uses default path + default filename)


###4.1.2 SW-REQ-10-2

The test should check that no wallet backup has been made BEFORE the
fork trigger height X, i.e. check at the block X-1 that the backup does
not exist yet, then check after block X that the backup now exists.

It is recommended that the test check also for the presence of log messages
related to the creation of the backup.


###4.1.3 SW-REQ-10-3

The test should check that a backup is made when a wallet is active.
This will be covered by the test section for SW-REQ-10-2 already, so that
section can list this requirement as covered.


###4.1.4 SW-REQ-10-4

The test should check that no backup is made when the `--disable-wallet`
option has been used to disable the wallet.

It is recommended that the test check for the presence of log messages
(if any) related to the skipping of the backup.


###4.1.5 SW-REQ-10-5

The test should verify that the client safely shuts down if the backup
fails (e.g. because the path to which to write is read-only).

