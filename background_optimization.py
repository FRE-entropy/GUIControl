#!/usr/bin/env python3
"""
后台性能优化配置
专门针对后台运行时性能下降问题的优化策略
"""

import time
import psutil
import ctypes
import win32con
import win32process
import win32api


class BackgroundOptimizer:
    """后台性能优化器"""
    
    def __init__(self):
        self.original_priority = None
        self.optimization_applied = False
        
    def apply_background_optimizations(self):
        """应用后台优化策略"""
        optimizations = [
            self._set_process_priority,
            self._set_thread_priority,
            self._enable_background_mode,
            self._reduce_cpu_usage
        ]
        
        success_count = 0
        for optimization in optimizations:
            if optimization():
                success_count += 1
        
        self.optimization_applied = success_count > 0
        return self.optimization_applied
    
    def _set_process_priority(self):
        """设置进程优先级"""
        try:
            # 获取当前优先级
            process_handle = ctypes.windll.kernel32.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, win32process.GetCurrentProcessId()
            )
            
            # 设置为高优先级
            ctypes.windll.kernel32.SetPriorityClass(
                process_handle, win32con.HIGH_PRIORITY_CLASS
            )
            
            ctypes.windll.kernel32.CloseHandle(process_handle)
            print("✓ 进程优先级已设置为高")
            return True
        except Exception as e:
            print(f"✗ 设置进程优先级失败: {e}")
            return False
    
    def _set_thread_priority(self):
        """设置线程优先级"""
        try:
            # 设置主线程优先级
            # 使用正确的线程访问权限常量
            THREAD_ALL_ACCESS = 0x1F03FF  # 标准线程所有访问权限
            thread_handle = ctypes.windll.kernel32.OpenThread(
                THREAD_ALL_ACCESS, False, win32api.GetCurrentThreadId()
            )
            
            ctypes.windll.kernel32.SetThreadPriority(
                thread_handle, win32con.THREAD_PRIORITY_HIGHEST
            )
            
            ctypes.windll.kernel32.CloseHandle(thread_handle)
            print("✓ 线程优先级已设置为最高")
            return True
        except Exception as e:
            print(f"✗ 设置线程优先级失败: {e}")
            return False
    
    def _enable_background_mode(self):
        """启用后台模式"""
        try:
            process_handle = ctypes.windll.kernel32.OpenProcess(
                win32con.PROCESS_ALL_ACCESS, False, win32process.GetCurrentProcessId()
            )
            
            # 使用标准的高优先级类，而不是不存在的后台模式常量
            ctypes.windll.kernel32.SetPriorityClass(
                process_handle, win32con.HIGH_PRIORITY_CLASS
            )
            
            ctypes.windll.kernel32.CloseHandle(process_handle)
            print("✓ 后台模式已启用（使用高优先级）")
            return True
        except Exception as e:
            print(f"✗ 启用后台模式失败: {e}")
            return False
    
    def _reduce_cpu_usage(self):
        """降低CPU使用率策略"""
        try:
            # 设置进程亲和性（限制CPU核心使用）
            process = psutil.Process()
            
            # 获取可用CPU核心
            available_cores = list(range(psutil.cpu_count()))
            if len(available_cores) > 2:
                # 如果系统有多个核心，限制使用部分核心
                restricted_cores = available_cores[:2]  # 只使用前2个核心
                process.cpu_affinity(restricted_cores)
                print(f"✓ CPU亲和性已限制为: {restricted_cores}")
            
            return True
        except Exception as e:
            print(f"✗ 降低CPU使用率失败: {e}")
            return False
    
    def get_system_info(self):
        """获取系统信息"""
        info = {
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            'memory_available': psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent
        }
        return info
    
    def monitor_performance(self, duration=10):
        """监控性能表现"""
        print("开始性能监控...")
        
        cpu_usage = []
        memory_usage = []
        
        start_time = time.time()
        while time.time() - start_time < duration:
            cpu_usage.append(psutil.cpu_percent(interval=0.1))
            memory_usage.append(psutil.virtual_memory().percent)
            time.sleep(0.1)
        
        avg_cpu = sum(cpu_usage) / len(cpu_usage)
        avg_memory = sum(memory_usage) / len(memory_usage)
        
        print(f"平均CPU使用率: {avg_cpu:.1f}%")
        print(f"平均内存使用率: {avg_memory:.1f}%")
        
        return {
            'avg_cpu': avg_cpu,
            'avg_memory': avg_memory,
            'cpu_samples': cpu_usage,
            'memory_samples': memory_usage
        }


def optimize_for_background():
    """应用后台优化"""
    optimizer = BackgroundOptimizer()
    
    print("=" * 50)
    print("后台性能优化")
    print("=" * 50)
    
    # 显示系统信息
    system_info = optimizer.get_system_info()
    print(f"系统信息: {system_info['cpu_count']}核CPU, {system_info['memory_total']:.1f}GB内存")
    print(f"当前CPU使用率: {system_info['cpu_usage']:.1f}%")
    print(f"当前内存使用率: {system_info['memory_usage']:.1f}%")
    
    # 应用优化
    print("\n应用优化策略...")
    success = optimizer.apply_background_optimizations()
    
    if success:
        print("\n✓ 后台优化已成功应用")
        
        # 监控优化效果
        print("\n监控优化效果...")
        performance = optimizer.monitor_performance(duration=5)
        
        print("\n优化完成！")
        return True
    else:
        print("\n✗ 后台优化应用失败")
        return False


if __name__ == "__main__":
    optimize_for_background()