# web-sites · 作品集与网页模板

兰亭（1150986295）的网页仓库：一个门面作品集 + 若干可复用的单页/多页模板 + 一套开工资料。

**线上**：https://1150986295.github.io/web-sites/

## 目录

| 路径 | 是什么 |
|---|---|
| `index.html` | 门面作品集，12 张卡片 |
| `quiz/` | 城轨运营刷题台：应急处置 + 客运英语，可自建题库 |
| `toolbox/` | 小工具集合页 |
| `lanting-assoc/` | 兰亭书画协会展示页（活动照、碑帖灯箱） |
| `tpl-a/` `tpl-b/` | 单页静态站 / 多页应用两套模板（模板 B 含路由、三态、后台） |
| `ai-tools-nav/` `interactive-lab/` | AI 工具导航、交互实验室 |
| `ziliao-tpl/` | 资料整理型单页模板 |
| `jingmo/` `lanting-xinyou/` | 竞墨赛事系统、兰亭新猷（前端快照，后端已剥离） |
| `开工包/` | 做网页的规矩、验收门禁、巡检脚本、交接文档（**接手先读 `开工包/START_HERE.md`**） |
| `screenshots/` | 门面卡片封面图（800×500 或 16:9） |

## 怎么发布

push 到 `main`，GitHub Pages 自动构建，1–2 分钟生效。没有单独的"发布"步骤。

```bash
git add -A && git commit -m "改了什么" && git push origin main
```

不会用 git 时，可在 GitHub 网页版 `Add file → Upload files` 直接覆盖同名文件，手机也能做。

## 改之前

- 从零新建一个站 → 看 `开工包/START_HERE.md` 的 5 步（总入口）；开工前同时读 `开工包/docs/00_做网页的规矩_总纲.md`
- **要加交互效果 → 先查 `开工包/reference/INTERACTIONS.md`**（场景速查表 + 86 项详情）；想要现成可跑的实现，看 `interactive-lab/index.html` 的 86 项本地演示，复制 `reg()` 定义即可复用
- 改完跑门禁与巡检，全绿再推：
  ```bash
  python3 开工包/tools/验收门禁.py <页面.html> --kind static|app
  python3 开工包/tools/网页巡检.py --config 开工包/tools/巡检配置_全仓库.json
  ```
  **门禁是"格式体检"，不是"可用性验收"**：它只做静态关键词与结构检查，不点按钮、不量真实尺寸、不做安全审计。**15/15 ≠ 页面能用**，交互与视觉仍要浏览器实测。巡检用 `discover` 自动扫全仓库 `index.html`（新页面不会被漏掉），`jingmo` 是登记在案的快照页，失败属预期。
- 题库页有跨对话维护的历史，动它之前先看 `quiz/README.md`

## 许可

- 代码：MIT，见 `LICENSE`
- 页面内的书法字体各自遵循其原始许可，见 `jingmo/fonts/README.md`
- 碑帖图片来自公开出版物与博物馆公开资源，仅作学习与展示，不用于商业分发
