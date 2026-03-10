@echo off
:: 强制将命令行窗口的编码切换为 UTF-8，解决火星文乱码
chcp 65001 >nul

title 运行 main.py
echo 🚀 正在启动 main.py，请稍候...
echo --------------------------------------------------

:: 调用 python 运行当前目录下的 main.py
python main.py

echo --------------------------------------------------
echo ✅ 程序执行完毕，或遇到错误意外停止。
pause