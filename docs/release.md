# Building a Binary Release

This page describes how the official binary release archives are produced. The
process is driven by the `fsbuild` helper scripts in the project root and
currently covers Linux (`FS-UAE_<version>_Linux_x86-64.tar.xz`). macOS, Windows
and SteamOS use their own scripts under `dist/`.

## Overview

The Linux release archive has this structure:

```
FS-UAE/
  Linux/
    x86-64/          fs-uae, fs-uae-device-helper, fs-uae.dat, bundled .so files
  Locale/            translations
  Licenses/
  ai/                AI integration: fs-uae-debugger skill + reference driver
  Plugin.ini
  ReadMe.txt         upstream FS-UAE readme
  ReadMe.md          this fork's readme (features and new options)
  Version.txt
```

The binary is built normally, then `dist/linux/build.py` assembles the package
and `dist/linux/standalone-linux.py` copies the non-system shared libraries next
to the binary and sets an `$ORIGIN` rpath so they are preferred. Finally the
`fsbuild` scripts add `Plugin.ini` / `Version.txt` and pack everything into a
`.tar.xz` archive.

## Requirements

In addition to the build dependencies listed in [Compiling FS-UAE](compiling.md),
the packaging scripts need:

- `patchelf` — used to set the `$ORIGIN` rpath on the binary and the bundled
  libraries. Without it the packaging step aborts.
- `unix2dos` — used to convert `Plugin.ini` and `Version.txt` to CRLF line
  endings.

On Debian/Ubuntu:

    sudo apt-get install patchelf unix2dos

## Setting the version

The version is stored in `BASEVERSION.FS`. To change it, edit that file and run
the version helper, which updates `configure.ac`, `PACKAGE.FS`, `VERSION.FS`,
`debian/changelog` and `fs-uae.spec`:

    printf '3.3.0\n' > BASEVERSION.FS
    ./fsbuild/version

`PACKAGE_VERSION` (and the version reported by `fs-uae --version`) is taken from
`configure.ac`, so you must re-run `./bootstrap` and `./configure` afterwards for
the new version to be compiled in. The three-component `X.Y.Z` scheme is
required; the packaging metadata and the FS-UAE plugin system expect it.

## Producing the release

The whole pipeline can be run in one step:

    ./fsbuild/all

which is equivalent to:

    ./fsbuild/bootstrap
    ./fsbuild/configure
    ./fsbuild/make
    ./fsbuild/bundle
    ./fsbuild/sign
    ./fsbuild/notarize
    ./fsbuild/archive

Or, explicitly:

    ./bootstrap
    ./configure
    make -j"$(nproc)"
    ./fsbuild/bundle
    ./fsbuild/archive

The archive is written to:

    fsbuild/_dist/FS-UAE_<version>_Linux_x86-64.tar.xz

`fsbuild/sign` and `fsbuild/notarize` are no-ops outside macOS.

## Publishing on GitHub

Create a tag (for example `3.3.0`) and attach
`fsbuild/_dist/FS-UAE_<version>_Linux_x86-64.tar.xz` as a release asset. Users
can extract the archive and run `FS-UAE/Linux/x86-64/fs-uae`, or point the
FS-UAE Launcher at the extracted directory (`Plugin.ini` is what identifies it
as an FS-UAE installation).

## Fork notes

This fork bundles the packaging fixes needed on current Linux distributions:

- `dist/linux/standalone-linux.py` no longer aborts when it encounters
  `libgpg-error.so` (pulled in via `libgcrypt`/`libsystemd`). It skips that
  library instead, leaving it to the host system, so the standalone packaging
  completes on modern systems.