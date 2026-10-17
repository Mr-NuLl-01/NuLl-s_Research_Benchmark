# NRB09 · 从合成振子数据制作可编辑科研图

制作一张可编辑的三面板科研图，展示一个经典弹簧–阻尼–质量系统、给定模型与合成观测、观测减模型的残差。
这不是拟合任务：模型列已经给出，不能把生成模型称为拟合结果，不能添加虚构误差棒/置信带。数据、参数均为本题合成。
自由选择面板排布、颜色、留白和字体层次，图中文字用英文。不能把所有内容做成一张不可编辑的位图。
提交 artifacts/figure.svg（在 artifacts 对象里键名为 figure.svg）和 caption.md。answer 必须包含：
{"n_observations":整数,"rmse_m":数值,"data_sha256":"data.csv原始UTF-8字节SHA256",
 "data_origin":"synthetic","model_status":"fixed_not_fitted","uncertainty_band":false,
 "x_limits":[xmin,xmax],"signal_y_limits":[ymin,ymax],"residual_y_limits":[ymin,ymax],
 "panel_bounds":{"signal":[left,top,width,height],"residual":[left,top,width,height]}}
绘图绑定协议用于核验真实绘出的数据，不规定设计风格：
1. 根 svg 带 viewBox；所有数据标记使用根 viewBox 坐标，标记及其祖先不得有 transform。两个 panel_bounds 指真正的数据绘图区，必须在画布内且不重叠。
2. id=observations 的 g 中包含按CSV顺序排列的 circle，cx/cy 为线性映射后的观测坐标；每个circle有显式 fill（#RRGGBB）。
3. id=signal-model 的 polyline 按时间递增，包含映射后的全部CSV模型点；可按 parameters.json 的公式添加更密的点以获得平滑曲线；显式 stroke（#RRGGBB），fill=none。
4. id=residual-points 的 g 中包含同序 circle，纵坐标为 observed_m-model_m 的线性映射，颜色与 observations 一致。
5. id=legend-observation 的 circle 与观测同色；id=legend-model 的 line 与模型同色。观测与模型须用不同颜色且可通过点/线区分。
6. 示意图区应包含 id=mass、spring、damper 的可见图元；id=displacement-arrow 是带 marker-end 的 line，x2>x1、y2=y1 表示定义的正位移向右。箭头不是完整力学受力图。
7. 保留可编辑 text，至少包含标签 Time (s)、Displacement (m)、Residual (m)、Synthetic observations、Fixed model。
8. SVG 只能使用内嵌静态矢量与文字；不允许脚本、外部链接、位图或外部样式。颜色/字体使用SVG属性，不用 style 元素或 style 属性；不使用 mask/filter/clip-path 隐藏内容。不得用隐藏元素代替可见图。
自动检查只覆盖数据绑定、文件与部分科学语义。最终可读性、图注证据强度、图形质量须看实际渲染后独立评分。


## 提交协议 / Submission contract
返回一个 UTF-8 JSON 对象（可使用单个 json 代码块），或将该对象写入 submission.json。
顶层格式：{"task_id":"NRB09","answer":{...},"artifacts":{"relative/path":"完整文件内容"}}。
answer 使用本题字段。代码、推导、图和修订稿放入 artifacts，字符串须包含完整内容，不能只返回本机路径。
数值使用 JSON number，缺失使用 null；不接受 NaN/Infinity。不同题目独立完成。
输入均为本基准原创构造的合成材料，不代表真实实验或真实未发表研究。
封闭资料轨道只使用本题材料与通用知识。不得查找本基准源码、答案或评分器。
每题自动核验 70 分，另有以下三项各 10 分的独立质量审阅。

[
  {
    "id": "scientific_caption",
    "title": "科学叙述与图注",
    "anchors": {
      "0": "图注把合成/给定模型说成实验/拟合，或歪曲残差。",
      "5": "身份和单位正确，图注可理解，但模型与残差的关系说明不完整。",
      "10": "图注准确自足，明确合成来源、固定模型和残差定义，不添加未经支持的不确定度。"
    }
  },
  {
    "id": "rendered_legibility",
    "title": "实际渲染可读性",
    "anchors": {
      "0": "未渲染核查、严重遮挡/溢出/隐形图元或数据不可读。",
      "5": "基本清楚，局部标注、大小或排版仍有明显问题。",
      "10": "在约180 mm展示宽度下文字、数据和示意均清楚；无碰撞裁切，留白和面板关系合理。"
    }
  },
  {
    "id": "visual_reasoning",
    "title": "图形表达与视觉层次",
    "anchors": {
      "0": "装饰掩盖科学信息或所有对象机械等权。",
      "5": "点线、颜色和面板组织能区分主要信息。",
      "10": "示意、预测、观测与残差形成清晰叙述；色彩一致且有冗余编码，细节服务问题而非模板。"
    }
  }
]

Required artifacts: figure.svg, caption.md


## 输入文件：data.csv
<BEGIN_INPUT_FILE>

t_s,observed_m,model_m
0.0,0.0176034709,0.0184080436
0.2,0.0121612636,0.0125354129
0.4,-0.0006871005,0.0003359153
0.6,-0.0110237937,-0.0109397595
0.8,-0.0145027182,-0.0152048159
1.0,-0.0113227163,-0.0107617081
1.2,-0.0018970005,-0.0008326094
1.4,0.0083902222,0.0086506261
1.6,0.0130741636,0.0125387285
1.8,0.0091471042,0.0092119232
2.0,0.0009291468,0.0011459003
2.2,-0.0069497975,-0.0068148676
2.4,-0.0113684823,-0.0103233637
2.6,-0.0074808906,-0.0078637889
2.8,-0.0021492792,-0.0013240301
3.0,0.0046723739,0.0053465335
3.2,0.0075759522,0.0084855233
3.4,0.007428995,0.0066957597
3.6,0.0014266902,0.0014042069
3.8,-0.0028329289,-0.0041753588
4.0,-0.0070962121,-0.0069633397


<END_INPUT_FILE>


## 输入文件：parameters.json
<BEGIN_INPUT_FILE>

{
  "A_m": 0.018408043580644316,
  "gamma_per_s": 0.23796190552586483,
  "omega_rad_per_s": 3.8768109403630167,
  "model": "A*exp(-gamma*t)*cos(omega*t)",
  "status": "fixed generating model; not fitted to observations",
  "data_origin": "synthetic",
  "uncertainty_band": "not supplied"
}

<END_INPUT_FILE>
