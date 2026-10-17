# NRB V1.1 · X04 · SIGNAL IN MOTION · 文字驱动制作

用所附 source.mp4 制作一支原创动态排版短片：10.000 秒，1920×1080，24 fps，共 240 帧，输出可播放的 H.264 MP4。主题是“人把信号转化成运动”。本赛道没有参考成片，请独立完成视觉设计。

## 输入与风格

source.mp4 来自 Tears of Steel 镜头 04_3b 的前 10 秒：一位穿浅色连体服的男子查看手持黑色面板。保留人物身份、服装、道具及自然动作，连续使用完整 10 秒，不循环、不变速，不要求他表演新动作。通过裁切、粗遮罩和绿幕抠像移除棚内设备与背景，保留人物及干净轮廓。人物脚下有棕色垫子，可用局部遮罩或有意设计的前景/舞台遮挡处理；不要把棕垫与棚内设备带进成片。

统一使用深海军蓝背景、冰青信号光、暖白大字和少量洋红点缀；风格像精致的未来信号台。以原创几何、文字和代码驱动的运动设计为主，不依赖外部图片或手绘素材。人物与画面融为一体，不带着原片矩形边框。

## 六个连续段落

1. **0–1.5 s｜SIGNAL IN MOTION**：人物居中，背后多层径向光晕扩张；大标题弹入，有短促、可读的位移抖动。
2. **1.5–4 s｜STAY IN ORBIT**：文字绕人物运行。必须看出空间轨道和尺度变化，并至少发生一次“人物后方 → 人物前方”的真实遮挡切换；不能只整体调透明度。
3. **4–5.5 s｜CAPTURE / SPLIT / RECOMBINE**：画面变为三个同时可见的竖向面板，各显示同一人物的不同裁切或缩放，并分别显示这三个词。面板进入与汇合都有运动。
4. **5.5–7 s｜RIDE THE WAVE**：连续波形和流动带状元素穿过画面，文字沿波势运动；至少一条带状元素与人物发生清楚的前后遮挡。
5. **7–8.5 s｜LOCK ON**：用六边形孔径收拢再展开完成一次非矩形虹膜转场。孔径边缘有信号光，文字清楚可读，过渡后人物仍在新画面中。
6. **8.5–10 s｜SIGNAL RECEIVED**：人物落在抽象舞台/发光基座上，少量几何彩屑释放；结尾大字稳定落定，最后至少 0.5 秒可读，不能突然截断。

六段顺序和主要时间范围保持一致，允许短暂重叠转场。动画应连续、缓动清楚，复杂效果不能遮没人物或淹没文案。对照 COPY.txt 逐字检查；只需这些英文文案，不添加产品、品牌或演员代言信息。

## 交付与评估

交付 output.mp4，以及可复现的代码/工程、最短运行说明和实际使用的第三方资产许可。将统一提供的 soundtrack.wav 原样合入成片，不另用音乐；保留 LICENSES 中的来源与署名。优先使用代码实现合成、文字和几何动效。

按技术交付 10、时间结构 15、绿幕合成 15、排版与文字 15、运动设计 20、遮挡与空间 10、视觉完成度 15 分评估。不要求与任何未提供的视频相同。报告实际使用的工具和任何未完成项；不知道 token、成本或耗时的项目写“未提供”，不要猜测。


## NRB V1.1 固定交付合同 / Required delivery

本题为可选视频质量赛道；不计入科学编程或科研总分。每题新会话、新工作目录，A/B 不共享候选上下文。仅使用本包和已授权的本地工具，不访问仓库、作者演示代码、评审材料、其他会话或外部素材。无法观看输入视频或无法制作视频时，应记录 unavailable，不得伪称已观看、渲染或评分；这类能力不可用的运行不进入启用轨道的比较分母。

交付 output.mp4、source.zip（完整可编辑代码/工程）、README.md（运行命令、依赖、实际运行与限制）、LICENSES.md（来源/署名/许可/修改说明）和 run-record.json。记录模型/版本、工具、预算、尝试次数、人工干预、实际测得耗时与输入/输出哈希；未暴露的 token、耗时与费用填 null。可使用包内 RUN_RECORD.template.json 作为起点，不能把 not_run 改成成功而没有实际执行。

This optional task is scored separately from coding/research and from the other video track. Use a fresh session and isolated workspace for each track. Submit output.mp4, source.zip (editable project), README.md, LICENSES.md and run-record.json. Do not access repository/evaluator/reference implementation files. Report unavailable modalities honestly; unavailable runs are excluded from the enabled-track comparison denominator. Record measured usage only; unknown values are null. Keep first output, retries and human intervention in the record. Read the entire source video; track B must also watch the entire supplied reference. A never receives the reference.

视觉质量人工 100 分，每项为整数 0–4 级，得分＝权重×等级/4。原样合入给定音轨；音频单独核对，不给视觉总分新增权重。不要把作者参考演示登记为模型实测。
