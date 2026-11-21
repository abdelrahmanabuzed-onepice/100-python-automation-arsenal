#!/usr/bin/env python3
"""
Windows Service & Process Watchdog
==================================
Monitors critical Windows services and background processes, logs state changes,
detects service crashes, and performs automated self-healing / restarts.

Keywords: windows sysadmin, service monitor, auto-restart, process watchdog, windows automation
"""

import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

try:
    import psutil
except ImportError:
    psutil = None


def get_windows_service_status(service_name: str) -> Dict[str, Any]:
    """Query service status using Windows sc.exe or PowerShell."""
    status_info = {
        "service": service_name,
        "exists": False,
        "state": "UNKNOWN",
        "win32_exit_code": 0,
        "pid": None
    }
    
    if sys.platform != "win32":
        status_info["state"] = "NON_WINDOWS_PLATFORM"
        return status_info

    try:
        cmd = ["sc.exe", "query", service_name]
        res = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = res.stdout
        
        if "FAILED 1060" in output:
            status_info["exists"] = False
            status_info["state"] = "NOT_INSTALLED"
            return status_info
        
        status_info["exists"] = True
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("STATE"):
                parts = line.split(":")
                if len(parts) > 1:
                    status_info["state"] = parts[1].strip()
            elif line.startswith("WIN32_EXIT_CODE"):
                parts = line.split(":")
                if len(parts) > 1:
                    try:
                        status_info["win32_exit_code"] = int(parts[1].strip().split()[0])
                    except (ValueError, IndexError):
                        pass

        # Query PID if running
        if "RUNNING" in status_info["state"]:
            queryex = subprocess.run(["sc.exe", "queryex", service_name], capture_output=True, text=True, check=False)
            for line in queryex.stdout.splitlines():
                if "PID" in line and ":" in line:
                    val = line.split(":")[-1].strip()
                    if val.isdigit():
                        status_info["pid"] = int(val)
    except Exception as e:
        status_info["error"] = str(e)

    return status_info


def restart_windows_service(service_name: str) -> bool:
    """Attempt to restart a Windows service via net or sc."""
    try:
        subprocess.run(["net.exe", "stop", service_name], capture_output=True, text=True, check=False)
        time.sleep(1.5)
        start_res = subprocess.run(["net.exe", "start", service_name], capture_output=True, text=True, check=False)
        return start_res.returncode == 0
    except Exception:
        return False


def get_process_status(process_name: str) -> List[Dict[str, Any]]:
    """Scan running processes matching the process_name."""
    matches = []
    if not psutil:
        return matches

    for proc in psutil.process_iter(['pid', 'name', 'status', 'memory_info', 'cpu_percent']):
        try:
            info = proc.info
            if process_name.lower() in (info['name'] or '').lower():
                mem_mb = round(info['memory_info'].rss / (1024 * 1024), 2) if info.get('memory_info') else 0
                matches.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "status": info['status'],
                    "memory_mb": mem_mb,
                    "cpu_percent": info.get('cpu_percent', 0.0)
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return matches


def list_common_services() -> List[str]:
    """Return a default list of common critical Windows services to watch."""
    return [
        "Spooler",          # Print Spooler
        "wuauserv",         # Windows Update
        "Winmgmt",          # Windows Management Instrumentation
        "LanmanServer",     # Server service
        "Dhcp",             # DHCP Client
        "Dnscache",         # DNS Client
        "EventLog"          # Windows Event Log
    ]


def run_audit(services: List[str], processes: Optional[List[str]] = None) -> Dict[str, Any]:
    """Run an immediate one-shot health check of services and processes."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "services": {},
        "processes": {}
    }
    
    print(f"\n[*] Auditing {len(services)} Windows Services...")
    print(f"{'Service Name':<25} | {'State':<20} | {'PID':<10}")
    print("-" * 60)
    for svc in services:
        status = get_windows_service_status(svc)
        results["services"][svc] = status
        pid_str = str(status.get("pid") or "-")
        state_str = status.get("state", "UNKNOWN")
        print(f"{svc:<25} | {state_str:<20} | {pid_str:<10}")

    if processes:
        print(f"\n[*] Auditing {len(processes)} Target Processes...")
        print(f"{'Process Name':<25} | {'Instances':<10} | {'PIDs':<20}")
        print("-" * 60)
        for proc_name in processes:
            procs = get_process_status(proc_name)
            results["processes"][proc_name] = procs
            pids = ",".join(str(p["pid"]) for p in procs) if procs else "NONE"
            print(f"{proc_name:<25} | {len(procs):<10} | {pids:<20}")

    return results


def run_watchdog(services: List[str], interval: int = 5, auto_restart: bool = False,
                 log_path: Optional[str] = None):
    """Run continuous monitoring loop."""
    print(f"[*] Starting Service Watchdog (Interval: {interval}s, Auto-Restart: {auto_restart})")
    print(f"[*] Monitoring: {', '.join(services)}")
    print("[*] Press Ctrl+C to stop.")

    try:
        while True:
            for svc in services:
                st = get_windows_service_status(svc)
                state = st.get("state", "")
                if "RUNNING" not in state and state != "NOT_INSTALLED":
                    msg = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] WARNING: Service '{svc}' is in state: {state}"
                    print(msg)
                    if log_path:
                        with open(log_path, "a", encoding="utf-8") as f:
                            f.write(msg + "\n")
                    
                    if auto_restart:
                        print(f"[*] Auto-restart triggered for '{svc}'...")
                        ok = restart_windows_service(svc)
                        res_msg = f"[*] Service '{svc}' restart {'SUCCEEDED' if ok else 'FAILED'}"
                        print(res_msg)
                        if log_path:
                            with open(log_path, "a", encoding="utf-8") as f:
                                f.write(res_msg + "\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[*] Watchdog stopped by user.")


def main():
    parser = argparse.ArgumentParser(
        description="Windows Service & Process Watchdog - Auto-monitor and self-heal services."
    )
    parser.add_argument("action", choices=["audit", "watch", "list-defaults"],
                        help="Action: 'audit' (one-shot check), 'watch' (continuous monitor), 'list-defaults'")
    parser.add_argument("--services", "-s", nargs="+", default=None,
                        help="Service name(s) to check/watch. Defaults to critical Windows services.")
    parser.add_argument("--processes", "-p", nargs="+", default=None,
                        help="Process name(s) to check (e.g. 'chrome.exe', 'python.exe')")
    parser.add_argument("--interval", "-i", type=int, default=5,
                        help="Watch loop polling interval in seconds (default: 5)")
    parser.add_argument("--auto-restart", action="store_true",
                        help="Automatically attempt to restart stopped/crashed services")
    parser.add_argument("--log-file", type=str, default=None,
                        help="Path to write watchdog alert events")
    parser.add_argument("--json", action="store_true",
                        help="Output results as JSON")

    args = parser.parse_args()
    svcs = args.services or list_common_services()

    if args.action == "list-defaults":
        print("Default monitored services:")
        for s in list_common_services():
            print(f" - {s}")
        return

    if args.action == "audit":
        data = run_audit(svcs, args.processes)
        if args.json:
            print(json.dumps(data, indent=2))
    elif args.action == "watch":
        run_watchdog(svcs, interval=args.interval, auto_restart=args.auto_restart, log_path=args.log_file)


if __name__ == "__main__":
    main()
