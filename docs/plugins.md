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

`market/catalog.json` 由工具生成，包含 `manifest`、`packageUrl`、`sha256`。不可手写虚假校验值或复用同一版本号替换包内容。提交新版本后重新打包，合入 `main` 即更新公共目录；客户端点击刷新后在「可更新」中安装。
