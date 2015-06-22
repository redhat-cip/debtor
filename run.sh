#!/bin/sh
#
# Copyright (C) 2015 Red Hat Inc
#
# Author: Frederic Lepied <frederic.lepied@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

top=$(cd $(dirname $0); pwd)

if [ $# != 4 ]; then
    echo "Usage: $0 <git top dir> <exclude> <urlpath without http://>" "<branch>" 1>&2
    exit 1
fi

gitdir="$1"
exclude="$2"
urlpath="$3"
branch="$4"
date=${DATE:=$(date '+%Y%m%d')}
name=$(basename $(dirname $urlpath))

mkdir -p $top/srpms/$name/$date
cd $top/srpms/$name/$date
if [ ! -d $urlpath ]; then
    wget --level=1 --recursive --no-parent --accept 'src.rpm' http://$urlpath
fi

resultdir=$top/results/$name/$date
mkdir -p $resultdir
for p in $urlpath/*.src.rpm; do
    if [ ! -d $resultdir/$(basename $p) ]; then
        $top/extract.sh $p $gitdir $exclude $resultdir $branch
    fi
    if [ -d $resultdir/$(basename $p) ]; then
        $top/score.py $resultdir/$(basename $p) > $resultdir/$(basename $p)/score 2> $resultdir/$(basename $p)/score.html
    fi
done

echo "<h2>Global score is a technical debt assessment, the lower, the better</h2>"> $resultdir/score.html
global=0
for f in $resultdir/*/score; do
    global=$(($(cat $f) + $global))
done
echo "<h3>Score for the set of packages: $global</h3>" >> $resultdir/score.html
echo "Date: $date<br/>" >> $resultdir/score.html
echo "Packages: <a href=\"http://$urlpath\">http://$urlpath</a> <br/> <br/>" >> $resultdir/score.html
echo "<table>" >> $resultdir/score.html
for f in $resultdir/*/score; do
    echo "$(cat $f) $(basename $(dirname $f))"
done | sort -nr | while read score file; do
    count=$(ls -d $resultdir/$file/*.patch 2> /dev/null|wc -l || echo 0)
    if [ $count -gt 1 ]; then
        es=es
    else
        es=
    fi
    if [ $count = 0 ]; then
        style="color:green"
    elif [ $(( $score/$count )) -gt 50 ]; then
        style="color:red"
    else
        style="color:orange"
    fi
    echo "<tr><td>$score</td><td><a href=\"$file/score.html\" style=\"$style\">$file</a></td><td><a href=\"$file\">$count patch$es</a></td></tr>" >> $resultdir/score.html
done
echo "</table>" >> $resultdir/score.html

echo "<p>Legend:</p>" >> $resultdir/score.html
echo "<p style=\"color:green\">Score per patch is 0</p>" >> $resultdir/score.html
echo "<p style=\"color:orange\">Score per patch is lower than 50</p>" >> $resultdir/score.html
echo "<p style=\"color:red\">Score per patch is greater than 50</p>" >> $resultdir/score.html

cd $resultdir/..
rm -f latest
ln -s $date latest

# run.sh ends here
