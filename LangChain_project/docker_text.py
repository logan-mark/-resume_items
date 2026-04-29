import os
import platform

print(f"当前操作系统: {platform.system()}")
print(f"当前用户 ID: {os.getuid() if hasattr(os, 'getuid') else 'N/A'}")
print(f"项目目录内容: {os.listdir('.')}")