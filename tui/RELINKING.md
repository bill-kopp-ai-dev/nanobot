# Native TUI corresponding source and relinking

The nanobot TUI release archive contains the executable, its complete JavaScript/TypeScript
application source, dependency lockfile, build scripts, and third-party notices. It is built with
Bun 1.4.4 and OpenTUI 0.5.11. See `SOURCE_OFFER.md` for the corresponding-source
offer that accompanies the executable. The archive also contains the complete LGPL 2.0 and
LGPL 2.1 license texts.

Corresponding upstream source:

- nanobot TUI: the `tui/` and `packages/client-events/` directories in the GitHub release tag that contains this archive
- Bun 1.4.4 (`38afee6c84fcf48c0edb2466aa4b27d287a59c30`):
  <https://github.com/oven-sh/bun/tree/bun-v1.4.4>
- Bun's patched WebKit (`d6375c72affe0f70222cdcb45012b10f0bf3a9d5`):
  <https://github.com/oven-sh/WebKit/tree/d6375c72affe0f70222cdcb45012b10f0bf3a9d5>
- OpenTUI 0.5.11: <https://www.npmjs.com/package/@opentui/core/v/0.5.11>
  (source: <https://github.com/anomalyco/opentui/tree/6b9863ea7c5fae22bfebb23c242ddcc4c2b0aa0e>)

To rebuild against a modified JavaScriptCore/WebKit, first build Bun 1.4.4 from its complete
source checkout together with the WebKit revision above by following Bun's pinned license and
build instructions. Then unpack
`nanobot-tui-source.tar.gz` from the release archive and run the resulting Bun executable:

```bash
cd nanobot-tui-source/tui
/path/to/modified/bun install --frozen-lockfile
/path/to/modified/bun run build -- <target>
```

Supported targets are `darwin-arm64`, `darwin-x64`, `linux-arm64`, `linux-x64`, and `win32-x64`.
The resulting executable is written to `dist/`.

Questions about source availability can be reported at
<https://github.com/HKUDS/nanobot/issues>.
