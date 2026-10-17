# NRB V1.1 optional video / 可选视频

X04: prompt-driven green-screen motion design / 文字驱动绿幕动态排版。
X05: visual reconstruction with a supplied reference / 参考视觉重建。

The .md files here are instructions only, not standalone candidate packets.
此处题面不能单独交给候选；需使用命令生成完整媒体目录。

    python -m nrb_v1 generate-pack --task X04 --dest /tmp/candidate-X04
    python -m nrb_v1 generate-pack --task X05 --dest /tmp/candidate-X05

Use a fresh independent session for each. A must never receive B's reference, the
author implementation or evaluator files. Give the generated directory only.
Both tracks are optional manual 100-point scores and are reported separately.

[Protocol / 评估协议](../../docs/v1.1/video-protocol.md) ·
[Original 19 V1 tasks / 原19题](../v1.0/)
