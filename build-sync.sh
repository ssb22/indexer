#!/bin/bash
# sync OHI to SVN
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi.py
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi_online.py
wget -N http://people.ds.cam.ac.uk/ssb22/gradint/ohi_latex.py
svn commit -m "Update OHI"
