# 地球物理科研工作流 · Agent Skill

[English](README.md) · [核心技能说明](SKILL.md) · [合成示例](examples/README.md) · [示例结果](examples/synthetic-output/demo_metrics.json) · [GitHub 发布指南](docs/publishing.md)

这是一套面向**地球物理科研、受控试验与论文证据核查**的开放式 Agent Skill。它把原先分开的科研执行和论文证据组织合并为一个通用工作流，并提供可以运行的离线检查脚本。

> **使用边界：它不是重力反演或地震层析成像求解器，也不能凭借检查通过来证明地球物理结论正确。** Skill 的作用是帮助研究人员组织实验、辨别数据/先验角色、追踪证据与核查科研表达。

## 能做什么

| 工作模式 | 主要内容 |
| --- | --- |
| 科研执行 | 数据来源/授权记录、Moho与模型先验辨别、受控恢复试验与敏感性实验计划 |
| 论文写作 | 主张—结果—图件—参考文献证据链，审稿问题和修改记录 |
| 公开发布 | 隐私和授权核查、静态风险检查、合成示例构建 |
| 项目迁移 | 保留可复用科研方法，隔离旧项目的参数、结论和历史论文状态 |

Skill 按通行 `SKILL.md` 格式组织，脚本使用 Python 3.10+ 标准库，无第三方Python依赖；实际科学计算仍需独立配置模型求解器和数据。

## 安装和运行

把整个 `geophysical-research-workflow` 目录放到所用 Agent 客户端认可的 Skills 目录中，例如部分客户端支持项目内 `.agents/skills/geophysical-research-workflow/`。请按实际客户端文档确认路径，不要只复制 `SKILL.md`。

在本仓库目录中运行下面的命令：

```bash
# 科研项目应存放在源码仓库外，避免未来误提交真实科研数据。
python scripts/workflow.py init ../my-geophysics-study
# 手动填写 project.json、数据来源与试验登记之后再验证。
python scripts/workflow.py validate ../my-geophysics-study
# 刚生成的空白模板会检查失败：这是预期行为。

# 完全合成的数据演示，不包含真实地质区位和观测资料。
python scripts/demo_resolution.py --output ../toy-output
python scripts/build_toy_project.py ../toy-audited-project
python scripts/workflow.py validate ../toy-audited-project
# 预期：STRUCTURE_OK_SCIENCE_UNVERIFIED

python scripts/validate_skill.py .
python scripts/check_release.py .
python -m unittest discover -s tests -v
```

## 适合向AI助手提出的问题

- “使用这个Skill辨别我的重力反演中独立观测、Moho几何约束和密度先验各是什么。”
- “帮我事前登记不同边界宽度、模型参数和正则化方案下的合成恢复试验。”
- “核对论文中的每一项定量结论是否有对应结果文件、实验登记和限制说明。”
- “审查准备发布的科研方法仓库是否包含不允许公开的材料。”

## 结果可信度与安全声明

`validate` 核对登记表字段、输入数据角色、文件路径、时间逻辑及结果文件 SHA-256 哈希。台账里自行填写的 `validated` **不等于科研结论已经得到证明**；必须结合实际正演/反演计算、误差模型、受控恢复、独立数据和领域审查。合成演示不能支持任何真实地质结论。

公开仓库不含羌塘项目的历史数值结果、未发表图件、审稿材料、第三方重力/地震数据、密钥或个人资料。对早期研究项目应先确认最新状态，不能把旧参数作为通用默认值。

## GitHub 发布前

请阅读 [发布清单](docs/publishing.md)。MIT许可证只覆盖具备发布权的原创仓库内容；不代表拥有第三方数据或合作代码的再许可权。技术检查通过也不等于机构和协作者已经批准公开。

源码变更、测试和安全报告方法见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [SECURITY.md](SECURITY.md)。
