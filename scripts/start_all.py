"""一键启动所有服务。"""

import subprocess
import sys
import time
import signal

processes = []


def cleanup(sig=None, frame=None):
    print("\n🛑 停止所有服务...")
    for p in processes:
        p.terminate()
    sys.exit(0)


signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)


def main():
    print("🚀 OpsAgent 一键启动\n")

    cmds = [
        ("API Server", [sys.executable, "-m", "api.main"]),
    ]

    for name, cmd in cmds:
        print(f"  ▶ 启动 {name}...")
        p = subprocess.Popen(cmd)
        processes.append(p)
        time.sleep(1)

    print("\n✅ 所有服务已启动")
    print("   API:  http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止所有服务\n")

    for p in processes:
        p.wait()


if __name__ == "__main__":
    main()
