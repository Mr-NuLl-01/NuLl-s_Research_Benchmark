# NuLl's Research Benchmark · V2.0

**20 道题已完整实现：8 Python、3 Fortran、1 Lean、6 主观科研、2 聊天端。13 题自动评分，7 题按证据量表评阅。**

[使用指南](docs/v2.0/usage.zh-CN.md) · [单题材料](tasks/v2.0/) · [设计与来源](docs/v2.0/design.zh-CN.md) · [验证记录](docs/v2.0/validation.md) · [下载清单](docs/v2.0/downloads.json) · [网页源码](web/)

本次从第一轮提交 `be2f5c8` 接续，完成其余 12 题，保留八道 Python 的科学任务、V1 原题、原始材料和历史记录。题目使用公开问题、可核验文献与合成数据；没有把作者控制或界面测试记成模型成绩。难度为设计先验，尚未做真实模型成功率标定。

## 完整题库

|题号|任务|设计难度|评分|
|---|---|---:|---|
|[P01](tasks/v2.0/P01.md)|仪器 CSV 清洗、单位与测量不确定度|1/5|自动|
|[P02](tasks/v2.0/P02.md)|独立组与分层 bootstrap 模型比较|2/5|自动|
|[P03](tasks/v2.0/P03.md)|修复分层导热有限体积求解器|3/5|自动|
|[P04](tasks/v2.0/P04.md)|被动吸收多层薄膜的稳定光学传输|4/5|自动|
|[P05](tasks/v2.0/P05.md)|带源项时间表的刚性反应自适应积分|5/5|自动|
|[P06](tasks/v2.0/P06.md)|带独立基线与幅度的逆热扩散：剖面似然与退化诊断|4/5|自动|
|[P07](tasks/v2.0/P07.md)|二维异质各向异性椭圆方程：守恒通量与制造解|4/5|自动|
|[P08](tasks/v2.0/P08.md)|修复反应扩散反演流水线：切线导数、守恒、重启和参数自举|5/5|自动|
|[F01](tasks/v2.0/F01.md)|Fortran 非均匀网格守恒漂移扩散|3/5|自动|
|[F02](tasks/v2.0/F02.md)|Fortran 隐式反应扩散与源汇账本|4/5|自动|
|[F03](tasks/v2.0/F03.md)|Fortran 自洽漂移扩散–Poisson|5/5|自动|
|[L01](tasks/v2.0/L01.md)|已有守恒结论的 Lean 形式化|4/5|自动|
|[R01](tasks/v2.0/R01.md)|参考学习与可编辑科研 SVG|4/5|证据量表|
|[R02](tasks/v2.0/R02.md)|小差异、宽动态范围与删失数据绘图|4/5|证据量表|
|[R03](tasks/v2.0/R03.md)|保持事实与证据强度的英文润色|3/5|证据量表|
|[R04](tasks/v2.0/R04.md)|从图版与数据撰写结果和讨论|4/5|证据量表|
|[R05](tasks/v2.0/R05.md)|文献证据综合与有界方法复现|5/5|证据量表|
|[R06](tasks/v2.0/R06.md)|视频修改与参考视觉重建|4/5|证据量表|
|[H01](tasks/v2.0/H01.md)|聊天端单 HTML 科研工作台|4/5|证据量表|
|[H02](tasks/v2.0/H02.md)|聊天端有回流网络的定量推理|5/5|自动|

R06 的 A/B 是预先选定的两种输入条件，合计一道题。R05 合并旧精读与 mini-review，保留三文综合与两项有界复现。H02 可在聊天端交付 JSON，由网页直接重新求解、验证和评分。

## 使用

1. 从网页的 Google Drive 入口下载**单题、单模式候选包**，在新会话中交给模型。完整合集由评测者保管，不把评分器、参考解或整个仓库交给候选。
2. Python 提交 `solution.py`；Fortran 提交 `solution.f90`；Lean 提交 `proofs.json`；H02 提交 `answer.json`。各题的文件清单和明确算法约束以题面为准。
3. 解压 `NRB-v2.0.0-evaluator.zip`。首次运行 `Build-Environment` 建立本地评测依赖和两个候选容器，然后把提交放入相应 `submissions/<题号>/`，运行 `Grade-Results`。
4. 程序题在网页导入单题报告；H02 可直接粘贴答案；主观题在网页逐项评级并记录观察。保存后可查看证据、导出备份与同条件比较。

命令行从源码使用：

```bash
python -m pip install -e .
docker build -t nrb-v2:local -f environments/v2/Dockerfile .
docker build -t nrb-v2-lean:local -f environments/v2/LeanDockerfile .
python -m nrb_v2 grade --task F02 --source submissions/F02/solution.f90 --out results/F02.json
python -m nrb_v2 grade --task L01 --source submissions/L01/proofs.json --out results/L01.json
python -m nrb_v2 grade --task H02 --source submissions/H02/answer.json --out results/H02.json
python -m nrb_v2 batch --input submissions --out-dir results/run01
```

宿主 Python ≥3.11，NumPy 2.3.5；候选 Python 容器固定 Python 3.12 / NumPy 2.3.5 / SciPy 1.17.0，Fortran 记录实际 gfortran 版本与编译参数，Lean 固定 4.19.0。普通候选代码通过容器执行，H02 仅验证 JSON，不执行提交代码。下载包的系统启动脚本会安装局部虚拟环境，具体操作见使用指南。

## 成绩的含义

自动题满分100，按固定检查权重归一化。程序题不再设人工分；实际失败保留部分分或0分，环境不可用为 `null`。Lean 核对六个固定命题的真实类型、实际内核检查与传递公理依赖；受限证明语言拒绝 `sorry`、额外公理及受禁止的求值入口。

主观题从0–4级锚点按维度权重计算，再应用有证据的分数上限。未观察不补零；LLM 暂评保留独立身份。R06 输入模式违规不进入有效比较。题面、实际附件、量表和提交身份分别绑定，不能只改总分。

本地自动报告可编辑，内容指纹不是执行认证签名。网页对代码报告验证完整检查合同、重算分数；对 H02 重新验算答案；对主观记录重新计算量表分。没有承诺网页已经执行上传的源码。

完整20题均分只在两组或以上模型对同样20题有可比记录时生成；否则显示共同子集与覆盖。逐题对齐实际镜像、预算、模式、评阅人，默认使用首次作答，冲突重复不自动择优。第一轮 V2 报告按原版本读取，V1 手工分保留历史身份。

## 维护

```bash
python -m unittest discover -s tests_v2 -v
python scripts/v2/check_round2.py contracts --out contracts.json
python scripts/v2/check_round2.py controls --execution trusted --seeds 0,17,2026 --mutants representative --out native-controls.json
node web/checks.cjs
python scripts/package_v2_release.py --out exports/v2.0.0
```

`trusted` 仅供已审读的作者参考与错误控制使用。实际 Docker 验证、浏览器操作和发布状态以 [validation.md](docs/v2.0/validation.md) 与对应提交的 Actions 为准。旧 `nrb`、`nrb_v1`、兼容工作流和材料保持；[第一轮验证](docs/v2.0/round1-validation.md)单独保留。

代码与原创合成题目遵循 MIT；第三方图像、文献与视频保留各自许可。Google Drive 继续使用既有授权范围；记录仍保存在当前浏览器并可导出恢复。
