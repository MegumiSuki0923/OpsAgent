"""下载 NAB 数据集样本和运维文档。"""

import urllib.request
from pathlib import Path

NAB_FILES = [
    ("realKnownCause/ambient_temperature_system_failure.csv",
     "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ambient_temperature_system_failure.csv"),
    ("realKnownCause/cpu_utilization_asg_misconfiguration.csv",
     "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/cpu_utilization_asg_misconfiguration.csv"),
    ("realKnownCause/ec2_request_latency_system_failure.csv",
     "https://raw.githubusercontent.com/numenta/NAB/master/data/realKnownCause/ec2_request_latency_system_failure.csv"),
]

OPS_DOCS = {
    "k8s_troubleshooting.md": """\
# Kubernetes 常见故障排查

## Pod CrashLoopBackOff
当 Pod 反复崩溃重启时，状态会显示为 CrashLoopBackOff。

排查步骤：
1. `kubectl describe pod <pod-name>` 查看事件和退出码
2. `kubectl logs <pod-name> --previous` 查看上次崩溃前的日志
3. 常见原因：应用启动失败、配置错误、依赖服务不可用、资源不足（OOMKilled）
4. 如果是 OOMKilled，检查 resources.limits.memory 是否设置过低

## Pod Pending
Pod 一直处于 Pending 状态无法调度。

排查步骤：
1. `kubectl describe pod <pod-name>` 查看 Events 中的调度失败原因
2. 常见原因：节点资源不足、NodeSelector/Affinity 不匹配、PVC 未绑定
3. `kubectl get nodes -o wide` 检查节点资源使用情况
4. `kubectl describe node <node-name>` 查看 Allocatable 资源

## Pod OOMKilled
容器因内存超出限制被 Linux OOM Killer 杀掉。

排查步骤：
1. `kubectl describe pod` 查看 Last State 中的 Reason: OOMKilled
2. 检查 resources.limits.memory 设置
3. 使用 `kubectl top pod` 查看实际内存使用
4. 考虑增加 memory limits 或优化应用内存使用
5. 检查是否有内存泄漏：观察内存是否持续增长

## Service 无法访问
Service 创建后无法通过 ClusterIP 或 NodePort 访问。

排查步骤：
1. `kubectl get endpoints <service-name>` 检查是否有关联的 Endpoints
2. 确认 Service 的 selector 和 Pod 的 labels 匹配
3. `kubectl get pods -l <selector>` 确认匹配的 Pod 是否 Running
4. 在 Pod 内部使用 curl 测试连通性
""",

    "linux_performance.md": """\
# Linux 性能问题排查

## CPU 使用率飙高
排查步骤：
1. `top -c` 或 `htop` 查看 CPU 占用最高的进程
2. `pidstat -u 1 5` 持续观察各进程 CPU 使用情况
3. `perf top` 查看热点函数（需要 perf 工具）
4. 检查是否有定时任务（crontab）导致周期性 CPU 飙高
5. 检查系统 load average：`uptime` 或 `cat /proc/loadavg`

常见原因：
- 应用死循环或计算密集型任务
- GC（垃圾回收）导致的 CPU 尖峰
- 恶意进程或挖矿程序
- 内核态 CPU 高：可能是 I/O 等待或锁竞争

## 内存不足
排查步骤：
1. `free -h` 查看内存使用概况
2. `cat /proc/meminfo` 查看详细内存信息
3. `ps aux --sort=-%mem | head -20` 查看内存占用最高的进程
4. 检查 swap 使用：swap 被大量使用会导致性能下降
5. 检查是否有内存泄漏：观察 RSS 是否持续增长

## 磁盘 I/O 高
排查步骤：
1. `iostat -x 1 5` 查看磁盘 I/O 统计
2. `iotop` 查看哪个进程在大量读写
3. `df -h` 检查磁盘空间
4. `lsof +D /path` 查看正在访问某目录的进程
""",

    "mysql_troubleshooting.md": """\
# MySQL 常见故障排查

## 连接数耗尽
错误信息：Too many connections

排查步骤：
1. `SHOW VARIABLES LIKE 'max_connections';` 查看最大连接数
2. `SHOW PROCESSLIST;` 查看当前连接
3. `SHOW STATUS LIKE 'Threads_connected';` 查看当前连接数
4. 检查应用是否正确关闭数据库连接（连接泄漏）
5. 检查连接池配置是否合理

修复方案：
- 临时：`SET GLOBAL max_connections = 500;`
- 永久：修改 my.cnf 的 max_connections
- 根本：排查连接泄漏，优化连接池配置

## 主从复制延迟
排查步骤：
1. 在从库执行 `SHOW SLAVE STATUS\\G` 查看 Seconds_Behind_Master
2. 检查主库是否有大事务
3. 检查从库 I/O 线程和 SQL 线程状态
4. 检查网络延迟：`ping` 主库地址
5. 检查从库磁盘 I/O 性能

常见原因：
- 主库大事务（如大表 DDL、批量 INSERT）
- 从库硬件性能不足
- 网络带宽不足
- 从库存在锁等待

## 慢查询
排查步骤：
1. 开启慢查询日志：`SET GLOBAL slow_query_log = ON;`
2. `EXPLAIN` 分析查询执行计划
3. 检查是否缺少索引
4. `SHOW INDEX FROM table_name;` 查看表索引
5. 检查表数据量和查询模式是否匹配
""",

    "nginx_troubleshooting.md": """\
# Nginx 常见故障排查

## 502 Bad Gateway
Nginx 无法连接到后端服务时返回 502。

排查步骤：
1. 检查后端服务是否正常运行：`curl http://backend:port/health`
2. 查看 Nginx error log：`tail -f /var/log/nginx/error.log`
3. 检查 upstream 配置是否正确
4. 检查后端服务的连接超时设置
5. 检查系统 ulimit 和文件描述符限制

常见原因：
- 后端服务宕机或重启中
- 后端服务连接数耗尽
- upstream 地址配置错误
- proxy_pass 端口错误

## 504 Gateway Timeout
Nginx 等待后端服务响应超时。

排查步骤：
1. 检查 proxy_read_timeout 和 proxy_connect_timeout 配置
2. 检查后端服务处理是否过慢
3. 检查网络连通性
4. 查看后端服务日志排查慢请求

## 高并发下性能下降
优化方向：
1. worker_processes 设为 CPU 核心数
2. worker_connections 调大（如 10240）
3. 开启 sendfile、tcp_nopush、tcp_nodelay
4. 配置合理的 keepalive_timeout
5. 启用 gzip 压缩
6. 配置静态资源缓存
""",

    "redis_troubleshooting.md": """\
# Redis 常见故障排查

## 内存占用过高 / OOM
排查步骤：
1. `redis-cli INFO memory` 查看内存使用详情
2. `redis-cli --bigkeys` 扫描大 key
3. 检查 maxmemory 和 maxmemory-policy 配置
4. 使用 `MEMORY USAGE <key>` 检查特定 key 的内存占用
5. 检查是否有大量过期但未清理的 key

修复方案：
- 设置合理的 maxmemory 和淘汰策略（如 allkeys-lru）
- 清理大 key 和无用数据
- 使用 UNLINK（异步删除）代替 DEL 删除大 key
- 考虑 Redis Cluster 分片

## 延迟突增
排查步骤：
1. `redis-cli --latency` 测试延迟
2. `redis-cli SLOWLOG GET 10` 查看慢命令
3. 检查是否使用了 KEYS、SMEMBERS 等 O(N) 命令
4. 检查是否触发了 RDB/AOF 持久化
5. 检查系统 swap 使用情况

## 连接被拒绝
排查步骤：
1. 检查 maxclients 配置
2. `redis-cli INFO clients` 查看当前连接数
3. 检查应用连接池配置
4. 检查是否有连接泄漏
5. 检查 bind 和 protected-mode 配置
""",
}


def download_nab(output_dir: str = "./data/nab_sample"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for name, url in NAB_FILES:
        filename = name.split("/")[-1]
        dest = out / filename
        if dest.exists():
            print(f"  ⏭️  {filename} 已存在，跳过")
            continue
        print(f"  ⬇️  下载 {filename}...")
        try:
            urllib.request.urlretrieve(url, str(dest))
            print(f"  ✅ {filename}")
        except Exception as e:
            print(f"  ❌ {filename}: {e}")


def create_ops_docs(output_dir: str = "./data/ops_docs"):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    for filename, content in OPS_DOCS.items():
        dest = out / filename
        dest.write_text(content, encoding="utf-8")
        print(f"  ✅ {filename}")


def main():
    print("📥 下载 NAB 数据集样本...")
    download_nab()
    print("\n📝 创建运维文档...")
    create_ops_docs()
    print("\n✅ 数据准备完成！")
    print("   下一步：运行 python -m mcp_servers.ops_knowledge_rag.indexer 构建索引")


if __name__ == "__main__":
    main()
