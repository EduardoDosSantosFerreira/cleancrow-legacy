# ============================================================================
# DIAGNÓSTICO DE ESPAÇO (FUNÇÃO FALTANTE)
# ============================================================================

def diagnosticar_espaco() -> Dict:
    """
    Diagnostica quanto espaço pode ser liberado
    
    Returns:
        Dict com estimativas
    """
    resultados = {
        "windows_update_mb": 0,
        "temp_mb": 0,
        "logs_mb": 0,
        "recycle_mb": 0,
        "total_mb": 0,
        "total_gb": 0,
    }
    
    # Estimar espaço de temporários
    try:
        temp_dirs = [
            os.environ.get('TEMP', ''),
            os.environ.get('TMP', ''),
            "C:/Windows/Temp",
        ]
        for dir_path in temp_dirs:
            if dir_path and os.path.exists(dir_path):
                total = 0
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        try:
                            total += os.path.getsize(os.path.join(root, file))
                        except:
                            pass
                resultados["temp_mb"] += total // (1024 * 1024)
    except:
        pass
    
    # Estimar espaço do Windows Update
    try:
        update_paths = [
            "C:/Windows/SoftwareDistribution/Download",
            "C:/Windows/SoftwareDistribution/DeliveryOptimization",
        ]
        for path_str in update_paths:
            if os.path.exists(path_str):
                total = 0
                for root, dirs, files in os.walk(path_str):
                    for file in files:
                        try:
                            total += os.path.getsize(os.path.join(root, file))
                        except:
                            pass
                resultados["windows_update_mb"] += total // (1024 * 1024)
    except:
        pass
    
    # Estimar espaço de logs
    try:
        log_paths = [
            "C:/Windows/Logs/CBS",
            "C:/Windows/Logs/DISM",
            "C:/Windows/Panther",
        ]
        for path_str in log_paths:
            if os.path.exists(path_str):
                total = 0
                for root, dirs, files in os.walk(path_str):
                    for file in files:
                        try:
                            total += os.path.getsize(os.path.join(root, file))
                        except:
                            pass
                resultados["logs_mb"] += total // (1024 * 1024)
    except:
        pass
    
    # Estimar espaço da lixeira
    try:
        from core.win32_api import obter_tamanho_lixeira
        resultados["recycle_mb"] = obter_tamanho_lixeira() // (1024 * 1024)
    except:
        pass
    
    resultados["total_mb"] = sum([
        resultados["windows_update_mb"],
        resultados["temp_mb"],
        resultados["logs_mb"],
        resultados["recycle_mb"],
    ])
    resultados["total_gb"] = resultados["total_mb"] / 1024
    
    return resultados