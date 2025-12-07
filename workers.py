import time
import psutil
from PySide6.QtCore import QThread, Signal

IGNORED_PROCESSES = {
    "System Idle Process", "System", "Registry", "MemCompression", "vmmem",
    "smss.exe", "csrss.exe", "wininit.exe", "services.exe", "lsass.exe",
    "winlogon.exe", "Memory Compression", "svchost.exe", "RuntimeBroker.exe"
}


class WorkerThread(QThread):
    data_signal = Signal(dict)

    def run(self):
        wmi_c = None
        has_wmi = False
        try:
            import pythoncom
            import wmi
            pythoncom.CoInitialize()
            wmi_c = wmi.WMI(namespace="root\\cimv2")
            has_wmi = True
        except:
            pass

        gpu_mode = "NONE"
        nvml_handle = None
        wmi_gpu = None

        try:
            import pynvml
            pynvml.nvmlInit()
            nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_mode = "NVIDIA"
        except:
            if has_wmi:
                try:
                    if wmi_c.Win32_VideoController():
                        gpu_mode = "WMI"
                except:
                    pass

        self.prev_net_per_nic = psutil.net_io_counters(pernic=True)
        last_time = time.time()

        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt <= 0: dt = 0.001
            last_time = current_time

            data = {'gpu': 0, 'disk_io': {}, 'disk_usage': {}}

            data['cpu'] = psutil.cpu_percent(interval=None)
            try:
                freq = psutil.cpu_freq()
                if freq:
                    val = freq.current if freq.current > 100 else freq.max
                    data['cpu_extra'] = f"{val / 1000:.2f} GHz"
                else:
                    data['cpu_extra'] = ""
            except:
                data['cpu_extra'] = ""

            mem = psutil.virtual_memory()
            data['ram'] = mem.percent
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            data['ram_extra'] = f"{used_gb:.1f} / {total_gb:.1f} GB"

            data['gpu_extra'] = ""
            if gpu_mode == "NVIDIA" and nvml_handle:
                try:
                    import pynvml
                    util = pynvml.nvmlDeviceGetUtilizationRates(nvml_handle)
                    data['gpu'] = util.gpu
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(nvml_handle)
                    vram_used = mem_info.used / (1024 ** 3)
                    vram_total = mem_info.total / (1024 ** 3)
                    data['gpu_extra'] = f"{vram_used:.1f} / {vram_total:.1f} GB"
                except:
                    pass
            elif gpu_mode == "WMI" and has_wmi:
                try:
                    gpu_list = wmi_c.Win32_VideoController()
                    if gpu_list:
                        if hasattr(gpu_list[0], 'LoadPercentage'):
                            data['gpu'] = gpu_list[0].LoadPercentage
                        if hasattr(gpu_list[0], 'AdapterRAM') and gpu_list[0].AdapterRAM:
                            vram_total = int(gpu_list[0].AdapterRAM) / (1024 ** 3)
                            data['gpu_extra'] = f"Total: {vram_total:.1f} GB"
                except:
                    pass

            curr_net_per_nic = psutil.net_io_counters(pernic=True)
            total_sent_delta = 0
            total_recv_delta = 0
            active_iface_name = "Ethernet"
            max_activity = -1
            blacklist = ['loopback', 'vethernet', 'wsl', 'vmware', 'virtualbox', 'adapter', 'pseudo', 'teredo']

            for name, io in curr_net_per_nic.items():
                if any(x in name.lower() for x in blacklist): continue
                prev_io = self.prev_net_per_nic.get(name, io)
                delta_s = io.bytes_sent - prev_io.bytes_sent
                delta_r = io.bytes_recv - prev_io.bytes_recv
                if delta_s < 0: delta_s = 0
                if delta_r < 0: delta_r = 0
                total_sent_delta += delta_s
                total_recv_delta += delta_r
                if (delta_s + delta_r) > max_activity:
                    max_activity = (delta_s + delta_r)
                    active_iface_name = name

            self.prev_net_per_nic = curr_net_per_nic
            data['net_up'] = (total_sent_delta / dt) / (1024 ** 2)
            data['net_down'] = (total_recv_delta / dt) / (1024 ** 2)
            data['net_iface'] = active_iface_name

            if has_wmi:
                try:
                    for i in wmi_c.Win32_PerfFormattedData_PerfDisk_LogicalDisk():
                        read_mb = int(i.DiskReadBytesPerSec) / (1024 ** 2)
                        write_mb = int(i.DiskWriteBytesPerSec) / (1024 ** 2)
                        data['disk_io'][i.Name] = (read_mb, write_mb)
                except:
                    pass

            try:
                partitions = psutil.disk_partitions(all=False)
                for p in partitions:
                    if 'cdrom' in p.opts or p.fstype == '': continue
                    try:
                        usage = psutil.disk_usage(p.mountpoint).percent
                        data['disk_usage'][p.device.rstrip("\\")] = usage
                    except:
                        pass
            except:
                pass

            self.data_signal.emit(data)
            self.msleep(1000)


class ProcessWorker(QThread):
    processes_signal = Signal(list)

    def run(self):
        prev_io_data = {}
        logical_cores = psutil.cpu_count(logical=True) or 1

        while True:
            procs = []
            try:
                current_time = time.time()
                for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'exe', 'io_counters']):
                    try:
                        p_info = p.info
                        name = p_info['name']
                        if not name: continue
                        if name in IGNORED_PROCESSES: continue

                        pid = p_info['pid']

                        disk_usage = 0.0
                        io = p_info['io_counters']
                        if io:
                            current_total = io.read_bytes + io.write_bytes
                            if pid in prev_io_data:
                                prev = prev_io_data[pid]
                                dt = current_time - prev['time']
                                if dt > 0:
                                    diff = current_total - prev['total']
                                    if diff < 0: diff = 0
                                    disk_usage = (diff / dt) / (1024 * 1024)
                            prev_io_data[pid] = {'total': current_total, 'time': current_time}

                        raw_cpu = p_info['cpu_percent'] or 0.0
                        normalized_cpu = raw_cpu / logical_cores

                        try:
                            mem_full = p.memory_full_info()
                            ram_bytes = mem_full.uss
                        except:
                            ram_bytes = p.memory_info().rss / 2

                        procs.append({
                            'pid': pid,
                            'name': name,
                            'cpu': normalized_cpu,
                            'ram': ram_bytes,
                            'disk': disk_usage,
                            'exe': p_info['exe'] or ""
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
            except:
                pass

            current_pids = {p['pid'] for p in procs}
            prev_io_data = {k: v for k, v in prev_io_data.items() if k in current_pids}

            self.processes_signal.emit(procs)
            self.sleep(2)