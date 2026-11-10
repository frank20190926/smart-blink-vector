# Smart Blink IT — V2

本地交付入口：[index.html](index.html)。三张 3200×2400 展板在 `deliverables/`，1200px 预览与校验报告在 `review/`。`docs/` 为相同版本的静态发布目录，本轮未发布。

## 重建

使用本机现有依赖，无新增安装：

```sh
/usr/local/bin/python3.11 scripts/build_v2.py
/usr/local/bin/python3.11 scripts/render_verify_v2.py
/usr/local/bin/python3.11 scripts/verify_geometry.py
```

- `source/wordmark_paths.json` 保存原工程的字标曲线；构建时修正 i 竖干与圆点字高，所有生产 SVG 仅包含 M/L/C/Z 路径。
- 电路中心线为 24 units；左右以 x=450 镜像；每侧四个实心端点和三个 evenodd 镂空端点；纯蓝中心圆之外使用 2.5-unit Cyan 细圈。
- 三个 PNG 均为 3200px 宽 RGBA；独立图标保留用户指定的 `3000px` 文件名，但实际宽度为 3200px。
- AI 为 PDF 1.5 兼容矢量文件、八个页面。未伪称具有 Illustrator 私有图层/AI 编辑数据；当前机器无 Illustrator，未做原生应用打开测试。
- EPS 为 Level 3 文档、可编辑路径与真实 eofill 镂空；结构已检查，当前无原生 PostScript 解释器渲染验证。
- 品牌 PDF 共 11 页：三页规范展板 + 八页矢量。白色单色稿在白色页面上不可见属透明反白稿的预期行为，规范展板提供深底预览。
- HEX/RGB 为确定值；CMYK 为注明的名义转换值。未提供官方 Pantone 色号，不编造精确等效色，规范中注明需实体色卡匹配。
- 首图主标实际横向占幅约 94%，上下两个标志展示区占整板高度 94.17%；不将其误报为像素着墨面积占比。
- ZIP 包含 14 个生产文件；ZIP 本身为交付清单第 15 项。

## 验证

`review/validation.json` 记录三张展板 DOM 几何、移动端/桌面端页面、文件尺寸、PDF 结构、同步与 ZIP CRC；`review/geometry-checks.json` 记录镜像、i 字高、6 处真实透明孔与所有本地下载路径。

旧网页截图与旧生产包已归档到项目 `99_归档/历史版本/smart-blink-vector/V1-before-20261110/`。未改动原图和既有任务单。
