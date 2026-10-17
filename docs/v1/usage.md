# V1.0 使用与多 harness 接入

## 1. 选题与轨道

候选题目录是 [tasks/v1.0](../../tasks/v1.0/README.md)。`C01.md` 至 `C10.md` 是科学代码题；`R01.html` 至 `R06.html` 是科研题；`X01.html` 至 `X03.html` 是可选扩展。每题只需下载对应单文件。

先声明本轮评的是哪一种条件：

- **response-only**：模型读题并一次生成源代码和报告，不给执行工具；评分端仍会执行提交。
- **agent-coding**：候选有固定终端、Python/Fortran 和文件工具，可运行修复；每题使用新环境。
- **research-multimodal**：候选能读取文件及真实图像，允许预定的本地科研工具；成果由人工评阅。
- **optional-media**：预先声明启用 HTML、视频或音频中的哪些任务。未启用不进入该轨道；启用后缺最终成果不能当作未测试。

V1 默认本地离线工具合同。若另测云端媒体生成服务、联网论文搜索或不同 skill 组合，必须另命名轨道并记录额外工具与成本，不与默认闭卷条件混比。当前文献题测给定论文的阅读/综合，不能代替开放检索能力测试。

## 2. 评分端准备

核心评分器支持 Python 3.11+；使用本版固定的 Harbor 0.24.0 时需 Python 3.12+。promptfoo 0.124.1 另需 Node.js 22.22.0+（本版 CI 使用 Node.js 24）。以下操作只在评测者环境进行：

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m pip install -e .
python -m nrb_v1 list --tasks all
python -m nrb_v1 identity

docker build -t nrb-v1:local -f environments/v1/Dockerfile .
```

镜像包含 Python、GNU Fortran、NumPy、SciPy、Matplotlib、Pillow、CairoSVG、FFmpeg 与字体。代码题的参考解只需标准库和编译器，但候选可使用题面允许且已安装的库。镜像构建完成后记录实际 ID；正式重复比较尽量固定镜像 digest 和 CPU/内存。

没有 Docker 时仍可导题、打包和做人工研究评阅。未知候选代码的自动执行应使用 Docker；`selftest --execution trusted` 只针对仓库可信参考与错误候选，不能用于任意 AI 代码。

CLI 输出路径默认要求不存在，防止用新运行覆盖旧证据。版本和参数不同的运行应各有目录。

## 3. 下载与生成题包

固定公开版本可直接下载 `tasks/v1.0` 中的一题。需要新的科学参数变体时，在评测者端生成：

```bash
python -m nrb_v1 export --format files --tasks coding --seed 2026 \
  --dest exports/coding-s2026
python -m nrb_v1 export --format files --tasks all --seed 17 \
  --dest exports/all-s17
```

`--tasks` 接受 `coding`、`research`、`optional`、`required`、`all` 或 `C04,C06` 这样的列表。`required` 是十代码加六科研。R/X 当前题面固定，不因种子标签变化得到新科学样本；正式研究题使用公开 seed17，重复作答独立记录运行次数。

候选只接收单个任务文件。目录中的 catalog 供评测者管理，完整仓库和框架配置不属于候选上下文。HTML 的完整文件应离线打开；纯文字模型不能通过读取 base64 字符串被认定为看过图像。

## 4. 提交和统一自动评分

Python：

```json
{
  "task_id": "C04",
  "artifacts": {
    "solution.py": "完整 Python 源代码",
    "report.md": "完整科学说明及实际运行记录",
    "tests.py": "完整独立测试代码"
  },
  "answer": {}
}
```

Fortran 将 `solution.py` 替为 `main.f90`。JSON 示例仅定义容器；科学函数、输入、输出、误差和异常规则都在各题。不要把代码仓库链接、一个路径或伪代码当成实际源码。

科研、图像和媒体题可先直接收集真实文件，再打包；UTF-8 文件原样嵌入，二进制文件用 `{encoding:"base64",data:"..."}`：

```bash
python -m nrb_v1 pack --task R01 --from-dir received/R01 \
  --out received/R01.json
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --execution docker \
  --out results/C04-auto.json
```

全部十代码题接收目录中的 `C01.json`…`C10.json`：

```bash
python -m nrb_v1 grade-suite --tasks coding --seed 17 \
  --submissions received --execution docker --out results/coding-auto.json
```

缺提交的题会保留失败行，不从分母删除。自动70/70的报告仍是 `total=null`、`pending_review`；这是尚未作质量/核心审阅的真实状态。

## 5. 人工评阅与合并

```bash
python -m nrb_v1 review-packet --task C04 --seed 17 \
  --submission received/C04.json --execution docker --dest reviews/C04
python -m nrb_v1 review-packet --task R01 --seed 17 \
  --submission received/R01.json --dest reviews/R01
```

每份评阅包有真实任务、`artifacts/`、原始自动结果、原提交和 `review.json`。评阅者按 [评分规则](scoring.md) 和 [科研详细量表](research-guide.md) 填写身份、0–4 等级、证据、科学理由、核心责任及模态观察。量表模板中不预填正确判断。

对代码题，评阅人除了看源码和科学说明，还应在候选隔离环境运行提交的 `tests.py`，检查其独立性。测试脚本可与 `solution.py` 一起放在一个只包含该提交的目录中：

```bash
# SUBMISSION_DIR 只含这一份候选提交，不能指向仓库或 Home。
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --pids-limit 64 --memory 1g --cpus 2 \
  --user 65534:65534 --mount type=bind,src="$SUBMISSION_DIR",dst=/task,readonly \
  --tmpfs /tmp:rw,exec,nosuid,size=268435456 --workdir /task \
  nrb-v1:local python -B tests.py
```

Fortran 提交测试可能要求在临时可写目录编译；其报告应给准确运行方式。不要把主机 Docker socket 传给候选脚本。

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --review reviews/C04/review.json \
  --out results/C04-final.json
python -m nrb_v1 grade-suite --tasks coding --seed 17 \
  --submissions received --reviews reviews --execution docker \
  --out results/coding-final.json
```

题包、评分器、提交或评阅成果字节变化会导致绑定不匹配；应在同一个固定评分器环境重新生成和评阅。`review.json` 的 `sha256`、权重、责任文本由工具生成，评阅者不要修改。

## 6. Inspect AI

验证目标版本为 **inspect-ai 0.3.281**：

```bash
python -m pip install 'inspect-ai==0.3.281'
inspect eval adapters/v1/inspect_eval.py@null_research_v1 \
  --model PROVIDER/MODEL_ID -T seed=17 -T selection=coding \
  -T execution=docker --log-format json --log-dir logs/inspect-v1
```

`PROVIDER/MODEL_ID` 按所用服务实际填写；凭据通过该框架的正常凭据管理设置，不写入题面或提交。默认 solver 是 `generate()`，因此是 response-only 轨道；模型不会在生成阶段得到终端。想评 agent 的迭代编程，应使用固定工具 solver 或 Harbor，另记配置。

十个 Sample 的 `target` 为空；模型输入只有候选题，评分器在模型调用之后执行。原始报告在 `score.metadata.nrb_v1_report`。无执行环境时使用原生未评分状态；不能把 NaN 或缺项算成真实0分。用程序提取一个日志的标准报告：

```python
from nrb_v1.adapters import summarize_inspect_log
result = summarize_inspect_log("logs/inspect-v1/实际日志.json", selection="coding")
# result['reports'] 是完整标准报告，result['summary'] 保留缺题与未评项。
```

本版真实 mock 验证使用 JSON 日志；不把未在本环境完成读取的 `.eval` 懒加载 ZIP 路径列为已验证。固定 epoch 分别汇总重复尝试，不把同一题多次输出并入一次首次成功率。

## 7. promptfoo

验证目标版本为 **promptfoo 0.124.1**，先安装 **Node.js 22.22.0+**：

```bash
npm install -g promptfoo@0.124.1
python -m nrb_v1 export --format promptfoo --tasks coding --seed 17 \
  --dest exports/promptfoo-v1
promptfoo eval -c exports/promptfoo-v1/promptfooconfig.yaml \
  --no-cache --no-share --output results/promptfoo-v1.json
```

默认 provider 是空 mock，预期十题均失败，不调用模型。实际模型测试只替换 providers，保留题面、seed、hash 和 assertion。框架配置在评测者端，不能整体挂载给候选 shell。

```python
from nrb_v1.adapters import summarize_promptfoo_results
result = summarize_promptfoo_results("results/promptfoo-v1.json", selection="coding")
```

Python assertion 的标量为 `auto_points/70`。完整报告保留于 metadata 和 reason；转换器核对任务、题面、评分器身份与标量，拒绝多 provider/prompt 混成一组。promptfoo 可能脱敏长十六进制变量，此时只从原日志完整题面与 sealed canonical report 恢复身份，不用当前代码伪造历史哈希。

## 8. Harbor

验证目标 **Harbor 0.24.0**、任务 schema **1.4**；以下安装及运行使用 **Python 3.12+**：

```bash
python -m pip install 'harbor==0.24.0'
python -m nrb_v1 export --format harbor --tasks coding --seed 17 \
  --image nrb-v1:local --dest exports/harbor-v1
harbor run -p exports/harbor-v1 -a YOUR_AGENT -m PROVIDER/MODEL_ID \
  --env docker --jobs-dir logs/harbor-v1 --n-concurrent 1 \
  --n-attempts 1 --max-retries 0
```

`YOUR_AGENT` 必须是本地安装版本实际支持的 agent。每个任务建议预算写入 task.toml；比较前若统一修改，需记录新配置。候选作答默认断网；推理客户端需要 API 网络时，在导出命令加 `--agent-hosts api.example.com`，以真实所需域名替换示例，保留最小允许集合并关闭远程搜索工具。

候选只看到 `/app/task.md` 和空 `/app/submission.json`。独立 verifier 读取提交并运行，输出 `verifier/report.json` 和自动70分对应的 `reward.txt`。参考程序只在 `tests/grader/` 内；正式导出不含 `solution/`。不要关闭独立 verifier。

从每个实际 trial 取 `report.json` 后，用标准汇总接口汇总一个模型、一个配置、一个重复轮次。Harbor reward=1 仅表示自动满分，仍须另行人工审阅 30 分与核心责任。

## 9. 任意 CLI / 文件型 harness

原生命令适配器支持 `--command-json` argv；`{task}` 和 `{workdir}` 会替换为本轮路径。它在候选目录启动命令，stdin 提供代码题正文；图文题要求命令打开本地 HTML。候选可以写 `submission.json`，或在 stdout 返回严格 JSON。

无模型调用的最小自检：

```bash
# 从仓库根目录运行；此命令仅验证文件协议，不是正式闭卷或模型测试。
python -m nrb_v1 run \
  --command-json "[\"python\",\"$PWD/adapters/v1/mock_agent.py\",\"{task}\"]" \
  --tasks C01 --seed 17 --dest runs/v1-cli-smoke \
  --model-label mock-empty --harness-label file-protocol \
  --execution none
```

实际测试替换为你的隔离 agent wrapper，固定模型和 harness 标签，并用 `--metadata run-config.json` 记录生成参数、skills、工具、版本与运行限制。Runner 保存实际耗时、退出状态、原始输出、提交和统一报告。未知 token/cost 保持 null，不填0。

**原生 runner 是宿主子进程，不是生成阶段的安全沙箱。** 新目录只能减少意外上下文污染；正式闭卷请让 wrapper 启动独立候选容器/机器，或直接采用 Harbor 的独立环境。详细边界见 [防答案访问](closed-evaluation.md)。

## 10. 结果阅读和比较

```bash
python -m nrb_v1 summarize --tasks coding \
  --reports results/coding-final.json --out results/coding-summary.json
```

报告按任务家族等权，所选 task/seed 缺项保留，自动与人工结果分开，C/R/X 三种画像分开。同一个比较队列必须有一致 evaluator commit/内容身份；人工与 LLM 暂评不能混队。不同模型/harness 的运行应各有目录，再按同题、同种子、同预算配对比较。

V1 工具没有替你调用真实模型或生成排名。正式选型可先跑 C01/C03/C04/C06/C09/C10 定位梯度，再补全十代码；日常科研适配按 R01–R06 单项画像判断。这个子集建议只是起步诊断，不能拿子集均分冒充十题总结果。
