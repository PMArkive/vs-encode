# vs-encode

This module is still in BETA! Use with care!

Requires Python 3.10.

## How to install

Install `vs-encode` with the following command:

```sh
pip3 install vs-encode --no-cache-dir -U
```

Or if you want the latest git version, install it with this command:

```sh
pip3 install git+https://github.com/Irrational-Encoding-Wizardry/vs-encode.git --no-cache-dir -U
```

## Disclaimer

Anything **MAY** change at any time.
The public API **SHOULD NOT** be considered stable.
If you use lvsfunc in any of your projects,
consider hardcoding a version requirement.

## TODO

* Proper README
* Comprehensive documentation
* Rewrite the module from the ground up

  * Reimplement `FileInfo` as `Source`
  * Rewrite methods/functions/classes for video/audio/file handling
  * Use `Tracks` to easily build towards an output file
  * Offer a lot of codecs and encoders, fallbacks
  * Make it easily expandable by the user so they can support their own encoders if necessary
  * Lots of useful utility functions, like timecode generation/checking?

* Consider implementing the following functionality:

  * SubKt-like behaviour? Allow merging multiple files? (likely not or at least left super basic, because out-of-scope)
  * Multi-track support, call runner once for every track
  * `keep_attachments` flag per track
  * Allow external files to be used for tracks
  * `track_id` to only grab specific tracks from files
  * Per-track metadata handling, open to the end-user
  * Custom ini files, don't 100% require one if not necessary

* Unit testing?
* Refactor code for readability's sake
* Feature parity (or as close as reasonable) with vardautomation
