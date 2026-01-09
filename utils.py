def format_speed(val_mb, use_bits):
    val = val_mb * 8 if use_bits else val_mb

    if use_bits:
        units = ["Kbps", "Mbps", "Gbps"]
    else:
        units = ["KB/s", "MB/s", "GB/s"]

    val_k = val * 1024

    if val_k < 1000:
        return f"{format_decimal(val_k)} {units[0]}"
    elif val_k < 1000 * 1024:
        return f"{format_decimal(val)} {units[1]}"
    else:
        return f"{format_decimal(val / 1024)} {units[2]}"

def format_decimal(value):
    try:
        s = "{:,.1f}".format(value)
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,0"
