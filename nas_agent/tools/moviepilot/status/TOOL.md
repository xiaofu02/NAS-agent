---
name: mp_status
category: moviepilot
description: 获取 MoviePilot 服务状态
command: /mp
aliases: [moviepilot, moviepilot_status]
keywords: [moviepilot状态, 查看moviepilot, moviepilot在线, moviepilot服务]
show_in_help: true
handler: tools.moviepilot.status.tool:get_moviepilot_status
formatter: tools.moviepilot.status.formatter:print_result
arg_mode: none
---

# MoviePilot 状态工具