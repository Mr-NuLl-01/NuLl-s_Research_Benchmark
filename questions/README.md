# 完整 10 题 · seed 0

此目录提供可直接阅读的完整题面、合成输入及质量量表。每个 `instruction.md` 已内嵌全部文本输入；同目录还提供原始文件，便于工具读取。

请只把单题目录或新导出的题包交给被测 agent。本仓库其余目录含评分器和参考答案，不能暴露给候选系统。正式比较建议生成新的种子变体；公开种子不构成无污染保证。

| ID | 任务 | 必需交付物 |
|---|---|---|
| [NRB01](NRB01/instruction.md) | 版本冲突下的证据与贡献审计 | reasoning.md |
| [NRB02](NRB02/instruction.md) | 热响应中的参数退化与判别实验 | reasoning.md |
| [NRB03](NRB03/instruction.md) | 有限预算下的鲁棒校准设计 | reasoning.md, solve.py |
| [NRB04](NRB04/instruction.md) | 非均匀网格上的守恒热扩散修复 | reasoning.md, solution.py |
| [NRB05](NRB05/instruction.md) | 自适应积分器的回滚与终止 | reasoning.md, solution.py |
| [NRB06](NRB06/instruction.md) | 传感器校准、噪声谱与相关不确定度 | reasoning.md |
| [NRB07](NRB07/instruction.md) | 重复测量下的数据泄漏与分组评测 | reasoning.md |
| [NRB08](NRB08/instruction.md) | 仿射收缩的证明、反例与误差证书 | reasoning.md |
| [NRB09](NRB09/instruction.md) | 从合成振子数据制作可编辑科研图 | figure.svg, caption.md |
| [NRB10](NRB10/instruction.md) | 交接证据审计与保守英文修订 | audit.md, revised_excerpt.md, reproduce.md |

每题自动 70 分，三项独立质量审阅各 10 分。答题协议和自动核验对象见题面；分数含义、缺失处理及质量审阅流程见 [评分方法](../docs/scoring.md)。

```bash
python -m nrb export --format native --seed 17 --dest exports/native-s17
```
