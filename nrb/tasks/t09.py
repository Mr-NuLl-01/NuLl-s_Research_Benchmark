"""NRB09: editable scientific figure from a synthetic damped oscillator."""
from __future__ import annotations
import csv
import hashlib
import io
import json
import math
import random
import re
import xml.etree.ElementTree as ET
from nrb.checks import check, close, numbers_close
from nrb.rendering import parse_static_svg, svg_viewbox


def build(seed=0):
    rng = random.Random(seed + 9001)
    amplitude = rng.uniform(0.018, 0.029)
    gamma = rng.uniform(0.20, 0.35)
    omega = rng.uniform(3.2, 4.4)
    n = 21 + 2 * (seed % 4)
    rows = []
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["t_s", "observed_m", "model_m"])
    for i in range(n):
        t = i * 0.2
        model = amplitude * math.exp(-gamma * t) * math.cos(omega * t)
        observed = model + rng.gauss(0, 0.00065)
        row = [round(t, 8), round(observed, 10), round(model, 10)]
        rows.append(row)
        writer.writerow(row)
    data = out.getvalue()
    params = {"A_m": amplitude, "gamma_per_s": gamma, "omega_rad_per_s": omega,
              "model": "A*exp(-gamma*t)*cos(omega*t)", "status": "fixed generating model; not fitted to observations",
              "data_origin": "synthetic", "uncertainty_band": "not supplied"}
    prompt = """制作一张可编辑的三面板科研图，展示一个经典弹簧–阻尼–质量系统、给定模型与合成观测、观测减模型的残差。
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
6. 示意图区应包含 id=mass、spring、damper 的可见图元；这些图元及其祖先也使用根viewBox坐标，不加transform（可用含实际图元的g）；id=displacement-arrow 是带 marker-end 的 line，x2>x1、y2=y1 表示定义的正位移向右。箭头不是完整力学受力图。
7. 保留可编辑 text；位置、字号、半径与线宽用不带单位的viewBox数值。文字可用rotate(angle cx cy)旋转，关键文字/示意不使用其他transform。至少包含标签 Time (s)、Displacement (m)、Residual (m)、Synthetic observations、Fixed model。
8. 以180 mm宽度展示时，数据点直径至少0.2 mm、关键线宽至少0.08 mm，祖先opacity乘积与继承的绘制透明度合并后至少0.3。这是排除近乎不可见对象的暂定工程阈值，并非期刊通用标准。示意g/marker必须含有实际可见图元；标签与示意落在画布内。
9. SVG 只能使用内嵌静态矢量与文字；不允许脚本、外部链接、位图或外部样式。颜色/字体使用SVG属性，不用 style 元素或 style 属性；不使用 mask/filter/clip-path 隐藏内容。不得用隐藏元素代替可见图。
自动检查只覆盖数据绑定、文件与部分科学语义。最终可读性、图注证据强度、图形质量须看实际渲染后独立评分。
"""
    return {"id": "NRB09", "seed": seed, "title": "从合成振子数据制作可编辑科研图", "domain": "scientific_visualization",
            "prompt": prompt, "files": {"data.csv": data, "parameters.json": json.dumps(params, indent=2)},
            "expected": {"rows": rows, "parameters": params, "rmse": math.sqrt(sum((o-m)**2 for _, o, m in rows)/n),
                         "data_hash": hashlib.sha256(data.encode()).hexdigest()},
            "rubric": [
                {"id": "scientific_caption", "title": "科学叙述与图注", "anchors": {"0": "图注把合成/给定模型说成实验/拟合，或歪曲残差。", "5": "身份和单位正确，图注可理解，但模型与残差的关系说明不完整。", "10": "图注准确自足，明确合成来源、固定模型和残差定义，不添加未经支持的不确定度。"}},
                {"id": "rendered_legibility", "title": "实际渲染可读性", "anchors": {"0": "未渲染核查、严重遮挡/溢出/隐形图元或数据不可读。", "5": "基本清楚，局部标注、大小或排版仍有明显问题。", "10": "在约180 mm展示宽度下文字、数据和示意均清楚；无碰撞裁切，留白和面板关系合理。"}},
                {"id": "visual_reasoning", "title": "图形表达与视觉层次", "anchors": {"0": "装饰掩盖科学信息或所有对象机械等权。", "5": "点线、颜色和面板组织能区分主要信息。", "10": "示意、预测、观测与残差形成清晰叙述；色彩一致且有冗余编码，细节服务问题而非模板。"}}]}


def _mapped(rows, xb, yb, bounds, column):
    x0, y0, width, height = bounds
    return [(x0+(r[0]-xb[0])/(xb[1]-xb[0])*width,
             y0+(yb[1]-(r[1]-r[2] if column == 3 else r[column]))/(yb[1]-yb[0])*height) for r in rows]


def reference(case):
    rows = case["expected"]["rows"]
    amp = max(abs(v) for r in rows for v in r[1:]) * 1.2
    residual = max(abs(r[1]-r[2]) for r in rows) * 1.35
    answer = {"n_observations": len(rows), "rmse_m": case["expected"]["rmse"],
              "data_sha256": case["expected"]["data_hash"], "data_origin": "synthetic",
              "model_status": "fixed_not_fitted", "uncertainty_band": False,
              "x_limits": [0, rows[-1][0]], "signal_y_limits": [-amp, amp], "residual_y_limits": [-residual, residual],
              "panel_bounds": {"signal": [450, 90, 675, 300], "residual": [450, 495, 675, 135]}}
    obs = _mapped(rows, answer["x_limits"], answer["signal_y_limits"], answer["panel_bounds"]["signal"], 1)
    par = case["expected"]["parameters"]
    dense_rows = []
    for i in range((len(rows)-1)*20+1):
        t = i*.01
        m = par["A_m"]*math.exp(-par["gamma_per_s"]*t)*math.cos(par["omega_rad_per_s"]*t)
        dense_rows.append([t, m, m])
    model = _mapped(dense_rows, answer["x_limits"], answer["signal_y_limits"], answer["panel_bounds"]["signal"], 2)
    resid = _mapped(rows, answer["x_limits"], answer["residual_y_limits"], answer["panel_bounds"]["residual"], 3)
    circles = lambda pts: "\n".join(f'<circle cx="{x:.5f}" cy="{y:.5f}" r="4" fill="#147D92"/>' for x, y in pts)
    line = " ".join(f"{x:.5f},{y:.5f}" for x, y in model)
    labels = []
    for name, yr in (("signal", answer["signal_y_limits"]), ("residual", answer["residual_y_limits"])):
        x, y, w, h = answer["panel_bounds"][name]
        for i in range(5):
            px = x+w*i/4
            labels.append(f'<line x1="{px}" y1="{y+h}" x2="{px}" y2="{y+h+5}" stroke="#64748B" stroke-width="1"/>')
            labels.append(f'<text x="{px}" y="{y+h+25}" text-anchor="middle" font-size="16">{rows[-1][0]*i/4:.1f}</text>')
        for i in range(3):
            py = y+h*i/2
            val = yr[1]-(yr[1]-yr[0])*i/2
            labels.append(f'<text x="{x-12}" y="{py+5}" text-anchor="end" font-size="16">{val:.4f}</text>')
        labels.append(f'<path d="M {x} {y} V {y+h} H {x+w}" stroke="#475569" stroke-width="1" fill="none"/>')
        labels.append(f'<line x1="{x}" y1="{y+h/2}" x2="{x+w}" y2="{y+h/2}" stroke="#CBD5E1" stroke-width="1" stroke-dasharray="4 4"/>')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 720" width="180mm" height="108mm">
<title>Synthetic damped oscillator: fixed model, observations and residuals</title>
<defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="6" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 Z" fill="#475569"/></marker></defs>
<rect width="1200" height="720" fill="#FFFFFF"/>
<g font-family="Arial, Helvetica, sans-serif" fill="#263446">
<text x="45" y="48" font-size="24" font-weight="bold">a</text><text x="77" y="48" font-size="22">Damped oscillator</text>
<text x="430" y="48" font-size="24" font-weight="bold">b</text><text x="465" y="48" font-size="22">Prediction and observations</text>
<text x="430" y="460" font-size="24" font-weight="bold">c</text><text x="465" y="460" font-size="22">Residual check</text>
<line x1="75" y1="165" x2="75" y2="410" stroke="#64748B" stroke-width="5"/>
<path id="spring" d="M75 235 H100 l12 -18 l24 36 l24 -36 l24 36 l12 -18 H230" fill="none" stroke="#475569" stroke-width="3"/>
<path id="damper" d="M75 340 H138 M138 324 V356 H174 V324 H138 M156 340 H230" fill="none" stroke="#475569" stroke-width="3"/>
<rect id="mass" x="230" y="205" width="90" height="175" rx="8" fill="#E7EBF3" stroke="#5C6682" stroke-width="2"/>
<text x="275" y="300" text-anchor="middle" font-size="24">m</text><text x="138" y="199" font-size="19">spring</text><text x="124" y="390" font-size="19">damper</text>
<line id="displacement-arrow" x1="220" y1="445" x2="330" y2="445" stroke="#475569" stroke-width="2.5" marker-end="url(#arrow)"/>
<text x="253" y="475" font-size="20">+x</text>
<text x="72" y="550" font-size="18">Prescribed generating model</text><text x="72" y="580" font-size="18">No parameter fitting</text>
{''.join(labels)}
<polyline id="signal-model" points="{line}" fill="none" stroke="#8C4E78" stroke-width="2.8"/>
<g id="observations">{circles(obs)}</g><g id="residual-points">{circles(resid)}</g>
<circle id="legend-observation" cx="615" cy="78" r="4" fill="#147D92"/><text x="628" y="84" font-size="17">Synthetic observations</text>
<line id="legend-model" x1="870" y1="78" x2="904" y2="78" stroke="#8C4E78" stroke-width="2.8"/><text x="914" y="84" font-size="17">Fixed model</text>
<text x="785" y="435" text-anchor="middle" font-size="19">Time (s)</text><text x="785" y="680" text-anchor="middle" font-size="19">Time (s)</text>
<text x="372" y="255" transform="rotate(-90 372 255)" text-anchor="middle" font-size="19">Displacement (m)</text>
<text x="372" y="565" transform="rotate(-90 372 565)" text-anchor="middle" font-size="19">Residual (m)</text>
</g></svg>'''
    caption = ("Synthetic damped oscillator. (a) Spring, damper and mass with positive displacement defined to the right. "
               "(b) The fixed generating model and synthetic observations from data.csv; the model was not fitted to these points. "
               f"(c) Residuals are observations minus model, with RMSE {answer['rmse_m']:.6g} m. "
               "No uncertainty band was supplied or inferred.\n")
    return {"task_id": case["id"], "answer": answer, "artifacts": {"figure.svg": svg, "caption.md": caption}}


# Provisional engineering limits for rejecting nearly invisible *essential*
# objects at the task's 180 mm displayed width. These are not journal standards
# or a substitute for actual rendering/reviewer acceptance.
DISPLAY_WIDTH_MM = 180.0
MIN_POINT_DIAMETER_MM = 0.20
MIN_STROKE_MM = 0.08
MIN_EFFECTIVE_OPACITY = 0.30


def _svg_info(text):
    return parse_static_svg(text)


def _inherited(node, parents, attr, default):
    while node is not None:
        if attr in node.attrib:
            return node.attrib[attr]
        node = parents.get(node)
    return default


def _opacity(node, parents, paint):
    """SVG opacity composites at every ancestor; paint opacity is inherited."""
    opacity = float(_inherited(node, parents, paint + "-opacity", "1"))
    while node is not None:
        opacity *= float(node.attrib.get("opacity", "1"))
        node = parents.get(node)
    return opacity


def _stroke_visible(node, parents, view):
    color = _inherited(node, parents, "stroke", "none").strip().lower()
    width = float(_inherited(node, parents, "stroke-width", "1"))
    # A non-scaling stroke is viewport-dependent and outside this protocol.
    return (color not in {"none", "transparent"} and math.isfinite(width)
            and width * DISPLAY_WIDTH_MM / view[2] >= MIN_STROKE_MM
            and _opacity(node, parents, "stroke") >= MIN_EFFECTIVE_OPACITY
            and _inherited(node, parents, "vector-effect", "none") == "none")


def _fill_visible(node, parents):
    return (_inherited(node, parents, "fill", "#000000").strip().lower() not in {"none", "transparent"}
            and _opacity(node, parents, "fill") >= MIN_EFFECTIVE_OPACITY)


def _root_coordinates(node, parents):
    while node is not None:
        if "transform" in node.attrib:
            return False
        node = parents.get(node)
    return True


def _path_vertices(data):
    """Conservative path hull in path coordinates, including curve controls.

    This is a minimum coordinate screen, not a renderer. Curve-control hulls
    can be larger than the painted curve; actual occlusion always needs review.
    """
    pattern = r"[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?"
    tokens = re.findall(r"[A-Za-z]|" + pattern, data)
    if re.sub(r"[A-Za-z]|" + pattern + r"|[\s,]", "", data):
        raise ValueError("Invalid path token")
    counts = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}
    x = y = 0.0
    start = (0.0, 0.0)
    vertices, index, command = [], 0, None
    while index < len(tokens):
        if tokens[index].isalpha():
            command = tokens[index]
            index += 1
            if command.upper() == "Z":
                x, y = start
                vertices.append(start)
                command = None
                continue
        if command is None or command.upper() not in counts:
            raise ValueError("Invalid path command")
        name, relative = command.upper(), command.islower()
        count = counts[name]
        values = [float(v) for v in tokens[index:index+count]]
        if len(values) != count or not all(math.isfinite(v) for v in values):
            raise ValueError("Invalid path coordinates")
        index += count
        if name == "H":
            x = values[0] + (x if relative else 0)
            vertices.append((x, y))
        elif name == "V":
            y = values[0] + (y if relative else 0)
            vertices.append((x, y))
        elif name == "A":
            rx, ry, angle, large, sweep, ex, ey = values
            if min(rx, ry) < 0 or large not in (0, 1) or sweep not in (0, 1):
                raise ValueError("Invalid arc parameters")
            ex, ey = ex + (x if relative else 0), ey + (y if relative else 0)
            # Rotated elliptical arcs remain within this conservative envelope.
            radius = math.hypot(rx, ry)
            vertices.extend(((min(x, ex)-radius, min(y, ey)-radius),
                             (max(x, ex)+radius, max(y, ey)+radius), (ex, ey)))
            x, y = ex, ey
        else:
            coords = [(values[j]+(x if relative else 0), values[j+1]+(y if relative else 0)) for j in range(0, count, 2)]
            vertices.extend(coords)
            x, y = coords[-1]
            if name == "M":
                start = (x, y)
                command = "l" if relative else "L"
    return vertices


def _geometry_box(node):
    name = node.tag.split("}")[-1]
    def number(key, default=None):
        value = float(node.attrib[key] if default is None else node.attrib.get(key, default))
        if not math.isfinite(value):
            raise ValueError("Nonfinite SVG geometry")
        return value
    if name == "rect":
        x, y, w, h = number("x", 0), number("y", 0), number("width"), number("height")
        if min(w, h) <= 0:
            raise ValueError("Empty rectangle")
        return x, y, x+w, y+h
    if name in {"circle", "ellipse"}:
        x, y = number("cx", 0), number("cy", 0)
        rx = number("r") if name == "circle" else number("rx")
        ry = rx if name == "circle" else number("ry")
        if min(rx, ry) <= 0:
            raise ValueError("Empty ellipse")
        return x-rx, y-ry, x+rx, y+ry
    if name == "line":
        pts = [(number("x1", 0), number("y1", 0)), (number("x2", 0), number("y2", 0))]
    elif name in {"polyline", "polygon"}:
        values = [float(v) for v in re.split(r"[\s,]+", node.attrib["points"].strip())]
        if len(values) % 2 or not all(math.isfinite(v) for v in values):
            raise ValueError("Invalid points")
        pts = list(zip(values[::2], values[1::2]))
    elif name == "path":
        pts = _path_vertices(node.attrib["d"])
    else:
        raise ValueError("Not a drawable geometric primitive")
    if len(set(pts)) < 2:
        raise ValueError("Empty geometry")
    return min(x for x, _ in pts), min(y for _, y in pts), max(x for x, _ in pts), max(y for _, y in pts)


def _inside(box, view):
    tol = view[2] * 1e-9
    return (box[0] >= view[0]-tol and box[1] >= view[1]-tol
            and box[2] <= view[0]+view[2]+tol and box[3] <= view[1]+view[3]+tol)


def _visible_graphic(node, parents, view, *, in_marker=False, mm_per_unit=None):
    """At least one nondegenerate painted primitive; empty groups do not count."""
    for child in node.iter():
        if child.tag.split("}")[-1] not in {"rect", "circle", "ellipse", "line", "polyline", "polygon", "path"}:
            continue
        try:
            if not _root_coordinates(child, parents):
                continue
            if not in_marker and not _directly_rendered(child, parents):
                continue
            box = _geometry_box(child)
            if not _inside(box, view):
                continue
            name = child.tag.split("}")[-1]
            width, height = box[2]-box[0], box[3]-box[1]
            filled = name not in {"line", "polyline"} and min(width, height) > 0 and _fill_visible(child, parents)
            stroke_view = view if mm_per_unit is None else [0, 0, DISPLAY_WIDTH_MM/mm_per_unit, 1]
            stroked = _stroke_visible(child, parents, stroke_view)
            physical_scale = DISPLAY_WIDTH_MM / view[2] if mm_per_unit is None else mm_per_unit
            if (filled or stroked) and max(width, height) * physical_scale >= MIN_POINT_DIAMETER_MM:
                return True
        except (ValueError, KeyError, TypeError, OverflowError):
            continue
    return False


def _text_in_canvas(node, parents, view):
    try:
        if not _directly_rendered(node, parents) or not _fill_visible(node, parents):
            return False
        # SVG labels use root coordinates; permit the oracle's ordinary rotated
        # axis labels, while rejecting transforms whose mapping we cannot audit.
        x, y = float(node.attrib.get("x", "0")), float(node.attrib.get("y", "0"))
        size = float(_inherited(node, parents, "font-size", "16"))
        if not all(math.isfinite(v) for v in (x, y, size)) or size <= 0:
            return False
        length = len("".join(node.itertext())) * size * 0.6
        anchor = _inherited(node, parents, "text-anchor", "start")
        x -= length / 2 if anchor == "middle" else length if anchor == "end" else 0
        points = [(x, y-size), (x+length, y-size), (x, y+size*.2), (x+length, y+size*.2)]
        current = node
        while current is not None:
            transform = current.attrib.get("transform")
            if transform:
                values = re.fullmatch(r"rotate\(\s*([-+0-9.eE]+)(?:[\s,]+([-+0-9.eE]+)[\s,]+([-+0-9.eE]+))?\s*\)", transform)
                if not values:
                    return False
                angle, cx, cy = [float(v or 0) for v in values.groups()]
                theta = math.radians(angle)
                points = [(cx+(px-cx)*math.cos(theta)-(py-cy)*math.sin(theta),
                           cy+(px-cx)*math.sin(theta)+(py-cy)*math.cos(theta)) for px, py in points]
            current = parents.get(current)
        return _inside((min(x for x, _ in points), min(y for _, y in points),
                        max(x for x, _ in points), max(y for _, y in points)), view)
    except (ValueError, TypeError, OverflowError):
        return False


def _directly_rendered(node, parents):
    """Definition-area content does not count as drawn data or visible labels."""
    hidden_context = {"defs", "symbol", "marker", "pattern", "clippath", "mask", "metadata", "title", "desc"}
    while node is not None:
        if node.tag.split("}")[-1].lower() in hidden_context:
            return False
        node = parents.get(node)
    return True


def grade(case, submission, execution="none"):
    a = submission.get("answer", {})
    art = submission.get("artifacts", {})
    ex = case["expected"]
    checks = [check("metrics", 10, a.get("n_observations") == len(ex["rows"]) and close(a.get("rmse_m"), ex["rmse"], atol=1e-10)),
              check("provenance", 5, a.get("data_sha256") == ex["data_hash"] and a.get("data_origin") == "synthetic" and a.get("model_status") == "fixed_not_fitted" and a.get("uncertainty_band") is False, critical=True)]
    try:
        root, ids, parents = _svg_info(art.get("figure.svg", ""))
        view = svg_viewbox(root)
        svg_ok = root.tag.split("}")[-1] == "svg" and any(n.tag.endswith("text") and _directly_rendered(n, parents) for n in root.iter())
    except (ValueError, KeyError, TypeError, OverflowError, ET.ParseError, AssertionError):
        svg_ok, ids, parents, root, view = False, {}, {}, None, [0, 0, 0, 0]
    checks.append(check("editable_svg", 5, svg_ok, "SVG syntax, editable text, no scripts/bitmaps/external resources"))
    bounds_ok = False
    try:
        boxes = a["panel_bounds"]
        for name in ("signal", "residual"):
            b = boxes[name]
            assert len(b) == 4 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in b)
            assert b[2] > 0 and b[3] > 0 and b[0] >= view[0] and b[1] >= view[1] and b[0]+b[2] <= view[0]+view[2] and b[1]+b[3] <= view[1]+view[3]
        b, c = boxes["signal"], boxes["residual"]
        assert b[0]+b[2] <= c[0] or c[0]+c[2] <= b[0] or b[1]+b[3] <= c[1] or c[1]+c[3] <= b[1]
        for name in ("x_limits", "signal_y_limits", "residual_y_limits"):
            lim = a[name]
            assert len(lim) == 2 and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in lim) and lim[1] > lim[0]
        assert a["x_limits"][0] <= ex["rows"][0][0] and a["x_limits"][1] >= ex["rows"][-1][0]
        for row in ex["rows"]:
            assert a["signal_y_limits"][0] <= min(row[1:]) <= max(row[1:]) <= a["signal_y_limits"][1]
            assert a["residual_y_limits"][0] <= row[1]-row[2] <= a["residual_y_limits"][1]
        bounds_ok = svg_ok
    except (ValueError, KeyError, TypeError, OverflowError, AssertionError):
        pass
    # A viewBox unit is arbitrary: preserve the same physical geometric
    # tolerance when all coordinates are scaled together.
    xtol, ytol = abs(view[2]) * (0.03/1200), abs(view[3]) * (0.03/720)
    def untransformed(node):
        if not _directly_rendered(node, parents):
            return False
        while node is not None:
            if "transform" in node.attrib:
                return False
            node = parents.get(node)
        return True
    def mark_check(id, column, panel, ylimits):
        if not bounds_ok or id not in ids:
            return False
        try:
            if ids[id].tag.split("}")[-1] != "g":
                return False
            points = list(ids[id])
            target = _mapped(ex["rows"], a["x_limits"], a[ylimits], boxes[panel], column)
            return len(points) == len(target) and all(p.tag.endswith("circle") and untransformed(p) and math.isfinite(float(p.attrib.get("r", 0))) and 2*float(p.attrib.get("r", 0))*DISPLAY_WIDTH_MM/view[2] >= MIN_POINT_DIAMETER_MM and _fill_visible(p, parents) and close(float(p.attrib["cx"]), x, rtol=0, atol=xtol) and close(float(p.attrib["cy"]), y, rtol=0, atol=ytol) for p, (x, y) in zip(points, target))
        except (ValueError, KeyError, TypeError, OverflowError):
            return False
    checks.append(check("observation_geometry", 15, mark_check("observations", 1, "signal", "signal_y_limits"), "CSV coordinates and provisional minimum diameter 0.2 mm/effective opacity 0.3 at 180 mm", critical=True))
    model_ok = False
    if bounds_ok and "signal-model" in ids:
        try:
            node = ids["signal-model"]
            vals = [float(v) for v in re.split(r"[\s,]+", node.attrib["points"].strip())]
            points = list(zip(vals[::2], vals[1::2]))
            required = _mapped(ex["rows"], a["x_limits"], a["signal_y_limits"], boxes["signal"], 2)
            includes_required = all(any(abs(x-px) <= xtol and abs(y-py) <= ytol for px, py in points) for x, y in required)
            params = ex["parameters"]
            bx, by, bw, bh = boxes["signal"]
            ylo, yhi = a["signal_y_limits"]
            xlo, xhi = a["x_limits"]
            formula_ok = True
            for px, py in points:
                t = xlo+(px-bx)/bw*(xhi-xlo)
                m = params["A_m"]*math.exp(-params["gamma_per_s"]*t)*math.cos(params["omega_rad_per_s"]*t)
                target_y = by+(yhi-m)/(yhi-ylo)*bh
                formula_ok = formula_ok and bx-xtol <= px <= bx+bw+xtol and abs(py-target_y) <= ytol*4/3
            model_ok = len(vals) % 2 == 0 and len(points) >= len(required) and all(p[0]<q[0] for p,q in zip(points,points[1:])) and node.tag.endswith("polyline") and untransformed(node) and node.attrib.get("fill") == "none" and _stroke_visible(node, parents, view) and includes_required and formula_ok
        except (ValueError, KeyError, TypeError, OverflowError):
            pass
    checks.append(check("model_geometry", 10, model_ok, "CSV model, positive effective stroke; provisional minimum 0.08 mm at 180 mm", critical=True))
    checks.append(check("residual_geometry", 10, mark_check("residual-points", 3, "residual", "residual_y_limits"), critical=True))
    colors_ok = False
    try:
        obscolors = {n.attrib["fill"].lower() for n in ids["observations"]}
        rescolors = {n.attrib["fill"].lower() for n in ids["residual-points"]}
        mc = ids["signal-model"].attrib["stroke"].lower()
        colors_ok = all(_directly_rendered(ids[k], parents) for k in ("observations", "residual-points", "signal-model", "legend-observation", "legend-model")) and len(obscolors) == 1 and rescolors == obscolors and mc not in obscolors and all(re.fullmatch(r"#[0-9a-f]{6}", x) for x in obscolors | {mc}) and ids["legend-observation"].attrib["fill"].lower() in obscolors and ids["legend-model"].attrib["stroke"].lower() == mc
    except (KeyError, TypeError):
        pass
    checks.append(check("legend_and_identity", 5, colors_ok))
    schematic_ok = False
    try:
        ar = ids["displacement-arrow"]
        marker = ar.attrib["marker-end"]
        marker_id = marker[5:-1] if re.fullmatch(r"url\(#[A-Za-z0-9_-]+\)", marker) else ""
        marker_node = ids.get(marker_id)
        marker_width = float(marker_node.attrib.get("markerWidth", "3")) if marker_node is not None else 0
        marker_height = float(marker_node.attrib.get("markerHeight", "3")) if marker_node is not None else 0
        marker_view = [0, 0, marker_width, marker_height]
        if marker_node is not None and "viewBox" in marker_node.attrib:
            marker_view = svg_viewbox(marker_node)
        marker_ref = [float(marker_node.attrib.get("refX", "0")), float(marker_node.attrib.get("refY", "0"))] if marker_node is not None else [0, 0]
        marker_units = marker_node.attrib.get("markerUnits", "strokeWidth") if marker_node is not None else ""
        marker_multiplier = float(_inherited(ar, parents, "stroke-width", "1")) if marker_units == "strokeWidth" else 1
        marker_scale = (min(marker_width/marker_view[2], marker_height/marker_view[3])
                        * marker_multiplier * DISPLAY_WIDTH_MM/view[2]) if min(marker_view[2:]) > 0 else 0
        marker_ok = (marker_node is not None and marker_node.tag.split("}")[-1] == "marker"
                     and marker_units in {"strokeWidth", "userSpaceOnUse"}
                     and min(marker_width, marker_height) > 0 and math.isfinite(marker_scale) and marker_scale > 0
                     and all(math.isfinite(v) for v in marker_view + marker_ref)
                     and _inside([marker_ref[0], marker_ref[1], marker_ref[0], marker_ref[1]], marker_view)
                     and _visible_graphic(marker_node, parents, marker_view, in_marker=True, mm_per_unit=marker_scale))
        schematic_ok = (all(x in ids and _visible_graphic(ids[x], parents, view) for x in ("mass", "spring", "damper", "displacement-arrow"))
                        and ar.tag.endswith("line") and float(ar.attrib["x2"]) > float(ar.attrib["x1"])
                        and close(float(ar.attrib["y2"]), float(ar.attrib["y1"]), rtol=0, atol=ytol)
                        and _stroke_visible(ar, parents, view) and marker_ok)
    except (ValueError, KeyError, TypeError):
        pass
    checks.append(check("schematic_direction", 5, schematic_ok, "Nonempty on-canvas schematic and a painted marker; connections require actual review", critical=True))
    labels = " ".join("".join(n.itertext()) for n in root.iter() if n.tag.endswith("text") and _text_in_canvas(n, parents, view)) if root is not None else ""
    checks.append(check("labels_and_layout", 5, bounds_ok and all(x in labels for x in ("Time (s)", "Displacement (m)", "Residual (m)", "Synthetic observations", "Fixed model")), "Required labels have on-canvas approximate text bounds; actual glyph layout/occlusion requires rendering"))
    return checks
