# V1.1 详细使用指南

[English](usage.en.md) · [中文总览](../../README.zh-CN.md) · [离线评分页](scorecard.html)

下列评分命令从仓库根目录运行，用于准备输入和评阅已收集的成果，不会自动选择或调用模型。每次运行使用新的输出目录。示例中的 `received/C04/` 等路径，表示你已经收集了题目要求的真实文件。

## 1. 先确定本轮比较条件

在查看结果之前，先固定题目、模型/版本、允许的工具、预算、尝试次数和评阅方式。

| 条件 | 候选能使用什么 | 怎样报告 |
|---|---|---|
| response-only | 题目输入与一次生成，没有执行工具 | 与可用工具的 agent 分开 |
| 离线 agent / 科研 | 给定输入及固定本地运行环境，不搜索网页或额外下载素材 | 默认闭卷输入条件 |
| resourceful（资源增强） | 预先声明的额外工具、服务、搜索或 skills | 另命名实验条件，记录资源、成本和人工干预 |

resourceful 是实验协议选择，不是 CLI 的 `--mode` 参数。它改变了原有离线合同，应明确作为扩展条件。为模型推理连接 API，不等于允许网页搜索或访问仓库。构建环境、下载已允许输入等准备工作应在计时作答前完成。

每题使用新会话与隔离的候选环境，只给本题的候选文件/素材包，不给 GitHub 链接或完整仓库。评分端有参考实现、测试和演示工程，不能经挂载目录、shell、对话历史或共享检索工具泄露给候选。详见[闭卷评测说明](../v1/closed-evaluation.md)。

C01–C10 是代码画像，R01–R06 是科研画像，X01–X03 是原有可选画像；新增可选视频测试有 A/X04、B/X05 两种可选模式，分别记为 `optional_video_a`、`optional_video_b`。可选其一或明确启用两者，均不进入 `coding` 或 `required` 范围。可选题是否启用应事先声明。已选题没交成果，应记录缺交，不能看过结果再从分母中移除。

## 2. 安装评分端

### 核心环境

需要 Git 和 Python 3.11+。命令使用 POSIX shell；Windows PowerShell 将激活命令换为 `.venv\Scripts\Activate.ps1`。

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m nrb_v1 --version
python -m nrb_v1 identity
python -m nrb_v1 list --tasks all
```

正式比较前，切换到选定 commit，并保存 `identity` 输出。`nrb-v1` 与 `python -m nrb_v1` 是同一入口；旧 `nrb` 命令属于 V0.2 协议。

核心评分器没有强制第三方 Python 依赖。导题、打包与人工评阅不需要 Docker。原有科研 HTML 已嵌入阅读材料和图片，普通使用不需要重新下载或构建来源包。

### 执行未知代码：Docker

安装 Docker 并启动其后台服务，然后运行：

```bash
docker version
docker build -t nrb-v1:local -f environments/v1/Dockerfile .
docker image inspect nrb-v1:local
```

仓库 Dockerfile 提供 Python 3.12、GNU Fortran、NumPy、SciPy、Matplotlib、Pillow、CairoSVG、FFmpeg 和 DejaVu 字体。记录实际镜像 ID/digest 与硬件限制。C06/C09 在容器内编译 Fortran，此路径不要求宿主另装 `gfortran`。

使用 trusted 本地参考自检时，C06/C09 需要宿主 `gfortran`；用 `gfortran --version` 检查，缺失时通过操作系统包管理器安装。完整测试集也包含依赖编译器的检查。环境缺失应保留未评，不能写成候选失败或测试通过。

未知提交不能走 trusted 执行。`grade --execution none` 表示跳过代码执行，不是获得自动科学分数的另一种方法。

视频评阅需要真正能播放画面和声音的播放器。FFmpeg/ffprobe 可测量格式、时长与帧数，但不能代替观看。宿主媒体工具与 Docker 镜像内的工具是不同环境。

## 3. 准备且只准备所选题目

### 原有单文件题目

固定 seed 17 输入在 [tasks/v1.0/](../../tasks/v1.0/)。C 题是 Markdown，R01–R06、X01–X03 是自包含 HTML。

生成单题或明确的子集：

```bash
python -m nrb_v1 export --format files --tasks C04 --seed 17 \
  --dest candidates/C04-s17
python -m nrb_v1 export --format files --tasks C04,C06 --seed 2026 \
  --dest candidates/selected-s2026
```

每个候选只接收自己的题目文件；`catalog.json` 留给评测者管理。`--tasks coding` 选择 C01–C10，`research` 选择 R01–R06，`required` 选择这 16 题，`optional` 选择 X01–X05，`video` 选择 X04/X05。`list --tasks all` 可查看当前安装版本的完整题目注册表；需要精确子集时直接写题号。

代码种子会生成参数变体。科研/媒体题面固定，换 seed 标签不会产生新的科学样本。这类固定题采用公开 seed 17，重复尝试另外建运行记录。

HTML 应完整下载、打开并展开阅读材料。GitHub 预览截图不是完整输入；文字 harness 读取 base64 字符串，不等于获得视觉证据。应通过其真实多模态输入接口提供内嵌图像，否则明确记录模态限制。

### 新增可选视频测试：选择 A 或 B

```bash
# 选择 A 模式：
python -m nrb_v1 generate-pack --task X04 --dest candidates/X04
# 或选择 B 模式：
python -m nrb_v1 generate-pack --task X05 --dest candidates/X05
```

这是同一个可选视频测试的两种模式：X04/A 为文字驱动制作，X05/B 为参考视觉重建。只运行选定模式，或明确启用两者。两题均为 *SIGNAL IN MOTION*：使用给定实拍素材和音轨，制作 10 秒、1920×1080、24 fps、240 帧的 H.264 视频，并完成六段指定场景。只有 X05 包含 `reference.mp4`；X04 候选不能接收或查看它。

生成目录包含 `TASK.md`、`COPY.txt`、`source.mp4`、`soundtrack.wav`、`assets/` 中的字体、`LICENSES/` 和空白 `RUN_RECORD.template.json`。`INPUT_MANIFEST.json` 记录文件大小与 SHA-256 身份，其中 `packet_hash` 覆盖素材包，不只覆盖题面。应保持目录结构完整交付。单独的 `tasks/v1.1/X04.md` 或 `X05.md` 不包含全部媒体输入。两题都不能提供 `demo_project/`、评分端场景参数、QA 记录或完整来源工程。X05 可观察参考，但不能直接复制参考帧作为输出。

视频必交 `output.mp4`、`source.zip`、`README.md`、`LICENSES.md`、`run-record.json`。ZIP 保存可编辑源码，README 写复现命令和依赖，许可说明保留署名及改动，运行记录区分实测用量与未知值。首次输出和重试结果分别保留。剪辑计划、截图或渲染代码都不能代替可播放视频。

## 4. 收集并打包提交

C04 将 `solution.py`、`report.md`、`tests.py` 放入 `received/C04/`。Fortran 题把 `solution.py` 换为 `main.f90`。科学接口及其他要求以具体题面为准。

```bash
python -m nrb_v1 pack --task C04 --from-dir received/C04 \
  --out received/C04.json
python -m nrb_v1 pack --task R01 --from-dir received/R01 \
  --out received/R01.json
python -m nrb_v1 pack --task X04 --from-dir received/X04 \
  --out received/X04.json
```

只执行已收集成果对应的命令。`pack` 会嵌入 UTF-8 文本，将二进制文件编码为 base64，保留相对文件名；拒绝符号链接和不安全路径。当前解码后的全部成果字节上限为 100 MiB。只打包要求的最终成果，不要混入临时帧、缓存或重复输入副本。

提交容器如下，示例文字不是可评分解答：

```json
{
  "task_id": "C04",
  "artifacts": {
    "solution.py": "完整源代码文本",
    "report.md": "完整科学说明",
    "tests.py": "完整独立测试源代码"
  },
  "answer": {}
}
```

只写文件名、远程链接、伪代码或稍后交付的承诺，不等于提交文件内容。

## 5. 自动评分与人工评阅

### 代码题

若只需要自动结果：

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --execution docker --image nrb-v1:local \
  --out results/C04-auto.json
```

生成可人工评阅的完整目录：

```bash
python -m nrb_v1 review-packet --task C04 --seed 17 \
  --submission received/C04.json --execution docker --image nrb-v1:local \
  --dest reviews/C04
```

`review-packet` 自身会执行自动评分，因此前一条命令可省略。它生成题目、`artifacts/`、`submission.json`、`automatic.json` 和空白 `review.json`。

人工评阅科学解释、独立测试、实现和交接质量。应在无答案的隔离环境实际运行候选测试，核查预期值是否独立于实现。不要在评分宿主直接执行未知 `tests.py`，也不要把仓库、Home 或 Docker socket 挂给候选。

### 科研与原有媒体题

```bash
python -m nrb_v1 review-packet --task R01 --seed 17 \
  --submission received/R01.json --dest reviews/R01
```

R02–R06、X01–X03 对应替换题号即可。必须检查真实渲染成果，不能只看源码：图片按目标尺寸查看，HTML 实际操作控件，视频完整观看，音频完整收听。结合[科研详细量表](../v1/research-guide.md)和生成账本评分。

### X04/X05 视频评阅

```bash
python -m nrb_v1 evaluate-skeleton --task X04 \
  --submission received/X04.json --dest reviews/X04
```

`evaluate-skeleton` 准备正式评阅材料，并在 `inputs/` 中附上原素材和 X05 参考，不会自动判断视频质量或认证完成。现有 `review-packet`、`grade` 也支持新题号。两种评阅生成命令都会保留绑定的 `inputs/` 素材包；`evaluate-skeleton` 还附上 `video-rubric.md`。

完整观看 `inputs/source.mp4`，并带声音观看全部 `artifacts/output.mp4`，记录带时间码的发现。X05 还需观看参考，比较场景结构、尺度、运动轨迹、节奏、遮挡和转场。单一像素距离不能代替参考重建评分。记录实际技术测量及规定的媒体评阅信息；无法完成的观察保持未执行。核对工程源码、运行说明和署名许可。

`media_review` 要求记录全部六段：0–1.5、1.5–4、4–5.5、5.5–7、7–8.5、8.5–10 秒。每段填写区间内实际时间码与观察发现，另记原素材/参考观看及输出收听。音轨检查不新增视觉分权重；确实缺声音时写明证据并将音频核心项判失败，无法观察则保持未评。仅有技术探测数据不能补齐这些字段。详见[视频协议](video-protocol.md)。

X04 有七个人工维度，X05 有八个，后者包含参考重建。权重与要求来自各自生成的评阅表，不能套用 X02 科学解释视频量表。

## 6. 使用双语离线评分页

1. 下载 [scorecard.html](scorecard.html)，在现代浏览器中打开，可切换中英文。GitHub 源码预览不会运行评分界面。
2. 导入评分器生成的 `review.json` 和配套 `automatic.json`。自动报告只读；另行打开评阅目录中的真实成果。
3. 填真实评阅身份。每个维度选择 0–4 整数等级，填写具体证据和理由；逐项填写核心责任 pass、fail 或 unassessed。如实填写实际观察，视频还需补齐规定的媒体评阅项。
4. 未完成时导出草稿，缺失等级仍为 `null`。完整性检查导出只验证必填项，不证明已经观察媒体，也不能替代最后的 CLI 校验。
5. 将下载的评阅文件存为 `reviews/C04/review.json`，或用同一评阅目录内的其他文件名，并在下方命令使用该准确路径。旁边必须保留 `automatic.json` 与 `artifacts/`，X04/X05 还需完整保留生成的 `inputs/`，不改动其中内容。可另存空白账本备份。

修改保存在当前浏览器页面内，关闭或刷新前应导出草稿。评分页编辑评阅账本，不执行候选代码、不调用模型，也不会直接写入你的评阅目录。不要通过修改题号、seed、哈希、量表权重、维度或成果清单来绕过不匹配。

合并 C04：

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --review reviews/C04/review.json \
  --out results/C04-final.json
```

完成视频评阅后合并 X04：

```bash
python -m nrb_v1 grade --task X04 \
  --submission received/X04.json --review reviews/X04/review.json \
  --out results/X04-final.json
```

CLI 会重新核对当前评分器、题面、提交、自动证据与实际成果字节。X04/X05 还会验证评阅目录内实际输入媒体、字体、许可说明和清单，文件被改动或含符号链接会被拒绝。评阅后修改提交，需要重新生成评阅包。LLM 评阅须记录模型和评阅提示词指纹，结论始终为暂评，不能与人工评阅混算。

## 7. 按实际选题范围汇总

单题：

```bash
python -m nrb_v1 summarize --tasks C04 \
  --reports results/C04-final.json --out results/C04-summary.json
```

明确的题目子集，先收齐对应提交与评阅：

```bash
python -m nrb_v1 grade-suite --tasks C04,C06 --seed 17 \
  --submissions received --reviews reviews --execution docker \
  --out results/selected-final.json
python -m nrb_v1 summarize --tasks C04,C06 \
  --reports results/selected-final.json --out results/selected-summary.json
```

`grade-suite` 按 `received/C04.json`、`received/C06.json` 等找提交，按 `reviews/C04/review.json` 等找评阅。所选题缺提交保留失败行，缺评阅保留待评。只有范围确实是全部十道代码题时才使用 `--tasks coding`，不能把两题均分当十题结果。

若已明确启用并评阅两种视频模式：

```bash
python -m nrb_v1 summarize --tasks X04,X05 \
  --reports results/X04-final.json results/X05-final.json \
  --out results/video-profiles.json
```

输出保留视频 A、B 两个独立画像。多个轨道不合成总分。不同模型、配置、人工/LLM 评阅队列或重复尝试不能塞进同一汇总；重复 task/seed 会被拒绝，应分别汇总每次尝试。

### 关键结果字段

| 字段 | 含义 |
|---|---|
| `auto_points` / `auto_scored_max` | 自动实得分及已覆盖分值；代码题满分 70 |
| `review_points` / `total` | 人工分与完整总分；未完成保持 `null` |
| `completion_status` | `failed`、`infrastructure_unscored`、`pending_review` 或 `complete` |
| `critical_failures` / `pending_items` | 核心失败和待评项，两者都要看 |
| `quality_qualified` | 核心完成且完整总分 ≥80 才为 true |
| `completion_authority` | 人工判断或 LLM 暂评 |
| `cohort_check` | 已核对的配置与缺失来源记录 |
| `comparison_eligible` | 有记录时表示运行器明确的可比较资格；缺字段不证明条件受控 |

自动 70/70 仍需人工评阅。基础设施缺失保留未评。同一提交既缺成果又无法执行时，可能显示 `failed`，同时在 `pending_items` 保留未知检查；不能只读状态而忽略证据。

## 8. 耗时、token 与复现记录

记录模型/服务商/版本、准确输入哈希、harness 与版本、提示词/设置、工具/skills、网络条件、硬件、预算、重试/best-of-N 规则及人工干预，保留原始输出与服务商日志。

有测量时分别记录端到端耗时、模型生成、渲染和下载耗时。只拿文件执行 `grade`，无法反推出生成时间、token 或成本，这些字段保持 `null`。命令运行器记录子进程总耗时，不是纯模型推理耗时，也不推测服务商 token 用量。不能把渲染时间称为模型速度，也不能把未知值补成零。

视频可从[运行记录模板](../../sources/v1.1/signal-in-motion/evaluator/run_record.template.json)开始，保留真实测量及其方法。候选超时属于任务结果，编译器/容器不可用属于基础设施问题。

## 9. Harness 接入

所有任务都可采用文件交付流程。Inspect AI、promptfoo、Harbor 自动适配器只支持代码题；视频使用真实文件与人工媒体评阅。

```bash
python -m nrb_v1 export --format jsonl --tasks C04 --seed 17 \
  --dest exports/jsonl-C04
python -m nrb_v1 export --format promptfoo --tasks C04 --seed 17 \
  --dest exports/promptfoo-C04
python -m nrb_v1 export --format harbor --tasks C04 --seed 17 \
  --image nrb-v1:local --dest exports/harbor-C04
```

仓库固定接入版本为 Inspect AI 0.3.281、promptfoo 0.124.1、Harbor 0.24.0。固定 Harbor 运行时需要 Python 3.12+；promptfoo 需要 Node.js 22.22.0+，仓库 CI 配置使用 Node 24。这些是可选依赖，不是人工评分的前置要求。服务商配置与执行示例见 [harness 指南](../v1/usage.md)。

Inspect 默认是 response-only；promptfoo 导出后的默认 provider 是不调用模型的空 mock。Harbor 分离候选与 verifier 容器，应保留该边界。框架标量只表示自动分/70。

原生 `run --command-json` 不传递 X04/X05 媒体包；对其支持的题目，它在宿主启动进程，新建候选目录不是安全隔离。正式闭卷应通过独立隔离 wrapper 运行，填写 `--model-label`、`--harness-label`、`--metadata`。文件协议 mock 不能登记为真实模型作答。

## 10. V1.1 可比性与验证

完整变化见[发布说明](release-notes.md)与[评分修复记录](../v1/scoring-fixes-20261017.md)。V1.1 修正数值输出类型、导入/初始化异常处理、独立残差核验，以及汇总资格与同队列配置核对。实数物理量允许等价 JSON 整数/浮点表示，离散计数仍要求精确整数；初始化失败不能冒充题目某个输入要求的异常；自报零残差不能代替独立方程检查。

评分逻辑变更后，保留原成果，但用同一固定评分器重新生成评阅/报告。不能改历史报告哈希后继续使用，也不能混用新旧报告。题面没变，不代表评分版本可互换。已知配置冲突会拒绝汇总，缺失来源仍保持未知。公开测试与参考结果不能校准真实模型表现。

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution docker --image nrb-v1:local \
  --out validation-run.json
```

核对[精确 commit 对应的 CI](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml)。[V1.0 历史验证](../v1/validation.md)只适用于其记载的提交。本地通过、存在 CI 配置、远程 CI 真正完成，是三种不同证据。

## 11. 常见问题

- **输出已存在：**换新目标路径，保留旧运行证据，不静默覆盖。
- **Docker、镜像或编译器不可用：**修复评分环境后重评，不把基础设施缺失算成模型零分。
- **评阅绑定不匹配：**使用同一固定评分器和原提交，恢复配套 `automatic.json` 与成果，或重建评阅包；不要改哈希。
- **缺少必需观察：**实际打开相应成果并填写证据，否则保持未评。
- **评分页可导入导出，CLI 仍拒绝：**CLI 还检查本地文件字节与评分器身份。评阅文件需与原 `automatic.json`、`artifacts/` 保持同一目录，X04/X05 还需保留未修改的 `inputs/`。
- **视频输入不齐：**使用 `generate-pack`，只下载题面 Markdown 不会获得实拍素材、音轨、字体或 X05 参考。
- **混合配置或重复报告：**拆分模型、配置与尝试，只汇总本轮指定题号。
- **最终均分为空：**检查缺题、未执行、未评阅和不可比较标记，不从成功子集补造总均分。

## 12. 来源许可

仓库 [MIT 许可](../../LICENSE)覆盖其代码、文档和原创合成内容。论文与图像保留各自许可：P1/P3 为 CC BY 4.0，P2 为 CC0 1.0，见[供给范围与署名](../../sources/v1/README.md)。

X04/X05 的 *Tears of Steel* 实拍素材属于 Blender Foundation，适用 CC BY 3.0。提供片段及改编参考应保留署名、许可链接和改动说明；DejaVu 字体保留 Bitstream Vera/DejaVu 条款。详见[视频许可状态](../../sources/v1.1/signal-in-motion/PACKAGE_LICENSE_STATUS.md)及生成包中的 `LICENSES/`。仓库 MIT 不覆盖第三方素材，收录素材不表示作者或演员背书。
