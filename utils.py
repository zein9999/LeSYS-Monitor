def format_speed(val_mb, use_bits):
    val = val_mb * 8 if use_bits else val_mb

    if use_bits:
        units = ["Kbps", "Mbps", "Gbps"]
    else:
        units = ["KB/s", "MB/s", "GB/s"]

    val_k = val * 1024

    if val_k < 1000:
        return f"{val_k:.1f} {units[0]}"
    elif val_k < 1000 * 1024:
        return f"{val:.1f} {units[1]}"
    else:
        return f"{val / 1024:.2f} {units[2]}"