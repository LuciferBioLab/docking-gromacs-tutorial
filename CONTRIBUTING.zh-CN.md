# 贡献指南

[English](CONTRIBUTING.md) · **简体中文**

先查看[现有 Issues](https://github.com/LuciferBioLab/docking-gromacs-tutorial/issues)，并按工作流、平台或工具选择模板。提交可复现报告时，请提供阶段（01–12）、软件版本、平台类型、用占位符脱敏后的命令、预期结果，以及首条报错和前后两三行。使用公开示例数据，移除私人路径、主机名和分子标识。

在 `docs/source/` 中同时修改相应文档的中英文字段。两种语言中相同的命令写入共用块。工具、作者和参考文献沿用英文名称。中文版图件和文档文件名加 `.zh-CN`。生成文档并检查结构后再提交 PR。

```bash
make docs
make check-docs fixtures
python -m unittest discover -s tests -v
```

修改科研命令时，请记录工具版本及是否通过公开示例实际运行，并将来源补入[参考文献](docs/REFERENCES.zh-CN.md)。贡献适用 [LICENSE](LICENSE) 中相应的许可。
