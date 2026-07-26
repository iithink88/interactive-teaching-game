# 语文互动教学游戏生成器 (interactive-teaching-game)

将任意文学文本（古文、童话、散文等）一键转化为**自包含、可离线打开**的互动教学游戏网页。

> 由 WorkBuddy 技能驱动：提供文本 → 自动拆分场景、设计闯关选项、生成水墨风配图 → 输出单文件 HTML。

## 功能特性
- **闯关式互动**：5–10 个连贯场景，每关 3 选 1（1 正确 + 2 干扰），选错重选、选对进关。
- **课程复盘**：结尾提炼核心知识点 + 课堂讨论题。
- **自包含单文件**：所有配图以 Base64 内联，无外链、无相对路径，双击即玩、可离线、可发微信。
- **可复用**：游戏内容存于 `game_config.json`，改文案/换配色即可重新生成。

## 工作流（四步）
1. **故事解析与教学设计** — 拆分场景、设计选项与反馈，输出 `user-data/game_config.json`。
2. **视觉生成** — 为封面 + 每个场景生成统一风格配图，存入 `user-data/images/`。
3. **网页组装** — 运行 `scripts/build_game.py` 把数据与图片合成单文件 HTML。
4. **交付** — 输出可双击打开的互动游戏网页。

## 本地使用
```bash
python scripts/build_game.py user-data/game_config.json assets/template.html user-data/output_game.html
```

## DEMO 示例
- [《陋室铭》互动游戏](demo/陋室铭/陋室铭_互动游戏.html) — 7 关闯关 + 课程复盘
- [《陋室铭》游戏数据](demo/陋室铭/game_config.json) — 输入 JSON 示例

在线预览：https://iithink88.github.io/interactive-teaching-game/demo/%E5%8C%A1%E5%AE%A4%E9%93%AD/%E5%8C%A1%E5%AE%A4%E9%93%AD_%E4%BA%92%E5%8A%A8%E6%B8%B8%E6%88%8F.html

## 许可证
MIT
