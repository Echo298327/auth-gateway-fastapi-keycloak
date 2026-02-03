"""
Logging utility functions for formatted console output.
Used by all services for consistent startup/shutdown banners.
"""

from datetime import datetime
from typing import Optional

# ANSI color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

LINE = "─" * 45


def log_header(service_name: str, version: str) -> None:
    """
    Print the startup header banner (call at the very start).
    """
    header = f"""
{CYAN}{LINE}{RESET}
{CYAN}  ▪  {BOLD}{service_name.upper()}{RESET}
{DIM}     v{version}{RESET}
{CYAN}{LINE}{RESET}
"""
    print(header, flush=True)


def log_ready(
    service_name: str,
    environment: str,
    host: str,
    port: int,
    workers: int,
    db_name: Optional[str] = None
) -> None:
    """
    Print the ready confirmation (call after all initialization is complete).
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    url = f"http://{host}:{port}"
    
    env_color = GREEN if environment == "production" else YELLOW
    
    config_lines = [
        f"     Environment : {env_color}{environment}{RESET}",
        f"     Host        : {host}",
        f"     Port        : {port}",
        f"     Workers     : {workers}",
    ]
    
    if db_name:
        config_lines.append(f"     Database    : {db_name}")
    
    config_section = "\n".join(config_lines)
    
    ready_msg = f"""
{DIM}  ▸  Configuration{RESET}
{config_section}

{GREEN}  ✓  Service initialized{RESET}

{GREEN}{LINE}{RESET}
{GREEN}  ●  {BOLD}{service_name} is running{RESET}
     URL     : {url}
     Started : {timestamp}
{GREEN}{LINE}{RESET}
"""
    print(ready_msg, flush=True)


def log_shutdown(service_name: str) -> None:
    """Print a shutdown message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"\n{YELLOW}  ■  {service_name} shutting down...{RESET} {DIM}[{timestamp}]{RESET}\n", flush=True)
