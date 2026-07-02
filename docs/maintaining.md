# Maintaining these docs

The documentation is plain **Markdown** in the `docs/` folder, built into
a static website with [MkDocs](https://www.mkdocs.org/) and the
[Material theme](https://squidfunk.github.io/mkdocs-material/). No content
lives anywhere else — to change the docs, edit the `.md` files.

## Layout

```text
mkdocs.yml                  # site configuration + navigation menu
docs/
  index.md                  # home page
  getting-started/          # installation, data, quickstart
  user-guide/               # one page per module/topic
  tutorials/                # numbered hands-on course
  reference/                # file guide, troubleshooting
  maintaining.md            # this page
docs_tools/
  requirements-docs.txt     # pinned build dependencies
  export_aspx.py            # SharePoint (.aspx) export script
```

## Editing

1. Edit or add Markdown files under `docs/`.
2. If you add a page, add it to the `nav:` section of `mkdocs.yml` so it
   appears in the menu.
3. Preview live while editing:

```bash
pip install -r docs_tools/requirements-docs.txt
mkdocs serve        # http://127.0.0.1:8000, auto-reloads on save
```

Useful syntax beyond standard Markdown (all configured in `mkdocs.yml`):

- Call-out boxes: `!!! note`, `!!! tip`, `!!! warning`, `!!! danger`
  followed by an indented paragraph.
- Fenced code blocks with language names get syntax highlighting.
- ` ```mermaid ` blocks render as diagrams.

## Building the static site

```bash
mkdocs build        # writes the website to site/
```

`site/` is self-contained static HTML/CSS/JS — host it anywhere (a shared
drive, internal web server, GitHub Pages, etc.).
`use_directory_urls: false` in `mkdocs.yml` means every page is a plain
`.html` file and links work when served straight from a filesystem.

The `site/` folder is a build artefact: don't edit it, and don't commit it
(`site/` and `site_aspx/` are in `.gitignore`).

## Publishing to GitHub Pages

The docs are published at
**<https://desnz-sice.github.io/SCORES/>** via GitHub Pages. The workflow
`.github/workflows/docs.yml` rebuilds and redeploys automatically whenever
`docs/` or `mkdocs.yml` change on `master` — so for routine edits,
merging to `master` *is* publishing (allow a minute or two).

Details:

- The workflow runs `mkdocs gh-deploy`, which pushes the built site to
  the `gh-pages` branch; GitHub Pages serves that branch. Never edit
  `gh-pages` by hand.
- One-off manual deploys also work from a local checkout:
  `mkdocs gh-deploy` (requires push access).
- The repository is public, so the published docs are public too — don't
  put anything sensitive in `docs/`.
- If Pages ever stops serving, check **Settings → Pages** on GitHub: the
  source should be "Deploy from a branch", branch `gh-pages`, folder `/`.

## Publishing to the intranet (.aspx export)

SharePoint document libraries force `.html` files to download rather than
display, but serve `.aspx` files inline. `docs_tools/export_aspx.py`
converts a built site into an uploadable copy: it renames every `.html`
file to `.aspx` and rewrites all internal links to match.

```bash
mkdocs build
python docs_tools/export_aspx.py            # site/ -> site_aspx/
python docs_tools/export_aspx.py --out MyFolder   # custom output folder
```

Upload the contents of `site_aspx/` to a SharePoint document library,
preserving the folder structure, and link people to `index.aspx`.

Limitations of the `.aspx` copy:

- The client-side **search box does not work** (the search index refers to
  the original filenames). Navigation and links are unaffected.
- If your SharePoint blocks even `.aspx` uploads by policy, host the
  normal `site/` build on any internal web server instead.

## Conventions for content

- **Scope:** document only files tracked in git — untracked scratch
  scripts in the working tree are deliberately excluded (see the
  [file guide](reference/file-guide.md)).
- **Known issues** are flagged inline with a `!!! warning` / `!!! danger`
  box at the point a user would trip over the problem. When an issue is
  fixed, search `docs/` for the warning and remove it.
- **Units** follow the conventions table in
  [Model architecture](user-guide/architecture.md); if the code's
  conventions change, update that table first.
- Keep code examples runnable from the repository root, and prefer keyword
  arguments in examples so they stay valid if signatures grow.
