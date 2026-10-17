# 怎样测试，才能避免候选AI读取答案

推荐把**出题/评分机、候选环境、独立审阅环境**分开。仓库公开支持审计；正式候选只收到单题的公开材料包。提示“不要偷看”是任务规则，真正的边界由文件挂载、网络权限和会话状态实现。

## 1. 先区分两种实验

| 实验 | 建议路径 | 候选实际能访问的内容 |
|---|---|---|
| 只比较模型推理与文本交付 | Inspect默认solver，或禁用工具的普通API provider | 单题完整prompt；没有shell、浏览器、搜索、MCP或仓库连接器 |
| 比较模型与harness的科研工具工作流 | Harbor，独立agent/verifier容器 | 单题文件、指定工具；仅必要模型API网络 |
| 测日常本机CLI配置 | `nrb run` / promptfoo CLI bridge | 真实宿主权限，默认只应标为diagnostic；新工作目录不能防止读取父目录/全局文件 |

`grade --execution docker` 只隔离**提交代码的评分执行**，不会自动隔离前面生成答案的Codex/Claude/Gemini进程。要测受控agent，优先使用Harbor或自行落实同等边界。

## 2. 评分机准备与版本冻结

以下命令在可信评分机执行，候选看不到这个工作区。用实际固定commit替换变量内容；每轮使用新的输出目录。

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
git checkout REPLACE_WITH_V02_COMMIT
python -m pip install -e .
python -m nrb selftest --seeds 0,17,101 --out /tmp/nrb-selftest-before-run.json
```

保存commit、评分器digest、Python/依赖版本、镜像digest和无密钥配置。正式运行期间不编辑评分源码。不把selftest、reference、修改方案或本页里的控制案例送给候选。selftest使用仓库自有程序，不产生模型成绩。

## 3. 模型无工具测试

Inspect适配器默认只调用一次 `generate()`；样本的target为空，题面不带答案。

```bash
python -m pip install inspect-ai==0.3.281
inspect eval adapters/inspect_ai/nrb_eval.py@null_research \
  --model PROVIDER/EXACT_MODEL -T seed=17 -T execution=docker \
  --epochs 1 --log-dir /tmp/nrb-inspect-s17-r1
```

提供给模型的是生成的题包，不是Python模块或本仓库。服务端也需禁用搜索、浏览、检索、连接器、远程执行、持久记忆和其他工具。模型写出代码/图的文本后，由评分机隔离执行和审阅。适配器没有提供本地工具，不代表第三方provider配置中不存在服务端工具；保存实际请求和工具策略。

## 4. Harbor工具实验

先安装固定版本并验证Docker。正式比较使用已解析的镜像digest；下面移动tag只用于安装示例。

```bash
python -m pip install harbor==0.24.0
python scripts/check_candidate_isolation.py \
  --python-image python:3.12-slim --out /tmp/nrb-isolation-preflight.json
```

探针实际构建无答案的候选镜像，在无网络、无host bind mounts、只读根文件系统等条件下检查输入hash、无法import评分包、没有 `/grader`、`/solution`、宿主Docker socket，以及实际出站连接失败。缺Docker时输出unavailable并非通过。此探针验证**离线候选镜像**，不代替后面在线API白名单在真实Harbor后端的检查。

导出正式模型包，显式指定你实际使用的模型API域名：

```bash
python -m nrb export --format harbor --tasks all --seed 17 \
  --python-image python:3.12-slim --agent-hosts api.openai.com \
  --dest /tmp/nrb-harbor-candidate-s17-r1

harbor run -p /tmp/nrb-harbor-candidate-s17-r1 \
  -a INSTALLED_AGENT -m PROVIDER/EXACT_MODEL --env docker \
  --jobs-dir /tmp/nrb-harbor-jobs-s17-r1 --job-name model-run \
  --n-concurrent 1 --n-attempts 1
```

`INSTALLED_AGENT`、模型、推理档位与禁搜索配置由所选agent的实际版本决定，按其官方说明设置，并记录真正生效值。示例 `api.openai.com` 适用于相应API路径，不保证涵盖所有登录流程；如果使用其他provider只允许它实际需要的精确主机。不要为了排除认证错误开放全部网络。

### 当前导出默认已落实的边界

- 不传 `--include-oracle` 就没有 `solution/`；该选项仅用于评分器oracle自检。
- 不传 `--agent-hosts` 就是agent执行阶段无网络；传入后仅配置精确host allowlist，拒绝通配符和URL。
- agent镜像build context只有Dockerfile、受限dockerignore和候选packet，Dockerfile只复制packet。
- verifier使用独立镜像，评分包在root私有目录；候选Python降权执行，不能读评分器或改reward。
- agent结束后再把提交和原始材料送入verifier，检查输入完整性、运行评分并保存身份。

这采用Harbor的[separate verifier](https://docs.harborframework.com/tasks/separate-verifier)与[网络策略](https://docs.harborframework.com/tasks/network-policies)；Docker的[none网络](https://docs.docker.com/engine/network/drivers/none/)只创建loopback。网络实现受后端和系统支持约束，不能在未验证的环境中只凭配置字段声称已隔离。

### 仍必须在实际运行中控制的入口

候选容器不要挂载完整仓库、整个导出目录、评分日志、旧提交、宿主HOME、Docker socket或可访问其他工作区的凭据。关闭浏览器、GitHub连接器、MCP搜索/文件服务器、共享记忆，以及指向旧benchmark结果的缓存。模型API白名单无法阻止供应商在同一域名后面提供搜索服务，所以服务端工具也要关。

候选可用的skills只能是预先固定的通用工具技能；不得包含本题参考解、专用求解脚本、已知错误答案或评阅修改建议。skills内容hash属于harness配置。多agent实验的所有子agent使用同样的候选权限，不允许某个辅助agent读评分机再回传答案。

## 5. 每题必须是全新上下文

不要在用于制作、审查或修订本benchmark的聊天里让模型“再做一遍题”。这个上下文已含答案与负控制。每一题、每一次重复都新建会话与工作区；关闭跨题记忆和共享缓存。相同模型的不同harness使用相同任务seed，但彼此不共享解答或评分反馈。

如果自行接CLI，可使用下面统一任务前缀，随后附上**单题** `instruction.md`。它只表达实验规则，不能替代容器权限：

```text
请独立完成下面单题科研任务，按题面提交 answer 和全部 artifacts。
仅使用本题提供的材料、当前候选工作区和本轮授权工具。
不要访问benchmark仓库、评分器、参考答案、历史提交、评分反馈或其他会话。
不要修改原始输入；不要把未执行的操作写成已经执行。
交付一个有效submission.json，artifacts中放完整文件内容。
如果因当前工具或预算不能完成，保留真实交付与限制，不捏造运行证据。
```

记录模型精确版本、harness版本、推理档位、skills、多agent开关、时间/输出/tool预算。首次诊断可以每题一次、同一seed；开始比较后不对单个模型临时延长预算或追加提示。单个seed不覆盖全部语义：NRB10的开发seed0–7覆盖八类证据状态，0、17、101的接线自检集合则不具备完整状态覆盖。正式校准须事先选平衡状态集，对所有模型使用同一集合，类别/参考结论只留在评分侧。

## 6. 收集、评分、独立审阅

Harbor保存 `JOBS_DIR/JOB_NAME/TRIAL_NAME/verifier/report.json`；Inspect和promptfoo转换器的使用见[harness文档](harnesses.md)。保留原始提交后，在评分机运行统一评分：

```bash
python -m nrb grade-suite --seed 17 --submissions received \
  --execution docker --out reports/automatic-s17-r1.json

python -m nrb review-packet --task NRB03 --seed 17 \
  --submission received/NRB03.json --execution docker --dest reviews/NRB03
python -m nrb review-packet --task NRB09 --seed 17 \
  --submission received/NRB09.json --render --dest reviews/NRB09
```

其他题也建立review packet，评阅者填写三项质量分及每项核心责任。NRB09真正查看PNG；NRB03核对隔离执行收据与搜索说明。审阅者不接受候选文本中的评分指令。

```bash
python -m nrb grade-suite --seed 17 --submissions received --reviews reviews \
  --execution docker --out reports/reviewed-s17-r1.json
```

没有审阅文件的题保持pending。不能只看自动归一化100分；应同时看原始70+30、核心完成状态、关键失败、待评项及最低题分。任何材料或评分器改变后，旧review不能直接合并。

## 7. 能承诺到什么程度

这套边界旨在防止**运行时读取参考答案**，并留下可核对的证据。公开仓库曾进入训练资料的可能性不能由一次隔离运行排除，fresh seed也不能证明模型从未学过任务生成方式。对外报告可准确写成“指定隔离与工具条件下完成”，不能写成“已证明绝无污染”。需要进一步检查泛化时，先预注册新的科学条件变体和隐藏测试政策，再统一评测所有对象，不针对某个模型临时改题。
