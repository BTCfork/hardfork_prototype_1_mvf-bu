# MVF-BU test plan

##1. Contents <a id="1-contents"></a>

1. [Contents](#1-contents)
2. [Introduction](#2-introduction)
3. [Test items](#3-test-items)
4. [Test environment](#4-test-environment)
5. [Test procedures](#5-test-procedures)
   1. [Verification methods](#5-1=verification-methods)
   2. [Test levels](#5-2=test-levels)
   3. [Test types](#5-3=test-types)
   4. [Test phases](#5-4=test-phases)
6. [Testing of functional changes (fork features)](#6-testing-functional)
   1. [TRIG (fork triggering)](#6-1-fork-triggering)
   2. [NSEP (network separation)](#6-2-network-separation)
   3. [DIAD (difficulty adjustment)](#6-3-difficulty-adjustment)
   4. [CSIG (signature change)](#6-4-signature-change)
   5. [WABU (wallet backup)](#6-5-wallet-backup)
   6. [IDME (system identification)](#6-6-system-identification)
7. [Regression testing](#7-regression-testing)
8. [Features not tested](#8-features-not-tested)
9. [Risks and mitigations](#9-risks-and-mitigations)



##2. Introduction <a id="2-introduction"></a>

This document describes the planned verification and validation (V&V)
activities for the MVF-BU [1], in general and specific terms.


###2.1 Overview

It is the objective of this test plan to provide general information
on V&V activities and procedures planned for the MVF-BU software.

V&V is more than just "testing" - there are other verification methods
such as inspection and analysis that contribute to the process of
verifying that a system conforms to its specifications.

During software development, a variety of additional quality assurance
methods such as code reviews and walkthroughs are employed. For MVF-BU,
these are conducted via public repositories of the [BTCfork organization](https://github.com/BTCfork) [0].


###2.2 Scope

This document focuses only on the verification aspects, not other
quality assurance processes.


###2.3 Intended audience

This document should be of interest to those participating in MVF-BU V&V 
activities or generally interested to check that the software will be
adequately verified and validated.

This includes the following persons:

  - software developers
  - software testers
  - integrators from other organizations


###2.4 Context

The MVF-BU is a spin-off (hard fork) client derived from Bitcoin Unlimited.
The changes made to it are intended to be minimal yet sufficient to
produce a viable fork of the Bitcoin network in order to upgrade the
block size from its current 1MB limit.

The MVF-BU design assumes only minimal initial support by existing miners.

TODO: link to development roadmap


###2.5 Related documents

TODO: this is under construction.

1. https://github.com/BTCfork/hardfork_prototype_1_mvf-bu
2. https://github.com/BTCfork
3. [MVF-BU requirements](requirements.md)
4. [MVF-BU design](design.md)
5. [MVF-BU test design](mvf-bu-test-design.md)
6. [MVF-BU roadmap](TODO)



##3. Test items <a id="3-test-items"></a>


###3.1 MVF-BU software

The software is developed in a public repository on GitHub [1].
The `master` branch represents the integration branch. 

There may be feature branches for large developments and release branches
for test releases.


###3.2 Operating systems

Unit tests should be conducted on a variety of operating systems.

The following platforms are expected to be covered by official tests:

- Windows (32- and 64-bit builds)
  - Windows 7
  - Windows 8
  - Windows 10
- Linux (32- and 64-bit builds)
  - Ubuntu 14.04
  - Ubuntu 16.04
  - Debian 7
  - Debian 8
- Mac OSX
  - TODO: versions

It is hoped that developers and testers will provide coverage on
additional operating systems.

##4. Test environment <a id="4-test-environment"></a>


###4.1 Local development environments (regtestnet)

These are any hardware/software platforms that developers on the MVF-BU
project want to use.

They should preferably be capable of building the software with all
functionality (i.e. including GUI, wallet etc), although partial test
results from exotic platforms which only support partial functionality
may still be interesting.

Generally, we find that building with a larger variety of platforms 
will highlight problems in the code and thus lead to a more portable
product.


###4.2 Integration test environment (Github-centric)

The integration test environment will consist of continuous integration
services running the unit and regression tests upon updates of the 
integration branch.

These integration tests may be run on third-party services such as e.g.
Travis, and also various contributors building and running the 
tests in automated ways, e.g. daily runs on their available platform.


###4.3 Isolated (private) testnet / mainnet network clones

Further testing can be done using historic testnet/mainnet blockchain data
on private LANs (IP addresses not routable on from the Internet).


###4.4 Public test network (testnet)

There is an existing public test network (testnet) for Bitcoin which
could be used for initial public network testing.

If deemed necessary, a separate testnet could be deployed.


###4.5 Public operational network (mainnet)

The operational network (mainnet) could be used for a final smoke test
before the MVF-BU is deployed operationally.



##5. Test procedures <a id="5-test-procedures"></a>

The following sections describe verification methods, test types, test
levels and phases. The descriptions are derived from but may deviate
slightly from IEEE software engineering methodology.


###5.1 Verification methods <a id="5-1=verification-methods"></a>

This section describes different verification methods that may be employed.


####5.1.1 Test

Although the most prevalent, testing is just one of several methods
available to verify compliance with requirements. Not all requirements
lend themselves to testing.

Testing is the operation of the system, or a part of the system using
instrumentation or other special test equipment to collect data for later
analysis.


####5.1.2 Demonstration

This refers to the operation of the system, or a part of the system, 
that relies on observable functional operation not requiring the use of
instrumentation, special test equipment, or subsequent analysis.


####5.1.3 Inspection

The visual examination of system components,  e.g. source code and
documentation.


####5.1.4 Analysis

The processing of accumulated data obtained from other qualification
methods. Examples are reduction, interpolation or extrapolation of 
measured data.



###5.2 Test levels <a id="5-2=test-levels"></a>


####5.2.1 Unit test

Also called subunit tests, module test or component test, this refers to
the testing of individual software components or groups of related
components.

A subunit is a piece of software that has a well-defined interface to
its environment and realizes a closed piece of functionality. The
objective of unit testing is to verify that the subunit has been
correctly implemented with regard to its interface definition.

In general, unit testing involves the use of a test harness that allows
artificial input of data and analysis of the subunit output.

In the Bitcoin software, C++ unit tests reside under the src/test/ folder.

TODO: discuss coverage of the unit tests.

For critical subunits, additional software validation methods such as
detailed code walkthroughs may be used.


####5.2.2 Integration test

Integration testing ombines software components and evaluates the
interactions between them.

It is the objective of integration testing to identify interface errors, 
in particular to find differences

- between the specification of an interface function and its actual realisation
- between the specification of the interface usage and its actual usage

In general, integration testing proceeds bottom up, i.e. it starts with 
the integration of basic software services, and proceeds step by step with
the integration of components of higher software layers.
Integration testing ends with a complete running system, which serves as 
starting point for the overall system tests.


####5.2.3 System test

A system test is a test conducted on a complete, integrated system to
evaluate the system's compliance with its specified (system) requirements.


####5.2.3 Acceptance test

The acceptance testing is formal testing conducted to determine whether
or not a system satisfies certain acceptance criteria and to enable the users
to determine whether or not to accept the system.

In traditional development, this is usually done together with the 
customer(s) in Factory Acceptance Tests and later Site Acceptance Tests,
once the system has been delivered and installed.

For MVF-BU, this test phase starts with the deployment of the official
spin-off client which is ready for operational use.

These "customers" are all Bitcoin users who accept the MVF-BU by
running it - or not. They may of course elect to run a derivative of the
MVF-BU, or a network-compatible alternative client (MVF-X), or a
completely different client, or stick with the existing popular 
implementation (Bitcoin Core) and its network.


###5.3 Test types <a id="5-3=test-types"></a>

The following definitions are provided as a basis for talking about
the kinds of tests.


####5.3.1 Functional test

A test which focuses on a specific functionality.


####5.3.2 Performance test

A test which focuses on performance aspects specified by non-functional
requirements.


####5.3.3 Reliability and availability test

A test which focuses on reliability and availability specified by
non-functional requirements.


####5.3.4 Robustness test

A test which focuses on robustness specified by non-functional requirements.


####5.3.5 Regression test

A test which is executed to verify that there is no regression of the
system w.r.t functional or non-functional requirements.


###5.4 Test phases <a id="5-4=test-phases"></a>


####5.4.1 Unit testing phase

Developers construct unit tests covering the new functionality where
possible and run these in their local development environments.


####5.4.2 Integration testing phase

Functional items are integrated on the `master` branch of the software
repository.

Automated continuous integration (CI) should ensure that
builds and unit tests pass on various operating systems.


####5.4.3 Testnet testing phase

When the functionality has been completed to a satisfactory degree and
local / isolated testnet testing shows that there is little to no risk of
disruption to existing networks, testing may move to the `testnet` public
Bitcoin test network on the Internet.


####5.4.4 Mainnet testing phase

When testing on the testnet shows no significant problems and indicates
that there is no risk of disruption to the network, testing may move to
the `mainnet` public Bitcoin operational network for final testing prior
to deployment.



##6. Testing of functional changes (fork features) <a id="6-testing-functional"></a>

New functionality should be accompanied by unit tests where possible,
and have at least one software test covering the software requirements.

Successful execution of these tests should be visible through logs
produced by public continuous integration test systems.

Any tests which cannot be performed automatically should be conducted
and evidence deposited into a public repository of MVF-BU test results.
Test records there should be electronically signed by the developers or 
testers who performed them.

TODO: create a "test records" repository for MVF-BU results, including
especially those for non-automatic tests.

The status of these tests (pass/fail/inconclusive) can be voted on by 
the active MVF-BU developers and testers.


##6.1 TRIG (fork triggering) <a id="6-1-fork-triggering"></a>

To be completed.


##6.2 NSEP (network separation) <a id="6-2-network-separation"></a>

To be completed.


##6.3 DIAD (difficulty adjustment) <a id="6-3-difficulty-adjustment"></a>

To be completed.


##6.4 CSIG (signature change) <a id="6-4-signature-change"></a>

To be completed.


##6.5 WABU (wallet backup) <a id="6-5-wallet-backup"></a>

This functionality is quite independent from the rest, and lends itself
well to unit testing.

A single software test can probably cover all the software requirements
for this functionality.


##6.6 IDME (system identification) <a id="6-6-system-identification"></a>

To be completed.



##7. Regression testing <a id="7-regression-testing"></a>

The entire unit test suites and "qa" test suite should be successfully
executed as a regression test.

If there are "qa" tests which do not pass and intended to be waived,
this must be clearly documented, with justification, in drafts and
final versions of the MVF-BU release notes.



##8. Features not tested <a id="8-features-not-tested"></a>

Any features which are implemented but not tested must be clearly
documented in this section, with justification, and mentioned in drafts
and final versions of the MVF-BU release notes.


###8.1 Safe shutdown on failure to backup wallet

Currently the method of exiting (runtime error) cannot be caught by
the qa test framework, making the expected shutdown of a client
not possible to test in the automatic test.

It might be necessary to change how the node exits, or to adapt the
test framework to be able to handle this case.


##9. Risks and mitigations <a id="9-risks-and-mitigations"></a>

To be completed.
