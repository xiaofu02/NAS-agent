---
name: mp_get
category: moviepilot
description: 对 MoviePilot 指定路径执行只读 GET
command: /mpget
aliases: [moviepilot_get, mpget]
keywords: []
show_in_help: true
handler: tools.moviepilot.get.tool:moviepilot_get
formatter: tools.moviepilot.get.formatter:print_result
arg_mode: text_tail
---

# MoviePilot GET 工具