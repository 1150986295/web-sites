#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收门禁 · 格式体检（不含交互 / 真实尺寸 / 安全）
--------------------------------------------------
设计目的：把"该不该放进去"从某个AI的主观判断，变成任何AI/任何人跑一下
都得到同样结果的机械检查。换会话、换AI、上下文满了，都不影响结论。

⚠ 它只是"格式体检"，不是"可用性验收"：
   · 不点按钮，证明不了交互跑通
   · 不量真实尺寸，证明不了 44px 真的达标
   · 不做安全审计，证明不了没有 XSS
  15/15 只说明"没有常见的结构性低级错误"，不等于页面能用。

站型分组（v2）：
  · app    —— 多页应用（有路由表/切场引擎的特征），要求 ROUTES/切场/三态
  · static —— 单页静态站，不要求路由与切场，改查静态站该有的 5 项底线
  自动识别，也可用 --kind 强制指定。

能力边界（务必如实转述）：
  本脚本只做**静态关键词与结构检查**，不代表功能可用、不代表交互跑通。
  全项 PASS 之后仍必须浏览器实测关键交互（见 SOP 第 3 步）。

用法：
    python3 tools/验收门禁.py <html文件路径> [--kind static|app] [--json]
输出：逐项 PASS/WARN/FAIL + 站型 + 结论（格式项全过 / 有 FAIL 需处理）
退出码：0=可进仓库，1=有FAIL需打回，2=用法/文件错误（脚本本身问题）
"""
import sys, os, re, json, shutil, subprocess, tempfile

# ---------- 站型识别 ----------
APP_MARKERS = r'\bROUTES\b|function\s+goto\s*\(|\.view\.leaving|ENTER_SEEN'
def detect_kind(src, override=None):
    if override in ("static", "app"):
        return override, "命令行指定"
    if re.search(APP_MARKERS, src):
        return "app", "检测到路由表/切场引擎特征"
    return "static", "未检测到路由/切场特征，按单页静态站验收"

# ---------- 骨架检查项：两种站型各 5 项，总项数都是 15 ----------
SKELETON_APP = {
    "路由表ROUTES": r'\bROUTES\b',
    "错误红点": r'errlog|errLog|errDot',
    "切场引擎": r'\.view\.leaving|function goto|ENTER_SEEN',
    "设计令牌:root": r':root\s*\{',
    "三态(加载/空/错误)": r'listLoading|listEmpty|listErr|loading.*empty.*err',
}
SKELETON_STATIC = {
    "设计令牌:root": r':root\s*\{',
    "主标题h1": r'<h1[\s>]',
    "键盘焦点可见": r':focus-visible|:focus\s*\{|:focus\b',
}

def check(path, kind_override=None):
    results=[]
    def add(name, ok, detail="", warn=False):
        results.append({"name":name,"ok":bool(ok),"warn":bool(warn),"detail":str(detail)})

    if not os.path.isfile(path):
        return None, f"文件不存在: {path}"
    src=open(path,encoding="utf-8",errors="replace").read()
    # 先抽出脚本再判站型：正文/注释里提到 ROUTES 不该被判成多页应用
    scripts=re.findall(r"<script[^>]*>(.*?)</script>",src,re.S)
    js="\n".join(s for s in scripts if s.strip())
    kind, why = detect_kind(js, kind_override)
    # 可见文字：去掉 script/style 与所有标签。空壳页能堆关键字，但堆不出正文
    _t=re.sub(r"<(script|style)\b[^>]*>.*?</\1>"," ",src,flags=re.S|re.I)
    _t=re.sub(r"<[^>]+>"," ",_t)
    visible=re.sub(r"\s+","",_t)
    add("有效内容(非空壳)", len(src.strip())>500 and len(visible)>=50,
        f"{len(src)}字符 / 可见文字{len(visible)}字"
        + ("" if len(visible)>=50 else "（可见文字<50，疑似空壳页）"))

    # 1. HTML 基本结构
    add("HTML文档声明", "<!DOCTYPE html" in src[:200], "开头有 <!DOCTYPE html>")
    add("viewport移动端适配", "viewport" in src and "width=device-width" in src, "有 meta viewport")
    add("中文语言标记", 'lang="zh' in src[:500], "html lang=zh")

    # 2. JS 语法（node --check）
    if not js.strip():
        # 纯静态站没有脚本是合法形态，不能算失败；但要说清"没检查"
        add("存在JS逻辑", kind=="static", "纯静态站，无脚本（N/A）" if kind=="static" else "多页应用没有脚本，请说明站型")
        # 无 JS 就少一项语法检查，补一项静态站该有的底线，保证总项数恒为 15
        add("内联样式存在", "<style" in src.lower(), "有 <style> 内联样式" if "<style" in src.lower() else "没有内联样式")
    else:
        add("存在JS逻辑", True, f"{len(js)}字符")
        if not shutil.which("node"):
            add("JS语法无错误", False, "环境没有 node，无法检查语法（请装 node 后重跑）")
        else:
            with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False,encoding="utf-8") as f:
                f.write(js); tmp=f.name
            try:
                r=subprocess.run(["node","--check",tmp],capture_output=True,text=True,timeout=30)
                add("JS语法无错误", r.returncode==0, (r.stderr or "语法OK").strip()[:180].replace("\n"," "))
            except Exception as e:
                add("JS语法无错误", False, repr(e)[:120])
            finally:
                os.unlink(tmp)

    # 3. 平台污染（豆包/WorkBuddy 最容易塞的东西）
    #    降为 WARN：模板/文档里正常引用平台名不该判死，交给人工看一眼上下文
    hits=[]
    for w in ["豆包","doubao","WorkBuddy","AI生成","由AI生成"]:
        i=src.lower().find(w.lower())
        if i>=0: hits.append(f"{w}@{i}…{src[max(0,i-15):i+len(w)+15].replace(chr(10),' ')}")
    add("无AI平台水印", True,
        "干净" if not hits else "需人工确认（WARN）: "+"; ".join(hits[:3]), warn=bool(hits))

    # 外链资源：断网/迁移后会裂，必须内联或本地
    ext=[]
    for m in re.finditer(r'<(?:script|img|link|iframe|source)[^>]+(?:src|href)\s*=\s*["\']([^"\']+)',src,re.I):
        u=m.group(1)
        if u.startswith(("http://","https://","//")): ext.append(u[:70])
    for m in re.finditer(r'srcset\s*=\s*["\']([^"\']+)',src,re.I):
        for part in m.group(1).split(","):
            u=part.strip().split(" ")[0]
            if u.startswith(("http://","https://","//")): ext.append("srcset:"+u[:60])
    ext += [u[:70] for u in re.findall(r'url\(\s*["\']?(https?://[^)"\']+)',src,re.I)]
    ext += [u[:70] for u in re.findall(r'@import\s+(?:url\(\s*)?["\']?(https?://[^)"\']+)',src,re.I)]
    ext += [u[:70] for u in re.findall(r'fetch\s*\(\s*["\'](https?://[^"\']+)',src,re.I)]
    ext=list(dict.fromkeys(ext))   # 去重保序
    add("无外部资源依赖(全内联)", not ext, ("发现外链: "+"; ".join(ext[:4])) if ext else "无外链")

    # 4. 骨架完整性：按站型分组
    if kind=="app":
        for name,pat in SKELETON_APP.items():
            ok=bool(re.search(pat,src,re.I))
            add("骨架·"+name, ok, "存在" if ok else "缺失")
    else:
        for name,pat in SKELETON_STATIC.items():
            if name=="主标题h1":
                # 既然查主标题就数个数：0 个是空壳/结构缺失的强信号；
                # 多于 1 个只告警不判死（在用页面一刀切变红，人就再也不看门禁了）
                n=len(re.findall(r'<h1[\s>]',src,re.I))
                if n==1:
                    add("骨架·主标题h1", True, "1 个 h1")
                elif n==0:
                    add("骨架·主标题h1", False, "0 个 h1（主标题缺失：空壳页/结构缺失的强信号）")
                else:
                    add("骨架·主标题h1", True, f"{n} 个 h1（应只保留 1 个，其余降为 h2）", warn=True)
                continue
            ok=bool(re.search(pat,src,re.I))
            add("骨架·"+name, ok, "存在" if ok else "缺失")
        # 触控目标：没有交互元素的页面 N/A，不硬判（仿图片 alt 的 N/A 逻辑）
        has_ui=bool(re.search(r'<(?:button|a|input|select|textarea)\b|data-act\s*=',src,re.I))
        tap_ok=bool(re.search(r'44px|--tap\s*:',src,re.I))
        # 声明了 44px ≠ 每个按钮真有 44px：静态扫一遍按钮类选择器里的固定小尺寸，
        # 纯静态做不精确（calc/继承/媒体查询会漏），所以只报 WARN，不判死
        small=[]
        if has_ui and tap_ok:
            for sel,body in re.findall(r'([^{}]{1,120})\{([^{}]*)\}',src):
                if '::' in sel: continue                      # 伪元素不是可点区域
                if re.search(r'(?:svg|img|\.n)\s*$',sel.strip(),re.I): continue  # 图标/角标数字
                if not re.search(r'btn|button|close|clear|dot|tab|act|star|icon|tool',sel,re.I): continue
                for m in re.finditer(r'(?:^|;)\s*(?:width|height|min-width|min-height)\s*:\s*(\d{1,2})px',body):
                    if int(m.group(1))<40:
                        small.append(f"{sel.strip()[-26:]}:{m.group(1)}px")
        small=list(dict.fromkeys(small))
        if not has_ui:
            add("骨架·触控目标44px", True, "无交互元素（N/A）")
        elif not tap_ok:
            add("骨架·触控目标44px", False, "有交互元素但未声明 44px/--tap")
        elif small:
            add("骨架·触控目标44px", True,
                "仅检测到 44px/--tap 声明，未验证真实尺寸；静态扫到疑似小尺寸（WARN，需浏览器实测）: "
                +"; ".join(small[:4]), warn=True)
        else:
            add("骨架·触控目标44px", True, "仅检测到 44px/--tap 声明，未验证真实尺寸；未扫到明显小尺寸")
        # 静态站第 5 项：图片必须都有 alt（无图片则 N/A 通过）
        imgs=re.findall(r'<img\b[^>]*>',src,re.I)
        noalt=[t[:60] for t in imgs if not re.search(r'\balt\s*=',t,re.I)]
        add("骨架·图片替代文本alt",
            len(noalt)==0,
            (f"无图片（N/A）" if not imgs else (f"{len(imgs)} 张图全部有 alt" if not noalt else f"{len(noalt)} 张缺 alt: {noalt[0]}")))

    # 5. 常见致命坑
    # eval / new Function：按"标识符边界"判断，但允许点号前缀——
    # window.eval( / obj["x"].eval( 是真实的动态执行，不能因为前面有 . 就放过；
    # retrieval( / interval( 这类函数名仍要排除。
    # 另外三类同样能执行任意代码，必须一起查：
    #   constructor.constructor("...")()  —— 不出现 eval/Function 字样，旧正则会漏
    #   setTimeout("代码", 0) / setInterval("代码", 0) —— 字符串参数会被当代码解析
    dyn=[]
    for pat,label in [
        (r'(?<![A-Za-z0-9_$])(?:eval|Function)\s*\(', 'eval/Function'),
        (r'constructor\s*\.\s*constructor', 'constructor.constructor'),
        (r'setTimeout\s*\(\s*[\'"`]', 'setTimeout(字符串)'),
        (r'setInterval\s*\(\s*[\'"`]', 'setInterval(字符串)'),
    ]:
        n=len(re.findall(pat,src))
        if n: dyn.append(f"{label}×{n}")
    add("无动态代码执行(eval/Function)", not dyn,
        "无 eval/Function/constructor.constructor/字符串定时器" if not dyn
        else "命中: "+"、".join(dyn)+"（可执行任意代码，需人工确认或移除）")
    token_ok=not bool(re.search(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})',src))
    # demo 站常见：mock 登录 + 明文密码种子。不算失败，但要在结论里提醒人工确认
    mock_pw=bool(kind=="app"
                 and re.search(r'\bmock\s*\(',src)
                 and re.search(r'(?:password|passwd|pwd|密码)\s*[:=]\s*["\']?(?:123456|admin|password|888888)',src,re.I))
    add("无硬编码密钥/token", token_ok,
        ("无token痕迹" if token_ok else "发现密钥痕迹")
        + ("；WARN: mock 登录含明文密码种子，仅限演示，上线前须替换" if mock_pw else ""),
        warn=mock_pw)

    passed=sum(1 for r in results if r["ok"]); total=len(results)
    warns=sum(1 for r in results if r.get("warn"))
    green = passed==total
    return {"verdict":"格式项全过(GREEN) · 仍需实测" if green else "有 FAIL 需处理(RED)",
            "green":green,"passed":passed,"total":total,"warnings":warns,
            "kind":kind,"kind_reason":why,
            "node": shutil.which("node") or "",
            "checks":results}, None

def main():
    args=[a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args)<1:
        print("用法: python3 tools/验收门禁.py <html文件路径> [--kind static|app] [--json]"); sys.exit(2)
    path=args[0]; as_json="--json" in sys.argv
    kind=None
    if "--kind" in sys.argv:
        i=sys.argv.index("--kind")
        kind=sys.argv[i+1] if i+1<len(sys.argv) else None
        if kind not in ("static","app"):
            print("--kind 只能是 static 或 app"); sys.exit(2)
    report,err=check(path,kind)
    if err:
        print(err); sys.exit(2)
    if as_json:
        print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        KINDNAME={"static":"单页静态站","app":"多页应用"}
        print("\n"+"="*58)
        print("  验收门禁 · 格式体检（不含交互 / 真实尺寸 / 安全）")
        print("  文件："+os.path.basename(path))
        print(f"  站型：{KINDNAME[report['kind']]}（{report['kind_reason']}）")
        print(f"  环境：node {'可用' if report['node'] else '缺失（JS 语法项会 FAIL，装好再跑）'}")
        print("="*58)
        for c in report["checks"]:
            tag="WARN" if c.get("warn") else ("PASS" if c["ok"] else "FAIL")
            print(f"  [{tag}] {c['name']}"+(f" | {c['detail']}" if c["detail"] else ""))
        print("="*58)
        print(f"  {report['passed']}/{report['total']} 通过 → {report['verdict']}")
        if report.get("warnings"):
            print(f"  另有 {report['warnings']} 项 WARN：需人工确认上下文，不计失败")
        print("="*58+"\n")
        if not report["green"]:
            print("  ⚠ 有 FAIL 项：把这份结果发给制作方打回重做，不要放进仓库。")
        print("  ⚠ 格式项全过 ≠ 页面可用：交互、真实尺寸、安全都必须浏览器/人眼实测。\n")
    sys.exit(0 if report["green"] else 1)

if __name__=="__main__":
    main()
