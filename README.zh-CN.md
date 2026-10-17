# NuLl's Research Benchmark · V1.1

**简体中文** · [English](README.en.md) · [详细使用指南](docs/v1.1/usage.zh-CN.md) · [离线评分页](docs/v1.1/scorecard.html)

面向日常科研和创作交付的能力基准：**10 道科学编程题、6 道科研工作流题、3 道原有可选扩展，以及 1 个新增可选视频测试（A/B 两种模式）**。每题要求可检查的真实成果，分别记录分数、核心责任是否完成，以及仍未评估的部分。

V1.1 新增含 A/B 两种可选模式的视频测试、双语人工评分页，并修正评分器。原有 19 道 V1.0 候选题面保持冻结。**即使题面未变，V1.1 成绩也不能与旧评分器报告混算**；比较时应使用同一固定评分器重新评阅保留的提交。

这是公开开发基准。难度是设计先验，尚未通过真实模型表现校准。参考解、错误候选、mock 和基础设施测试都不登记为 AI 成绩。

## 先选你关心的任务

| 题目 | 评测内容 | 评分 |
|---|---|---|
| C01–C05 | 测量 CSV、bootstrap、导热求解器修复、多层薄膜光学、刚性积分 | 自动 70 + 人工 30 |
| C06–C10 | Fortran 漂移扩散、逆热扩散、各向异性椭圆方程、漂移扩散–Poisson 耦合、反应扩散反演修复 | 自动 70 + 人工 30 |
| R01–R03 | 可编辑科研图、Python 绘图、保守英文润色 | 人工 100 |
| R04–R06 | 根据证据写结果/讨论、论文精读与有界复现、迷你综述 | 人工 100 |
| X01–X03 | 可交互 HTML、科学解释视频、原创器乐 | 人工 100；可选 |
| 新增视频选项 · X04/A 或 X05/B | A：根据文字说明制作 10 秒动态设计；B：重建给定参考成片 | 每种模式人工 100，A/B 分别呈现 |

C06、C09 使用 Fortran 2008，其余代码题使用 Python。具体合同见[原有单文件题目](tasks/v1.0/)与 [V1.1 视频题目](tasks/v1.1/)。X04/X05 必须生成带素材的完整题包，不能只发 Markdown 说明。原有 X02 科学解释视频题保持不变。

新增视频选项不进入默认核心范围，可选择 A（`X04`）、B（`X05`），或明确启用两者。代码、科研、原有可选媒体、视频 A（`optional_video_a`）、视频 B（`optional_video_b`）分别呈现能力画像；不把科研与娱乐创作加成一个总分，也不把 A/B 成绩互换。

## 从一道题开始

### 1. 准备评分端

需要 Python 3.11+ 和 Git。执行未知代码提交需要 Docker。以下命令都在**评测者环境**运行：

```bash
git clone https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark.git
cd NuLl-s_Research_Benchmark
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
python -m nrb_v1 --version
python -m nrb_v1 identity

docker build -t nrb-v1:local -f environments/v1/Dockerfile .
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活。Docker 镜像已提供 GNU Fortran 和科学计算/媒体工具；采用 Docker 评分时，不需另装宿主 Fortran 编译器。只导题、打包或人工评阅科研/媒体题，不需要 Docker。

### 2. 只把本题输入交给候选

例如只测 C04：

```bash
python -m nrb_v1 export --format files --tasks C04 --seed 17 \
  --dest candidates/C04-s17
```

把 `candidates/C04-s17/C04.md` 交给新会话、隔离环境中的候选。不要给仓库链接、评分器目录、参考实现、历史提交或评测者文件。只有一个新目录，并不能隔离具备工具访问能力的 agent。

视频题使用：

```bash
python -m nrb_v1 generate-pack --task X04 --dest candidates/X04
# 若改测视频 B：
python -m nrb_v1 generate-pack --task X05 --dest candidates/X05
```

候选只拿所选生成目录，其中包含题面、实拍素材、音轨、字体和许可说明；只有 X05 获得参考视频。两题都不能拿到演示渲染器和评分端专用材料。

### 3. 收集真实成果，生成评阅包

C04 作答结束后，将真实文件放入 `received/C04/`：

```bash
python -m nrb_v1 pack --task C04 --from-dir received/C04 \
  --out received/C04.json
python -m nrb_v1 review-packet --task C04 --seed 17 \
  --submission received/C04.json --execution docker \
  --dest reviews/C04
```

下载[评分页](docs/v1.1/scorecard.html)，用浏览器打开，导入 `reviews/C04/review.json` 和同目录的 `automatic.json`。实际检查源码、说明和测试结果，填写等级、证据、核心责任和评阅身份。完成后把导出的评阅文件放回原评阅目录，保留原成果文件与 `automatic.json`。

```bash
python -m nrb_v1 grade --task C04 --seed 17 \
  --submission received/C04.json --review reviews/C04/review.json \
  --out results/C04-final.json
python -m nrb_v1 summarize --tasks C04 \
  --reports results/C04-final.json --out results/C04-summary.json
```

评分页是评阅编辑器。最终 CLI 会核对评阅账本与提交、成果字节、量表、评分器身份的绑定。新输出路径不能已经存在。

## 怎样读分数

- 编程题自动分满分是 **70**，不等于完整质量满分 100；其余 30 分与核心责任需要人工评阅。
- 科研和媒体题必须实际观察。读取元数据、抽帧或看脚本，不能代替观看、收听最终成果。
- 执行环境不可用、人工评阅未完成，应保留未评。未知耗时、token 和成本保持 `null`，不能填成 0。
- `complete` 表示核心检查和评阅均完成；`quality_qualified` 还要求完整总分至少 80。高分不能抵消核心失败。
- 人工评阅与 LLM 暂评单独记录。只有文件分数、缺少模型和 harness 来源记录，不足以证明完成了同条件模型比较。

视频完整流程、只测部分题目、离线/资源增强条件、harness 接入、计时与排错见[详细使用指南](docs/v1.1/usage.zh-CN.md)。[评分规则](docs/v1/scoring.md)解释科学判断，[科研详细量表](docs/v1/research-guide.md)覆盖 R01–R06 与 X01–X03。

## 复现与验证

固定评分器 commit、内容指纹、题包/素材哈希、模型版本、工具/skills、预算、环境镜像、种子和评阅身份。不同模型、配置、尝试分别建输出目录。

```bash
python -m unittest discover -s tests_v1 -v
python -m nrb_v1 selftest --tasks coding --seeds 0,17,2026 \
  --include-mutants --execution docker --image nrb-v1:local \
  --out validation-run.json
```

这些命令验证基础设施和已知控制，不调用候选模型。`trusted` 仅供受控参考自检，且需准备宿主依赖；不能用于未知提交。

请在 [GitHub Actions](https://github.com/Mr-NuLl-01/NuLl-s_Research_Benchmark/actions/workflows/ci.yml) 核对实际使用 commit 的结果。[V1.0 验证记录](docs/v1/validation.md)是历史证据，不能证明后续 V1.1 修改已通过。旧 `nrb` CLI 与 `questions/` 属于 V0.2；此处使用 `nrb-v1` 或 `python -m nrb_v1`。

## 许可

仓库代码、文档和原创合成题目保留现有 [MIT 许可](LICENSE)。第三方材料继续适用各自许可：

- Weissgerber（2015）、Crameri（2020）：CC BY 4.0；Rougier（2014）：CC0 1.0。完整范围与署名见[科研来源说明](sources/v1/README.md)。
- X04/X05 实拍素材：Blender Foundation 的 *Tears of Steel* 镜头 04_3b，CC BY 3.0。提供的片段经过选帧、色彩与编码转换；参考成片的进一步改编也应保留署名。
- DejaVu 字体保留 Bitstream Vera/DejaVu 条款，不改标为 CC0 或 MIT。

再分发媒体时保留[视频包许可说明](sources/v1.1/signal-in-motion/PACKAGE_LICENSE_STATUS.md)及随附 `LICENSES/`。引用基准时标注精确 commit 和素材来源；不得暗示原作者或演员认可该基准或相关产品。
