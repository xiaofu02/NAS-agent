---
name: system_status
category: system
description: 获取完整系统状态和硬件信息
command: /sys
aliases: [sys, status, hardware_status]
keywords: [系统状态, 硬件状态, 当前硬件环境, 系统信息, 硬件信息, 查看系统状态, 查看当前硬件环境]
show_in_help: true
handler: tools.system.status.tool:get_system_status
formatter: tools.system.status.formatter:print_result
arg_mode: none
---

# 系统状态工具