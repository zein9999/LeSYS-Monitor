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

# ESTA ES LA FUNCIÓN QUE TE FALTA O QUE NO ENCUENTRA
def format_decimal(value):
    """
    Formatea un número float a string con estilo europeo:
    Ej: 2389.5 -> "2.389,5"
    """
    try:
        # Formato estándar inglés (coma miles, punto decimal)
        s = "{:,.1f}".format(value)
        # Invertimos: Coma -> X, Punto -> Coma, X -> Punto
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "0,0"