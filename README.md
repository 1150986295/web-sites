# web-sites · 作品集与网页模板

兰亭（1150986295）的网页仓库：一个门面作品集 + 若干可复用的单页/多页模板 + 一套开工资料。

**线上**：https://1150986295.github.io/web-sites/

## 目录

| 路径 | 是什么 |
|---|---|
| `index.html` | 门面作品集，11 张卡片 |
| `quiz/` | 城轨运营刷题台：应急处置 + 客运英语，可自建题库 |
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

- 先读 `开工包/START_HERE.md`（总入口）和 `开工包/docs/00_做网页的规矩_总纲.md`
- 改完跑门禁与巡检，全绿再推：
  ```bash
  python3 开工包/tools/验收门禁.py <页面.html> --kind static|app
  python3 开工包/tools/网页巡检.py --config 开工包/tools/巡检配置_全仓库.json
  ```
- 题库页有跨对话维护的历史，动它之前先看 `quiz/README.md`

## 许可

- 代码：MIT，见 `LICENSE`
- 页面内的书法字体各自遵循其原始许可，见 `jingmo/fonts/README.md`
- 碑帖图片来自公开出版物与博物馆公开资源，仅作学习与展示，不用于商业分发
