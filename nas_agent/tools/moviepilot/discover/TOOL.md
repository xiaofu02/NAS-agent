---
name: mp_discover
category: moviepilot
description: 自动发现 MoviePilot 前端资源中的 API 路径线索
command: /mpdiscover
aliases: [moviepilot_discover, mpdiscover]
keywords: [发现moviepilot接口, 扫描moviepilot接口, 查找moviepilot接口, moviepilot接口线索]
show_in_help: true
handler: tools.moviepilot.discover.tool:discover_moviepilot_routes
formatter: tools.moviepilot.discover.formatter:print_result
arg_mode: none
---

# MoviePilot 接口发现工具