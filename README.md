# InfinityNikki Photo Skill

A multimodal photo management skill for Infinity Nikki.

一个用于管理、理解、检索《无限暖暖》游戏摄影资产，并关联搭配码与摄影参数的本地多模态 Skill。

## 项目简介

《无限暖暖》游戏摄影过程中会积累大量本地照片，随着照片数量增加，仅依靠文件夹和文件名很难快速查找过去拍摄的作品。

本项目直接读取游戏本地相册目录，通过 SQLite 建立照片数据库，并使用 Qwen2.5-VL 自动分析照片内容，为照片生成结构化语义标签。

最终通过 WorkBuddy Skill，可以使用自然语言搜索本地游戏照片，例如：

> 帮我找 5 张竖屏、夜晚、全身人物照片。

系统会根据照片语义标签查询数据库，并返回匹配照片及相关信息。

## 当前功能

- 直接扫描《无限暖暖》本地游戏相册
- 自动提取照片文件名、时间、尺寸、横竖屏等基础信息
- 使用 SHA256 为照片建立唯一标识，避免重复入库
- 使用 Qwen2.5-VL 进行本地图片语义分析
- 自动识别人像、构图、人物方向、场景、游戏时间、色调和背景
- 使用 SQLite 保存照片及语义信息
- 支持新增照片增量分析
- 支持按语义标签搜索照片
- 支持自然语言照片检索
- 支持照片与搭配码关联
- 支持照片与摄影参数码关联
- 支持 WorkBuddy Skill 调用

## 整体流程

```text
Infinity Nikki 游戏相册
        ↓
scan_photos.py
        ↓
SQLite 照片数据库
        ↓
Qwen2.5-VL
        ↓
照片语义标签
        ↓
语义检索
        ↓
InfinityNikki Photo Skill
        ↓
WorkBuddy