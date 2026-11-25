#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""
验收门禁 · 判断一份外部AI产出的HTML能不能放进仓库
--------------------------------------------------
设计目的：把"该不该放进去"从某个AI的主观判断，变成任何AI/任何人跑一下
都得到同样结果的机械检查。换会话、换AI、上下文满了，都不影响结论。

用法：
    python3.11 tools/验收门禁.py <html文件路径>
    python3.11 tools/验收门禁.py <html文件路径> --json

输出：逐项 PASS/FAIL + 结论（可进仓库 / 打回重做）
退出码：0=可进仓库，1=有FAIL需打回，2=用法/文件错误（脚本本身问题）
"""
import sys, os, re, json, subprocess, tempfile

def check(path):
    results=[]
    def add(name, ok, detail=""):
        results.append({"name":name,"ok":bool(ok),"detail":str(detail)})

    if not os.path.isfile(path):
        return None, f"文件不存在: {path}"
    src=open(path,encoding="utf-8",errors="replace").read()
    add("文件存在且非空", len(src.strip())>500, f"{len(src)}字符")

    # 1. HTML 基本结构
    add("HTML文档声明", "<!DOCTYPE html" in src[:200], "开头有 <!DOCTYPE html>")
    add("viewport移动端适配", "viewport" in src and "width=device-width" in src, "有 meta viewport")
    add("中文语言标记", 'lang="zh' in src[:500], "html lang=zh")

    # 2. JS 语法（node --check）
    scripts=re.findall(r"<script[^>]*>(.*?)</script>",src,re.S)
    js="\n".join(s for s in scripts if s.strip())
    if not js.strip():
        add("存在JS逻辑", False, "没有 <script> 内容，纯静态站请说明站型")
    else:
        add("存在JS逻辑", True, f"{len(js)}字符")
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
    watermarks=[w for w in ["豆包","doubao","WorkBuddy","by 豆包","AI生成","由AI生成"] if w.lower() in src.lower()]
    add("无AI平台水印", not watermarks, ",".join(watermarks) if watermarks else "干净")

    # 外链资源：断网/迁移后会裂，必须内联或本地
    ext=[]
    for m in re.finditer(r'<(?:script|img|link|iframe)[^>]+(?:src|href)\s*=\s*["\']([^"\']+)',src,re.I):
        u=m.group(1)
        if u.startswith(("http://","https://","//")): ext.append(u[:70])
    css_urls=re.findall(r'url\(\s*["\']?(https?://[^)"\']+)',src,re.I)
    ext+= [u[:70] for u in css_urls]
    add("无外部资源依赖(全内联)", not ext, ("发现外链: "+"; ".join(ext[:4])) if ext else "无外链")

    # 4. 骨架完整性（模板B生成的站必须有这些防坑件）
    skeleton={
        "路由表ROUTES": r'\bROUTES\b',
        "错误红点": r'errlog|errLog|errDot',
        "切场引擎": r'\.view\.leaving|function goto|ENTER_SEEN',
        "设计令牌:root": r':root\s*\{',
        "三态(加载/空/错误)": r'listLoading|listEmpty|listErr|loading.*empty.*err',
    }
    for name,pat in skeleton.items():
        add("骨架·"+name, bool(re.search(pat,src,re.I)), "存在" if re.search(pat,src,re.I) else "缺失")

    # 5. 常见致命坑
    # 死循环/空catch 这种静态难判，用特征串兜一下
    add("无eval动态执行", "eval(" not in src, "无 eval" if "eval(" not in src else "含 eval( 需人工确认")
    add("无硬编码密钥/token", not bool(re.search(r'(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9]{20,})',src)), "无token痕迹")

    passed=sum(1 for r in results if r["ok"]); total=len(results)
    green = passed==total
    return {"verdict":"可进仓库(GREEN)" if green else "打回重做(RED)",
            "green":green,"passed":passed,"total":total,"checks":results}, None

def main():
    if len(sys.argv)<2:
        print("用法: python3.11 tools/验收门禁.py <html文件路径> [--json]"); sys.exit(2)
    path=sys.argv[1]; as_json="--json" in sys.argv
    report,err=check(path)
    if err:
        print(err); sys.exit(2)
    if as_json:
        print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        print("\n"+"="*58)
        print("  验收门禁 · "+os.path.basename(path))
        print("="*58)
        for c in report["checks"]:
            tag="PASS" if c["ok"] else "FAIL"
            print(f"  [{tag}] {c['name']}"+(f" | {c['detail']}" if c["detail"] else ""))
        print("="*58)
        print(f"  {report['passed']}/{report['total']} 通过 → {report['verdict']}")
        print("="*58+"\n")
        if not report["green"]:
            print("  ⚠ 有 FAIL 项：把这份结果发给制作方打回重做，不要放进仓库。")
            print("  ⚠ 全部 PASS 后，仍需浏览器实测一遍关键交互（见 SOP 第3步）。\n")
    sys.exit(0 if report["green"] else 1)

if __name__=="__main__":
    main()
