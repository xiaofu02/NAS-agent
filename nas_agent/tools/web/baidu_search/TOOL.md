---
name: baidu_web_search
category: web
description: 通过百度千帆智能搜索生成进行联网搜索
command: /search
aliases: [search, web, baidu]
keywords: [联网搜索, 百度搜索, 搜索一下, 帮我查, 网上查, 查一下]
show_in_help: true
handler: tools.web.baidu_search.tool:search_web
formatter: tools.web.baidu_search.formatter:print_result
arg_mode: text_tail
---

# 百度联网搜索工具