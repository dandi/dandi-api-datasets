#!/bin/bash
set -ex

PYTHON=$HOME/miniconda3/bin/python
DANDISETS=/mnt/backup/dandi/dandisets

cd "$(dirname "$0")"/..
git reset --hard HEAD
git clean -dxf
git pull

mkdir -p .cronlib
cd .cronlib
if [ -e dandi-cli ]
then ( cd dandi-cli; git pull )
else git clone https://github.com/dandi/dandi-cli
fi
dandi_version="$(cd dandi-cli; git describe)"

$PYTHON -m virtualenv --clear venv
. venv/bin/activate
pip install ./dandi-cli

cd ..

rmdir dandisets
ln -s "$DANDISETS" dandisets
python tools/populate_dandiset_asset_yamls.py dandisets/[0-9]*

(
    echo '# Dandisets with Conversion Errors'
    (
        for d in [0-9]*
        do
            if [ -e "$d"/CONVERSION.errors ]
            then echo "$d"
            fi
        done
    ) | nl -n ln -w 1 -s '. '

    echo

    echo '# Dandisets with Validation Errors'
    (
        for d in [0-9]*
        do
            if [ -e "$d"/VALIDATION.errors ]
            then echo "$d"
            fi
        done
    ) | nl -n ln -w 1 -s '. '

    echo

    echo '# Dandisets with Assets and No Errors'
    (
        for d in [0-9]*
        do
            if [ ! -e "$d"/CONVERSION.errors ] && [ ! -e "$d"/VALIDATION.errors ] && compgen -G "$d/sub-*" &>/dev/null
            then echo "$d"
            fi
        done
    ) | nl -n ln -w 1 -s '. '

) > SUMMARY.md

# In case the repo was updated while we were working:
git pull --autostash --rebase

git add [0-9]* SUMMARY.md
if ! git diff --quiet --cached
then git commit -F - <<EOT
Ran populate_dandiset_asset_yamls.py

dandi $dandi_version
$(pip freeze | grep -Pi '^(pynwb|hdmf)==')
EOT
     git push
else echo "No changes to commit"
fi

# vim:set et sts=4:
