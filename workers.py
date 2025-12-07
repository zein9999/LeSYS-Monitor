import time
import psutil
from PySide6.QtCore import QThread, Signal


class WorkerThread(QThread):
    data_signal = Signal(dict)

    def run(self):
        # --- WMI CHECK ---
        try:
            import pythoncom
            import wmi
            pythoncom.CoInitialize()
            wmi_c = wmi.WMI(namespace="root\\cimv2")
            has_wmi = True
        except:
            has_wmi = False

        # --- GPU SETUP ---
        gpu_mode = "NONE"
        nvml_handle = None
        wmi_gpu = None

        # Intentar NVIDIA
        try:
            import pynvml
            pynvml.nvmlInit()
            nvml_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            gpu_mode = "NVIDIA"
        except:
            if has_wmi:
                try:
                    wmi_gpu = wmi_c.Win32_VideoController()[0]
                    gpu_mode = "WMI"
                except:
                    pass

        # --- RED ---
        self.prev_net_per_nic = psutil.net_io_counters(pernic=True)
        last_time = time.time()

        while True:
            current_time = time.time()
            dt = current_time - last_time
            if dt <= 0: dt = 0.001
            last_time = current_time

            data = {'gpu': 0, 'disk_io': {}, 'disk_usage': {}}

            # --- CPU ---
            data['cpu'] = psutil.cpu_percent(interval=None)
            try:
                freq = psutil.cpu_freq()
                if freq:
                    data['cpu_extra'] = f"{freq.current / 1000:.2f} GHz"
                else:
                    data['cpu_extra'] = ""
            except:
                data['cpu_extra'] = ""

            # --- RAM (Usada / Total) ---
            mem = psutil.virtual_memory()
            data['ram'] = mem.percent
            used_gb = mem.used / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            data['ram_extra'] = f"{used_gb:.1f} / {total_gb:.1f} GB"

            # --- GPU (Usada / Total) ---
            data['gpu_extra'] = ""

            if gpu_mode == "NVIDIA" and nvml_handle:
                try:
                    import pynvml  # Re-import local por seguridad en hilos
                    util = pynvml.nvmlDeviceGetUtilizationRates(nvml_handle)
                    data['gpu'] = util.gpu

                    # Memoria
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(nvml_handle)
                    vram_used = mem_info.used / (1024 ** 3)
                    vram_total = mem_info.total / (1024 ** 3)
                    data['gpu_extra'] = f"{vram_used:.1f} / {vram_total:.1f} GB"
                except:
                    pass

            elif gpu_mode == "WMI":
                try:
                    if hasattr(wmi_gpu, 'LoadPercentage'):
                        data['gpu'] = wmi_gpu.LoadPercentage

                    # Intentar leer VRAM total de WMI (AdapterRAM devuelve bytes)
                    if hasattr(wmi_gpu, 'AdapterRAM') and wmi_gpu.AdapterRAM:
                        vram_total = int(wmi_gpu.AdapterRAM) / (1024 ** 3)
                        # WMI no suele dar "VRAM Usada" fácilmente, así que mostramos solo total
                        data['gpu_extra'] = f"Total: {vram_total:.1f} GB"
                except:
                    pass

            # --- RED ---
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

            # --- DISCOS ---
            if has_wmi:
                try:
                    for i in wmi_c.Win32_PerfFormattedData_PerfDisk_LogicalDisk():
                        data['disk_io'][i.Name] = (int(i.DiskReadBytesPerSec) / 1024 ** 2,
                                                   int(i.DiskWriteBytesPerSec) / 1024 ** 2)
                except:
                    pass
            else:
                io = psutil.disk_io_counters()
                if io: data['disk_io']['Total'] = (io.read_bytes / 1024 ** 2, io.write_bytes / 1024 ** 2)

            for p in psutil.disk_partitions():
                if 'cdrom' not in p.opts and p.fstype != '':
                    try:
                        data['disk_usage'][p.device.rstrip("\\")] = psutil.disk_usage(p.mountpoint).percent
                    except:
                        pass

            self.data_signal.emit(data)
            self.msleep(1000)