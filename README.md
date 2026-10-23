# NuLl's Research Benchmark · V2 第一轮

**版本 `2.0.0-rc.1`：8 道 Python 已开放，全部自动评分；完整20题结构已确定，其余12题在第二轮完成。**

[候选题面](tasks/v2.0/) · [使用指南](docs/v2.0/usage.zh-CN.md) · [题库设计](docs/v2.0/design.zh-CN.md) · [验证范围](docs/v2.0/validation.md) · [第二轮交接](docs/v2.0/round2-handoff.md) · [网页源码](web/)

本轮程序题只要求完整的 `solution.py`。离线验证器实际执行程序，给出自动百分制分数、逐项检查和错误原因，没有人工30分或确认门槛。网页导入本地JSON报告，核对发行版本与检查清单后重新计算分数，保存运行条件，并比较相同条件下的结果。

材料使用公开经典问题和原创合成数据，不使用个人未发表研究、私有代码或真实实验数据。设计难度尚未用真实模型成绩标定；参考程序、故意错误程序和界面测试都不计为模型成绩。

## 本轮八题

|题号|任务|设计难度|主要区分点|
|---|---|---:|---|
|[P01](tasks/v2.0/P01.md)|仪器CSV清洗、单位与测量不确定度|1/5|数据身份、重复记录、单位、不确定度量级|
|[P02](tasks/v2.0/P02.md)|独立组与分层bootstrap|2/5|统计单位、层与组权重、确定性重采样|
|[P03](tasks/v2.0/P03.md)|修复分层导热有限体积求解器|3/5|非均匀网格、界面热阻、隐式推进、能量账本|
|[P04](tasks/v2.0/P04.md)|被动吸收多层薄膜的稳定光学传输|4/5|复数分支、s/p偏振、能流、极厚吸收层|
|[P05](tasks/v2.0/P05.md)|刚性反应自适应积分|5/5|规定算法、拒步回滚、源项事件、浮点停点|
|[P06](tasks/v2.0/P06.md)|逆热扩散、剖面区间与退化诊断|4/5|变量投影、绝对sigma、端点附近内部极小值|
|[P07](tasks/v2.0/P07.md)|二维异质各向异性椭圆方程|4/5|守恒面通量、方向性、边界积分、独立残差|
|[P08](tasks/v2.0/P08.md)|修复反应扩散反演流水线|5/5|离散切线、协方差、JSON重启、重拟合bootstrap|

八题统一允许 Python 3.12 标准库、NumPy 2.3.5、SciPy 1.17.0，仍须遵守各题明确的算法合同。P06修复旧参考遗漏端点邻域内部极小值的问题；P06的数值秩条件、P07的实际残差阈值均已公开写入题面。旧 `nrb_v1` 和冻结题包保持原样。

## 使用

1. 从网页的Google Drive链接下载单题候选文件，在新会话中交给模型。不要把评分器、参考解或整个仓库交给候选。
2. 下载并解压 `NRB-v2.0.0-rc.1-python-grader.zip`，将代码放入 `submissions/P01/solution.py` 等相应目录。
3. 首次运行 `Build-Environment` 脚本构建Docker环境；之后运行 `Grade-Results`，打开新结果目录的 `index.html`。
4. 将单题JSON导入网页，核验后填写模型与运行条件、保存记录。记录可导出备份和恢复。

命令行也可使用仓库：

```bash
python -m pip install -e .
docker build -t nrb-v2-python:local -f environments/v2/Dockerfile .
python -m nrb_v2 grade --task P04 --source submissions/P04/solution.py --execution docker --seed 17 --out results/P04.json
python -m nrb_v2 batch --input submissions --out-dir results/run01 --execution docker --seed 17
```

Windows也可用 `py -3`，macOS/Linux也可用 `python3`。解压包内提供对应系统的启动脚本，详细操作见[使用指南](docs/v2.0/usage.zh-CN.md)。

## 分数与比较

- 满分100，按 `100 × 已通过检查权重 / 全部检查权重` 计算。基础、科学、边界相对权重为20/30/20，没有额外人工分。
- `passed` 表示全部检查通过；`failed` 保留实际部分分或0分；环境不可用为 `unscored/null`。
- 完整八题均分只在8题均有有效分数时生成，否则显示覆盖数和已评分子集均分。完整20题成绩尚不生成。
- 网页校验报告身份、逐项检查和分数一致性。可编辑JSON和内容哈希不构成不可伪造的执行认证。
- 比较时固定版本、种子、工具、环境、预算与尝试规则。作者 `trusted` 自检报告单独标记，不进入模型比较。

## 完整20题与第二轮

`8 Python + 3 Fortran + 1 Lean + 6 主观科研 + 2 聊天端 = 20`。

第二轮完成F01–F03、L01、R01–R06、H01–H02。新增视频A/B合并为R06的两种预先声明模式；旧精读与mini-review合并为R05。H01为离线单HTML科研工作台；H02为有回流网络的定量推理与可验证反例。这12题现在仅为计划，不宣称已完成评分器。

## 维护与历史

```bash
python -m unittest discover -s tests_v2 -v
python -m nrb_v2 selftest --tasks python --seeds 0,17,2026 --include-mutants --execution trusted --out controls.json
node web/checks.cjs
```

`trusted` 只适用于已经审读的仓库控制程序。未知候选使用Docker。新CI包含实际Docker中的八题参考、错误控制和隔离探针；结果以对应提交的工作流为准，不能把配置当作已经通过的证据。

V1.1历史说明：[中文](README.zh-CN.md) · [English](README.en.md) · [原题](tasks/v1.0/)与[视频材料](tasks/v1.1/) · [旧使用说明](docs/v1.1/usage.zh-CN.md)。旧评分不与V2混比；旧网页记录和题包保留。原 `nrb` 与 `nrb_v1` 命令仍可使用。

代码与原创合成题目遵循MIT；第三方文献、图像和视频保留各自许可。请引用精确commit、版本与评分器指纹。下载清单中的Drive引用不授予公开访问权限。
