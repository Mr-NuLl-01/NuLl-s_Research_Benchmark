> V1.1 注：下文记录原 V1.0 历史验证，不是 V1.1 发布通过证据。请查阅 [V1.1 发布说明](../v1.1/release-notes.md) 的实际验证范围。

# V1.0 验证记录

本页记录评分器、参考实现、已知错误候选、框架和隔离的实际检查，不是被测 AI 成绩。版本发布前后的 GitHub Actions 原始报告按精确提交保存；所有 mock、oracle 和自检均标记 `not_model_performance=true`，模型提供商调用数为 0。

## 最终 GitHub CI：8 / 8 作业通过

[运行 39054465838](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/runs/39054465838) 已完成，八个作业全部成功。实际验证的源码提交是 [9d03a3ba33dfe78f6365d78fa50f4da478f683b3](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/commit/9d03a3ba33dfe78f6365d78fa50f4da478f683b3)。

| 实际检查 | 结果与范围 |
| --- | --- |
| V1 Python 3.11 / 3.12 | 每个环境注册 59 项，执行 56 项通过、3 项可选框架检查跳过；另有独立框架作业实际执行对应检查。 |
| 三种子科学自检 | 每个 Python 环境完成 114 次参考／错误候选验证，全部符合预期；两种环境是重复验证，不增加独立任务家族数。 |
| 冻结题包 | 十九份单文件与生成器输出逐字节一致。 |
| Inspect / promptfoo / Harbor schema | 独立框架作业实际执行 14 项检查，全部通过；promptfoo 十个空提交得到 10 个预期失败、0 个框架错误。 |
| Docker 科学执行 | 十个参考实现自动 70/70，八个有明确科学缺陷的候选被相应检查拒绝，18 次结果全部符合预期；实际编译 Fortran。 |
| 候选镜像隔离 | 实际非 root、只读根目录、无主机挂载、不可导入评分器、只含题目和空提交、仅 loopback 网络，所有检查通过。 |
| Harbor 全链路 | 十个实际 trial 全通过；分别转移成果并用独立 verifier 评分。全部自动 70/70，人工分和总分仍为 null，状态均为 `pending_review`。 |
| 历史协议 | V0.2 的两个 Python 作业、框架作业、Docker / Harbor 作业均通过。 |

已将四份 V1 CI ZIP 的 SHA-256 与 GitHub artifact 摘要核对，并保留其关键原始报告。38 份候选标准报告通过内容封印、精确提交和评分器源码指纹复核。详见 [CI 摘要](../../validation/v1.0.0/ci-summary.json)、[原始证据目录](../../validation/v1.0.0/ci/README.md)、[Docker 科学报告](../../validation/v1.0.0/ci/docker/science.json)、[实际隔离报告](../../validation/v1.0.0/ci/docker/isolation.json) 和 [十题 Harbor 报告](../../validation/v1.0.0/ci/docker/harbor-runtime.json)。

这次运行的评分器内容指纹为 `237225fb99bc6d1f0317a9deedd5562a59df6c6a7098a9d2d9b7c7c932d905c7`。实际科学镜像 ID 是 `sha256:cdc7a498cfea7bcc86caaa3dd6bfd795ebc1e4d58bc87095472a71bd62e8c6f5`；Docker Engine 28.0.4，容器内 Python 3.12.15、GNU Fortran 14.2.0。镜像 ID 是本次构建的执行证据，不是承诺未来从浮动基础标签重建出相同字节。

发布收尾的文档／证据提交不改写这些报告中的 `evaluator_commit`。要精确复现本次 CI 身份，应 checkout 上述源码提交；在新的提交上开始模型比较时，应让所有比较对象使用同一新身份，不把不同 commit 的分数混合。

### 保留首次失败与修复

首次源码提交 `12b245b0664dc44f31fe6dbc886f57b489fe11c8` 的 Docker 科学检查已经通过，但隔离探针对一个 `/root` 子路径调用 `Path.exists()` 时遇到 `PermissionError`，提前退出，因而当时没有把隔离或尚未执行的 Harbor 标记为成功。修复使用明确 `lstat()` 分类：不存在、权限拒绝、存在三种状态分开记录；其他异常仍使探针失败。

最终真实探针记录 **15 个不存在路径、1 个权限拒绝路径、0 个存在的禁用路径**。权限拒绝的路径没有被宣称为不存在。[首次失败摘要](../../validation/v1.0.0/first-ci-isolation-failure.json) 保留原提交、运行和 artifact 身份；成功结论只来自修复后的实际 CI。

## 本地结果

发布源码完成后，本地合并测试 **59 项通过、0 跳过**；其中运行了真实 Inspect/promptfoo/Harbor schema 检查。三个种子的 **114 次参考/错误候选验证全部符合预期**。旧协议 **193 项检查通过，5 项可选环境跳过**。安装后的 wheel 从仓库外成功生成十九题，与冻结题面字节一致。

[本地摘要](../../validation/v1.0.0/local-summary.json) · [完整测试日志](../../validation/v1.0.0/local-tests.log) · [114 次执行记录](../../validation/v1.0.0/local-selftest.json)。本地记录的 Git commit 为 null，保留实际源码指纹；发布后的 CI 另记录可证实的精确提交身份。

## 科学与评分验证范围

十道参考实现均已在真实 Python 子进程或 GNU Fortran 编译后的程序中运行。三组科学变体使用种子 0、17、2026。每组有 10 个参考和 28 个有具体科学缺陷的实现，合计 114 个候选/种子执行结果。自动满分的参考仍保留 30 分人工评阅及核心责任未评，不自动获得 100 分或人工完成认证。

独立检查包括解析传输解、有限体积守恒、导热特征模、独立复数光学矩阵、精确线性反应关系、分组随机流重放、Boltzmann 平衡、规范不变性、原始耦合残差、参数剖面曲率、绝对 sigma 缩放、连续制造解细化、周期 Fourier 离散切线、有限差分导数、逆问题恢复、JSON 重启以及随机状态延续。详细科学边界见 [Python题说明](../v1-python-notes.md) 和 [进阶题说明](../v1-advanced-notes.md)。

评分合同的负控制覆盖非法路径别名、文件/目录碰撞、输入修改、整数被浮点替代、NaN/Infinity 输出、超大整数、畸形工作进程结果帧、超时、执行不可用、量表和报告修改、提交字节修改、缺模态观察、分数补偿关键失败等。人工账本测试使用明确标记的合成记录，不能解释为实际看过模型图片或听过模型音频。

科研题完整性检查验证 9 份独立 HTML、19 份冻结题面的对应关系、数据/文献/图像离线内嵌、17 张真实参考图、三篇正文和声明的补充材料范围、准确许可和原始文件字节指纹。没有声称执行过一个模型的 R01–X03 答卷。

## 运行命令

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution trusted --out v1-selftest.json
python -m nrb_v1 export --format files --tasks all --seed 17 --dest regenerated
```

`trusted` 仅执行仓库受控实现。未知候选使用 Docker。冻结检查比较 `regenerated` 与 `tasks/v1.0` 的实际字节，而不只比较文件名。

## 真实框架与隔离门禁

固定框架版本：Inspect AI 0.3.281、promptfoo 0.124.1、Harbor 0.24.0。这些是本版本验证目标，不宣称为最新发布版。

- Inspect：真实 mock 评测，正、负、执行不可用三种情况，完整 canonical report 回收；使用 JSON 日志。mock 显式给零用量，避免下载 tokenizer。不是模型能力结果。
- promptfoo：真实 CLI、十个空提交，预期 10 个断言失败、0 框架错误，完整自动均分 0；程序检查退出状态和原始报告。
- Harbor：用真实 TaskConfig 验证 schema 1.4，候选与验证环境分离；默认导出没有 oracle。运行自检显式在评测者端加入参考成果，检验真实生成/转移/评分链路。
- Docker：科学镜像内执行十个参考和八个指定科学错误候选，实际编译 Fortran；记录镜像 ID、编译器与依赖版本。
- 隔离：构建真实候选镜像，检查无评分器/仓库/主机挂载、非 root、只读根目录、断网和题包完整性；Harbor 验证器另检查 root 独占评分路径与日志权限。

本地开发环境没有 Docker，真实 Docker/Harbor 由上面的 GitHub Actions 运行提供证据。隔离探针的实际镜像检查范围是 C01；十题的成果转移、独立验证器和权限检查由 Harbor 全链路另行完成。没有验证真实推理 API 白名单或任意宿主 CLI 的隔离，也没有把静态 schema 检查当成容器运行。

## 证据解释限制

已知错误实现产生分数梯度，只说明验收能发现这些已知缺陷。十个题族的规模不足以推导稳定的所有模型总排名；种子变体也不是新的独立研究领域。没有执行商业模型比较，因此目前不提供模型榜单、置信区间或“某模型最适合你”的结论。

C03 当前小网格压力案例验证隐式稳定性，不能单凭时间测量证明 O(n) 渐近复杂度。C09 验原始离散方程，不主张一般非线性系统的全局唯一性。R05 两项复现是明确限定的合成方法演示，并未恢复三篇论文所有原始实验或完整软件。
