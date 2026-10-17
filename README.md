# NuLl's Research Benchmark · V1.0

**10 道有难度梯度的科学编程题 + 6 道科研工作流题 + 3 道可选扩展题。每题一个离线文件，统一评分并单独判断核心责任是否完成。**

[![NRB validation](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml/badge.svg)](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml)

面向把研究想法变成可检查成果的日常工作：Python 数据与数值计算、TMM 仿真、Fortran 漂移扩散、复杂 bug 修复、科研绘图、保守英文修订、图文写作、论文精读与部分方法复现、综述综合。全部例子来自经典公开问题、公开许可文献和原创合成数据；不使用个人正在推进的研究、未发表数据或私有代码。

当前是 **V1.0.0 公开开发基准**。难度 1–5 是设计先验；参考实现和错误候选用于检验评分，不能代替真实模型的难度校准。仓库不把 oracle、mock 或人工规则测试登记为 AI 成绩。

**直接下载题目： [tasks/v1.0/](tasks/v1.0/README.md)**。候选每次只拿其中一个 `.md` 或 `.html` 文件。HTML 已嵌入所需图像、数据和论文文本；下载后打开即可，不需要让被测 AI 克隆或搜索这个仓库。

[完整设计报告](docs/v1/design-report.md) · [运行及 harness 指南](docs/v1/usage.md) · [评分规则](docs/v1/scoring.md) · [科研题详细人工量表](docs/v1/research-guide.md) · [防答案访问](docs/v1/closed-evaluation.md) · [验证记录](docs/v1/validation.md)

## 十道代码题

每题 **70 自动分 + 30 人工质量分**；自动分分为基础 20、科学正确性 30、压力与边界 20。题目不仅要求代码，还要求科学说明和独立测试。Fortran 必须实际编译，候选 Python 必须实际执行。

| 题目 | 语言 | 设计难度 | 主要区分点 | 建议作答预算 |
|---|---|---:|---|---:|
| [C01](tasks/v1.0/C01.md) 仪器 CSV 清洗与测量不确定度 | Python | 1/5 | 单位、重复身份、缺失记录、绝对不确定度 | 15 min |
| [C02](tasks/v1.0/C02.md) 独立组与分层 bootstrap | Python | 2/5 | 统计单位、组与行权重、确定性随机重采样 | 15 min |
| [C03](tasks/v1.0/C03.md) 分层导热求解器修复 | Python | 3/5 | 非均匀有限体积、界面热阻、隐式稳定性、守恒 | 15 min |
| [C04](tasks/v1.0/C04.md) 稳定多层薄膜光学仿真 | Python | 4/5 | s/p 偏振、斜入射、复数分支、吸收与厚层稳定性 | 30 min |
| [C05](tasks/v1.0/C05.md) 刚性反应自适应积分 | Python | 5/5 | 源项事件、拒步回滚、误差控制、浮点终点 | 30 min |
| [C06](tasks/v1.0/C06.md) Fortran 守恒漂移扩散 | Fortran 2008 | 3/5 | SG 通量、正反漂移、非均匀网格、大 Peclet 数 | 30 min |
| [C07](tasks/v1.0/C07.md) 逆热扩散与参数可辨识性 | Python | 4/5 | 多实验基线/幅度、剖面区间、秩退化、绝对 sigma | 40 min |
| [C08](tasks/v1.0/C08.md) 二维异质各向异性椭圆方程 | Python | 4/5 | 面系数、方向性、边界积分通量、制造解 | 40 min |
| [C09](tasks/v1.0/C09.md) Fortran 自洽漂移扩散–Poisson | Fortran 2008 | 5/5 | 耦合非线性、正密度、阻尼 Newton、规范不变性 | 60 min |
| [C10](tasks/v1.0/C10.md) 反应扩散反演流水线修复 | Python | 5/5 | 守恒、离散灵敏度、协方差、JSON 重启、重拟合自举 | 75 min |

预算是正式比较前可统一调整的建议，不是已经验证的模型耗时。模型之间必须固定预算、工具与环境。题号按能力组合排列，不承诺难度严格递增。

## 科研与可选扩展题

每题 100 分人工评阅，五个维度按 0–4 级加权。必须给证据和理由；看图、交互、视频、音频有明确的实际观察要求。

| 题目 | 核心工作 | 必须检查的成果 |
|---|---|---|
| [R01](tasks/v1.0/R01.html) 参考论文图学习与 SVG | 分析三张真实参考图，再组织三面板科学表达 | 可编辑 SVG、实际 PNG、设计依据、源项目 |
| [R02](tasks/v1.0/R02.html) Python 科研绘图 | 小差异、宽动态范围、负数/零/删失值各自选择尺度 | 代码、主图、替代尺度诊断、数值摘要 |
| [R03](tasks/v1.0/R03.html) 保守英文润色 | 去套话、减夸张、保持事实和证据边界 | 修订正文、逐项事实账本、修改说明 |
| [R04](tasks/v1.0/R04.html) 从图和草稿写论文 | 根据嵌入的两面板图、原始数据和作者粗略想法写结果/讨论 | 英文正文、图注、计算、主张证据表 |
| [R05](tasks/v1.0/R05.html) 精读与部分方法复现 | 三篇论文的关键词、方法、明线暗线、落地方案及两项有界复现 | 来源卡、逻辑图表、可运行代码、真实结果图 |
| [R06](tasks/v1.0/R06.html) 迷你综述 | 跨论文综合，完成正文、图、表和引文 | 综述、证据 SVG、比较表、BibTeX、证据账本 |
| [X01](tasks/v1.0/X01.html) 可选 HTML | 离线科学仪表板及真实交互 | 单 HTML、交互核对记录 |
| [X02](tasks/v1.0/X02.html) 可选视频 | 45–60 秒科学解释、字幕、场景证据和来源 | 实际 MP4、SRT、可编辑源项目 |
| [X03](tasks/v1.0/X03.html) 可选音乐/音频 | 32 秒原创器乐，服务旁白和时间结构 | 实际 WAV、可编辑源文件、技术与听评记录 |

三篇离线文献是 Weissgerber et al. (2015)、Rougier et al. (2014)、Crameri et al. (2020) 的公开图形与科学传播研究。全文供给范围、17 张原始图像的来源和准确许可见 [sources/v1/README.md](sources/v1/README.md)。这些材料检验真实阅读和方法落地，不能据此声称覆盖了所有专业领域。

## 最短使用流程

### 1. 给候选单题文件

从 [tasks/v1.0/](tasks/v1.0/) 下载一题，放入新的无答案环境，使用新会话。不要同时提供仓库、量表实现、参考程序或旧对话。图文题应确认候选确实收到图像；HTML 源码中的 base64 字符串不等于已提供视觉输入。

### 2. 在评分端安装并执行

以下命令在评测者环境中运行，不在候选环境中运行：

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m pip install -e .
docker build -t nrb-v1:local -f environments/v1/Dockerfile .

python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --execution docker \
  --out results/C04-auto.json
```

Python 编程题统一 `solve(problem)` 接口；Fortran 使用题内规定的数值行输入输出。提交格式是 `{"task_id":"C04","artifacts":{"solution.py":"完整文本","report.md":"完整文本","tests.py":"完整文本"},"answer":{}}`。每道题的具体合同优先。

已有真实文件可由评测者打包，二进制内容自动使用 base64：

```bash
python -m nrb_v1 pack --task R01 --from-dir received/R01 \
  --out received/R01.json
```

### 3. 人工评阅后合并

```bash
python -m nrb_v1 review-packet --task R01 --submission received/R01.json \
  --dest reviews/R01
```

评阅人打开该目录中的题目和真实成果，填写 `review.json` 的身份、各维度等级、证据、理由、核心责任和实际观察记录，然后：

```bash
python -m nrb_v1 grade --task R01 --submission received/R01.json \
  --review reviews/R01/review.json --out results/R01-final.json
```

**自动 70/70 仍不是最终完成。** 汇总同时保留总分、核心完成状态、关键失败、待评项和评分器 commit/内容指纹。`complete` 表示核心责任均通过；`quality_qualified` 还要求完整总分达到 80。人工评阅与 LLM 辅助评阅分别记录，不能混在同一比较队列。

## Harness 支持

- **单文件 / 任意文件型 harness**：十九题均可，成果统一 `pack → grade → review-packet`。
- **原生命令适配器**：十九题均可；传命令 argv，保存原始输出和正式报告。宿主进程不是隔离边界，正式闭卷须使用独立环境。
- **Inspect AI**：十道代码题，默认 response-only；公开导出不含 target 答案，统一自动评分及完整结果日志。
- **promptfoo**：十道代码题，Python assertion 调用同一评分器；默认空 mock，不发生模型调用。
- **Harbor**：十道代码题，candidate 与 verifier 分别构建容器，默认候选断网，参考程序仅在评分端；不默认导出 oracle。

```bash
python -m nrb_v1 export --format jsonl --tasks coding --dest exports/jsonl
python -m nrb_v1 export --format promptfoo --tasks coding --dest exports/promptfoo
python -m nrb_v1 export --format harbor --tasks coding --dest exports/harbor
```

详细配置、可执行示例、版本和自动分的解释见 [运行指南](docs/v1/usage.md)。文本适配器不声称支持自动评判视频或音乐；这类成果进入人工模态评阅流程。

## 版本与验证

新 CLI 是 `nrb-v1` / `python -m nrb_v1`。旧 `nrb` 与 [questions/](questions/) 保留为 V0.2 历史协议，旧分数与 V1.0 不混比。

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution trusted --out validation-run.json
```

`trusted` 只用于仓库受控参考/错误候选自检；未知代码使用 Docker。正式比较应固定 commit、评分器内容指纹、题包 hash、模型版本、harness/skills/工具、预算、环境镜像、种子和人工评阅身份。当前执行证据和限制见 [V1 验证记录](docs/v1/validation.md)。

仓库代码和原创合成题目遵循 MIT；所附第三方文献/图像保留各自许可，不能用仓库 MIT 覆盖。请引用精确 commit，而不只写“用了 NRB”。
