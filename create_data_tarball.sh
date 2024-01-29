#!/usr/bin/bash

set -xe

rm -rf data
mkdir data
cd data

# LICENSE: Unicode-3.0
curl -o UCD-15.0.0.zip https://www.unicode.org/Public/15.0.0/ucd/UCD.zip
mkdir ucd
unzip UCD-15.0.0.zip -d ucd
rm -f UCD-15.0.0.zip

# LICENSE: Apache-2.0
git clone https://github.com/nigeltao/parse-number-fxx-test-data
rm -rf parse-number-fxx-test-data/.git

# LICENSE: MIT
git clone https://github.com/json5/json5-tests.git
rm -rf json5-tests/.git
curl -O https://raw.githubusercontent.com/Perl/perl5/blead/t/re/re_tests

tar caf ../vss-tests-data.tar.bz2 .
