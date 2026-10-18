# 源码导读：中文注释与研究流程

本文帮助第一次阅读本仓库的用户理解**每个 Python 文件为何存在、应该怎样调用，以及它明确不能证明什么**。更详细的技术说明直接写在源码的中文模块文档、函数文档和关键逻辑注释中。

## 1. 运行环境与代码设计

- Python 3.10+；核心脚本只使用标准库。
- `scripts/` 放置实际可执行工具；`tests/` 使用 `unittest` 自动检查正确与错误的输入情形。
- **真实研究项目应在仓库之外**。所有脚本都应当明确区分源码根目录和研究数据目录。
- 结构检查成功不代表真实物理计算已经运行，更不代表地质模型被独立识别。

## 2. 脚本与入口

| 文件 | 主要入口 | 要解决的问题 |
| --- | --- | --- |
| `scripts/workflow.py` | `init`、`validate`、`hash` | 创建台账、检查跨表证据链、生成文件哈希 |
| `scripts/demo_resolution.py` | `--output` | 生成可重复的一维合成演示，检验文件输出过程 |
| `scripts/build_toy_project.py` | 目标目录参数 | 构建已登记试验、合成结果和 SHA-256 记录的完整示例 |
| `scripts/validate_skill.py` | 仓库根目录参数 | 检查 `SKILL.md` 的基础 frontmatter 结构 |
| `scripts/check_release.py` | 仓库根目录参数 | 静态扫描不适合公开的文件格式、目录及疑似敏感内容 |
| `tests/test_workflow.py` | `unittest discover` | 验证正确路径、错误路径、重复性与发布检查规则 |

## 3. `workflow.py` 的关键逻辑

1. **项目基本信息：** 读取 `project.json`；确认研究问题、坐标/深度约定、单位等字段存在。
2. **资料角色：** 依据 `observation`、`geometry`、`prior`、`external_model`、`posthoc_diagnostic` 和 `context` 区分数据用途。
3. **实验登记：** 读取 `experiment_registry.csv`，将实验与输入数据连接；防止在 `gravity_only` 记录中混入先验或后验诊断数据。
4. **时间审计：** 检查登记与执行时间的先后关系；但普通 CSV 时间戳可以修改，**不等于独立的事前注册证明**。
5. **论文证据：** `evidence_ledger.csv` 中标为 `validated` 的记录，必须能关联实验、结果文件、定位字段、不确定性和局限。
6. **图件和引文：** 检查最终图件的源文件、绘图代码、单位及显示变换；区分文献基本信息核验与直接论断支持。
7. **文件哈希：** 检查相对路径、文件存在性与 SHA-256 是否一致。哈希可发现文件变动，**不能证明内容正确**。

### 核查结果如何理解？

```text
VALIDATION: STRUCTURE_OK_SCIENCE_UNVERIFIED (errors=0, warnings=...)
```

它只意味着预设结构规则没有发现错误。进行科学判断仍需要正演/反演方法、合理的误差与先验设置、合成恢复及独立证据等。

## 4. 查看一个完整的合成示例

在仓库根目录运行：

```bash
python scripts/build_toy_project.py ../toy-audited-project
python scripts/workflow.py validate ../toy-audited-project
```

随后可打开 `../toy-audited-project/` 下的 `project.json`、`experiment_registry.csv`、`evidence_ledger.csv`、`file_manifest.csv`、`results/demo_metrics.json`，检查各条记录如何关联。

示例只用于展示科研材料组织与校验机制，**不是某一真实地区的重力或地震模型，也不用于证明物理结构分辨率**。

## 5. 二次开发时应注意什么？

- 增加台账字段时，同时更新 `assets/` 模板、`workflow.py` 的字段规则、`references/` 和测试。
- 修改“已核验”条件时，应补充失败用例，防止弱化证据要求。
- 修改研究模型的假设、数据角色或正则化规则时，先明确是通用方法还是具体项目条件；不要把旧项目经验写成默认的科学结论。
- 更改发布检查器时，不要把扫描通过描述为版权、隐私或安全认证。
- 修改源码后运行：

```bash
python -m compileall -q scripts tests
python scripts/validate_skill.py .
python scripts/check_release.py .
python -m unittest discover -s tests -v
```
