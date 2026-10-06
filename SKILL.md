---
name: infinitynikki-photo-skill
display_name: 无限暖暖摄影助手
display_name_en: Infinity Nikki Photo Skill
description: 搜索和查询本地《无限暖暖》摄影作品，并获取照片对应的搭配码和摄影参数。
description_zh: 根据人物构图、场景、游戏时间、色调、背景和横竖屏等条件搜索《无限暖暖》照片，并查询搭配码和摄影参数。
description_en: Search local Infinity Nikki photos by visual attributes and retrieve outfit codes and camera parameter codes.
allowed-tools: Bash
version: 0.1.0
author: local-user
---

# Infinity Nikki Photo Skill

用于搜索和查询用户本地的《无限暖暖》摄影照片。

## 搜索照片

当用户提出类似以下需求时使用搜索功能：

- 找全身照片
- 找竖屏人像
- 找夜晚白背景照片
- 找冷色调风景
- 找横屏建筑照片

执行：

`python scripts/skill_tool.py search [参数]`

可用参数：

- `--photo-type`
  - portrait：人物
  - scenery：景象

- `--framing`
  - close_up：大头照
  - half_body：半身照
  - full_body：全身照

- `--view`
  - front：正面
  - back：背面
  - side：侧面

- `--scene`
  - architecture：建筑
  - nature：自然风景
  - animal：动物
  - insect：昆虫
  - other：其他

- `--game-time`
  - day：白天
  - dusk：黄昏
  - night：夜晚
  - unknown：未知

- `--color-tone`
  - warm：暖色
  - cool：冷色

- `--background`
  - white：白色背景
  - black：黑色背景
  - normal：普通环境背景

- `--orientation`
  - landscape：横屏
  - portrait：竖屏
  - square：方形

- `--limit`
  - 默认返回20张

用户未提到的条件不要添加。

例如用户说：

“找竖屏夜晚全身照”

执行：

`python scripts/skill_tool.py search --framing full_body --orientation portrait --game-time night`

## 查询照片详情

当用户指定某张照片并询问：

- 这张照片的搭配码是什么
- 摄影参数是什么
- 怎么复刻这张照片
- 查看这张照片的完整信息

执行：

`python scripts/skill_tool.py detail --filename <文件名>`

返回信息可能包括：

- 文件名
- 本地路径
- 现实保存时间
- 横屏/竖屏
- 人像/景象
- 构图
- 人物朝向
- 场景
- 游戏时间
- 冷暖色调
- 背景
- 搭配码
- 摄影参数编码

如果某张照片没有录入搭配码或摄影参数，应明确告诉用户“尚未录入”，不要自行生成。

## 重要规则

1. 不要猜测搭配码。
2. 不要猜测摄影参数编码。
3. 搭配码和摄影参数必须以数据库实际结果为准。
4. 搜索条件只使用用户明确提出的条件。
5. 如果没有匹配结果，应告诉用户没有找到符合条件的照片。