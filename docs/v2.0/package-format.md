# V2 完整发布包格式

构建命令：

```bash
python scripts/package_v2_release.py --out /absolute/new/output-directory
```

默认种子为17，可用`--seed`指定其他合法种子。脚本只在`--out`内创建产物；如果目标包或总清单已经存在，整次构建在写包前停止，要求新目录。脚本不上传、不更新下载登记、不改写原始素材或历史文件。

## 发布产物

|文件|用途|清单kind|
|---|---|---|
|`NRB-v<version>-<task>-candidate.zip`|所选一题的题面和允许输入|`candidate`|
|`NRB-v<version>-R06-A-candidate.zip`、`...-R06-B-candidate.zip`|R06的两个独立模式|`candidate`|
|`NRB-v<version>-all-candidates.zip`|评测者保存和分发的20题主包|`candidate_collection`|
|`NRB-v<version>-evaluator.zip`|自动评分器、主观评阅协议与环境|`evaluator`|
|`package-manifest.json`|所有ZIP的文件名、路径、大小、SHA-256、kind、task_id、mode、seed|总索引|

默认生成23个ZIP：21个单题单模式包、一个主包和一个验证器包。题号仍为20个，R06的A/B不能当两道题，也不能运行后择优合并。

每个ZIP有一个同名根目录。单题包只包含`<task>.md`、该题白名单中的输入文件、`PACKET.json`、`README.txt`和`MANIFEST.json`。题面统一取`packets.candidate(task, seed)['content']`；主观白名单中的原始题面条目不再重复导出成`TASK.md`。Lean除统一`L01.md`外，包含固定`NRBPrelude.lean`、`lean-toolchain`与空`proofs.template.json`。

主包中的单题位于`tasks/<task>/`；R06位于`tasks/R06/A/`及`tasks/R06/B/`。运行时只把选定的一题、一个模式交给候选。A目录不含参考成片，B目录按白名单包含`assets/R06/reference.mp4`。禁止把主包整体交给某一次候选会话。候选包不含评分模块、参考解、错误控制或作者演示工程。

## 验证器包

验证器包括`nrb_v1/`、`nrb_v2/`中运行所需的Python/JSON/Lean文件，全部`environments/v2/`文件，版本启动脚本、LICENSE、使用说明、主观协议和`tasks/v2.0/*.md`。启动脚本保留在`release/<version>/`，并复制到解压根目录供直接运行。

主观题的允许输入按`candidate_inputs()`指定的原仓库source路径去重保存，供离线生成和验证`input_manifest_hash`。不递归打包整个`sources/`、演示工程或无关媒体。Lean的固定审计文件随环境目录保存。验证器因此也含评阅需要的输入材料，但不能交给候选。

13个自动题的`submissions/<task>/PLACE-SUBMISSION-HERE.txt`标出实际文件名和放置路径；包内不创建假的空提交。未放入实际提交时，批量评测保持`not_submitted`。七个人工题有八份空评阅模板：R06的A/B各一份。模板不带已观察证据或分数，包含当前题面、输入和rubric的身份。

H02的JSON答案校验、主观模板生成与协议评分可在只有Python标准库的离线环境运行。Python/Fortran/Lean候选代码仍需构建相应Docker镜像；分发ZIP不包含镜像本体或Lean编译器安装包。第一次构建需要下载固定依赖，之后候选容器执行断网。

## 两层清单和确定性

`PACKET.json`记录`task_id`、`mode`、`seed`、`packet_hash`及`input_manifest_hash`。其`input_files`必须与`packets.input_manifest()`的文件名、字节数和SHA-256逐项相同；不一致则停止构建。此输入身份不包括README或交付清单。

每个ZIP的`MANIFEST.json`逐文件记录SHA-256和字节数。清单不递归记录自身；外层`package-manifest.json`记录整个ZIP的SHA-256，因此覆盖内层清单。外层路径是本次调用的实际输出位置，不构成ZIP字节身份。哈希提供内容完整性和版本绑定，不提供不可伪造的签名或执行认证。

ZIP条目排序固定，时间戳固定为2026-10-23 00:00:00，权限固定，压缩级别固定，不记录文件系统时间或构建时间。在相同源文件、Git身份、Python/zlib版本和选项下，重复构建得到相同ZIP字节；回归测试直接比较重复构建的SHA-256。改变任何输入或运行时源码都应生成新包和新身份，不覆盖旧交付。

## 兼容选项

`--include-historical`额外生成`NRB-v1.1-historical-candidates.zip`，保留V1题面内容及原有媒体下载约定，不将旧成绩升级为V2。

`--include-python-compat`额外输出`-python-candidates.zip`和`-python-grader.zip`两个旧命名。前者只有八题Python题面，后者明确包含完整20题验证器，用于仍依赖旧命名的分发工具。现有外部链接不会被本地打包命令修改。常规新发布使用`-all-candidates.zip`、`-evaluator.zip`及单题包。
