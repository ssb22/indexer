#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi.py
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi_online.py
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi_latex.py
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/c2h.py
git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g')" && git push
