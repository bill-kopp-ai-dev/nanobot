# okf-bundle-core snapshot changes

Source revision and checksums are in `SOURCE.json`. Original MIT license is
`LICENSE.okf-bundle-core`. This snapshot keeps the core's relative imports and
on-disk bundle formats, with two deviations:

- `okf_bundle_core/frontmatter.py`: the lazy `ZettelError` import is package-
  relative so malformed YAML is reported correctly under the vendor namespace.
- `okf_bundle_core/lock.py`: retain `fcntl.flock` on POSIX for compatibility
  with legacy processes; on Windows use `msvcrt.locking` on byte zero of the
  existing lock file. Windows serializes readers as well as writers. Ensure
  descriptors are released on lock-acquisition failure.

When updating: rebuild a snapshot from a reviewed upstream revision, reapply
these two changes, run the core parity tests, then review and update the
vendor hashes and `patched_files` in `SOURCE.json` before building. The Hatch
hook verifies the manifest and refuses to silently accept changed code. Do not
copy runtime bundles into this directory.
