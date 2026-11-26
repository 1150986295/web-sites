# 竞墨字体来源与许可

`jingmo/index.html` 通过 `@font-face` 引用本目录三个 woff2。逐个说明来源，**不要笼统写"开源字体"**。

| 文件 | 字体名 | 来源 | 许可 | 状态 |
|---|---|---|---|---|
| `MaShanZheng.woff2` | Ma Shan Zheng（马善政毛笔楷书） | Google Fonts | SIL Open Font License 1.1 | ✅ 可随包分发 |
| `ZhiMangXing.woff2` | Zhi Mang Xing（志莽行书） | Google Fonts | SIL Open Font License 1.1 | ✅ 可随包分发 |
| `ChunJieKai.woff2` | ChunJieKai（春节楷） | **来源不明**，Google Fonts 无此字体 | **未确认** | ⚠️ 公开分发前须替换或取得授权 |

## 关于 OFL

Ma Shan Zheng 与 Zhi Mang Xing 在 Google Fonts 上以 SIL Open Font License 1.1 发布。OFL 1.1 全文以官方版本为准：

- 官方文本：https://openfontlicense.org/open-font-license-official-text/
- 中文说明：https://openfontlicense.org/

随包分发时，若需要把许可全文一并附上，从上面的官方链接取原文放进本目录，**不要凭记忆转写**。

## ChunJieKai 处理建议

1. **首选替换**：换成 Google Fonts 上同为楷体的 OFL 字体（如 Ma Shan Zheng 本身、Noto Serif SC），改 `@font-face` 与 `font-family` 引用即可，视觉差异需人工确认。
2. **次选取证**：找回下载来源，确认许可文件；拿不到就按"未授权"处理。
3. 在替换完成前，**不要把本仓库的字体文件单独打包对外分发**；页面在线展示的风险低于再分发，但仍建议尽快处理。

替换时同步改 `jingmo/index.html` 顶部三处 `@font-face`（约第 10–12 行）和 CSS 里的 `font-family` 引用。
