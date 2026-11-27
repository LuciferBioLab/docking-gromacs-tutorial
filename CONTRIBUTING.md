# Contributing

**English** · [简体中文](CONTRIBUTING.zh-CN.md)

Start with [existing issues](https://github.com/LuciferBioLab/docking-gromacs-tutorial/issues) and choose the workflow, platform, or tool report template. For a reproducible report, include the stage (01–12), software versions, platform family, exact command with placeholders, expected result, and the first error with two or three surrounding lines. Use public example data and remove private paths, hostnames, and molecular identifiers.

Edit both language fields in the corresponding file under `docs/source/`. Put identical commands in a shared block. Use English names for tools, authors, and references, and append `.zh-CN` to localized image and document filenames. Regenerate the documents and check their structure before opening a pull request.

```bash
make docs
make check-docs fixtures
python -m unittest discover -s tests -v
```

For changes to scientific commands, record the tool version and whether you exercised the command on a public fixture. Add the source to [References](docs/REFERENCES.md). Contributions use the applicable terms in [LICENSE](LICENSE).
