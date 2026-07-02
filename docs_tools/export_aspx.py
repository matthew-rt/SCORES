#!/usr/bin/env python3
"""Convert a built MkDocs site into a SharePoint-friendly .aspx copy.

SharePoint document libraries typically force .html files to download
instead of rendering them, but serve .aspx files inline in the browser.
This script copies the built site (default: site/) to a new folder
(default: site_aspx/), renames every .html file to .aspx, and rewrites
internal links inside HTML, CSS and JS files so they point at the
renamed files.

Usage:
    mkdocs build
    python docs_tools/export_aspx.py [--site site] [--out site_aspx]

Then upload the contents of the output folder to a SharePoint document
library, preserving folder structure, and share the link to index.aspx.

Note: the MkDocs client-side search will not work in the renamed copy
(its index references the original .html filenames); navigation links are
fully rewritten and work normally.
"""

import argparse
import re
import shutil
import sys
from pathlib import Path

# Rewrite ".html" references when they appear in link-like contexts:
#   href="page.html"  href='page.html#anchor'  url(page.html)
#   and bare references inside JS strings ("page.html").
# We deliberately only touch occurrences followed by a quote, '#', '?' or ')'
# so that unrelated text mentioning ".html" in prose is left alone.
HTML_REF = re.compile(r'\.html(?=["\'#?)])')

TEXT_SUFFIXES = {".html", ".css", ".js", ".xml"}


def export(site_dir: Path, out_dir: Path) -> int:
    if not (site_dir / "index.html").exists():
        print(
            f"error: {site_dir}/index.html not found - run 'mkdocs build' first",
            file=sys.stderr,
        )
        return 1

    if out_dir.exists():
        shutil.rmtree(out_dir)

    n_renamed = 0
    n_rewritten = 0
    for src in site_dir.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(site_dir)
        dest = out_dir / rel
        if src.suffix == ".html":
            dest = dest.with_suffix(".aspx")
            n_renamed += 1
        dest.parent.mkdir(parents=True, exist_ok=True)

        if src.suffix in TEXT_SUFFIXES:
            text = src.read_text(encoding="utf-8", errors="replace")
            new_text, n = HTML_REF.subn(".aspx", text)
            if n:
                n_rewritten += 1
            dest.write_text(new_text, encoding="utf-8")
        else:
            shutil.copy2(src, dest)

    print(f"exported {site_dir} -> {out_dir}")
    print(f"  {n_renamed} pages renamed .html -> .aspx")
    print(f"  {n_rewritten} files had internal links rewritten")
    print(f"upload the contents of {out_dir}/ and link to index.aspx")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--site", default="site", help="built site folder (default: site)")
    parser.add_argument("--out", default="site_aspx", help="output folder (default: site_aspx)")
    args = parser.parse_args()
    return export(Path(args.site), Path(args.out))


if __name__ == "__main__":
    sys.exit(main())
