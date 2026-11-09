# HELL

HelL 启动器插件公共目录。此仓库当前提供声明式启动页插件、可复现的打包工具和开发者提交说明。

## 在启动器中使用

进入「插件 → 市场源」，使用：

```text
https://raw.githubusercontent.com/addxiaoyi/HELL/main/market/catalog.json
```

当前提供桌面时钟、冒险手记、Minecraft 百科和服务器手册。安装后到「启动页 → 编辑布局 → 模块库」添加。插件支持停用、更新和卸载，启动页保存的内容会保留。

市场目录的每个包都有 SHA-256，启动器会检查包哈希、插件标识和版本。GitHub 无法访问时可下载 `market/*.hellplugin` 后从启动器本地导入。

## 提交 / 更新插件

1. 在 `plugins/<plugin-id>/plugin.json` 添加清单；图片只能放在该插件的 `assets/` 内。
2. 现有插件更新需增加 `version`，保留原插件 ID 和模块 ID，以便用户恢复配置。
3. 运行下面的命令并提交插件源码、`market` 中的生成文件。
4. 创建 Pull Request，说明模块用途和改动。校验工作流会重新打包、核对哈希并确认目录与源码一致。

```sh
python tools/test_plugin_catalog.py
python tools/build_plugin_catalog.py --source plugins --output market --base-url https://raw.githubusercontent.com/addxiaoyi/HELL/main/market
```

仅支持插件接口 v1 的 `notes`、`clock`、`links`、`image`、`system` 模块，不执行 DLL 或脚本。包及解压后最多 16 MB、128 个文件、20 个模块，拒绝路径穿越、符号链接和可执行文件。

协议见 [插件开发说明](docs/plugins.md)，示例见 [服务器手册](plugins/server-notebook/plugin.json)。此目录不包含用户配置、账号、游戏数据或启动器安装包。
