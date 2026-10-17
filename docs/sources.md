# 来源、设计依据与阅读范围

核对日期：2026-10-17。以下只列方法设计及接口核对使用的公开一手资料。题目数据、证据卡片、代码缺陷与交接记录均为本项目原创合成材料；没有把真实论文摘要改写成虚构引用，也没有复制第三方 benchmark 的题目。

## 评测设计

| 来源 | 本次实际核对范围 | 对本项目的作用及边界 |
|---|---|---|
| [SciCode 官方仓库](https://github.com/scicode-bench/SciCode) | README 中 scientific coding、主问题/子问题、任务和评测入口的说明 | 参考“科学推理需要转化为可执行结果”的任务观。本项目自建经典问题，不声称复现 SciCode 或使用其成绩。 |
| [CORE-Bench 论文](https://arxiv.org/abs/2409.11363) | 摘要及基准目标 | 支持把复现、文件环境与证据交接作为研究代理能力的一部分；未完整阅读或复现论文实验，不援引其榜单作模型推荐。 |
| [Inspect custom scorers](https://inspect.aisi.org.uk/custom-scorers.html) / [scorer API](https://inspect.aisi.org.uk/reference/inspect_ai.scorer.html) / [dataset API](https://inspect.aisi.org.uk/reference/inspect_ai.dataset.html) | Task、Sample、Score、metadata、未评分状态及 scorer 接口 | 以一个核心评分器接入框架。框架内均值不能替代本项目保留缺题状态的汇总。 |
| [promptfoo Python assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/python/) / [Python providers](https://www.promptfoo.dev/docs/providers/python/) / [CLI](https://www.promptfoo.dev/docs/usage/command-line/) | Python callback 入参/返回值、provider 配置、结果输出、退出码 | 直接复用同一自动评分器，区分低分与运行错误。 |
| [Harbor task configuration](https://docs.harborframework.com/tasks/configuration) / [verifier](https://docs.harborframework.com/tasks/verifier) / [separate verifier](https://docs.harborframework.com/tasks/separate-verifier) / [network policies](https://docs.harborframework.com/tasks/network-policies) | 候选环境、评分环境、artifact 传递、reward、网络策略 | 将候选题包与评分源码分开，代码测试在独立 verifier 运行。配置核对不等于所有容器后端已经实测。 |

## 科学方法

| 来源 | 本次实际核对范围 | 相关任务 |
|---|---|---|
| [NIST paired observations](https://www.itl.nist.gov/div898/handbook/prc/section3/prc311.htm) | 该短页的配对差值、标准差和均值标准误定义 | NRB01 的配对样本统计；技术重复不增加独立实验单位。 |
| [NIST Dataplot T TEST](https://itl.nist.gov/div898/software/dataplot/refman1/auxillar/t_test.htm) | 定义和配对检验段落；没有复现全部软件示例 | NRB01 的独立统计核验。 |
| [NIST TN 1297: combined standard uncertainty](https://www.nist.gov/pml/nist-technical-note-1297/nist-tn-1297-5-combined-standard-uncertainty) | 合成标准不确定度与协方差项 | NRB06 的相关误差传播。题目声明测量方差和插值规则，避免让模型猜统计口径。 |
| [scikit-learn common pitfalls](https://scikit-learn.org/stable/common_pitfalls.html) / [cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html) | 数据泄漏及 grouped cross-validation 的说明 | NRB07 的分组、选模与测试隔离原则。评分器本身不依赖 scikit-learn，也不声称仅按组划分就保证所有外推。 |
| [Bertsekas, Abstract Dynamic Programming, 作者公开附录](https://web.mit.edu/dimitrib/www/Appendixes_REFS_Abstract_DP_2ND_EDITION.pdf) | Appendix B 中印刷页 325–331 的收缩定理、加权上确界范数、仿射映射条件 | NRB08 的范数、固定点及误差界。未读完整教材；本题也不提供有向舍入或形式化证明编译器。 |

NRB02–05、NRB09 使用基础线性模型、有限体积通量平衡、后向欧拉积分和解析阻尼振子。本仓库在题目及方法笔记内完整给出方程、约定和评分容差；数值参考通过独立公式、手算例、精确有理数或高精度递推核对。第三方文献不是答案正确性的替代品。

## 版本与 CLI 文档

可选依赖核对目标为 [inspect-ai 0.3.281](https://pypi.org/project/inspect-ai/0.3.281/)、[promptfoo 0.124.1](https://github.com/promptfoo/promptfoo/releases/tag/0.124.1)、[Harbor 0.24.0](https://pypi.org/project/harbor/0.24.0/)。安装后的真实版本和运行结果必须另存；“按文档实现”“通过接口单测”和“真实框架运行成功”是不同证据等级，具体见 [验证记录](validation.md)。

CLI 模板依据：[Codex noninteractive](https://developers.openai.com/codex/noninteractive/)、[Claude Code headless](https://code.claude.com/docs/en/headless)、[Claude CLI reference](https://code.claude.com/docs/en/cli-reference)、[Gemini CLI headless](https://geminicli.com/docs/cli/headless/)。本仓库不据这些页面推断用户安装的版本、已登录账户或实际模型。

## 可检查的设计决定

70/30 权重、每题等权、900 秒的命令示例预算、建议的复测矩阵和初始决策门槛，都是本项目的工程选择，**不是来源文献已证明的最优设置**。评分器自检能证明有限错误案例会失分；只有后续真实模型实验，才能估计难度、排序稳定性、质量评阅一致性和个人使用价值。
