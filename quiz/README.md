# quiz/ 题库页维护须知

单文件应用：HTML/CSS/JS 全部内联，零外链，双击即可离线用。线上地址
`https://1150986295.github.io/web-sites/quiz/`。

## 一、为什么有这个文件

这页的代码由多个对话接力改过。站点名（城轨运营刷题台）和分享链接（`?bank=`）是后来加的，
外部 AI 手里的基线可能还是旧的「应急处置刷题台」。**拿别人给的整份文件覆盖本页时，功能会变新，
但站点名和深链会丢。** 合并后按下面清单逐条核对，缺一不可。

## 二、站点级改动清单（7 处，合并外部版本后必查）

| # | 位置 | 应为本仓库的样子 |
|---|---|---|
| 1 | `<head>` 的 `<title>` | `城轨运营刷题台 · 多科目题库练习` |
| 2 | `<head>` 的 `meta description` | 含「多科目题库：应急处置、客运英语」 |
| 3 | 静态 `#kicker` / `#pageTitle` | `城轨运营刷题台 · 应急处置` / `应急处置 · 刷题台` |
| 4 | `BANK_YINGJI` 的 `kicker` / `title` | `城轨运营刷题台 · 应急处置` / `应急处置 · 刷题台` |
| 5 | `BANK_ENGLISH` 的 `kicker` / `title` | `城轨运营刷题台 · 客运英语` / `客运英语 · 刷题台` |
| 6 | `applyBankMeta()` 末尾 | `document.title = b.name + ' · 城轨运营刷题台';` |
| 7 | `switchBank()` 末尾 + `init()` | 调用 `syncUrlBank(id)`；该函数存在；`init()` 里读 `?bank=` |

自建题库的 kicker 保持 `自建题库 · 本机保存`，不用改。

## 三、改完怎么验（3 分钟）

```bash
python3 开工包/tools/验收门禁.py quiz/index.html --kind static      # 要 15/15
python3 开工包/tools/网页巡检.py --config 开工包/tools/巡检配置_全仓库.json   # 要 ALL GREEN
```

再打开页面手点三条：默认进应急处置、切客运英语后地址栏出现 `?bank=english`、
导入 1 道题追加到应急处置后题数 +1 并能撤回。

## 四、加新科目

- 长期用的内置题库：在 `BANKS` 里加对象、`BANK_ORDER` 加 id（参考 `BANK_ENGLISH`）。
- 临时题库：页面里点「＋题库」粘贴文本，自动识别成库，存本机。
