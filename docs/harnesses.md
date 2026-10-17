# Harness 接入与可复现运行

v0.2 的接入路径共享 `nrb.core.grade_submission`。同一比较固定任务、seed、候选输入哈希和评分器身份（版本、commit、实际源码digest）；框架只负责把任务交给模型或代理、收集提交及保存运行记录。Inspect AI 的默认任务是单次生成基线；原生 runner 和 Harbor 用于包含工具的代理流程；promptfoo 支持模型 provider，也支持本仓库的命令行代理 provider。

## 1. 先确定比较的对象

| 路径 | 实际测量对象 | 适合用途 | 自动评分 |
|---|---|---|---|
| Inspect AI `null_research` | 一次 `generate()` 的回答；不提供工具 | 比较模型对同一完整材料包的理解、推理与交付 | 自定义 scorer，保存逐项检查与待复核状态 |
| promptfoo + 模型 provider | provider 定义的生成流程 | 比较模型、提示或已有应用接口 | Python assertion 调用同一核心评分器 |
| promptfoo + `command_provider.py` | 外部 CLI 代理的完整调用 | 保留 promptfoo 的比较界面，测已有代理 | CLI 输出归一化后调用同一 assertion |
| 原生 `nrb run` | 实际 CLI、其配置、权限与技能的组合 | 日常回归、同一模型换 harness、技能消融 | 自动收集提交并评分，保存运行事实 |
| Harbor | 容器中的代理工作流 | 更严格地控制候选文件可见性及评分环境 | 独立 verifier 容器调用同一核心评分器 |

这些路径的原始分数不能混成一张无条件排名表。先固定工具、技能、联网范围、预算和推理设置；一次只改变所研究的因素。例如，比较两个 harness 时固定同一模型快照；比较技能是否有效时固定模型、harness 和工具，只改变技能集合。所有核心题使用提供的合成材料，禁用外部搜索和检索本仓库答案的工具。

每题 **70 分自动检查 + 30 分独立质量复核**。框架显示的 `score` 或 Harbor `reward` 为自动分数除以 70，范围 0–1；它不表示完整的 100 分研究质量。`total` 在独立复核前为 `null`，不自动补满、不折算为已复核总分。promptfoo 的 `pass` 只表示自动70分全通过且没有已确认关键失败，不表示核心责任已全部审阅或必经执行已具备证据。报告同时保存 `completion_status`、`quality_qualified`、关键失败和待评项；即使原始总分达到80，核心证明或交付失败仍是 `failed`。具体内容遵循[评分规范](scoring.md)与各题 rubric。

提交代码执行与候选代理隔离是两件事。v0.2 的必经检查包括：

| 题目 | 实际执行或审阅要求 | 对分数与完成状态的影响 |
|---|---|---|
| NRB03 | 通过受限执行器调用 `solve.py` 的 `solve(problem) -> answer_dict`，核对代码结果、提交与精确最优层级 | 不新增自动分；数值可得70而搜索复现失败，完成仍为 `failed`；执行环境不可用则为 `infrastructure_unscored` |
| NRB04/05 | 隔离执行提交的 `solution.py`，检查正常与异常行为 | 每题50分代码行为权重；未执行时该权重未评，`auto_percent=null` |
| NRB09 | 静态SVG检查之后，独立审阅实际渲染PNG，并看整图与180mm等效展示 | 渲染成功不增加自动分，也不自动通过可读性；缺执行或核心审阅证据不能完成 |

`execution=none` 可以读取其余可评的数值检查，不能用来声明上述责任已完成。对外部候选代码使用 Docker/container；`trusted` 仅供仓库自有参考程序和错误控制。

## 2. 安装及版本记录

在评测机的仓库根目录安装本项目。核心只需要 Python 3.11+ 标准库；Harbor 的官方包要求 Python 3.12+。

```bash
python -m pip install -e .
python -m nrb --version
python -m nrb list
```

下表是本次按官方资料核对的依赖目标，不是已经在所有平台实测兼容的范围。正式比较时固定确切版本，保存安装清单、模型快照、操作系统、容器 image digest 及仓库 commit。

| 可选组件 | 核对目标，2026-10-17 | 安装示例 |
|---|---|---|
| Inspect AI | `0.3.281`；本适配器使用 `Score.unscored` | `python -m pip install inspect-ai==0.3.281` |
| promptfoo | `0.124.1`；使用 Node 22.22+ 的环境 | `npm install -g promptfoo@0.124.1` |
| Harbor | `0.24.0`，task schema `1.4` | `python -m pip install harbor==0.24.0` |
| Docker | Linux 容器；具体 engine 版本由运行者固定 | 按所在系统安装，并记录 `docker version` |
| CLI 代理 | 按实际安装的 Codex / Claude Code / Gemini CLI 固定版本 | 记录对应命令的 `--version` 与完整无密钥配置 |

版本依据见 [Inspect 发布记录](https://inspect.aisi.org.uk/CHANGELOG.html)、[promptfoo 0.124.1 发布页](https://github.com/promptfoo/promptfoo/releases/tag/0.124.1)、[promptfoo 0.124.1 包配置](https://github.com/promptfoo/promptfoo/blob/0.124.1/package.json)及 [Harbor v0.24.0 任务配置源码](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/models/task/config.py)。Harbor 的 schema 1.4、separate verifier、网络模式和解析接口，以及 promptfoo 的 Node 要求均已检查对应发布 tag 的源码；后续升级必须重新运行可选接口测试。

## 3. 原生 CLI runner

### 3.1 输入和输出约定

`nrb run` 为每题建立新的工作目录，把完整题目放入标准输入，同时写入 `instruction.md`、候选数据文件及输入清单。代理应写入当前目录的 `submission.json`，或在最终文本中返回该 JSON：

```json
{
  "task_id": "NRB01",
  "answer": {},
  "artifacts": {
    "reasoning.md": "完整交付内容，而不是文件路径或生成内容的承诺"
  }
}
```

`answer` 的具体字段及必需 artifacts 由题目给出。所有交付物都应放在 `artifacts` 中，使用 UTF-8 字符串表示。有效 `submission.json` 优先于 stdout 的进度信息。JSONL 事件流和 CLI 的外层 JSON 不是提交文件；下面的 `--stdout-format` 会按明确指定的协议提取最终回答。

工作根目录必须是仓库以外的**新目录**；已有工作目录、已有评测日志目录和旧输出文件会被拒绝。输入文件哈希保存在候选目录之外，并在调用结束后复核。修改、删除或把原始输入替换成符号链接会使该次运行失去比较资格。

**原生 runner 是宿主机子进程桥接器，新的工作目录不构成安全隔离。** 它继承调用环境。正式受控运行应由外部容器或专用评测机落实可见文件、凭据和联网边界；仅将 `--execution` 设为 `docker` 只隔离提交代码的评分执行，不会隔离 CLI 代理本身。没有落实这些条件时，使用默认 `agent-diagnostic` 标签记录日常工作环境中的表现。

### 3.2 已按官方文档核对的命令模板

把 `REPLACE_WITH_EXACT_MODEL` 替换为实际模型名称，并让 `--model-label` 与真实调用一致。这里没有固定某个商业模型，也没有代为调用付费 API。每次运行使用新的目录和新会话。

Codex 的非交互 `exec` 可从 stdin 读入任务；`--json` 输出事件流，`--skip-git-repo-check` 支持本项目创建的非 git 工作目录。当前文档不再使用旧的 `--full-auto` 选项。参见 [Codex 非交互模式](https://developers.openai.com/codex/noninteractive/)。

```bash
python -m nrb run \
  --command-json '["codex","exec","--model","REPLACE_WITH_EXACT_MODEL","--sandbox","workspace-write","--skip-git-repo-check","--json","-"]' \
  --stdout-format codex-jsonl \
  --model-label REPLACE_WITH_EXACT_MODEL --harness-label codex \
  --seed 0 --timeout 900 --execution docker \
  --work-root /tmp/nrb-codex-s0-r1 --out /tmp/nrb-codex-s0-r1/result.json
```

Claude Code 的 `-p` 是非交互调用；`--output-format json` 包含最终结果与使用记录。权限、工具和技能配置需要作为 harness 设置记录。`--allowedTools` 管理自动允许的工具，不能替代限制可见工具的 `--tools`；不要混淆二者。需要无定制基线时，可按安装版本的官方说明配置 `--bare`。参见 [headless 模式](https://code.claude.com/docs/en/headless)和 [CLI reference](https://code.claude.com/docs/en/cli-reference)。

```bash
python -m nrb run \
  --command-json '["claude","-p","--model","REPLACE_WITH_EXACT_MODEL","--output-format","json"]' \
  --stdout-format claude-json \
  --model-label REPLACE_WITH_EXACT_MODEL --harness-label claude-code \
  --seed 0 --timeout 900 --execution docker \
  --work-root /tmp/nrb-claude-s0-r1 --out /tmp/nrb-claude-s0-r1/result.json
```

Gemini CLI 在 stdin 管道下进入 headless 模式；JSON 外层的 `response` 是最终文本，`stats` 是 CLI 提供的统计。参见 [headless 模式](https://geminicli.com/docs/cli/headless/)和 [CLI reference](https://geminicli.com/docs/cli/cli-reference/)。

```bash
python -m nrb run \
  --command-json '["gemini","--model","REPLACE_WITH_EXACT_MODEL","--output-format","json"]' \
  --stdout-format gemini-json \
  --model-label REPLACE_WITH_EXACT_MODEL --harness-label gemini-cli \
  --seed 0 --timeout 900 --execution docker \
  --work-root /tmp/nrb-gemini-s0-r1 --out /tmp/nrb-gemini-s0-r1/result.json
```

这些模板不强制绕过代理自己的权限设置。运行者应先在专用测试环境检查认证、工具权限和非交互调用，再开展正式比较。CLI 版本升级后先检查 `--help` 并运行本仓库的回归测试；不把新增或失效的选项当作模型能力变化。

### 3.3 受控配置及记录

实际落实隔离后，可追加 `--track agent-controlled --metadata run-config.json`。文件必须包含 `isolation`、`tool_policy`、`model_version`、`harness_version`、`skills`、`reasoning` 和 `budget` 七项。写明实际配置与证据，例如镜像 digest、出站域名范围、读写挂载、技能文件哈希和每题预算。CLI 检查字段存在，不验证环境真的具备所声明的隔离；该标签始终是运行者的声明。

每题的评测目录保存无密钥 argv、开始/结束时间、墙钟耗时、退出码、stdout/stderr、输入清单和哈希。POSIX 超时会终止本次进程组；输出流有大小上限。令牌数和费用只保留 CLI 明确报告的字段，未报告就是 `null`。Claude 的 `total_cost_usd` 被标为客户端估算值；不同供应商的 token、缓存和推理计数口径需要分别核对。不要把本项目的墙钟耗时当作模型生成耗时。

正常认证应通过 CLI 自己的认证或环境进行，不把 API key 写进 argv、配置或公开报告。日志对已知凭据做尽力脱敏，但原始提交与运行记录仍由运行者检查后再公开。

## 4. Inspect AI

适配器使用真实 `Task`、`Sample`、`generate()` 和自定义 scorer 接口；样本的 `target` 为空，模型输入不含答案。官方接口见 [custom scorers](https://inspect.aisi.org.uk/custom-scorers.html)、[Score / unscored](https://inspect.aisi.org.uk/reference/inspect_ai.scorer.html)和 [Sample](https://inspect.aisi.org.uk/reference/inspect_ai.dataset.html)。

```bash
inspect eval adapters/inspect_ai/nrb_eval.py@null_research \
  --model PROVIDER/EXACT_MODEL \
  -T seed=0 -T execution=docker \
  --epochs 1 --log-dir /tmp/nrb-inspect-s0-r1
```

这是无工具、一次生成的明确基线。若另写 Inspect solver 加工具，应给其独立的 harness 标签、记录工具策略和 solver commit，并继续使用 `nrb_automatic`；本适配器不把 `generate()` 描述成完整研究代理。

scorer 将逐题核心报告存入 `Score.metadata.nrb_report`。依赖缺失、代码评分未运行或导出版本漂移使用 `Score.unscored`。Inspect 自身的均值可能排除未评分样本，因此必须从具体 `.eval` 日志生成保留十题分母的报告：

```bash
python adapters/inspect_ai/summarize_log.py /tmp/nrb-inspect-s0-r1/ACTUAL_LOG.eval \
  --epoch 1 --out /tmp/nrb-inspect-s0-r1/nrb-result.json
```

每个 epoch 单独汇总。缺题、失败日志、未评分样本或混合 seed 不会得到可比较的完整总分。没有提供安全容器代码执行时，NRB04/05 的50分行为权重保留未评，NRB03的独立搜索复现责任也未评。NRB03仍可能显示数值自动满分，所以必须同时读取 `completion_status` 与 `mandatory_execution`；Inspect标量分数不能代替完成判定。NRB09的实际渲染与科学审阅由后续复核流程补齐。

## 5. promptfoo

### 5.1 先验证接线，再换模型

```bash
python -m nrb export --format promptfoo --seed 0 --execution docker \
  --dest /tmp/nrb-promptfoo-s0-r1
promptfoo eval -c /tmp/nrb-promptfoo-s0-r1/promptfooconfig.yaml \
  --no-cache --no-share --output /tmp/nrb-promptfoo-s0-r1/results.json
```

导出的 `.yaml` 使用 YAML 合法的 JSON 子集。默认 provider 是 `offline-empty-smoke`，故意交付十份空答案；预期是十题自动分 0，不能用它宣传模型能力。promptfoo 对断言失败默认返回退出码 100，运行错误返回 1；分数低与运行故障要分别处理。参见 [Python provider](https://www.promptfoo.dev/docs/providers/python/)、[Python assertions](https://www.promptfoo.dev/docs/configuration/expected-outputs/python/)和 [CLI exit codes](https://www.promptfoo.dev/docs/usage/command-line/)。

换模型时只改 `providers`；保留 task vars、题目、seed、哈希和 Python assertion。使用 promptfoo 官方支持的 provider 与明确模型 ID。禁用 provider 的搜索、外部检索或本仓库访问。先用单一 provider、单次重复导出一份报告；多个 provider 可在界面并排观察，但本仓库的完整结果转换要求每个比较对象各保存一份文件。

```bash
python adapters/promptfoo/summarize_results.py /tmp/nrb-promptfoo-s0-r1/results.json \
  --out /tmp/nrb-promptfoo-s0-r1/nrb-result.json
```

转换器读取已保存的核心报告，不另设科学评分规则。它检查任务身份、自动分口径和十题完整性；评分依赖失败不会悄悄变为模型零分或从分母消失。每次模型比较都使用 `--no-cache`，否则可能测到的是缓存结果。

promptfoo 0.124.1 的导出脱敏可能把SHA形状的变量值替换成 `[REDACTED]`。v0.2的处理以 `nrb.adapters.summarize_promptfoo_results` 为准，同时保留题包与评分身份：

- 评分回调核对导出的 `evaluator_identity` 与实际运行评分器身份，以及候选prompt哈希；修改评分源码后应重新导出，不仅检查题面有没有变。
- 转换器从日志中的 canonical `nrb_report` 读取本次实际评分身份。metadata与reason同时保存报告时，两份必须相同；它不会给历史记录补上当前评分器身份。
- 只有 `candidate_sha256` 明确为 `[REDACTED]` 时，才用完整记录的 `vars.prompt` 复算，并要求该题面与当前可重建题包一致；完整但错误的哈希、修改的prompt或不匹配的 `case_hash` 仍拒绝。补证任务列在 `provenance.hash_recovered_from_full_logged_prompt`。
- 导出变量中的 `evaluator_digest` / `evaluator_commit` 只有明确被脱敏时，才能从**同一条日志的canonical报告**补证；记录在 `provenance.evaluator_identity_recovered_from_canonical_report`。其他身份字段必须相同。缺少导出或canonical身份的任务另列 `unverified_export_evaluator_identity`；不把缺失值伪造为今天的身份。
- 转换后的当前报告仍需通过自动/已审报告封存、分数及完成状态校验；没有可验证身份的旧报告不能进入跨版本比较。转换不重新执行候选代码，也不重新评分。

v0.2迁移应重新导出并核对题包与评分器身份；上述脱敏补证只恢复同一日志中已有的证据。相关脱敏规则见 [0.124.1 sanitizer 源码](https://github.com/promptfoo/promptfoo/blob/0.124.1/src/util/sanitizer.ts)。

Inspect 与 promptfoo 的统一结果保留实际日志中的 `model_label`、`harness_label`、框架版本和生成配置。Inspect 读取 `EvalSpec.model`、模型参数与 solver plan；promptfoo 保存 provider ID、label、配置及配置哈希。promptfoo 的 `model_label` 表示 provider ID：若它是 Python 或命令 provider 的文件名，就不能当成已知的底层模型版本。无法由日志证明的模型快照保持 `metadata.model_version = null`，并标记 `metadata_incomplete`。任务 seed、运行 ID、时间戳放在独立的 `source_log`，不会把同一设置的不同题目变体误判为不同实验配置。Inspect 字段依据见 [0.3.281 EvalSpec 与 EvalPlan](https://github.com/UKGovernmentBEIS/inspect_ai/blob/0.3.281/src/inspect_ai/log/_log.py)。

### 5.2 调用实际 CLI 代理

可将导出的 `providers` 替换为以下结构，命令数组与原生 runner 兼容：

```yaml
providers:
  - id: file://command_provider.py
    label: codex-EXACT_MODEL
    config:
      command:
        - codex
        - exec
        - --model
        - REPLACE_WITH_EXACT_MODEL
        - --sandbox
        - workspace-write
        - --skip-git-repo-check
        - --json
        - '-'
      stdout_format: codex-jsonl
      workdir_root: /tmp/nrb-promptfoo-agents
      timeout_seconds: 900
      timeout: 960000
```

`timeout_seconds` 是本仓库的代理进程预算；`timeout` 是 promptfoo Python worker 的毫秒超时，留出收集和终止进程的余量。每行会创建新的 UUID 工作目录。该 provider 的宿主环境边界与原生 runner 相同；仅改 provider 名字不会产生容器隔离。provider metadata 保留代理调用记录与实际报告的使用统计。

## 6. Harbor 独立 verifier

先在评分侧做oracle接线自检，必须显式选择包含参考解的导出。这一目录只用于自检：

```bash
python -m nrb export --format harbor --seed 0 --include-oracle \
  --python-image python:3.12-slim --dest /tmp/nrb-harbor-oracle-s0-r1
harbor run -p /tmp/nrb-harbor-oracle-s0-r1 -a oracle --env docker \
  --jobs-dir /tmp/nrb-harbor-oracle-jobs --job-name oracle --n-concurrent 1 --n-attempts 1
```

正式模型运行重新导出独立目录，不传 `--include-oracle`。agent执行阶段默认无网络；需要在线模型API时，显式允许实际使用的精确DNS主机。下面的域名只是对应API路径的示例，其他provider应替换为其实际主机：

```bash
python -m nrb export --format harbor --seed 0 \
  --python-image python:3.12-slim --agent-hosts api.openai.com \
  --dest /tmp/nrb-harbor-candidate-s0-r1
harbor run -p /tmp/nrb-harbor-candidate-s0-r1 \
  -a INSTALLED_AGENT -m PROVIDER/EXACT_MODEL --env docker \
  --jobs-dir /tmp/nrb-harbor-model-jobs --job-name model-run --n-concurrent 1 --n-attempts 1
```

所选agent的推理、skills和禁搜索选项必须按其固定版本实际配置；没有适用于所有agent的通用 `--ak` 禁搜索保证。API主机白名单也不能关闭provider在同一主机背后的服务端搜索工具，需另行禁用并记录。

正式比较前把 `python:3.12-slim` 换成已解析并保存的 `python@sha256:...` digest；不要将移动 tag 当作锁定的执行环境。Harbor 的安装、任务格式和运行参数分别参见 [任务配置](https://docs.harborframework.com/tasks/configuration)、[独立 verifier](https://docs.harborframework.com/tasks/separate-verifier)和 [运行 job](https://docs.harborframework.com/jobs/run-a-job)。

导出包遵循以下可检查的边界：

- `environment/` 的 Docker build 只复制候选材料，不复制评测 Python 包、expected 或参考答案。候选目录是 `/app`，完整提交写入 `/app/submission.json`。
- `tests/` 构建独立评分镜像；它包含 root 私有的 `/grader`。评分主进程以 root 运行，候选 Python 子进程降为 UID/GID 65534，并使用核心执行器的资源限制。子进程不能读取 `/grader`。
- `artifacts = ["/app/"]` 把提交和原始输入传入 verifier，供评分器核对输入是否修改。代理结束之后才进行这些步骤。
- agent安装阶段可获取运行依赖；正式agent执行阶段默认 `no-network`。只有显式传入 `--agent-hosts` 才设置精确主机allowlist，拒绝通配符和URL；verifier始终无网络。部署后还须验证后端确实执行该策略。
- 默认没有 `solution/`；只有显式 `--include-oracle` 的自检包才生成它。正式候选使用另一份无solution导出，不挂载完整导出目录或评分目录，也不把verifier改成shared模式。
- agent构建上下文用受限 `.dockerignore` 限制为Dockerfile与candidate packet；评分器源码、答案键和可选oracle位于独立路径。不能通过自定义挂载绕过这一边界。

网络控制依赖 Harbor 后端的真实能力；Docker allowlist 需要适用的 Linux 网络条件。后端不支持时应按基础设施错误处理，不能自动退回无限联网并保留“受控”标签。参见 [Harbor network policies](https://docs.harborframework.com/tasks/network-policies)。

每题 verifier 写入 `report.json` 和自动分数的 `reward.txt`。v0.24.0 的确切宿主路径是 `JOBS_DIR/JOB_NAME/TRIAL_NAME/verifier/report.json`、同目录 `reward.txt`，以及上一层的 `result.json`。已对照 [TrialPaths 源码](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/models/trial/paths.py)和 [Verifier 源码](https://github.com/harbor-framework/harbor/blob/v0.24.0/src/harbor/verifier/verifier.py)核对；scalar reward 被框架解析为 `verifier_result.rewards.reward`。

修改输入或评分不能完成时不产生有效数字 reward。保留完整 verifier 日志并检查十题覆盖率，不仅看 Harbor 的成功率汇总；标准化报告中的 30 分质量复核仍为待定。任何从多个 job 合并出的结果都要先按模型、配置、seed、重复序号分组，避免重复题目混入均值。评分入口在运行时重新将 verifier 日志目录设为 root-owned 0755，因为 Harbor 的宿主挂载会覆盖镜像内权限；UID 65534 无法改写奖励文件。

## 7. 自动分之后的质量复核

原生runner把规范化提交保存为工作根目录的 `NRB01.json` 等文件；其他框架保留同一个提交JSON。`review-packet` 生成 `task.md`、`submission.json`、空 `review.json`、审阅说明，以及管理侧的 `automatic_report.json`。**整个目录包含自动分数**；质量评阅时使用题目、提交与量表，不根据管理侧自动分或模型/harness身份推断质量。

```bash
python -m nrb review-packet --task NRB01 --seed 0 \
  --submission /tmp/nrb-codex-s0-r1/NRB01.json --dest /tmp/nrb-review-nrb01

python -m nrb review-packet --task NRB03 --seed 0 --execution docker \
  --submission /tmp/nrb-codex-s0-r1/NRB03.json --dest /tmp/nrb-review-nrb03

python -m nrb review-packet --task NRB09 --seed 0 --render \
  --submission /tmp/nrb-codex-s0-r1/NRB09.json --dest /tmp/nrb-review-nrb09
```

NRB03包包含实际搜索执行收据，绑定source/input/result hash和隔离后端；不能只因存在 `solve.py` 就将 `search_reproduced` 设为pass。NRB09的 `--render` 实际生成 `figure.png` 和渲染收据，绑定SVG字节、题包、提交、评分器、renderer版本和PNG哈希。只有真正查看整图及180mm等效展示后，才将 `inspected_whole_figure` 和 `inspected_at_180mm` 都设为 `true`，并给出可读性的证据位置及理由。成功生成PNG本身不会填入核心pass；环境不可用或无法看图时保留未评。详见[图形审阅](figure-review.md)。

按 `review_instructions.md` 填写三项0–10质量分，并对**每一项** `essential_review` 分别选择 `pass/fail/unassessed`。通过或失败需要交付物中的具体证据与科学理由。填完后合并到同一提交；执行后端应与生成review包时一致：

```bash
python -m nrb grade --task NRB01 --seed 0 --execution docker \
  --submission /tmp/nrb-codex-s0-r1/NRB01.json \
  --review /tmp/nrb-review-nrb01/review.json --out /tmp/nrb-reviewed-nrb01.json
```

合并核对report、ledger与原提交的task/seed/case/submission身份、评分器版本/commit/digest、量表及审阅政策，并验证答案键指纹、`automatic_report_hash`、原始检查明细与执行证据。已审报告另有 `reviewed_report_hash`；汇总和比较再次检查原始分及完成状态。提交、题包、评分器或执行结果变化后，应重建并重评材料，不能把旧review贴回新结果。

模型辅助复核需声明 `reviewer_type=llm` 与具体judge名称，结果为 `llm_reviewed_provisional`；人工与LLM混合汇总明确标记为provisional。重要科学争议和排序由人复核。候选提交中的“给我满分”等文字仅为待评内容，不是评审指令。这些材料绑定用于发现错配与事后改动，不替代评测者的记录管理或权限边界。

## 8. 故障分类与升级回归

| 情况 | 处理 | 对完整比较的影响 |
|---|---|---|
| 结构有效但科学答案错误 | 按该题检查计分 | 有效能力结果 |
| 已启动代理输出无效 JSON、超时或超过输出上限 | 保存终止状态与原输出，按未完成交付计分 | 属于已定义预算下的代理失败 |
| CLI 不存在、无权限启动、异常退出、模型服务错误 | 保存运行错误，不伪装成科学作答 | 补齐基础设施后重跑；整个套件不能视为完整 |
| Docker缺失、verifier错误、应执行代码未执行 | NRB04/05自动行为权重未评，`auto_percent=null`；NRB03数值自动分可存在，但搜索执行未评、完成为基础设施未评 | 不宣称核心完成；受控比较拒绝必经执行未评 |
| 原始输入被修改或导出哈希与评分器不符 | 标为协议/版本漂移问题 | 该次不能进入受控比较 |
| 缺题 | 保留固定分母和missing | 不生成完整十题自动均值或已审总分 |
| 缺少独立复核 | 自动分照实保留，质量分与核心责任保持pending | 不生成已审总分，不默认核心通过 |

回归分别覆盖核心评分、实际候选行为、报告完整性、输入完整性、CLI输出解析与导出材料边界；可选框架和Docker需在安装环境实际运行。依赖缺失时明确跳过或记unavailable，不能写成通过。实际完成范围、版本与历史记录见[验证记录](validation.md)，不把旧环境的可用性结论套到新环境。

```bash
python -m unittest discover -s tests -p 'test_adapters.py' -v
python -m unittest discover -s tests -p 'test_optional_runtime.py' -v
python scripts/check_docker.py --out /tmp/nrb-docker-runtime-check.json
python adapters/promptfoo/smoke.py --dest /tmp/nrb-promptfoo-runtime-check
python adapters/harbor/smoke.py --dest /tmp/nrb-harbor-runtime-check --tasks all
```

`test_optional_runtime.py` 在依赖已安装时使用真实 Inspect mock 模型走完整 eval/scorer/log 流程，并通过真实 Harbor `TaskConfig` 校验十个导出任务。它不启动 Docker。promptfoo smoke 通过真实 CLI、Python provider 和 assertion 执行十个空提交，要求恰好 10 个预期断言失败、0 个运行错误及统一报告的 0 分。

Harbor smoke 会调用本仓库 CLI 导出任务，再实际启动 Docker oracle。脚本显式选择oracle导出；默认检查NRB04、NRB05、NRB09，`--tasks all` 检查全部十题并覆盖NRB03的必经搜索执行。它检查每个 trial 无异常、resolved verifier 为 separate、实际 reward 为 1、核心报告为 70/70 且覆盖完整、输入未改、日志目录权限正确和复核仍待定。结果与日志写入 `--dest`，核心运行证据为 `smoke_report.json` 和各 trial 文件。mock/oracle 的 token 或调用统计从不作为模型表现发布。

上述mock/oracle与执行器控制是程序和基础设施自检，尚不是任何真实模型的成绩。正式模型试跑仍需全新上下文和无答案候选包，见[测试操作指南](testing-without-answer-access.md)。

升级检查：保存旧版本与结果；在新环境运行核心和适配器测试；再运行可选框架测试及 Harbor oracle；最后用同一 seed 与预算做小规模真实代理对照。只有任务、输入、评分器与运行配置都可追溯时，才把新旧差值解释为模型或 harness 的变化。
