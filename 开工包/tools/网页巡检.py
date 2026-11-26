#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页巡检 · 批量验收一批页面（门禁 + 资源引用 + 可选线上 HTTP 检查）
------------------------------------------------------------------
为什么要有它：验收门禁只看单个 HTML 文件内部。真实上线前还要回答三个问题——
  ① 这批页面每份能不能进仓库（复用 验收门禁.py）
  ② 页面里引用的图片/CSS/JS/站内链接，文件到底在不在（裂图、死链）
  ③ 部署到线上后，这些 URL 是不是真的 200

用法：
  # 静态层（默认，不需要服务器）：查门禁 + 站内资源是否落地
  python3 tools/网页巡检.py --config tools/巡检配置_模板B阶段2.json --out /tmp/regress2

  # 再叠一层线上检查（可选）：本地或线上起好服务后给 --base-url
  python3 tools/网页巡检.py --config tools/巡检配置_模板B阶段2.json --out /tmp/regress2 \
      --base-url http://127.0.0.1:8791

  # 不写配置，直接扫整仓库
  python3 tools/网页巡检.py --all --out /tmp/patrol

配置格式（JSON）：
{
  "name": "模板B · 阶段2（身份系统）",
  "files": ["tpl-b/index.html"],
  "base_url": "http://127.0.0.1:8791"     // 可选，命令行 --base-url 优先
}

退出码：0=全部通过，1=有 FAIL，2=用法/配置错误
能力边界：静态层是文本分析，证明不了"交互跑通"；线上层只证明"能取到"，证明不了"长得对"。
"""

import sys, os, re, json, argparse, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))   # 开工包/tools -> 仓库根

def load_gate():
    """复用验收门禁，避免两套判定标准打架"""
    sys.path.insert(0, HERE)
    import importlib.util
    spec = importlib.util.spec_from_file_location("gate", os.path.join(HERE, "验收门禁.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

REF_RE = re.compile(r'<(img|script|link|iframe|source|video|audio)\b[^>]*?\b(?:src|href)\s*=\s*["\']([^"\']+)["\']', re.I)
A_RE   = re.compile(r'<a\b[^>]*?\bhref\s*=\s*["\']([^"\']+)["\']', re.I)

def is_external(u):
    return bool(re.match(r'^(https?:)?//|^data:|^mailto:|^tel:|^javascript:|^#', u.strip(), re.I))

def resolve(html_path, u):
    """把引用解析成本地路径（相对 HTML 所在目录）；站内绝对路径按仓库根算"""
    clean = u.split('#')[0].split('?')[0].strip()
    if not clean: return None
    clean = urllib.parse.unquote(clean)
    if clean.startswith('/'):
        return os.path.normpath(os.path.join(REPO, clean.lstrip('/')))
    return os.path.normpath(os.path.join(os.path.dirname(html_path), clean))

def scan_refs(html_path):
    src = open(html_path, encoding='utf-8', errors='replace').read()
    missing, external, ok = [], [], 0
    for tag, u in REF_RE.findall(src):
        if is_external(u):
            external.append(u[:80]); continue
        p = resolve(html_path, u)
        if p is None: continue
        if os.path.isdir(p): p = os.path.join(p, 'index.html')
        if os.path.isfile(p): ok += 1
        else: missing.append({"tag": tag.lower(), "ref": u[:120], "expect": os.path.relpath(p, REPO)})
    # 站内链接（a href）：只查本地相对链接，不跟进外链
    dead = []
    for u in A_RE.findall(src):
        if is_external(u): continue
        p = resolve(html_path, u)
        if p is None: continue
        if os.path.isdir(p): p = os.path.join(p, 'index.html')
        if not os.path.isfile(p): dead.append({"kind": "link", "ref": u[:120], "expect": os.path.relpath(p, REPO)})
    return {"ok_refs": ok, "missing": missing, "dead_links": dead,
            "external_sample": sorted(set(external))[:6]}

def http_probe(base_url, rel_paths):
    out = []
    for rel in rel_paths:
        url = base_url.rstrip('/') + '/' + rel.lstrip('/')
        try:
            req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'site-patrol/1.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                out.append({"url": url, "status": r.status})
        except Exception as e:
            code = getattr(e, 'code', None)
            out.append({"url": url, "status": code or 0, "error": str(e)[:100]})
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', help='巡检配置 JSON')
    ap.add_argument('--all', action='store_true', help='扫仓库里所有 index.html')
    ap.add_argument('--out', default='/tmp/patrol', help='报告输出目录')
    ap.add_argument('--base-url', default=None, help='可选：线上/本地服务地址，追加 HTTP 检查')
    a = ap.parse_args()

    if not a.config and not a.all:
        print("用法: python3 tools/网页巡检.py --config <配置.json> --out <目录> [--base-url URL]")
        print("      或 python3 tools/网页巡检.py --all --out <目录>")
        sys.exit(2)

    base_url = a.base_url
    if a.config:
        if not os.path.isfile(a.config):
            print(f"配置不存在: {a.config}"); sys.exit(2)
        cfg = json.load(open(a.config, encoding='utf-8'))
        name = cfg.get('name') or os.path.basename(a.config)
        files = cfg.get('files') or []
        base_url = base_url or cfg.get('base_url')
    else:
        name = '全仓库'
        files = []
        for root, dirs, fs in os.walk(REPO):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', 'images')]
            if 'index.html' in fs:
                files.append(os.path.relpath(os.path.join(root, 'index.html'), REPO))
        files.sort()

    gate = load_gate()
    report = {"name": name, "repo": REPO, "generated_at": __import__('datetime').datetime.now().isoformat(timespec='seconds'),
              "pages": [], "summary": {}}

    fail_pages, warn_pages = [], 0
    for rel in files:
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            report["pages"].append({"file": rel, "exists": False}); fail_pages.append(rel); continue
        g, err = gate.check(p)
        if err:
            report["pages"].append({"file": rel, "exists": False, "error": err}); fail_pages.append(rel); continue
        refs = scan_refs(p)
        page = {"file": rel, "exists": True, "kind": g["kind"],
                "gate": {"green": g["green"], "passed": g["passed"], "total": g["total"],
                         "fails": [c["name"] + (" | " + c["detail"] if c["detail"] else "") for c in g["checks"] if not c["ok"]]},
                "refs": refs}
        if refs["missing"] or refs["dead_links"]:
            page["ref_broken"] = True; fail_pages.append(rel)
        if not g["green"]:
            fail_pages.append(rel)
        report["pages"].append(page)

    # 可选线上层
    if base_url and files:
        probe_targets = list(files)
        for pg in report["pages"]:
            for m in pg.get("refs", {}).get("missing", []): pass
        probe = http_probe(base_url, probe_targets)
        report["http"] = probe
        for h in probe:
            if h["status"] != 200: fail_pages.append(h["url"])

    fail_pages = sorted(set(fail_pages))
    report["summary"] = {"pages": len(files), "fail_pages": fail_pages,
                         "verdict": "ALL GREEN" if not fail_pages else "有 FAIL",
                         "note": "静态检查只能证明文件与引用没坏，交互是否跑通必须浏览器实测"}

    os.makedirs(a.out, exist_ok=True)
    json_path = os.path.join(a.out, "patrol.json")
    md_path = os.path.join(a.out, "patrol.md")
    json.dump(report, open(json_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

    L = [f"# 巡检报告 · {name}", "", f"- 时间：{report['generated_at']}", f"- 仓库：`{REPO}`",
         f"- 结论：**{report['summary']['verdict']}**", ""]
    for pg in report["pages"]:
        if not pg.get("exists"):
            L.append(f"## ❌ {pg['file']}（文件不存在）"); continue
        g = pg["gate"]
        mark = "✅" if g["green"] else "❌"
        L.append(f"## {mark} {pg['file']}（{pg['kind']}）")
        L.append(f"- 门禁：{g['passed']}/{g['total']}" + ("" if g["green"] else " → 缺：" + "；".join(g["fails"])))
        r = pg["refs"]
        L.append(f"- 站内引用：{r['ok_refs']} 个正常，{len(r['missing'])} 个缺失，{len(r['dead_links'])} 个死链")
        for m in r["missing"][:5]:
            L.append(f"  - 缺文件 `{m['expect']}`（{m['tag']} 引用 `{m['ref']}`）")
        for d in r["dead_links"][:5]:
            L.append(f"  - 死链 `{d['ref']}` → 期望 `{d['expect']}`")
        if r["external_sample"]:
            L.append(f"- 外部引用（断网会裂）：{', '.join(r['external_sample'][:3])}")
        L.append("")
    if "http" in report:
        L.append("## 线上 HTTP")
        for h in report["http"]:
            L.append(f"- {h['status']} {h['url']}" + (f" ({h['error']})" if h.get('error') else ""))
    L.append("")
    L.append("> 提醒：本报告是静态分析结果，不代表交互可用；上线前仍需浏览器实测关键交互。")
    open(md_path, 'w', encoding='utf-8').write("\n".join(L))

    print("\n" + "=" * 58)
    print(f"  巡检 · {name}")
    print("=" * 58)
    for pg in report["pages"]:
        if not pg.get("exists"):
            print(f"  [MISS] {pg['file']}"); continue
        g = pg["gate"]; r = pg["refs"]
        tag = "PASS" if g["green"] and not r["missing"] and not r["dead_links"] else "FAIL"
        print(f"  [{tag}] {pg['file']}  门禁{g['passed']}/{g['total']}  "
              f"缺文件{len(r['missing'])} 死链{len(r['dead_links'])}")
        for f in g["fails"][:3]: print(f"         门禁缺: {f}")
        for m in r["missing"][:3]: print(f"         缺文件: {m['expect']}")
    if "http" in report:
        bad = [h for h in report["http"] if h["status"] != 200]
        print(f"  线上 HTTP：{len(report['http'])} 个地址，" + (f"{len(bad)} 个非 200" if bad else "全部 200"))
    print("=" * 58)
    print(f"  结论：{report['summary']['verdict']}")
    print(f"  报告：{json_path}")
    print(f"        {md_path}")
    print("=" * 58 + "\n")
    sys.exit(0 if not fail_pages else 1)

if __name__ == "__main__":
    main()
