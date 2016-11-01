# emacs: -*- mode: python; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##
#
#   See COPYING file distributed along with the repronim package for the
#   copyright and license terms.
#
# ## ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ### ##

# Sample output from Reprozip.
REPROZIP_OUTPUT = """
runs:
# Run 0
- architecture: x86_64
  date: 2016-02-22T22:19:01.735754
  argv: [echo, $MATH_EXPRESSION, '|', bc]
  binary: /usr/bin/bc
  distribution: [Ubuntu, '12.04']
  environ: {TERM: xterm, MATH_EXPRESSION: '2+2'}
  exitcode: 0
  gid: 1003
  hostname: nitrcce
  id: run0
  system: [Linux, 3.2.0-98-virtual]
  uid: 1002
  workingdir: /home/rbuccigrossi/simple_workflow
packages:
  - name: "base-files"
    version: "6.5ubuntu6.8"
    size: 429056
    packfiles: true
    files:
      # Total files used: 103.0 bytes
      # Installed package size: 419.00 KB
      - "/etc/debian_version" # 11.0 bytes
      - "/etc/host.conf" # 92.0 bytes
  - name: "bc"
    version: "1.06.95-2ubuntu1"
    size: 1449984
    packfiles: true
    files:
      # Total files used: 936.64 KB
      # Installed package size: 1.38 MB
      - "/bin/bash" # 936.64 KB
"""

# examples/demo_spec1.yml
DEMO_SPEC1 = """
# based on ReproZip format extended to support sufficiently detailed
# description of multiple distributions.
#
# It is used (over e.g. NIDM's) during prototyping since much easier
# to read/parse/change and translate into code structures ATM.  But ultimately
# might be 'translatable' into some NIDM
#
# ATM geared toward list of overlay distributions and packages (thus
#  no per file information)
# ATM composed manually
distributions:
 - name: debian-1
   origin: Debian
   label: Debian
   suite: stable
   version: 8.5
   codename: jessie
   date: Sat, 04 Jun 2016 13:24:54 UTC
   components: main contrib non-free
   architectures: amd64

 - name: debian-2
   origin: Debian
   label: Debian
   suite: testing
   codename: stretch
   date: Sat, 04 Jun 2016 13:24:54 UTC
   components: main contrib non-free
   architectures: amd64

 - name: neurodebian-1
   origin: Debian
   label: Debian
   suite: stable
   version: 8.5
   codename: jessie
   date: Sat, 04 Jun 2016 13:24:54 UTC
   components: main contrib non-free
   architectures: amd64

 - name: conda-1
   TODOMORE: TODO

 - name: pypi-1

packages:
 # should list packages, files used by "runs", and associate with distribution(s)
 # and their components from where they could have been obtained, checksums,
 - name: libc6-dev
   # --- Fields common to all "package"s, although content might be distribution specific
   distributions:
    - name: debian-1
      component: main         # as identified from /var/..._<suite=main>_binary-<arch>.Packages
      pin: 500
   version: 2.19-18+deb8u4   # from apt-cache policy
   # List files used from the package by any "runs"
   files:
    - "TODO"
    # --- Custom per distribution type (so must not mix types among distributions above)
   source: glibc
   upstream-name: "GNU C library"   # from copyright, Upstream-Name where present
                                     # and we might provide some translations for
                                     # some common victims
   rchitecture: amd64       # as identified from /var/..._<arch=amd64>_Packages filename
   # might be worth capturing information on alternative available versions
   # at that point.  Just an idea -- might be just a waste
   distributions-other-versions:
    - name: debian-2
      component: main
      version: 2.19-18  # hypothetical
      pin: 400
   size: 12602202
   SHA256: 0619d49952775fd1d9c1453aa2a065b876ec016e1dbcead09a90e44d1d82c561
   SHA1: 470747b71b367b1bfa472ad294a51f44cfba874b
   MD5sum: 17ba9548d5f3937431dab210b1a97aff

 - name: afni
   distributions:
    - name: neurodebian-1
   version: 16.2.07~dfsg.1-2~nd90+1
   # --- Custom
   source: afni
   upstream-name: afni
   TODOMORE: TODO
   component: contrib
   architecture: amd64

 - name: python-nibabel
   distributions:
    - name: debian-1
    - name: neurodebian-1  # unlikely to happen since we have custom version suffix
   version: 2.1.0-1
   source: nibabel
   upstream-name: nibabel
   architecture:   # empty for being 'all'
   # ...

 # if pkg version is no longer available from any apt source, we could list
 # where other versions are available from
 - name: python-numpy
   version: 1.11.0-1maybeevencustombuild
   # we still need somehow to note that it is of "debian" type, but not assign
   # as specific distribution listed among distributions
   distributions: debian
   source: python-numpy
   upstream-name: NumPy
   # ...
   distribution-other-versions:
    - name: debian-1
      component: main
      pin: 900
      version: 1:1.11.1~rc1-1   # hypothetical

# Some script used numpy from conda env
 - name: numpy
   distributions:
    - name: conda-1
   version: "1.11.0"
  # --- Custom
   python-env: py27_0
   build: "nomkl"
   size: 1
   SHA256: someTODO
   # ...

 - name: piponlypkg
   distributions: pypi-1
   version: TODO
   # --- Custom
   # ...

 - name: smthfromgit
   # we need to signal type somehow. We could either just reserve some
   # keywords or rely also on the fact that distributions listed within
   # distributions section should be of "name-#" format. And if there is
   # not "-" -- then handled internally
   distributions: git
   # although checksum is not a version -- it is a best descriptor...
   # but we could may be use output git describe to get something
   # semantic while also uniquely identifying the state
   # see: https://github.com/datalad/datalad/issues/763#issuecomment-248491791
   version: checksum
   # files:  -- could or could not be useful...
   # --- Custom
   path: /full/path/to/the/installation
   branch: master
   # name of the remote this branch tracks (from git-config)
   remote: origin
   remotes:
    - name: origin
      url: TODO
      # we might benefit from knowing either given commit is available from
      # remotes at the time of execution.  Could issue a warning/reminder etc
      has_version: True
    - name: someother
      url: TODO
      has_version: False
   describe: "output of git describe --tags"
   changes: False
   clean: False # so no changes but spurious files

 - name: smthfromannex
   distribution: git-annex
   ALLOFGIT: True
   # should inherit all of git, but also files becomes important so we would
   # know what to fetch
   files:
    - subdir/file1
   remotes:
   # will need additional fields for annexspecific info which could come very
   # handy
    - name: origin
      annex-uuid: u-u-i-d

 # tricky, in a sense that it could be a pure git or git-annex
 - name: dataladdataset
   distribution: datalad
   ALLOFGIT: True
   MAYBEALLOFGITANNEX: True
   # --- Custom
   dataset_id: "the one from .datalad/config"
"""