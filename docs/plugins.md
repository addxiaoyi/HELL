# 插件接口 v1

每个插件由 ZIP 根目录的 `plugin.json` 和可选 `assets/` 图片组成。扩展名为 `.hellplugin` 或 `.zip`。插件 ID 和模块 ID 使用 2–63 个小写字母、数字或短横线，以字母开头。

```json
{
  "apiVersion": 1,
  "id": "example-notes",
  "name": "世界笔记",
  "version": "1.0.0",
  "author": "作者",
  "description": "记录坐标和探索计划",
  "modules": [{
    "id": "notes",
    "title": "世界笔记",
    "kind": "notes",
    "settings": { "text": "基地坐标：" }
  }]
}
```

支持的 `kind` 与设置：

- `notes`：`text` 作为首次添加时的内容。
- `clock`：`format` 为 `12` 或 `24`。
- `links`：`label` 链接文字，`url` 必须为 HTTPS。
- `image`：`image` 为包内路径，例如 `assets/cover.jpg`。
- `system`：显示启动器托管内存与数据盘剩余空间。

所有设置值均为字符串，模块添加后由用户独立保存。更新清单只改变默认值，不应覆盖用户已编辑的内容。

## 详情与更新说明

清单可以增加以下可选字段：

```json
{
  "homepage": "https://github.com/addxiaoyi/HELL",
  "screenshots": ["assets/main-light.png", "assets/main-dark.png"],
  "releases": [
    { "version": "1.1.0", "date": "2026-11-09", "notes": "加入真实模块截图和版本说明。" }
  ]
}
```

主页必须为 HTTPS。截图最多 6 张，必须是包内确实存在的 `assets/` 图片；请从实际模块截图，避免使用无关图片。更新说明最多 20 条，每条最多 4000 字，日期为 `yyyy-MM-dd`。建议将最新版本放在最前面。

启动器下载并校验整个包后读取截图，失败时提供重试，点击图片可以放大。旧版启动器忽略这些可选字段。发布新版本时保留旧 `.hellplugin` 文件，避免尚未刷新目录的客户端下载失败；`SHA256SUMS` 记录当前目录中的版本。

`market/catalog.json` 由工具生成，包含 `manifest`、`packageUrl`、`sha256`。不可手写虚假校验值或复用同一版本号替换包内容。提交新版本后重新打包，合入 `main` 即更新公共目录；客户端点击刷新后在「可更新」中安装。
