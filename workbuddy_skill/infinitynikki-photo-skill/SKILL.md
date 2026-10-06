---
name: infinitynikki-photo-skill
display_name: 无限暖暖摄影助手
display_name_en: Infinity Nikki Photo Skill
description: 搜索本地《无限暖暖》摄影照片，并获取照片的搭配码、摄影参数和拍摄属性。
description_zh: 根据构图、人物方向、场景、游戏时间、色调、背景和横竖屏搜索无限暖暖照片，并获取照片详情。
description_en: Search local Infinity Nikki photos by visual attributes and retrieve photo details, outfit codes, and camera parameter codes.
allowed-tools: Bash
version: 0.3.0
author: local-user
user-invocable: true
disable-model-invocation: false
---

# 无限暖暖摄影助手

本技能用于查询用户本地保存的《无限暖暖》摄影作品。

照片已经提前完成图像分析，不需要再次使用视觉模型分析图片。

## 数据库状态检查

当需要确认照片库是否正常时执行：

`python scripts/skill_tool.py status`

## 搜索照片

当用户提出照片搜索需求时，将自然语言转换成下面的结构化参数，然后执行：

`python scripts/skill_tool.py search [参数]`

支持的参数：

`--photo-type`

- portrait：人物照片
- scenery：景物照片

`--framing`

- close_up：大头照
- half_body：半身照
- full_body：全身照

`--view`

- front：人物正面
- back：人物背面
- side：人物侧面

`--scene`

- architecture：建筑
- nature：自然风景
- animal：动物
- insect：昆虫
- other：其他

`--game-time`

- day：白天
- dusk：黄昏
- night：夜晚
- unknown：无法判断

`--color-tone`

- warm：暖色调
- cool：冷色调

`--background`

- white：白色背景
- black：黑色背景
- normal：普通环境背景

`--orientation`

- landscape：横屏
- portrait：竖屏
- square：方形

`--limit`

控制最大返回数量，默认10。

用户没有明确提出的条件不要自行添加。

例如：

用户说：

“找几张竖屏夜晚全身照”

执行：

`python scripts/skill_tool.py search --orientation portrait --game-time night --framing full_body`

用户说：

“找横屏的自然风景”

执行：

`python scripts/skill_tool.py search --orientation landscape --photo-type scenery --scene nature`

## 查询照片详情

当用户指定某张照片并询问以下内容时：

- 搭配码
- 摄影参数
- 图片属性
- 如何复刻
- 完整信息

执行：

`python scripts/skill_tool.py detail --filename "<文件名>"`

## 返回结果

搜索结果中的：

`absolute_path`

是照片在用户电脑中的实际路径。

`outfits`

保存该照片对应的搭配码。

`camera_params`

保存该照片对应的摄影参数编码。

如果 outfits 或 camera_params 为空，应告诉用户尚未录入，不允许自行生成搭配码或摄影参数。

## 规则

1. 只查询数据库，不猜测不存在的数据。
2. 不生成虚假的搭配码。
3. 不生成虚假的摄影参数编码。
4. 不要因为用户没有提到某个属性而自行添加筛选条件。
5. 搜索不到时明确说明没有符合条件的照片。
6. 优先返回照片文件名和本地路径。
7. 用户要求复刻照片时，同时返回搭配码和摄影参数。

## 录入搭配码

当用户明确要求给某张照片绑定或修改搭配码时：

`python scripts/skill_tool.py set-outfit --filename "<文件名>" --code "<搭配码>"`

如果有说明：

`python scripts/skill_tool.py set-outfit --filename "<文件名>" --code "<搭配码>" --description "<说明>"`

只有用户明确提供搭配码时才能执行，不允许自行生成。

## 录入摄影参数

当用户明确要求给某张照片绑定或修改摄影参数时：

`python scripts/skill_tool.py set-camera --filename "<文件名>" --code "<摄影参数码>"`

如果有说明：

`python scripts/skill_tool.py set-camera --filename "<文件名>" --code "<摄影参数码>" --description "<说明>"`

摄影参数码必须完整保存，不要修改、缩短或解析。