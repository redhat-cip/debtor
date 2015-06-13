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

if [ $# != 5 ]; then
    echo "Usage: $0 <src.rpm> <git top dir> <exclude file> <target dir> <branch>" 1>&2
    exit 1
fi

top=$(cd $(dirname $0); pwd)
pkg="$1"
base=$(basename $pkg)
exclude="$3"
target="$4/$base"
branch="$5"
project=$(echo $base|sed -e 's/^openstack-//' -e 's/-[0-9A-Z].*//')

# hack to avoid interdiff calling patch interactively
PATH=$top/hack:$PATH

# project we don't want to process
if grep -q "^$project\$" $exclude; then
    echo "$project on the exclude list. Stopping." 1>&2
    exit 0
fi

# translate package name to git repo name
case $project in
    tempest-kilo)
        project=tempest
        ;;
    swift-plugin-swift3)
        project=swift3
        ;;
    python-django-openstack-auth)
        project=django_openstack_auth
        ;;
    qemu-kvm-rhev)
        project=qemu
        ;;
    python-django-horizon)
        project=horizon
        ;;
esac

git="$2/$project"

try_cherry_pick() {
    if cd $git; then
        commitid=$(sed -n -e 's/.*cherry picked from commit \([0-9a-f]\{40\}\).*/\1/p' < $patchrpm | head -1)
        if [ -n "$commitid" ]; then
            git fetch origin master
            git show $commitid > $patchrpm.git
            interdiff -q --no-revert-omitted -w $patchrpm $patchrpm.git > "$target/$patch/interdiff.patch"
            cat > "$target/$patch/review.json" <<EOF
{"status":"CHERRY", "commit":"$commitid"}
EOF
        else
            cat > "$target/$patch/review.json" <<EOF
{"status":"NONE"}
EOF
            cp $patchrpm "$target/$patch/interdiff.patch"
        fi
    else
        echo "ERROR no git repo for $project" 1>&2
        cat > "$target/$patch/review.json" <<EOF
{"status":"NONE"}
EOF
        cp $patchrpm "$target/$patch/interdiff.patch"
    fi
    diffstat -t < "$target/$patch/interdiff.patch" > "$target/$patch/interdiff.diffstat"
}

set -x

temp=$(mktemp -d)
rpm2cpio "$pkg"|(cd $temp; cpio -id)
rm -rf "$target"
mkdir -p "$target"
cp $temp/*.spec "$target"
for patchrpm in $(ls $temp/*.patch); do
    chgid=$(sed -n -e 's/Upstream-Change-Id: //p' $patchrpm|tail -1)
    if [ -z "$chgid" ]; then
        chgid=$(sed -n -e 's/Change-Id: //p' $patchrpm|tail -1)
    fi
    patch=$(basename $patchrpm)
    mkdir -p "$target/$patch"
    cp $patchrpm "$target/$patch/patch"
    if [ -z "$chgid" ]; then
        try_cherry_pick
        continue
    fi
    cd $git || echo "ERROR no git repo for $project" 1>&2
    git review -d $chgid $branch
    ex=$?
    if [ $ex = 0 ]; then
        patchgit=$(git format-patch -1 HEAD)
        interdiff -q --no-revert-omitted -w $patchrpm $git/$patchgit > "$target/$patch/interdiff.patch"
        ret=$?
        cp $git/$patchgit "$target/$patch/review.patch"
        rm -f $git/$patchgit
        got_patchset=1
    else
        ret=1
        got_patchset=0
    fi
    if [ $ret != 0 ]; then
        cp $patchrpm "$target/$patch/interdiff.patch"
    fi
    if [ $got_patchset = 1 -a -r .gitreview ]; then
        eval $(fgrep = .gitreview)
        username=$(git config gitreview.username)
        ssh -p $port $username@$host gerrit query --all-approvals --current-patch-set --format JSON $chgid branch:$branch > "$target/$patch/review.json"
        if [ ! -f "$target/$patch/review.json" -o $(wc -l "$target/$patch/review.json"|cut -f1 -d' ') -le 1 ]; then
            ssh -p $port $username@$host gerrit query --all-approvals --current-patch-set --format JSON $chgid branch:master > "$target/$patch/review.json"
        fi
        diffstat -t < "$target/$patch/interdiff.patch" > "$target/$patch/interdiff.diffstat"
    else
        try_cherry_pick
    fi
done

rm -rf $temp

# extract.sh ends here
