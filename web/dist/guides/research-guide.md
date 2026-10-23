# 科研与多模态任务评测指南（V1.0）

本指南面向使用和复核 NRB V1.0 的研究人员，解释六道必做科研题 R01–R06 与三道可选能力题 X01–X03：实际要做什么、哪些证据能够支持评分、哪些结论仍然超出题目范围，以及怎样保留可复核的评阅记录。各题均为一个完整候选 HTML；需要的文字、合成数据、实际参考图和指定论文正文已内嵌，无需候选联网或克隆仓库。下载后应打开完整 HTML，不能用 GitHub 预览截图代替题包。

**能力轨道应分别报告。** 十道代码题、六道科研题和可选多模态题具有不同交付和评阅条件。R/X 每题由人工量表给出 100 分，不采用代码题的“自动 70 分＋质量 30 分”结构。可选题缺少音视频能力时，不能混入科研六题均分，更不能把“未能评阅”写成“质量为零”。

本指南列出的任务、权重、必需文件和原始锚点来自 `nrb_v1.research.tasks()`。中文锚点作忠实解释；每题折叠区保留对应英文机器源原文，便于发现翻译歧义及核对版本。它们是评分条件，不是本题科学答案、优秀范文或隐藏结论。候选应收到单个候选题文件；开发仓库、评阅台账与其他候选的成果不能成为正式作答上下文。

## 1. 为什么这些题能够检验日常科研能力

### 1.1 从实际论文图学习，需要完成一次科学迁移

R01 提供三幅完整、可离线阅读的实际论文参考图及原始图注。只写“配色统一、版式简洁”不能说明候选读过参考图，也不能说明其理解图为何这样设计。候选需要指出具体可见选择，解释其服务的比较关系，再决定哪些能够迁移到新的实验单位、配对关系、动态数据与目标尺寸。参考图可以既有值得学习的选择，也有在新数据上不适用的条件。

这一区分检验的是“参考—科学任务—视觉决策”的连接。照搬一张漂亮图的颜色、布局或图例，可能同时照搬了不适合新问题的基线、样本汇总或信息省略。评分因此同时检查科学编码、参考学习、尺度、不确定度、最终尺寸及可编辑性；不以审美印象代替数据保真，也不以可编辑 SVG 的机械检查代替真正看图。

### 1.2 坐标尺度是科学比较的一部分

R02 同时包含基线附近的小差异、大动态范围正值，以及带负数、零和左删失的空白扣除记录。它们对应不同问题：关心绝对改变量还是比例、需要保留何种基线上下文、零是否是合法估计、某一行究竟有数值还是只有上界。统一套用线性、对数或“自动优化”规则都不能独立回答这些问题。

高质量提交逐轴说明映射、范围、零点含义和取舍，并使用另一种尺度或比较方式作为诊断。使用对数本身没有加分；有理由的线性坐标、明确标示的放大／偏移或配对差值也可能适合具体问题。删失记录缺少点估计，与实测零、负估计以及一般缺失不同。为了让图能画出来而静默删除、取绝对值、截断或替换观测，会直接改变科学证据。

### 1.3 事实保真的文字编辑，比“像人写的”更可审计

R03 不使用 AI 检测器。它要求候选在改善英语句法、段落推进和具体措辞时，保持数量、实验设计、配对、独立单位、不确定度缺口及时间边界。对作者草稿中的显著性、机制或部署主张，需要依据给定事实记录决定保留、澄清、删除为无支持内容，或向作者查询，并留下逐主张台账。

这种评测能够区分两种常见的表面流畅：一种通过删掉限定和数据获得简洁，另一种通过加入“合理”实验背景获得完整。两者都可能损害科学记录。高分要求语言自然与事实保真同时成立，并清楚承认编辑并不等于独立验证了实验结果。

### 1.4 论文写作和精读，需要跨产物的一致证据链

R04 要求从真实内嵌的输入图和表中写出结果与讨论，不能仅把粗略笔记改写成流畅段落。定量陈述应能回到计算和面板位置，讨论应区分观测、推断和假说，并提出能区分替代解释的后续测量。

R05 把三篇互补论文作为封闭阅读集：候选需要辨认文章类型、证据单位、方法细节、显式论证和自己重建的隐含前提，随后给出可实施计划与有边界的部分代码复现。R06 再要求将这些来源组织成一个科学论证，并使正文、证据 SVG、比较表、主张台账和书目相互一致。流畅摘要、真实 DOI 或可运行代码，单独都不足以证明这些连接成立。

这些题具有设计上的区分目的；目前没有在本指南中宣称其难度已用真实模型标定、评分者一致性已经验证，或某个模型已取得某个成绩。真正的区分度与复评可靠性需要后续盲测数据支持。

## 2. 统一评分规则与核心责任

每题有五个维度，权重合计 100。每维取整数等级 0、1、2、3、4；表中 0、2、4 是锚点，1 或 3 表示位于相邻锚点之间的实际表现，需要写明为何处在中间。该维得分为：

$$
S_i = w_i\,r_i/4,\qquad S=\sum_i S_i.
$$

这里的 4 是最高等级；“0 级”表示评阅证据支持该低表现，不表示没有观察。尚未看到、打不开、听不到或评阅者不具备相关能力时，应保留未评状态和理由，不能填 0 来凑齐总分。当前附加评阅流程要求各维均有有效等级、证据和理由后才形成完整质量分；不完整评阅应保留待评台账。

三个核心责任单独记录在 `essential_review` 中，实际值使用 `pass`、`fail`、`unassessed`。通过或失败均应说明证据与科学理由。高总分不能补偿核心责任失败；同一问题也不应在加权分之外再次追加任意分数罚款。数值分保留部分表现信息，核心状态回答是否完成了不可替代的任务责任。

必须区分以下情形：

| 情形 | 合理记录 | 不应写成 |
| --- | --- | --- |
| 已启用任务，具备生成／评阅条件，但候选没有提交必需文件 | 缺交证据、相关维度表现与核心责任失败 | 无理由地标为环境不支持 |
| 文件存在，但评阅者无法打开或无法感知所需模态 | `unassessed`、具体原因、受影响维度／责任、待补观察 | 主观推测的低分或通过 |
| 可选任务的生产或评阅模态不支持，事前未能启用 | `capability.json` 中的 `unavailable` 和具体原因；从启用题目的分母排除 | 静默计零、假装完成或纳入科研六题均分 |
| 缺少可选编码器／某项可选测量工具，但核心音频可交付 | 对实际音频评阅，并透明记录这一局部工具缺口 | 将整项音频能力自动判为不存在 |

## 3. 必须实际看图、看视频、听音频

### 3.1 观察文件与字节身份绑定

文件存在、SVG 可解析、MP4 有正确扩展名、WAV 能读取元信息，均不等于内容已被观察。评阅者需要打开候选实际提交的图，在指定尺寸检查；视频需要实际观看画面与时间进程，音频需要实际收听。交互 HTML 还需要操作关键状态，验证可见数据、数量和汇总的变化。仅根据生成脚本或候选自述，不能给出视觉、节奏、听感或可达性通过结论。

`modal_observation_artifacts` 指定必须实际观察的输出文件。观察台账至少包括：精确文件名、对应提交字节的 SHA-256、实际动作（viewed／watched／listened／interacted）、评阅者、具体查看／收听范围和发现。以下只示范记录字段含义，不是当前某个成果的真实检查记录，也不预先证明门槛通过：

```json
{
  "artifact": "figure.svg",
  "sha256": "<实际提交字节的SHA-256：64个十六进制字符>",
  "action": "viewed",
  "performed": true,
  "evidence": "<实际以180 mm宽度查看整图与全部面板后的具体发现、影响和未核验范围>"
}
```

`review-packet` 会按任务的观察文件列表预填上述字段，初始 `performed:false`、`evidence` 为空。真实观察后才能置为 `true` 并填写具体发现。`attach-review` 核对精确字段、文件名、提交哈希及指定动作；声称已执行时必须有实际文件和非空证据。任何核心责任填 `pass` 都要求该题声明的全部输出模态已观察。不能擅自改变模板的权重、任务标识、必需责任或绑定哈希。程序可以拒绝缺记录、错字节或错动作，但一个勾选框仍不能证明人类真实打开过文件；观察者必须诚实报告。哈希用于确认“评阅的正是这些字节”，不证明科学正确性、原创性或听感质量。文件改动后需更新绑定并重新检查受影响部分，不能沿用旧文件的观察结论。

### 3.2 输出观察与输入阅读都不能省略

| 任务 | 必须实际观察的输出 |
| --- | --- |
| R01 | `figure.svg`、`figure.png` |
| R02 | `figure.svg`、`figure.png`、`alternative-scale.png` |
| R03 | 无图像输出；完整阅读编辑稿、台账和作者查询 |
| R04 | 无生成图像输出；必须实际阅读内嵌输入 Figure F1 的两个面板，再核对文字和计算 |
| R05 | `paired-demonstration.svg`、`colour-diagnostic.svg` |
| R06 | `evidence-map.svg`、`evidence-map.png`、`comparison.html` |
| X01 | `dashboard.html`，并实际操作筛选、比较、尺度、重置及导出 |
| X02 | `explainer.mp4`，同时检查字幕文件与逐字稿的同步／完整性 |
| X03 | `sound-bed.wav`，同时核对提示表与实际声音时间关系 |

R01 还需真正看三幅内嵌参考图；R05/R06 需阅读相应正文、图注和要求的补充方法段。纯文本提取可辅助定位，不能代替对二维布局、图形关系、时间进程或声音的观察。若候选环境只能读文字而看不到内嵌图，应单列文字能力轨道和材料可见性限制，不能与完整多模态轨道作无条件横比。

## 4. 逐题范围、交付与量表

建议时间描述任务规模，不是额外自动扣分条件。难度为 1–5 的设计先验。各题独立给材料；不能把 R03 的作者批准数值拿到另一题重算，或把两个不同实验的设备编号误连接。

### R01　从实际图中学习并制作科学 SVG

设计难度 **4/5**；建议 **60 min**；轨道：**必做科研**。

**实际工作。** 从 P1 图 2、P2 图 7、P3 图 3 中学习，制作三面板的原创新图：实验协议／测量关系、配对前后数据、六条瞬态响应。用 350–550 词英文设计说明解释从每幅实际参考图学到什么、为何采用或改变；另交 160–240 词图注、预览及针对性检查。配对实验与瞬态实验的设备身份不能跨表连接。

**真正评测的能力。** 分清实验单位、配对与批次；让小差异及其基线上下文可读；把参考图的设计逻辑迁移到新问题；在 180 mm 宽度保留可读文字和可单独编辑元素。没有提供物理机制或显著性检验，不能凭图的专业观感补造这些内容。SVG 文件名正确但整张图被栅格截图替代，不能满足可编辑核心责任。

**必需文件（精确名称）。** `figure.svg`、`figure.png`、`caption.md`、`design-note.md`、`source.zip`、`review.md`。

`source.zip` 内保留所选工具的自然可编辑格式和本地 README／再生成说明；不能只压入最终预览代替源项目。

**核心责任。**

- `data`：三个原创新面板忠实使用给定实验与数据，不编造科学内容。
- `refs`：设计说明实质性讨论三幅实际给定参考图。
- `vector`：交付可打开、含可修改文本与可独立编辑科学元素的 SVG。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R01-A` 科学编码与数据保真 | 30 | 数据、配对关系或单位被实质性编造或丢失。 | 大多数数值已表达，但仍存在一个实质性的实验设计或单位歧义。 | 全部给定观测、配对关系、批次身份及不同实验的独立单位均被忠实编码；汇总量有定义和依据。 |
| `R01-B` 从三幅实际参考图中学习 | 20 | 没有分析实际参考图，或用复制参考作品替代新图。 | 三份参考均被提及，但分析浅显，或采用的设计与新数据缺少联系。 | 针对三幅参考中具体可见的设计选择进行批判性分析，并连贯地适配到新的科学比较。 |
| `R01-C` 尺度、比较与不确定度判断 | 20 | 坐标或不确定度表达实质性歪曲科学比较。 | 尺度看似合理，但比较关系、基线或不确定度定义不清楚。 | 尺度选择同时支持微小变化与基线上下文；比较对象、样本单位及不确定度含义明确且可辩护。 |
| `R01-D` 构图、字体与可达的视觉身份 | 15 | 重要标签或数据不可读。 | 放大时可以读，但在目标尺寸仍有拥挤或对象身份不一致。 | 在 180 mm 宽度下读序清晰，身份编码一致，有可达的冗余编码，字体可读。 |
| `R01-E` 可编辑交付、图注与针对性视觉审查 | 15 | 缺少必要矢量／源文件，或没有有意义的图注。 | 有 SVG 和预览，但可编辑性、再生成方式或检查证据不完整。 | 可修改文本、独立元素、可再生成源文件、自足图注及具体检查证据共同支持后续复用。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R01",
  "rubric": [
    {
      "id": "R01-A",
      "name": "Scientific encoding and data fidelity",
      "weight": 30,
      "anchors": {
        "0": "Data, pairing or units are substantially invented or lost.",
        "2": "Most values are represented, but one material design or unit ambiguity remains.",
        "4": "All supplied observations, pairing, batch identity and distinct experimental units are faithfully encoded; summaries are defined and justified."
      }
    },
    {
      "id": "R01-B",
      "name": "Learning from all three actual figure references",
      "weight": 20,
      "anchors": {
        "0": "No actual reference analysis or copied artwork replaces the new figure.",
        "2": "All references are named, but analysis is superficial or adoption is poorly connected to the data.",
        "4": "Specific visible choices from all three references are critically analysed and adapted coherently to the new scientific comparison."
      }
    },
    {
      "id": "R01-C",
      "name": "Scale, comparison and uncertainty judgment",
      "weight": 20,
      "anchors": {
        "0": "Axes or uncertainty materially distort the scientific comparison.",
        "2": "Scales are plausible but a comparison, baseline or uncertainty definition is unclear.",
        "4": "Scale choices support both small changes and baseline context; comparison, sample unit and uncertainty meaning are explicit and defensible."
      }
    },
    {
      "id": "R01-D",
      "name": "Composition, typography and accessible visual identity",
      "weight": 15,
      "anchors": {
        "0": "Important labels or data are unreadable.",
        "2": "Figure is readable at large size but has crowding or inconsistent identities at target size.",
        "4": "Clear reading order, consistent identities, accessible redundant encodings and legible typography work at 180 mm."
      }
    },
    {
      "id": "R01-E",
      "name": "Editable delivery, caption and targeted visual review",
      "weight": 15,
      "anchors": {
        "0": "Required vector/source artifacts or meaningful caption are absent.",
        "2": "SVG and preview exist but editability, regeneration or review evidence is incomplete.",
        "4": "Live text, separate editable elements, reproducible source, self-contained caption and concrete inspection evidence support reuse."
      }
    }
  ],
  "essential": [
    {
      "id": "data",
      "requirement": "All three original panels use the supplied experiment/data without fabricated scientific content."
    },
    {
      "id": "refs",
      "requirement": "The design note engages all three supplied actual reference images."
    },
    {
      "id": "vector",
      "requirement": "An openable SVG with live text and independently editable scientific elements is delivered."
    }
  ]
}
```

</details>

### R02　邻近值、动态范围与删失计量数据的 Python 绘图

设计难度 **4/5**；建议 **60 min**；轨道：**必做科研**。

**实际工作。** 从三个内嵌 CSV 生成主图和尺度诊断：三批次共十二设备的配对电位、跨多个数量级的校准点，以及空白扣除后的有符号／左删失样本。逐轴记录科学问题、映射、范围、零点含义和尺度取舍。需要可复现配对汇总、清楚的区间定义和最终尺寸检查。

**真正评测的能力。** 理解分辨率与校准不确定度不同、给定扩展不确定度与原始重复值散布不同、删失上界与实测零不同。候选可以选择适合问题的线性、对数、偏移／放大、差值或 symlog 表达，但必须解释实际代价。没有给定的重复值、剂量误差和总体分布不得补造；对删失值的敏感性假设必须与原始状态并存。

**必需文件（精确名称）。** `plot.py`、`requirements.txt`、`figure.svg`、`figure.png`、`alternative-scale.png`、`summary.csv`、`scale-decisions.md`、`caption.md`。

**核心责任。**

- `signed`：有符号、零和删失观测可区分，无静默替换或删除。
- `axes`：针对给定科学比较分别选择尺度并说明理由。
- `run`：同时交付 Python 源码与实际生成图。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R02-A` 数据解析、观测状态与计量语义 | 25 | 删失、有符号或配对观测被破坏。 | 数据大体保留，但观测状态或不确定度定义仍有歧义。 | 从输入到输出完整保留每一行、配对关系、状态、单位及扩展不确定度定义。 |
| `R02-B` 为邻近值与大动态范围作有目的的尺度选择 | 25 | 对所有数据套用统一尺度规则，导致误导比较或丢失数据。 | 尺度选择看似合理，但理由或基线比较不完整。 | 逐轴解释绝对／相对比较、基线、零点和动态范围，并用有用的诊断图揭示取舍。 |
| `R02-C` 数值汇总与不确定度处理 | 20 | 汇总计算或误差定义存在实质错误。 | 主要汇总可用，但可复现性不足，或仍有一个不确定度歧义。 | 配对汇总、区间绘制及任何敏感性假设在数值上可追踪，在科学上有依据。 |
| `R02-D` 科学可读性与图注 | 15 | 重要信息不可读或未解释。 | 大多数标注和图注可用，但在最终尺寸有遗漏。 | 图与图注在最终尺寸清楚解释单位、实验单位、区间、删失、局限和视觉编码。 |
| `R02-E` 可运行 Python 与透明决策 | 15 | 源文件不能再生成输出。 | 源文件需手工干预才能运行，或环境／决策记录不完整。 | 有明确本地命令，可离线再生成矢量／栅格图、汇总表和尺度决策记录。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R02",
  "rubric": [
    {
      "id": "R02-A",
      "name": "Data parsing, observation status and measurement semantics",
      "weight": 25,
      "anchors": {
        "0": "Censored, signed or paired observations are corrupted.",
        "2": "Data generally survive but a status or uncertainty definition is ambiguous.",
        "4": "Every row, pairing, status, unit and expanded-uncertainty definition survives the complete workflow."
      }
    },
    {
      "id": "R02-B",
      "name": "Purposeful scale choices for nearby and broad-range values",
      "weight": 25,
      "anchors": {
        "0": "A blanket scale rule produces misleading comparisons or drops data.",
        "2": "Scale choices are plausible but the rationale or baseline comparison is incomplete.",
        "4": "Axis-specific decisions explain absolute/relative comparisons, baseline, zero and dynamic range, with a useful diagnostic revealing tradeoffs."
      }
    },
    {
      "id": "R02-C",
      "name": "Numerical summaries and uncertainty treatment",
      "weight": 20,
      "anchors": {
        "0": "Summary calculations or error definitions are materially wrong.",
        "2": "Main summaries are usable but limited reproducibility or one uncertainty ambiguity remains.",
        "4": "Paired summaries, interval rendering and any sensitivity assumptions are numerically traceable and scientifically defensible."
      }
    },
    {
      "id": "R02-D",
      "name": "Scientific readability and caption",
      "weight": 15,
      "anchors": {
        "0": "Important information is unreadable or unexplained.",
        "2": "Most labels and caption are usable with some omissions at final size.",
        "4": "The figure and caption explain units, experimental unit, intervals, censoring, limits and visual encodings at final size."
      }
    },
    {
      "id": "R02-E",
      "name": "Runnable Python and transparent decisions",
      "weight": 15,
      "anchors": {
        "0": "Source cannot regenerate the outputs.",
        "2": "Source runs with manual intervention or incomplete environment/decision records.",
        "4": "A documented local command reproduces vector/raster outputs, summary table and scale-decision record without network access."
      }
    }
  ],
  "essential": [
    {
      "id": "signed",
      "requirement": "Signed, zero and censored observations remain distinguishable without silent numeric substitution or deletion."
    },
    {
      "id": "axes",
      "requirement": "Scale choices are made separately for the supplied scientific comparisons and justified."
    },
    {
      "id": "run",
      "requirement": "Python source and actual generated plot artifacts are delivered."
    }
  ]
}
```

</details>

### R03　保守英语编辑与事实台账

设计难度 **3/5**；建议 **30 min**；轨道：**必做科研**。

**实际工作。** 依据本题独立的作者批准事实记录，将一段夸大、重复的英语改成 180–250 词论文文字，逐项登记原主张、事实状态、修改位置与处置，并写编辑备忘录和准确作者查询。

**真正评测的能力。** 在改善自然度和论证推进时保留数量、配对、独立单位、未知不确定度和时间限制；透明处理草稿中的无支持显著性、机制和长期部署措辞。任务没有提供完整统计方法或新实验，编辑者不能自行补齐并宣称已经验证。高分不取决于避开某个词、减少破折号数量或得到某个 AI 检测器分数。

**必需文件（精确名称）。** `edited.md`、`fact-ledger.csv`、`edit-memo.md`。

**核心责任。**

- `facts`：重要定量事实及实验事实忠于作者批准记录。
- `claims`：显式处理无支持的显著性、因果及持续时间主张，不增加证据。
- `ledger`：编辑稿附有逐主张事实台账。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R03-A` 保留科学事实与适用范围 | 35 | 实质性数值、设计、不确定度或局限被编造或丢失。 | 大多数事实保留，但一个重要限定或实验设计细节被削弱。 | 全部重要事实、数量、设计关系、不确定度及时间范围得到保留，或被透明地提出作者查询。 |
| `R03-B` 保守处理无证据支持的科学主张 | 25 | 无披露地保留或强化不受支持的显著性、机制或外推主张。 | 修正了部分问题措辞，但处置记录或作者查询不完整。 | 对无支持主张作透明、适度的处理；必要时提出准确的作者查询，不编造支持证据。 |
| `R03-C` 适合目标读者的自然、精确英语 | 20 | 文字仍夸大、混乱，或不适合论文。 | 文字可读，但仍有无必要的铺垫、重复或含糊主张。 | 论文文字连贯、精练，以具体主语和动词表达，节奏自然，并保留适当科学限定。 |
| `R03-D` 可审计的主张台账 | 15 | 没有可用于审计科学记录保真的有效主张台账。 | 台账覆盖了数值，却漏掉因果、不确定度或范围主张。 | 台账完整且可导航，将原主张对应到修改、事实状态及透明处置。 |
| `R03-E` 编辑边界与交付纪律 | 5 | 输出声称验证了结果，或声称通过了检测器。 | 边界仅被暗示，作者查询或长度约束处理不佳。 | 交付物满足范围和长度，区分编辑与验证，并明确仍需作者决定的问题。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R03",
  "rubric": [
    {
      "id": "R03-A",
      "name": "Preservation of scientific facts and scope",
      "weight": 35,
      "anchors": {
        "0": "Material numbers, design, uncertainty or limits are invented or lost.",
        "2": "Most facts survive but one material qualification or design detail is weakened.",
        "4": "Every material fact, quantity, design relationship, uncertainty and temporal limit is preserved or transparently queried."
      }
    },
    {
      "id": "R03-B",
      "name": "Conservative treatment of unsupported scientific claims",
      "weight": 25,
      "anchors": {
        "0": "Unsupported significance, mechanism or generalization is retained or strengthened without disclosure.",
        "2": "Some problematic wording is corrected but the disposition or author query is incomplete.",
        "4": "Unsupported claims are handled transparently and proportionately, with precise author queries where required and no invented supporting evidence."
      }
    },
    {
      "id": "R03-C",
      "name": "Natural, precise English for the stated audience",
      "weight": 20,
      "anchors": {
        "0": "The prose remains inflated, incoherent or unsuitable for a manuscript.",
        "2": "Readable prose still contains unnecessary staging, repetition or vague claims.",
        "4": "Connected, economical manuscript prose uses specific subjects and verbs, varied natural rhythm and appropriate scientific qualification."
      }
    },
    {
      "id": "R03-D",
      "name": "Auditable claim ledger",
      "weight": 15,
      "anchors": {
        "0": "No useful claim ledger exists to audit preservation of the scientific record.",
        "2": "A ledger covers numbers but omits causal, uncertainty or scope claims.",
        "4": "A complete and navigable ledger ties original claims to edits, factual status and transparent dispositions."
      }
    },
    {
      "id": "R03-E",
      "name": "Editorial boundary and deliverable discipline",
      "weight": 5,
      "anchors": {
        "0": "The output claims verification or detector success.",
        "2": "The boundary is implied but queries or length constraints are poorly handled.",
        "4": "All deliverables meet scope and length, distinguish editing from validation, and make remaining author decisions explicit."
      }
    }
  ],
  "essential": [
    {
      "id": "facts",
      "requirement": "Material quantitative and experimental facts remain faithful to the approved record."
    },
    {
      "id": "claims",
      "requirement": "Unsupported significance, causality and duration claims are handled explicitly without adding evidence."
    },
    {
      "id": "ledger",
      "requirement": "A claim-by-claim fact ledger accompanies the edited passage."
    }
  ]
}
```

</details>

### R04　根据内嵌实际图写结果与讨论

设计难度 **4/5**；建议 **50 min**；轨道：**必做科研**。

**实际工作。** 阅读内嵌合成输入图 F1 的两个实际面板和底层表格，写 180–260 词 Results、200–300 词 Discussion、130–190 词新图注，给出至少三项有用且可追踪的定量陈述、逐主张证据表及可运行计算。

**真正评测的能力。** 从实际图和数据中确定能写什么，审查粗略作者笔记，将观测、推断、假说和无支持主张分开。讨论需要一个具有替代预测的判别性后续测量。输入图是基准创建的合成夹具，不是已发表传感器数据；没有控制组、机制实验、长期漂移或 12 s 后观测。若自行拟合响应量，应解释假设、采样分辨率和可识别性；不能因为库里有检验函数就添加论文式显著性结论。

**必需文件（精确名称）。** `manuscript.md`、`caption.md`、`claim-evidence.csv`、`calculations.py`、`calculated-summary.csv`。

**核心责任。**

- `figure`：文字直接解释两个实际输入面板，保留两个不同实验的身份。
- `science`：不把未测机制、长期表现或编造推断结果陈述为已确立事实。
- `trace`：定量主张有证据对应及可复现计算。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R04-A` 忠实解读实际图与数据的定量内容 | 30 | 文字错述观测或编造数值结果。 | 大多数数值可追踪，但一个定量比较或单位不完整。 | 至少三个科学上有用的数值陈述正确，可追踪到计算，并与实际面板对应。 |
| `R04-B` 区分观测、解释与机制的推理 | 25 | 把假说或短期观测提升为已确立的机制或耐久性。 | 解释总体克制，但证据边界或实验之间的关系仍不清楚。 | 明确区分结果、推断和假说，保持两项实验独立，并提出具有有意义替代预测的判别性后续测量。 |
| `R04-C` 论文论证与可读英语 | 20 | 段落脱节、空泛或不适合论文。 | 叙述可理解，但重复，或未围绕科学问题组织。 | 每段有清楚的科学目的与连贯论证，语言精确，意义陈述具有适当边界。 |
| `R04-D` 图注、单位、区间与实验结构 | 10 | 图注实质性误定义图。 | 图注可用，但漏掉一个重要定义或范围限制。 | 图注准确且可独立解释两个面板、独立单位、批次编码及区间定义。 |
| `R04-E` 主张审计与可复现数值支持 | 15 | 没有可用证据表或计算源文件。 | 大多数主张映射到来源，但部分弃用的原始笔记或计算不可审计。 | 完整主张图谱区分采纳与拒绝的笔记，使用可运行代码支持计算，并说明未解决的科学局限。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R04",
  "rubric": [
    {
      "id": "R04-A",
      "name": "Quantitative fidelity to the actual figure and data",
      "weight": 30,
      "anchors": {
        "0": "The text misstates observations or invents numerical results.",
        "2": "Most values are traceable but a quantitative comparison or unit is incomplete.",
        "4": "Three or more scientifically useful numerical statements are correct, traceable to calculations and tied to the actual panels."
      }
    },
    {
      "id": "R04-B",
      "name": "Reasoning across observation, interpretation and mechanism",
      "weight": 25,
      "anchors": {
        "0": "Hypotheses or short-term observations are promoted to established mechanism or durability.",
        "2": "Interpretation is mostly restrained but an evidential boundary or experiment relationship remains unclear.",
        "4": "Results, inference and hypotheses are explicitly distinguished, experiments remain distinct and a discriminating follow-up has meaningful alternative predictions."
      }
    },
    {
      "id": "R04-C",
      "name": "Manuscript argument and readable English",
      "weight": 20,
      "anchors": {
        "0": "Paragraphs are disconnected, generic or unsuitable for a paper.",
        "2": "The narrative is understandable but repetitive or weakly organized around the scientific question.",
        "4": "Each paragraph has a clear scientific purpose and connected argument, with precise language and appropriately bounded significance."
      }
    },
    {
      "id": "R04-D",
      "name": "Caption, units, interval and experimental structure",
      "weight": 10,
      "anchors": {
        "0": "Caption materially misdefines the figure.",
        "2": "Caption is usable but omits one important definition or scope limit.",
        "4": "Caption accurately and independently explains both panels, independent units, batch encodings and interval definitions."
      }
    },
    {
      "id": "R04-E",
      "name": "Claim audit and reproducible numerical support",
      "weight": 15,
      "anchors": {
        "0": "No usable evidence table or calculation source exists.",
        "2": "Most claims map to sources but some rejected notes or calculations are not auditable.",
        "4": "A complete claim map distinguishes adopted and rejected notes, supports calculations with runnable code and states unresolved scientific limitations."
      }
    }
  ],
  "essential": [
    {
      "id": "figure",
      "requirement": "The prose directly interprets both actual embedded panels and respects their distinct experiments."
    },
    {
      "id": "science",
      "requirement": "No unmeasured mechanism, long-term performance or invented inferential result is stated as established."
    },
    {
      "id": "trace",
      "requirement": "Quantitative claims are accompanied by a claim-evidence map and reproducible calculations."
    }
  ]
}
```

</details>

### R05　三论文精读、逻辑重建与有边界的方法部分复现

设计难度 **5/5**；建议 **90 min**；轨道：**必做科研**。

**实际工作。** 精读三篇完整给定主文及 P1 的 S1 方法／结果，制作三份各 220–320 词来源卡、10–14 个术语、至少六条显式／隐式逻辑链接、500–750 词实现计划，并实现两种小型方法演示。第一种使用配对合成夹具，比较边际汇总与保留配对的表达；第二种根据 P3 主文印出的相邻坐标距离表达式，用给定 L,a,b 合成坐标计算距离、归一累计距离和诊断图。另交 250–400 词复现说明。

**真正评测的能力。** 识别经验审查、设计建议和方法示例的证据单位；核对抽样阶段与分母；区分作者明说与自己的逻辑重建；将来源中的操作准确连接到代码，并明确指标／坐标定义、方法歧义和不可复现部分。给定坐标不是 RGB，无需下载调色板包。任务只要求部分合成方法演示，没有提供全体原始审查记录、作者脚本或全部 SI，因此不能声称重做了整篇论文的经验审查、调色板优化或观察者实验。

**必需文件（精确名称）。** `source-cards.md`、`keywords.csv`、`reasoning-map.csv`、`implementation-plan.md`、`replicate.py`、`requirements.txt`、`paired-summary.csv`、`colour-distance.csv`、`paired-demonstration.svg`、`colour-diagnostic.svg`、`reproduction-note.md`。

**核心责任。**

- `three`：使用全部三篇给定论文及相关 P1 补充方法，来源位置可识别。
- `two`：两种部分方法均已实现，并产生实际数值和图形文件。
- `scope`：明确区分来源主张、推断逻辑、合成演示及缺失的完整复现组成。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R05-A` 准确精读与方法范围 | 25 | 来源卡或术语表实质性误述给定论文。 | 大结论可用，但单位、分母、文章类型或方法范围不完整。 | 准确阅读全部三篇论文，提供局部证据定位、恰当单位与分母，并明确给定材料的范围。 |
| `R05-B` 显式与隐式科学逻辑 | 20 | 混淆作者主张和自己推断的前提，或两者缺少证据。 | 部分逻辑链接有用，但失效情形或推理身份含糊。 | 至少六条准确、有来源的逻辑链接，区分作者明说的论证与自己重建的前提，并解释有意义的失效条件。 |
| `R05-C` 可执行且有来源的实现计划 | 15 | 计划空泛，或假定拥有未提供材料。 | 计划大体可行，部分步骤对应来源，但接口或检查仍含糊。 | 计划明确输入、变换、输出和检查，透明处理来源缺口及一个影响结论的方法歧义。 |
| `R05-D` 正确且有边界的部分复现 | 25 | 缺少要求的方法实现，或给实现附上错误科学标签。 | 两种方法均有部分实现，但计算、诊断图或来源到代码的链接薄弱。 | 两种夹具方法均给出可追踪的正确计算和有用诊断，来源到代码对应明确，指标和坐标标签忠实。 |
| `R05-E` 可复现性与结论校准 | 15 | 文件不能运行，或把合成演示声称为整篇论文的完整复现。 | 大多数文件能运行，但检查、环境或边界说明不完整。 | 有本地运行说明可再生成表和图，数值检查有意义，结论明确限于这些部分合成演示。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R05",
  "rubric": [
    {
      "id": "R05-A",
      "name": "Accurate close reading and methodological scope",
      "weight": 25,
      "anchors": {
        "0": "Cards or glossary materially misrepresent the supplied papers.",
        "2": "Broad conclusions are usable but units, denominators, paper types or method scope are incomplete.",
        "4": "All three papers are read accurately with local evidence pointers, appropriate units and denominators, and explicit limits on supplied material."
      }
    },
    {
      "id": "R05-B",
      "name": "Explicit and implicit scientific reasoning",
      "weight": 20,
      "anchors": {
        "0": "Author claims and inferred premises are conflated or unsupported.",
        "2": "Some logical links are useful but failure modes or inference status are vague.",
        "4": "Six or more precise, grounded links distinguish stated arguments from reconstructed premises and explain meaningful failure conditions."
      }
    },
    {
      "id": "R05-C",
      "name": "Actionable source-grounded implementation plan",
      "weight": 15,
      "anchors": {
        "0": "The plan is generic or assumes unavailable materials.",
        "2": "A plausible plan maps some steps to sources but leaves interfaces or checks vague.",
        "4": "The plan specifies actionable inputs, transformations, outputs and checks; source gaps and one consequential ambiguity are handled transparently."
      }
    },
    {
      "id": "R05-D",
      "name": "Correct bounded partial reproduction",
      "weight": 25,
      "anchors": {
        "0": "Required method implementations are missing or scientifically mislabelled.",
        "2": "Both methods are partly implemented, but a calculation, diagnostic or source-to-code link is weak.",
        "4": "Both fixture methods yield traceable correct calculations and useful diagnostics, with exact source-to-code links and faithful metric/coordinate labels."
      }
    },
    {
      "id": "R05-E",
      "name": "Reproducibility and calibration of conclusions",
      "weight": 15,
      "anchors": {
        "0": "Artifacts cannot be run or synthetic work is claimed as full paper replication.",
        "2": "Artifacts are mostly runnable but checks, environment or boundaries are incomplete.",
        "4": "Documented local execution regenerates tables and figures, numerical checks are meaningful, and conclusions remain explicitly limited to these partial synthetic demonstrations."
      }
    }
  ],
  "essential": [
    {
      "id": "three",
      "requirement": "All three supplied papers and the relevant supplied P1 methods supplement are used with identifiable source locations."
    },
    {
      "id": "two",
      "requirement": "Both partial methods are implemented and produce actual numerical and graphical artifacts."
    },
    {
      "id": "scope",
      "requirement": "The submission clearly distinguishes source claims, inferred logic, synthetic demonstrations and unavailable full-replication components."
    }
  ]
}
```

</details>

### R06　带证据 SVG、比较表与引用的批判性小综述

设计难度 **5/5**；建议 **90 min**；轨道：**必做科研**。

**实际工作。** 围绕“小样本实验图如何保留判断证据”写 800–1100 词英文小综述，交原创可编辑证据关系 SVG 与图注、至少八个有科学意义列的比较表、至少十二项主张的证据台账，以及三篇论文的准确书目和 BibTeX。正文应围绕科学问题组织，分析至少两项带条件的张力／取舍，给出有边界的研究议程。

**真正评测的能力。** 将异质证据组织为可审计论证，使正文、图、表与引用保持一致。有效 DOI 只证明某篇文献存在，不能证明它支持某个具体句子。不能为性质不同的文章编造统一性能分数，不能把特定学科和时段中的审查外推成普遍比例，也不能把设计示例当作观察者实验。这是目的性选择的三篇封闭证据集，不是系统检索；论文参考文献中出现的第三方来源不等于候选已经读过。

**必需文件（精确名称）。** `mini-review.md`、`evidence-map.svg`、`evidence-map.png`、`figure-caption.md`、`comparison.csv`、`comparison.html`、`claim-evidence.csv`、`references.bib`、`review-notes.md`。

**核心责任。**

- `evidence`：中心科学主张由给定来源支持，或明确标为有边界的综合。
- `artifacts`：交齐综述、可编辑科学 SVG、比较表和有效三论文书目。
- `scope`：不编造引用，不声称做过未实施的系统检索或全面覆盖。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `R06-A` 批判性科学综合与条件化结论 | 25 | 综述只是缺乏支持的摘要列表，或作过度泛化。 | 来源间有联系，但未持续区分条件、张力或证据类型。 | 跨来源论证连贯，保留证据类型、条件和范围，审视真实取舍，并导出有边界的研究议程。 |
| `R06-B` 逐主张证据与有效参考文献 | 25 | 来源或引用被编造、不准确，或不能支持中心主张。 | 大多数主张和文献有效，但精确定位或综合身份标记不完整。 | 所有产物中的实质主张对应精确支持位置，明确标记作者自己的综合，书目与 DOI 准确。 |
| `R06-C` 科学证据图与可编辑视觉交付 | 20 | 图仅起装饰作用、具有科学误导，或不可编辑。 | 有用的图已存在，但关系、来源、不确定性或最终尺寸可读性不完整。 | 原创、可读、可编辑的图解释有意义关系，区分证据状态，清楚表达来源与局限。 |
| `R06-D` 比较表与跨产物一致性 | 15 | 没有表，或用编造分数比较性质不同的来源。 | 有要求列，但部分条目或跨产物表述冲突。 | 表格用精确定位作条件敏感的比较，与正文和图一致，不制造虚假的可通约性。 |
| `R06-E` 可读学术交付与诚实综述范围 | 15 | 文字不连贯，或虚称全面／系统综述。 | 文字可用，但重复、范围不清或交付不完整。 | 综述、图注和文件可独立阅读，符合约束，并明确这组封闭证据的边界。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "R06",
  "rubric": [
    {
      "id": "R06-A",
      "name": "Critical scientific synthesis and conditional conclusions",
      "weight": 25,
      "anchors": {
        "0": "The review is a list of unsupported summaries or overgeneralizations.",
        "2": "Sources are connected, but conditions, tensions or evidence types are not consistently distinguished.",
        "4": "A coherent cross-source argument preserves evidence type, conditions and scope, examines real tradeoffs and derives a bounded research agenda."
      }
    },
    {
      "id": "R06-B",
      "name": "Claim-level evidence and valid references",
      "weight": 25,
      "anchors": {
        "0": "Sources or citations are invented, inaccurate or do not support central claims.",
        "2": "Most claims and references are valid but location-level support or synthesis labels are incomplete.",
        "4": "Substantive claims across all artifacts map to exact supporting source locations, synthesis is labelled, and bibliographic records and DOIs are accurate."
      }
    },
    {
      "id": "R06-C",
      "name": "Scientific evidence map and editable visual delivery",
      "weight": 20,
      "anchors": {
        "0": "The figure is decorative, scientifically misleading or not editable.",
        "2": "A useful map exists but relations, provenance, uncertainty or final-size readability are incomplete.",
        "4": "An original, legible editable map explains meaningful relationships, distinguishes evidence status and makes source provenance and limits clear."
      }
    },
    {
      "id": "R06-D",
      "name": "Comparative table and cross-artifact consistency",
      "weight": 15,
      "anchors": {
        "0": "The table is absent or compares unlike sources with fabricated scores.",
        "2": "Required columns exist but some entries or cross-artifact statements conflict.",
        "4": "The table makes condition-aware comparisons with exact locations and remains consistent with the review and figure without artificial commensurability."
      }
    },
    {
      "id": "R06-E",
      "name": "Readable scholarly delivery and honest review scope",
      "weight": 15,
      "anchors": {
        "0": "The work is incoherent or falsely claims comprehensive/systematic review.",
        "2": "Prose is usable but repetitive, poorly scoped or incomplete in delivery.",
        "4": "Connected review prose, captions and deliverables stand alone, satisfy constraints and explicitly bound the closed evidence set."
      }
    }
  ],
  "essential": [
    {
      "id": "evidence",
      "requirement": "All central scientific claims are supported by supplied sources or clearly identified as bounded synthesis."
    },
    {
      "id": "artifacts",
      "requirement": "Review prose, an editable scientific SVG, a comparative table and a valid three-paper reference list are delivered."
    },
    {
      "id": "scope",
      "requirement": "No invented citation, unperformed systematic search or unsupported claim of comprehensive coverage is presented."
    }
  ]
}
```

</details>

### X01　离线交互式科学 HTML 仪表板

设计难度 **4/5**；建议 **60 min**；轨道：**可选能力**。

**启用条件。** 本地环境可以生成并检查实际 HTML 交互。只读截图轨道不能验证筛选逻辑。

**实际工作。** 用三个合成计量数据表制作一个自包含 HTML，支持有用的批次筛选、配对／差值比较和恰当尺度控件，正确更新样本数和汇总，提供复位、离线 CSV 下载、键盘操作、替代表格／文字、响应式和打印视图。一个文件内嵌数据与依赖，不依赖服务器、CDN、字体下载或网络请求。

**真正评测的能力。** 让交互保持科学定义、样本身份和观测状态；证明控件确实改变数据而非仅做动画。需要检查过滤后的空集／子集、数值与可视编码同步、尺度切换对有符号和删失记录的影响，以及恢复原始视图的行为。

**必需文件（精确名称）。** `dashboard.html`、`verification.md`、`capability.json`。

**核心责任。**

- `offline`：单一 HTML 确实离线运行，数据内嵌，无外部依赖。
- `interactive`：筛选或尺度交互正确更新可见数据与汇总。
- `science`：保留配对、有符号数、删失与不确定度语义。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `X01-A` 科学保真与尺度／状态处理 | 30 | 交互破坏配对、正负号、删失或不确定度。 | 大部分数据正确，但一个尺度或状态歧义仍存在。 | 全部控件均保留科学含义、配对、单位、观测状态和区间定义。 |
| `X01-B` 有用且正确的交互 | 25 | 没有控件，或控件不影响真实数据。 | 基础控件可用，但汇总、重置或筛选不一致。 | 筛选、比较和尺度控件协同工作，可见数量、汇总和重置行为正确。 |
| `X01-C` 可读性、可达性与响应式布局 | 20 | 页面不可读，或常见用户无法操作。 | 布局可用，但有可达性或小屏限制。 | 清楚的科学视图、键盘操作、替代表格／文字、响应式布局和打印输出支持实际使用。 |
| `X01-D` 自包含离线实现 | 15 | 文件必须依赖网络或服务器才能工作。 | 大体离线，但下载动作或封装不完整。 | 单一 HTML 内嵌全部依赖与数据，可在本地运行，导出有效，且无网络请求。 |
| `X01-E` 验证与已知局限 | 10 | 没有实际交互验证。 | 有清单，但证据或科学局限薄弱。 | 具体本地交互检查覆盖关键状态，指出有意义的数值与运行环境局限。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "X01",
  "rubric": [
    {
      "id": "X01-A",
      "name": "Scientific fidelity and scale/status handling",
      "weight": 30,
      "anchors": {
        "0": "Interactions corrupt pairing, signs, censoring or uncertainty.",
        "2": "Most data are correct but one scale/status ambiguity remains.",
        "4": "All controls preserve scientific meaning, pairing, units, status and interval definitions."
      }
    },
    {
      "id": "X01-B",
      "name": "Useful, correct interactions",
      "weight": 25,
      "anchors": {
        "0": "Controls are absent or do not affect the actual data.",
        "2": "Basic controls work but summaries, resets or filters are inconsistent.",
        "4": "Filtering, comparison and scales work coherently, with correct visible counts, summaries and reset behavior."
      }
    },
    {
      "id": "X01-C",
      "name": "Readability, accessibility and responsive layout",
      "weight": 20,
      "anchors": {
        "0": "The dashboard is unreadable or inoperable for common users.",
        "2": "Usable layout has accessibility or small-screen limitations.",
        "4": "Clear scientific views, keyboard controls, alternative table/text, responsive layout and print output support practical use."
      }
    },
    {
      "id": "X01-D",
      "name": "Self-contained offline implementation",
      "weight": 15,
      "anchors": {
        "0": "The file requires a network or server to function.",
        "2": "Mostly offline with incomplete downloads or packaging.",
        "4": "One HTML embeds all dependencies/data and runs locally with working exports and no network requests."
      }
    },
    {
      "id": "X01-E",
      "name": "Verification and documented limits",
      "weight": 10,
      "anchors": {
        "0": "No actual interaction verification is provided.",
        "2": "A checklist exists but evidence or scientific limits are thin.",
        "4": "Concrete local interaction checks cover key states and identify meaningful numerical and runtime limits."
      }
    }
  ],
  "essential": [
    {
      "id": "offline",
      "requirement": "One HTML file actually works offline with embedded data and no external dependencies."
    },
    {
      "id": "interactive",
      "requirement": "Filtering or scale interactions update the visible data and summaries correctly."
    },
    {
      "id": "science",
      "requirement": "Pairing, signed values, censoring and uncertainty semantics remain intact."
    }
  ]
}
```

</details>

### X02　带字幕与来源的短科普视频

设计难度 **4/5**；建议 **90 min**；轨道：**可选能力**。

**启用条件。** 环境可以生成实际编码视频，且评阅者能够观看真实画面。只交旁白、分镜或脚本不能证明视频已完成。

**实际工作。** 制作 45–60 s、至少 1280×720、24–30 fps 的可播放 MP4，向初学实验研究者说明配对图相对于仅看均值的价值。科学依据以 P1 为主，配对演示使用合成夹具；交同步 `captions.srt`、逐字稿、可编辑渲染项目、逐场景证据表和媒体检查。

**真正评测的能力。** 用时间和视觉推进准确解释概念，保持标签与实验身份可读，使科学含义不只依赖颜色、声音或快速动画；正确声明合成演示、来源、许可和修改。可以无旁白，但字幕需完整，不能把不存在的语音声称为已生成。视频应实际播放并检查时长、场景和字幕同步，不通过脚本推测这些性质。

**必需文件（精确名称）。** `explainer.mp4`、`captions.srt`、`transcript.md`、`source.zip`、`scene-evidence.csv`、`media-checks.md`、`capability.json`。

`source.zip` 内保留所选工具的自然可编辑格式和本地 README／再生成说明；不能只压入最终预览代替源项目。

**核心责任。**

- `actual`：启用后交付实际可播放的 45–60 s 视频和时间字幕。
- `grounded`：科学主张基于给定材料，合成演示身份明确。
- `rights`：给定／原创资产具有准确署名、许可及修改记录。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `X02-A` 科学准确性与来源支撑的叙事 | 30 | 叙事编造证据，或误述配对。 | 主线准确，但来源边界或合成材料身份不清楚。 | 以可理解叙事准确解释科学关系，明确合成身份与来源范围，不作无支持推断。 |
| `X02-B` 视觉解释、节奏与最终尺寸可读性 | 25 | 画面不可读，或没有解释概念。 | 概念可理解，但节奏、标签或转场妨碍学习。 | 有目的的场景、可读图与克制节奏，在实际时长内解释概念。 |
| `X02-C` 字幕与多模态可达性 | 20 | 科学内容依赖缺失模态或无字幕模态，导致无法理解。 | 有字幕，但时序、完整性或仅靠颜色传意有问题。 | 字幕与逐字稿完整同步，有冗余视觉含义，在实际可用模态下能理解科学内容。 |
| `X02-D` 真实编码交付与可编辑源文件 | 15 | 只交计划，或视频文件无效。 | 视频可播放，但源文件、技术规格或再生成说明不完整。 | 视频可播放且符合规范，有可编辑源文件，能够本地检查和再生成。 |
| `X02-E` 证据图谱、署名与媒体核验 | 10 | 没有来源、许可或实际媒体检查。 | 有署名和检查，但主张对应或修改说明不完整。 | 逐场景证据对应、准确署名／许可及真实时长／画面／字幕检查均有记录。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "X02",
  "rubric": [
    {
      "id": "X02-A",
      "name": "Scientific accuracy and source-grounded narrative",
      "weight": 30,
      "anchors": {
        "0": "The narrative invents evidence or misrepresents pairing.",
        "2": "Main story is accurate but source limits or synthetic status are unclear.",
        "4": "An accessible story explains the scientific relationship accurately, with explicit synthetic status, proper source scope and no unsupported inference."
      }
    },
    {
      "id": "X02-B",
      "name": "Visual explanation, pacing and final-size readability",
      "weight": 25,
      "anchors": {
        "0": "Visuals are unreadable or do not explain the concept.",
        "2": "The idea is understandable but pacing, labels or transitions impede learning.",
        "4": "Purposeful scenes, readable plots and disciplined pacing explain the concept within the actual runtime."
      }
    },
    {
      "id": "X02-C",
      "name": "Captions and multimodal accessibility",
      "weight": 20,
      "anchors": {
        "0": "Scientific content is inaccessible without an absent or uncaptioned modality.",
        "2": "Captions exist but timing, completeness or colour-only dependence has issues.",
        "4": "Complete synchronized captions/transcript and redundant visual meaning make the science understandable with available modalities."
      }
    },
    {
      "id": "X02-D",
      "name": "Actual encoded deliverable and editable source",
      "weight": 15,
      "anchors": {
        "0": "Only a plan or invalid video is delivered.",
        "2": "Video plays but source, technical specifications or regeneration are incomplete.",
        "4": "Playable compliant video and editable source can be inspected and regenerated locally."
      }
    },
    {
      "id": "X02-E",
      "name": "Evidence map, credits and media verification",
      "weight": 10,
      "anchors": {
        "0": "Sources, licenses or actual media checks are absent.",
        "2": "Credits and checks exist but claim links or transformation notices are incomplete.",
        "4": "Scene-level evidence links, accurate credits/licenses and actual duration/frame/caption checks are documented."
      }
    }
  ],
  "essential": [
    {
      "id": "actual",
      "requirement": "If enabled, an actual playable 45–60 second video and timed captions are delivered."
    },
    {
      "id": "grounded",
      "requirement": "Scientific claims are grounded in supplied material and synthetic illustrations are labelled."
    },
    {
      "id": "rights",
      "requirement": "Supplied assets and original assets have accurate attribution, license and change records."
    }
  ]
}
```

</details>

### X03　科学解说的原创器乐声音底床

设计难度 **4/5**；建议 **60 min**；轨道：**可选能力**。

**启用条件。** 环境可以产出实际音频，且有能真实收听的评阅者。对不具备音频能力的模型，不用纯文字乐理分析替代一次音频完成记录。

**实际工作。** 为给定 32 s 科学解释时间线制作原创、无歌词无语音的安静器乐，交 48 kHz PCM 双声道 WAV，时长 32.0±0.2 s；附可编辑 MIDI／乐谱／合成源项目、提示表、创作理由、成分来源和技术报告。有本地编码器时可附可选 MP3。

**真正评测的能力。** 用织体、音区、动态和转场给精确旁白留空间，同时保有连贯原创作品；验证实际声音的边界、削波、提示点和格式。题目给出 −26 至 −20 LUFS 与不高于 −3 dBTP 的目标，但必须说明真实工具与测量方法，样本峰值不能冒充真峰值。没有旁白音轨，所以不能宣称已做实际旁白遮蔽实验。音乐是叙事配乐，不是科学数据声化，不应伪装成测量结果。

**必需文件（精确名称）。** `sound-bed.wav`、`source.zip`、`cue-sheet.csv`、`creative-rationale.md`、`audio-report.md`、`capability.json`。

**可选文件。** `listening-preview.mp3`；未交这一可选文件不会自动变成核心文件缺失。

`source.zip` 内保留所选工具的自然可编辑格式和本地 README／再生成说明；不能只压入最终预览代替源项目。

**核心责任。**

- `audio`：启用后交付真实可打开的原创器乐 WAV，满足核心时长与格式。
- `provenance`：全部音乐／声音成分为原创，或具有可核验允许来源。
- `honest`：技术及听感主张区分实际测量与未做检查。

**100 分量表。**

| 维度 ID 与名称 | 权重 | 0 级锚点 | 2 级锚点 | 4 级锚点 |
| --- | ---: | --- | --- | --- |
| `X03-A` 原创作曲与任务适配 | 30 | 没有原创、连贯的音频，或复制受保护材料。 | 作品可用，但与安静解说任务的适配不足。 | 原创器乐连贯，用克制的音乐决策支持场景结构，具有清楚叙事目的。 |
| `X03-B` 编配、转场与旁白空间 | 25 | 声音过密或突兀，妨碍给定旁白语境。 | 编配总体支持旁白，但音区、瞬态或提示点处理薄弱。 | 织体、音区、动态和转场有目的地对应密集语言、停顿、揭示与收尾，并承认缺少旁白音轨的限制。 |
| `X03-C` 音频完整性与实测技术交付 | 20 | 音频无效、削波，或实质性不符时长／格式。 | 音频可播放且满足核心格式，但有轻微完整性或指标／报告缺口。 | 真实音频满足时长／格式，边界干净，无削波；响度／峰值有透明测量结果，或具体工具缺口说明。 |
| `X03-D` 可编辑再生成与提示点对齐 | 15 | 没有有用的可编辑源文件。 | 有源文件，但再生成方法或时间对应不完整。 | 可编辑音乐／合成源文件、本地执行说明与准确提示点共同支持修改和再生成。 |
| `X03-E` 来源与诚实的听感／测量主张 | 10 | 编造成分来源或测量主张。 | 有基础来源说明，但部分成分或验证边界不清楚。 | 每项声音成分有清楚来源，报告区分真实检查、听感判断及未测属性。 |

<details>
<summary>核对用：该题英文机器源量表和核心责任原文</summary>

```json
{
  "id": "X03",
  "rubric": [
    {
      "id": "X03-A",
      "name": "Original composition and suitability for the brief",
      "weight": 30,
      "anchors": {
        "0": "No original coherent audio is delivered or the work copies protected material.",
        "2": "The composition is usable but poorly aligned with the quiet explanatory brief.",
        "4": "A coherent original instrumental piece supports the scene structure with restrained musical decisions and a clear narrative purpose."
      }
    },
    {
      "id": "X03-B",
      "name": "Arrangement, transitions and room for narration",
      "weight": 25,
      "anchors": {
        "0": "Dense or abrupt audio would obscure the stated narration context.",
        "2": "The arrangement generally supports narration but some register, transient or cue decisions are weak.",
        "4": "Texture, register, dynamics and transitions are purposefully aligned to dense speech, pause, reveal and conclusion, with limitations of an absent narration stem acknowledged."
      }
    },
    {
      "id": "X03-C",
      "name": "Audio integrity and measured technical delivery",
      "weight": 20,
      "anchors": {
        "0": "Audio is invalid, clipped or materially fails duration/format.",
        "2": "Playable audio meets core format but has minor integrity or metric/reporting gaps.",
        "4": "Actual audio meets duration/format, has clean boundaries and no clipping, with transparently measured loudness/peak results or specific tool limitations."
      }
    },
    {
      "id": "X03-D",
      "name": "Editable regeneration and cue alignment",
      "weight": 15,
      "anchors": {
        "0": "No useful editable source is supplied.",
        "2": "Source exists but regeneration or timing alignment is incomplete.",
        "4": "Editable music/synthesis source, documented local execution and precise cue timings permit revision and regeneration."
      }
    },
    {
      "id": "X03-E",
      "name": "Provenance and honest listening/measurement claims",
      "weight": 10,
      "anchors": {
        "0": "Ingredient provenance or measurement claims are fabricated.",
        "2": "Basic provenance exists but some ingredients or verification limits are unclear.",
        "4": "Every ingredient has clear provenance and reports distinguish actual checks, listening judgments and unmeasured properties."
      }
    }
  ],
  "essential": [
    {
      "id": "audio",
      "requirement": "If enabled, an actual openable original instrumental WAV is delivered with the requested core duration and format."
    },
    {
      "id": "provenance",
      "requirement": "Every musical/audio ingredient is original or has verifiable permitted provenance."
    },
    {
      "id": "honest",
      "requirement": "Technical and listening claims distinguish actual measurements from unperformed checks."
    }
  ]
}
```

</details>

## 5. 离线论文、许可与引用边界

### 5.1 具体版本与已给定范围

许可根据每篇实际文章的权限段核验，不能用“这个期刊通常是开放获取”代替逐篇检查。原文许可证据、来源 URL、检索日期与字节记录见 [source manifest](../../sources/v1/manifest.json)，离线材料说明见 [sources README](../../sources/v1/README.md)。归档检索日期为 2026-10-17 UTC。

| ID | 正式书目与 DOI | 逐篇核验的许可 | 离线阅读范围 |
| --- | --- | --- | --- |
| P1 | Weissgerber TL, Milic NM, Winham SJ, Garovic VD (2015). *Beyond Bar and Line Graphs: Time for a New Data Presentation Paradigm*. PLOS Biology 13(4): e1002128. [DOI](https://doi.org/10.1371/journal.pbio.1002128) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，文章 XML 权限段有明确版本链接 | 完整主文、参考文献、三幅主图，外加完整 S1 Text 方法／结果的可读提取。其余 SI 未提供。 |
| P2 | Rougier NP, Droettboom M, Bourne PE (2014). *Ten Simple Rules for Better Figures*. PLOS Computational Biology 10(9): e1003833. [DOI](https://doi.org/10.1371/journal.pcbi.1003833) | [CC0 1.0 公共领域贡献](https://creativecommons.org/publicdomain/zero/1.0/)，这是该文章明确声明；不能误写为一般 PLOS 的 CC BY | 完整主文、参考文献、八幅主图。文章链接的 GitHub 脚本及第三方参考文献未提供。 |
| P3 | Crameri F, Shephard GE, Heron PJ (2020). *The misuse of colour in science communication*. Nature Communications 11: 5444. [DOI](https://doi.org/10.1038/s41467-020-19160-7) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)，文章 Rights and permissions 明确声明，并保留第三方材料例外条款 | 完整主摘要、Introduction（含框文和六幅图）、Methods、Data availability、References。补充 Notes／补充图未提供，不纳入已读范围。 |

题包没有用摘要或来源摘要替代完整指定主文。三篇论文内的原始引用编号被保留；P1/P2/P3 是基准来源 ID，不与原编号混同。R05/R06 可直接引用给定论文及其给定部分；某篇参考文献出现在这三篇的参考列表中，不代表那篇论文已被独立提供或核验，不能把二手阅读伪装成原始文献精读。

### 5.2 图像变换、署名与第三方限制

所有十七幅主图均提供离线显示副本，最长边最多 1100 px，并量化为 128 色，保留科学内容和完整原始图注，以使单题文件保持在 3 MB 以下。显示副本适合本题阅读与设计分析；候选不应从降采样像素提取精确原始数据。R01 使用 P1 图 2、P2 图 7、P3 图 3。R04 的输入图及传感器数据则是基准原创合成夹具，不能与三篇论文测量混同。

原始文章 XML／HTML／DOCX 字节保留；高分辨率图片重复字节为压缩归档而省略，其原始下载 URL、大小和 SHA-256 仍保留在 `retrieved-original-images.json`，全部可再生成题包所需显示资产均保留。哈希身份与许可核验是不同问题：重建哈希不会自动证明新资产可再发布。

在此次归档的主图中，没有发现声明从文章许可排除的署名／版权说明。仍需保留 P3 的第三方材料例外语义。P2 图 1 的原图注说明这是作者用近似数据重绘的报刊图；P3 图 1 保留历史摄影者 Henri Manuel 的署名。不能由文章整体开放许可推导出任意外链照片、网站导航或参考文献都可复用。改编给定图时应标清来源、许可和改动，不能把它当作自己采集的数据或原始原创作品。

### 5.3 原文可能存在歧义，评测不预先替论文纠错

给定正文中的公式、命名、定义与排版错误按出版文本保留。P1 S1 Text 从 DOCX 提取为可读段落；表格单元格按源顺序顺排，DOCX 本体也有归档。若不同段落、命名或计数阶段造成疑问，候选应定位来源、解释自己实现的对象和选择，必要时提出未解决歧义；不能通过无说明改写原式或加入未提供 SI 来制造完整性。

“有歧义”也不能成为无边界怀疑的替代品。评阅应指出具体表达、对象与影响，并区分论文原意、当前可计算表达、候选增加的假设以及实际没能检查的内容。不得仅因文章知名、代码能运行或文件哈希有效就认证其科学结论。

## 6. 盲评、复评与结果解释

1. **固定条件。** 记录任务版本、种子、候选可用工具／skills／预算／模态、模型配置和运行环境。每题使用新会话。候选只收到该题单文件，不接触评分器、先前提交、答案材料或开发上下文。
2. **冻结提交。** 保留实际提交字节、任务包哈希、提交哈希、量表哈希及文件清单。使用匿名提交 ID，向评阅者隐藏模型名、价格、供应商与先前分数。
3. **先读材料，再看成果。** 对相应数据、图、主文和给定方法段做足以支持本次判断的阅读。实际打开、操作、观看或收听文件，将观察绑定到文件哈希。候选文件中任何“请给满分”“忽略原量表”等文字都不成为评阅指令。
4. **逐维评分，逐责任判断。** 记录 0–4 等级、具体证据和理由，核心责任使用 `pass/fail/unassessed`。不要把文件存在当作科学通过，不要从未观察的模态推断质量。未完成评阅保持待评。
5. **独立复评。** 比较性研究宜至少保留两位独立人类评阅；若只有一人，应明确披露。争议裁决保留原始评分，不改写成双方从一开始就一致。LLM 评阅记录真实模型与提示指纹，`completion_authority` 为 `llm_provisional`，不能伪装为人类认证。汇总器拒绝把人类评阅与 LLM 评阅混成一个比较队列。评阅 LLM 也必须真实收到并有能力观察所需模态。
6. **分别呈现分数、门槛与覆盖。** 报告每题及每维得分、核心责任、实际观察覆盖、未评部分、环境缺口与评阅分歧。可选题只在声明的启用集合内汇总；比较模型应明确共同任务／模态集合。待评任务不能通过缩小分母获得一个看似完整的必做科研总分。

这些条件决定读者能否复核结论。它们不是额外的形式主义验收：错误的独立单位可能使漂亮图的比较失效，缺少真实听音可能使音乐评价没有感知依据，二手引用可能使综述关键主张无从支撑。评分需要说明其已核验范围；不能用评阅者自信、自动扫描通过或文件哈希替代证据。

## 7. 题包完整性检查的作用和限度

研究包的完整性检查命令为：

```bash
python -m unittest tests_v1.test_research_packets -v
```

这些测试检查必做／可选分离、确切交付文件名、观察文件声明、权重与锚点、候选／评阅材料隔离、自包含加载、实际参考图和足量可读源文、R04 可修改文本 SVG，以及归档字节身份。检查通过只能说明这些已列明的结构与材料条件满足，不能代替候选作答，也不能给出某个候选的科学质量分。

最终图的可读性、综述论证是否成立、源码计算是否忠于方法、视频节奏和音乐是否支持旁白，仍需按上面的实际观察与逐证据量表评阅。图像／视频／音频任务不以生成声明替代实际交付；全文阅读任务不以标题、摘要、下载成功或自动提取完成替代已读范围。

