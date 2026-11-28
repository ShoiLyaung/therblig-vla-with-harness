# 冻结基线检查

在总仓执行 `python3 tools/checks/run_all.py`。入口先运行子仓契约测试，再核对目录投影、设计文档、D12 用例及三个仓库的差异。D12 须能读取用例钉住的 Git 对象。

在独立虚拟环境中用 `python3 -m pip install -r tools/checks/requirements.txt` 安装依赖。摘要测试使用 Node.js 的 ECMAScript 排序和 JSON 序列化实现 RFC 8785。子仓可单独执行 `python3 -m pytest tests/contract`。
