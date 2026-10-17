# v0.2 验证记录

本页只记录实际完成的验证，不包含真实模型能力成绩。v0.1 的代码与证据保留在历史commit及[原始验证说明](validation-v0.1.md)，不能用旧版CI代替v0.2结果。

## 本地已完成的验证

日期2026-10-17，Python3.12.14/Linux。代码自检只执行仓库自己的参考程序和错误控制。冻结评分内容指纹：

```
1b872d660f0a56f05c9ec390a90a150bed78d9af918efa81c5a8fcfb0f4e7cba
```

本地导入工作区没有Git HEAD，回执如实保留 `evaluator_commit=null`；没有把尚未发布的commit填成实际运行来源。远端CI检出固定commit后，会在其报告内记录真实commit。内容相同仍不能把不同commit身份混入一次比较。

| 核验 | 实际结果 | 支持范围 |
|---|---|---|
| 完整回归 | **188项，184通过，4因可选框架依赖缺失跳过** | 科学/数值、候选错误行为、核心完成、报告身份、真实本地渲染与离线适配器契约 |
| 3个seed × 10题selftest | 30个oracle均70/70，empty均0/70；哈希可复现，NRB03搜索实际执行通过 | 程序和变体自检，不是模型能力或质量30分 |
| 原生空提交runner | 10次真实子进程完成，自动均分0，完整质量总分null | 题包、进程、提交归一化和统一汇总实际走通 |
| native/JSONL/promptfoo/Harbor导出 | 四种格式均实际生成10题 | 导出成功；框架实际执行另列 |
| NRB09参考与7种负控制 | **8张实际渲染，逐张打开查看**；Inkscape1.2.2，1020×612、144DPI、180mm等效 | LLM provisional检查，非人工审阅或物理屏幕校准 |
| 本地候选隔离探针 | 静态材料检查通过；实际Docker执行为unavailable，退出2 | 本地没有Docker，不能写成容器隔离已通过 |

记录：[完整回归](../validation/v0.2.0/unit-tests.txt)、[selftest](../validation/v0.2.0/selftest.json)、[原生runner](../validation/v0.2.0/native-smoke.json)、[导出](../validation/v0.2.0/exports.json)、[本地隔离探针](../validation/v0.2.0/local-isolation.json)。

## 实际看图证据

[完整渲染材料](../validation/v0.2.0/render-controls/)保留SVG、提交、PNG、渲染收据、材料哈希和独立[看图记录](../validation/v0.2.0/render-controls/reviewer-results.json)。生成器的空审阅模板仍是unassessed，实际看图结论单独记录为LLM provisional。

| 图 | 自动分 | 实际可见问题与结论 |
|---|---:|---|
| oracle | 70 | 三个面板及科学内容可读，provisional pass |
| minimalpoint | 45 | 数据/残差点几乎消失，fail |
| zerostroke | 60 | 模型曲线消失，fail |
| whitecover | 70 | 整图空白，必须在核心看图责任失败 |
| emptydiagram | 65 | 示意部件图形缺失，fail |
| offcanvastext | 65 | 标签和单位在画布外，fail |
| nestedopacity | 55 | 数据仍部分可见但明显变淡，有效0.25低于公开暂定0.30，fail |
| emptymarker | 65 | 位移线无箭头头部，fail |

尺寸/opacity阈值是针对正常参考图与极端反例的工程标尺，不宣称是通用感知或期刊标准。未来候选仍要按其真实提交单独渲染和审阅。

## 科学与评分负控制

- NRB01–03的多个seed按最低9位有效数字舍入后仍通过；旧六位热时间常数例子与新约定被分别测试。
- NRB03独立有理数公式、最优/次优并列向量、严格阈值边界和极小目标差均被实际核验。必交搜索代码错误时，即使数值70也核心失败；selftest亦断言执行结果。
- NRB04/05新增80/78个候选行为案例，包含只缺对应处理的错误实现；50分行为总权重保持不变。
- NRB06用随机数接口替身直接核验传入sigma，另由公开CSV独立重算WLS；全零协方差/PSD、漏相关项等仍失败。
- NRB08自动70+质量0/0/10仍为原始80，但缺两个证明时failed/false；NRB10坏英文、NRB09白遮挡也不能补过。
- 已有分数、审阅、执行收据、协议资格或完成状态被改动后，附加审阅、汇总与比较不能沿用原封存身份。评分源码改变而题面不变时，内容digest确实改变。

具体回归见[tests](../tests/)、[科学任务说明](task-science-notes.md)、[数值任务说明](task-numerical-notes.md)和[评分规范](scoring.md)。

## v0.2 外部框架及容器CI

工作流设置了Python3.11/3.12核心测试；固定版本Inspect mock、promptfoo空provider、Harbor schema；真实CairoSVG渲染控制；真实Docker下的NRB03/04/05、候选镜像无答案/无网络探针，以及Harbor十题oracle与独立verifier。

**此段在发布时仍待本次固定commit的远端结果，不能以v0.1绿灯或本地跳过代替。** 实际日志、安装版本、镜像与执行回执由[GitHub Actions](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml)保留；观察到结果后在此追加固定run与commit证据。

## 仍未得到的证据

本次未调用商业模型API。真实模型分数、强弱配置区分度、排序稳定性、双人评分一致性、在线API白名单在所有后端的执行情况，以及完整跨平台支持仍需相应实测。隔离探针只证明其测试的实际离线镜像；公开seed与答案可能被训练学习，不能因此宣称绝无污染。
