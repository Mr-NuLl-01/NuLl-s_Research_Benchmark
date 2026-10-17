# V1.0 原始 CI 证据

来源：[GitHub Actions 39054465838](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/runs/39054465838)，源码提交 `9d03a3ba33dfe78f6365d78fa50f4da478f683b3`。八个作业全部成功。此目录是评测者证据，不属于候选题包；候选仅接收 `tasks/v1.0` 中的一道题。

这些是参考程序、特定科学错误候选和框架 mock 的基础设施检查，模型提供商调用数为 0，没有模型能力成绩。Harbor 参考提交的人工分仍未评，不能解释为 100 分或人工完成认证。

| 文件／目录 | 内容 |
| --- | --- |
| [run.json](run.json)、[jobs.json](jobs.json) | 精确运行身份、八个作业与各步骤状态。 |
| [artifacts.json](artifacts.json) | 八份 GitHub artifact 的 ID、ZIP 内容摘要、到期时间，以及四份 V1 ZIP 的实际下载校验标记。 |
| [extracted-files.json](extracted-files.json) | 所保留原始文件在 ZIP 中的准确成员名、保存路径和 SHA-256。 |
| [core-python-3.11](core-python-3.11/)、[core-python-3.12](core-python-3.12/) | 每环境 114 次科学自检、单元测试原日志、Fortran 版本。 |
| [framework](framework/) | 14 项实际框架测试日志、依赖版本、promptfoo 十空提交报告和标准评分报告。 |
| [docker/science.json](docker/science.json) | 18 次实际容器科学检查，含全部候选标准报告、镜像和编译器身份。 |
| [docker/isolation.json](docker/isolation.json) | 实际构建上下文、容器配置、路径／权限／网络探针和清理结果。 |
| [docker/harbor-runtime.json](docker/harbor-runtime.json) | 十个真实 Harbor trial 的检查与全部标准报告。 |
| [docker/harbor-schema.json](docker/harbor-schema.json) | 固定 Harbor 0.24.0 / schema 1.4 的十题配置检查。 |
| [docker/image.json](docker/image.json)、[docker/docker-version.txt](docker/docker-version.txt) | 实际镜像与 Docker 版本原始记录。 |

归档只保留与结论有关的原始报告，未复制 ZIP 中重复的导出评分源码、oracle 文件、缓存和临时数据库。完整 ZIP 在 GitHub artifact 保存期限内可下载；其 SHA-256 已核验。所保存的报告字节未改写，CI 运行路径仍保留原值。

后续文档提交与这次被测源码提交可能不同。所有原始报告继续保留原 `evaluator_commit` 和内容指纹；不能将旧报告重新贴上新提交标签。详细结果及首次隔离探针失败修复见 [验证说明](../../../docs/v1/validation.md) 和 [机器可读 CI 摘要](../ci-summary.json)。
