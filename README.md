# NuLl's Research Benchmark — NRB-10

**10 道可生成变体的科研工作流任务，同一套评分器，支持多种模型与 agent harness。**

NRB-10 面向需要把科学推理转成可检查成果的工作：阅读证据、辨认模型退化、设计实验、修复数值代码、处理不确定度、审查证明、制作图表，以及接续和修订研究成果。它使用经典科学问题和原创合成材料，不依赖个人的具体研究课题、真实未发表数据或私有代码。

当前版本：**0.1.0，公开开发基准**。题目、数值参考、评分逻辑和错误控制可运行；真实模型的难度分布、排序稳定性和题目区分度仍需用固定配置的重复实测校准。仓库中的 oracle 和 self-test 成绩是评测程序自检，**不是任何 AI 模型的成绩**。

[完整 10 题](questions/README.md) · [评分方法](docs/scoring.md) · [运行与 harness](docs/harnesses.md) · [实验设计](docs/methodology.md) · [验证记录](docs/validation.md) · [来源与阅读范围](docs/sources.md)

## 10 道主任务

每题含完整输入、提交字段、可执行自动评分与三项质量审阅量表。题内子问不是额外题目；`--seed` 改变数据、条件或参数，主任务数始终为 10。

| ID | 任务 | 主要区分点 |
|---|---|---|
| [NRB01](questions/NRB01/instruction.md) | 版本冲突下的证据与贡献审计 | 更正数据、独立统计单位、直接证据、因果与推广边界 |
| [NRB02](questions/NRB02/instruction.md) | 热响应中的参数退化与判别实验 | 结构可辨识性、尺度等价族、有效干预、独立脉冲预测 |
| [NRB03](questions/NRB03/instruction.md) | 有限预算下的鲁棒校准设计 | 未知截距、异方差、全部整数约束、全局 minimax 与严格次优 |
| [NRB04](questions/NRB04/instruction.md) | 非均匀网格上的守恒热扩散修复 | 串联热阻、非均匀体积、边界条件、离散能量收支 |
| [NRB05](questions/NRB05/instruction.md) | 自适应积分器的回滚与终止 | 全步/两半步误差、拒步不提交、终点和最小步长、有限失败 |
| [NRB06](questions/NRB06/instruction.md) | 传感器校准、噪声谱与相关不确定度 | 已知绝对测量方差、协方差、ASD/PSD、精确通带积分 |
| [NRB07](questions/NRB07/instruction.md) | 重复测量下的数据泄漏与分组评测 | 机器级划分、验证集选模、macro-F1、整组 bootstrap |
| [NRB08](questions/NRB08/instruction.md) | 仿射收缩的证明、反例与误差证书 | 范数一致性、存在唯一性、残差不等式、真正有效的反例 |
| [NRB09](questions/NRB09/instruction.md) | 从合成振子数据制作可编辑科研图 | 实际 SVG 数据坐标、来源标签、示意、图注与渲染质量 |
| [NRB10](questions/NRB10/instruction.md) | 交接证据审计与保守英文修订 | 原始字节、revision 冲突、实际执行范围、英文保真、可接续交接 |

## 立即自检：不需要模型 API

需要 Python 3.11+。在自己选择的工作目录执行：

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m nrb list
python -m unittest discover -s tests -v
python -m nrb selftest --seeds 0,17,101 --out selftest.json
```

核心只用 Python 标准库，无须安装依赖即可运行。`selftest` 只执行仓库自己提供的可信参考代码，检查每个参考答案是否得到 70/70 自动分、空提交是否得到 0，以及变体是否可复现。输出路径必须是新路径；这防止旧结果被静默覆盖。

也可安装命令行入口：

```bash
python -m pip install -e .
nrb list
```

## 使用方式

### 导出给模型或 agent 的题包

```bash
python -m nrb export --format native --seed 0 --dest exports/native-s0
python -m nrb export --format jsonl --seed 0 --dest exports/nrb-s0.jsonl
```

`native` 题包只有题目、输入和公开质量量表，不包含答案、评分器或参考程序。正式 agent 运行时只把每题题包送入新环境，**不要把本仓库根目录交给被测 agent**。JSONL 适合现有 API 请求管线。

所有 harness 交回同一个结构：

```json
{
  "task_id": "NRB04",
  "answer": {},
  "artifacts": {
    "solution.py": "完整代码内容",
    "reasoning.md": "完整解释内容"
  }
}
```

`answer` 的具体字段在每题中给出；`artifacts` 必须放文件全文。框架外的本机文件路径不能代替交付文件。

### 自动评分

```bash
docker pull python:3.12-slim
python -m nrb grade --task NRB04 --seed 0 \
  --submission received/NRB04.json --execution docker --out reports/NRB04.json

python -m nrb grade-suite --seed 0 --submissions received \
  --execution docker --out reports/suite.json
```

正式对比前固定 Docker 镜像 digest，将其配置到 `NRB_PYTHON_IMAGE`，并记录模型、harness、依赖、工具与预算。NRB04/05 的实际代码测试默认在 Docker 中执行；其余题目不需要执行候选代码。没有 Docker 时可以用 `--execution none` 查看可评部分，但代码题会保留未评项，套题总分不成立。`trusted` 只给仓库自身的参考/错误控制使用，不能用它执行外部候选程序。

### 多 harness

| 接口 | 适用范围 | 接入方式 |
|---|---|---|
| Inspect AI | 统一多模型 API 的固定输入测试，也可接自己的 solver | `adapters/inspect_ai/nrb_eval.py` |
| promptfoo | 多 provider 比较、固定输入测试；另有 CLI provider | `nrb export --format promptfoo` |
| Harbor | 在 agent 容器中做完整文件/工具任务，独立容器评分 | `nrb export --format harbor` |
| 通用 CLI bridge | Codex、Claude Code、Gemini CLI 或任何兼容 stdin/文件交付的命令 | `nrb run --command-json ...` |
| JSONL / 手工提交 | 自建 harness、网页模型或离线输出评分 | 统一 JSON 提交后 `nrb grade` |

适配器全部调用 `nrb.core.grade_submission`，不会各写一套分数。真实模型/API/认证由用户现有的 harness 提供。具体安装、命令、支持与实际验证范围见 [harness 使用文档](docs/harnesses.md)。

## 分数如何读

每题 **70 分自动核验 + 30 分独立质量审阅**，10 题等权。自动分可以直接用于连续监测；质量审阅用于确认成果是否真正可用。

- `auto_points`：0–70 的原始自动分。
- `auto_percent`：自动分除以 70 后得到的 0–100；**不是完整科研质量总分**。
- `review_points`：三项各 0–10。没有审阅时是 `null`，不能填零或默认满分。
- `total`：自动分加质量分，0–100；只有自动核验完整且审阅完成时才存在。
- `critical_failures`：关键科学/交付失误，单列报告；不要被平均分掩盖。
- `coverage`：真正完成评分的自动分权重比例。基础设施失败不是模型答错。

要追加质量评分：

```bash
python -m nrb review-packet --task NRB09 --seed 0 \
  --submission received/NRB09.json --dest reviews/NRB09
# 独立评阅者填写 reviews/NRB09/review.json；图题先看实际渲染。
python -m nrb grade --task NRB09 --seed 0 \
  --submission received/NRB09.json --review reviews/NRB09/review.json \
  --out reports/NRB09-reviewed.json
```

质量分也可以由另一模型辅助填写，`reviewer_type` 必须设为 `llm` 并记录精确 judge ID；合计会标为 **`llm_reviewed_provisional`**，不能冒充独立人工结论。

## 先测什么

第一次运行，先用 NRB04 检查代码执行链、用 NRB09 检查文件交付链。随后跑完整 10 题。正式比较建议同一组数据变体与多个重复，每次新会话；固定模型比较 harness，或固定 harness 比较模型。详细实验矩阵和配对统计见 [方法文档](docs/methodology.md)。

本版不声称覆盖实时文献检索、真实实验操作、完整大型求解器、Lean 编译、长达数日的自主研究或所有视觉审美。NRB01 测固定证据包的审读，NRB08 测证明和反例；这些边界是分数解释的一部分。

## 维护

题目输入、评分标准和容差改变必须版本化。新增失败案例先修复判据并回归，再更新题包；不要为偏好的模型调整答案、权重或阈值。公开变体仍可被学习，随机种子不是防污染保证。实际能力报告须注明提交 commit、配置、失败项和未评项。

代码及本项目原创合成题目沿用仓库的 [MIT License](LICENSE)。外部资料保留各自权利，本仓库只提供来源链接和方法说明。
