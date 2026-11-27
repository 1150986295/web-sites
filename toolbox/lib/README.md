# pdf-lib（本地内置副本）

| 项 | 值 |
|---|---|
| 包名 | `pdf-lib` |
| 版本 | 1.17.1 |
| 文件 | `pdf-lib.min.js`（525,099 B） |
| 来源 | `https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js` |
| 许可 | MIT，Copyright (c) 2019 Andrew Dillon |
| sha256 | `0f9a5cad07941f0826586c94e089d89b918c46e5c17cf2d5a3c6f666e3bc694f` |
| 用途 | `toolbox/index.html` 的 PDF 合并 / 拆页，进入 PDF 工具时才按需加载 |

## 为什么放在仓库里

页面用相对路径 `lib/pdf-lib.min.js` 加载，不引 CDN：断网可用、迁移不裂、门禁的「无外部资源依赖」才能过。

## 升级方式

1. 下载同版本线的新文件覆盖本目录
2. 更新上表的版本、大小、sha256（`sha256sum pdf-lib.min.js`）
3. 打开线上 `toolbox/` 点一次 PDF 工具，确认能选择文件并显示页数

## 许可证

MIT。全文见 https://github.com/Hopding/pdf-lib/blob/master/LICENSE.md
