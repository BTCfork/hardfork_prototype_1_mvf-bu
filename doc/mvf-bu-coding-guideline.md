# MVF-BU coding guideline

## Introduction

This document describes some of the coding guidelines that contributors to
MVF-BU should follow.

First of all, we need to keep in mind that MVF-BU is a fork of Bitcoin
Unlimited (BU), and maybe the projects will converge again / need to have
code merged in either direction or into other Bitcoin clients.
For that reason, we should try to follow the general rules/conventions
that apply to Satoshi-derived Bitcoin clients, and for the MVF-BU we should
follow BU-compatible coding rules.

The last thing we want to do is argue about coding conventions. So if you
have a question or suggestion, let us discuss it before you submit that
huge Pull Request, and we will get it sorted out beforehand and adapt
these guidelines where necessary. Please contact us on the #dev channel on
<https://btcforks.slack.com> to discuss.


## Related documents

Some of the general rules and those formulated by BU are documented in the
following files in this doc/ folder:

1. developer-notes.md: general coding rules and some guidelines for
   Bitcoin Unlimited (and therefore MVF-BU too)

[ TODO: list any additional files and what info they contain that should
be paid attention to: ]


## MVF-BU repositories and branching model

The original repository at <https://github.com/BTCfork/hardfork_prototype_1_mvf-bu>
is considered the main development repository for now.

If you want to develop, please clone from there or fork this repository
on GitHub.

The default development branch is `master`.

You should always branch off `master` in your own repo before doing some
development. Branch off into a feature branch if your development is
going to implement a new feature, or a hotfix branch if you are going to
fix an issue.

Branch naming convention in your own forked repo is your business,
but please make sure that you follow the commit message and PR naming
conventions laid out in further sections.

The following table gives an overview of the branches in the main repo
and their purpose.


| Branch name  | Purpose of branch                                     |
| ------------ |------------------------------------------------------ |
| master       | Main development and integration branch. Pull requests should be made relative to this branch. |
| 0.12.1bu     | Vendor branch - tracks upstream work on BU 0.12.1. No MVF development takes place here. It exists only so that MVF-BU can be more easily rebased onto latest BU 0.12.1 changes. If upstream rebases onto a newer version of Core, we will freeze this branch and create another upstream tracking branch.              |


## Marking code changes

More important than code markers are accurate commit messages.
However, BU uses code markers to help them with merging, and so will
we for this MVF development.

Ensure that changes are marked unless it is absolutely not possible
for technical reasons (some files simply do not allow it, it is
forgivable in those cases.


### Copyrights

Suggested we use the `The Bitcoin developers` for BTCfork related work.
Where necessary add to the copyright messages, or create a new one.
Do not remove existing attribution.


### Changing legacy code sections

Add a marker comment that shows that the section has been changed by MVF-BU.
A suitable comment format for single-line changes:

    // MVF-BU: some change description

For multi-line sections, it is often impractical/counterproductive to add
such a comment on each changed line.

In those cases a begin/end format can be used, e.g.

    // MVF-BU begin: some change description (include req/design id!)
    ... ( changed code section)
    // MVF-BU end


## Commit messages / PR descriptions

This is also not directly coding related, but will make all our lives
easier if we stick to some conventions.

What follows are draft proposals, and subject to change as we move along.
We will try to keep changes minimal however.

Think about whether a change you are making can be adequately expressed
by the conventions below.

If not, contact us before you commit, so that we can potentially extend
the guidelines as you need. This will make the end result more consistent.


### Commit messages

These should contain a brief description on the first line.
There can be other paragraphs giving more details.

If a commit or PR is only about documentation, like this document, then
it should be prefixed by `[doc]`, e.g:

    [doc] update the coding guideline

For regression tests (qa/ folder) it should be prefixed by `[qa]`, e.g.

    [qa] add a test for MVHF-BU-SW-REQ-x-y

If the commit is addressing a GitHub issue for the project,
then the first line (description) should reference the Issue number. If
this needs to be combined with other prefixes, the square bracket tags
should go in front, like this:

    [doc] Issue#123: correct the installation manual

A `[bld]` tag should be used for matters related to the build system,
packaging scripts or templates files, gitian descriptors or any
interfacing related to external continuous integration (CI) systems:

    [bld] Issue#444: add a specfile for building on CentOS

If a commit is solely non-issue related development work, please include
the identifier of a requirement or design element that this relates to,
and make sure that the requirement or design element is included in
a comment near code which you have changed.

    safe client shutdown for wallet backup failure (MVHF-BU-SW-REQ-10-5)


### Pull requests (PRs)

All PRs should be made against the `master` branch of `BTCfork/hardfork_prototype_1_mvf-bu` .

Where a PR is simple enough to be described by a single prefix tag like
`[doc]`, `[qa]` or `[bld]`, the title of the PR should contain this prefix.

For more complex PRs (which is typically the case), the title description
should contain an identifier such as an Issue# (like for commits) if the
PR covers


## General Bitcoin coding rules

To be completed if there is anything that still needs to be said that is
not in the referenced docs e.g. developer-notes.md.


## BU-specific rules

The BU project lead developer, Andrew Stone, has in the past given the
specific advice \[1\], which is summarized in this section.

This advice largely stems from Unlimited being periodically rebased onto Core.
This is a difficult operation that can be greatly helped by certain coding
techniques that might otherwise not be seen as "better" programming.

1. As much as possible, we \[BU\] isolate new logic into Unlimited-specific
   files and make a single function call in common code.
   MVF-BU should follow a similar guideline, isolating code into new
   MVF-BU-specific files where possible.
   Rationale: Having complex logic in isolated files means that it gets
   pulled in verbatim during a rebase.

2. \[code removal\] Once code is removed in BU, during a rebase it cannot
   distinguish it from code that is added in the new Core version.
   So the code will risk getting automatically added back in during every
   rebase. The solution is to "additively remove" the code.
   In other words, comment it out.  For example, rather than deleting:

       `const int MAX_OUTBOUND_CONNECTIONS = 8;`

   do

       `// const int MAX_OUTBOUND_CONNECTIONS = 8;  // BU constant replaced by configurable param.`

3. Finally, all changes to common code are marked with a `// BU` or
   `// BUIPXXX comment`, so the BU developers know to pay extra attention to
   these areas if they see merge conflicts in them.

   [MVF-BU note: we use the comment tag `// MVF-BU` instead of `// BU`

[1] https://github.com/BitcoinUnlimited/BitcoinUnlimited/pull/73#issuecomment-239594663


## MVF-BU-specific rules (added by BTCfork)

1. Code changes need to traceable back to design. In general, only things
   that are described in the design document should be coded up. If they
   are not, make sure you ask why they are not in the design document.
   Maybe they just need to be added. Or maybe there are not even
   requirements for them, in which case that needs changing first.
   Raise GH issues where necessary.

   Example of tracing back to a design element from a code change:

   `strClient = "Bitcoin MVF-BU client";  // MVF-BU client name (MVHF-BU-DES-IDME-1)`

   Please participate to make the design complete and precise where you
   want to make a change that is not presently described.

   In the final review we will look at all code changes and check that
   they are traceable.

2. Instead of `// BU` comments, we use `// MVF-BU` tags.

   This should generally be completed with some description of the change,
   preferably citing the associated design element (preferably) or requirement.

   If `// BU` tags need to be moved around, preserve their contents
   (including the BU tag).
