
import shutil
import subprocess
import time


# ============================================================
# SYSTEM METRICS
# ============================================================

def read_cpu_counters():
    """Read cumulative CPU time counters from Linux."""

    with open("/proc/stat") as file:
        values = file.readline().split()[1:9]

    values = [int(value) for value in values]

    total = sum(values)

    # Treat idle and I/O wait as idle time.
    idle = values[3] + values[4]

    return total, idle


def get_cpu_usage(previous, current):
    """Calculate CPU usage between two measurements."""

    previous_total, previous_idle = previous
    current_total, current_idle = current

    delta_total = current_total - previous_total
    delta_idle = current_idle - previous_idle

    if delta_total <= 0:
        return 0.0

    usage = (1 - delta_idle / delta_total) * 100

    return round(usage, 2)


def get_memory_usage():
    """Read total and available system memory."""

    memory = {}

    with open("/proc/meminfo") as file:
        for line in file:
            if line.startswith(("MemTotal:", "MemAvailable:")):
                key, value, *_ = line.split()
                memory[key.rstrip(":")] = int(value)

    # /proc/meminfo reports memory in KiB.
    total_kib = memory["MemTotal"]
    available_kib = memory["MemAvailable"]

    usage = (total_kib - available_kib) / total_kib * 100

    total_gib = total_kib / (1024 ** 2)
    available_gib = available_kib / (1024 ** 2)

    return round(usage, 2), total_gib, available_gib


def get_disk_usage():
    """Read usage of the filesystem containing /."""

    storage = shutil.disk_usage("/")

    usage = storage.used / storage.total * 100

    total_gib = storage.total / (1024 ** 3)
    used_gib = storage.used / (1024 ** 3)

    return round(usage, 2), total_gib, used_gib


def get_uptime():
    """Read system uptime and convert it to hours and minutes."""

    with open("/proc/uptime") as file:
        seconds = float(file.read().split()[0])

    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)

    return hours, minutes


def get_gpu_usage():
    """Read NVIDIA GPU utilization, temperature, and VRAM usage."""

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total",
                "--format=csv,noheader,nounits",
                "--id=0",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )

        output = result.stdout.strip()

        if not output:
            return None

        values = output.split(",")

        if len(values) != 4:
            return None

        gpu_usage, gpu_temp, memory_used, memory_total = (
            int(value.strip()) for value in values
        )

        return gpu_usage, gpu_temp, memory_used, memory_total

    except (
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        FileNotFoundError,
        ValueError,
    ):
        return None


# ============================================================
# TERMINAL INTERFACE
# ============================================================

def create_progress_bar(percentage, width=20):
    """Create a colored progress bar for a given percentage."""

    percentage = max(0, min(100, percentage))

    filled_length = int(width * percentage / 100)

    bar = "█" * filled_length + "-" * (width - filled_length)

    if percentage >= 85:
        color = "\033[38;2;239;68;68m"  # Red
    elif percentage >= 50:
        color = "\033[38;2;234;179;8m"  # Yellow
    else:
        color = "\033[38;2;34;197;94m"  # Green

    reset = "\033[0m"

    return f"{color}[{bar}]{reset} {percentage:.2f}%"

def display_monitor(cpu, memory, disk, uptime, gpu):
    """Render the system monitor in the terminal."""

    memory_usage, memory_total, memory_available = memory

    disk_usage, disk_total, disk_used = disk

    uptime_hours, uptime_minutes = uptime

    label_width = 20
    panel_width = 55

    # Clear the terminal and move the cursor to the top-left corner.
    print("\033[H\033[J", end="", flush=True)

    print("=" * panel_width)
    print("LINUX SYSTEM MONITOR")
    print("=" * panel_width)

    # CPU
    print(
        f"{'CPU:':<{label_width}}"
        f"{create_progress_bar(cpu)}"
    )

    # RAM
    print(
        f"{'RAM:':<{label_width}}"
        f"{create_progress_bar(memory_usage)}"
    )

    # DISK
    print(
        f"{'DISK:':<{label_width}}"
        f"{create_progress_bar(disk_usage)}"
    )

    print(
        f"{'UPTIME:':<{label_width}}"
        f"{uptime_hours}h {uptime_minutes:02d}m"
    )

    print("-" * panel_width)

    # NVIDIA GPU
    if gpu is not None:
        gpu_usage, gpu_temp, vram_used, vram_total = gpu

        vram_usage = (
            vram_used / vram_total * 100
            if vram_total > 0
            else 0.0
        )

        print(
            f"{'GPU:':<{label_width}}"
            f"{create_progress_bar(gpu_usage)}"
        )

        print(
            f"{'GPU TEMP:':<{label_width}}"
            f"{gpu_temp}°C"
        )

        print(
            f"{'VRAM:':<{label_width}}"
            f"{create_progress_bar(vram_usage)}"
        )

        print(
            f"{'VRAM USAGE:':<{label_width}}"
            f"{vram_used / 1024:.2f} / "
            f"{vram_total / 1024:.2f} GiB"
        )

    else:
        print(f"{'GPU:':<{label_width}}N/A")
        print(f"{'GPU TEMP:':<{label_width}}N/A")
        print(f"{'VRAM:':<{label_width}}N/A")
        print(f"{'VRAM USAGE:':<{label_width}}N/A")

    print("-" * panel_width)

    # Detailed system information
    print(
        f"{'Memory Total:':<{label_width}}"
        f"{memory_total:.2f} GiB"
    )

    print(
        f"{'Memory Available:':<{label_width}}"
        f"{memory_available:.2f} GiB"
    )

    print(
        f"{'Disk Total:':<{label_width}}"
        f"{disk_total:.2f} GiB"
    )

    print(
        f"{'Disk Used:':<{label_width}}"
        f"{disk_used:.2f} GiB"
    )

    print("=" * panel_width)
    print("Press Ctrl+C to exit")
    print("=" * panel_width, flush=True)


# ============================================================
# APPLICATION ENTRY POINT
# ============================================================

def main():
    """Continuously collect and display system metrics."""

    previous_cpu = read_cpu_counters()

    try:
        while True:
            time.sleep(1)

            current_cpu = read_cpu_counters()

            cpu = get_cpu_usage(previous_cpu, current_cpu)

            previous_cpu = current_cpu

            memory = get_memory_usage()
            disk = get_disk_usage()
            uptime = get_uptime()
            gpu = get_gpu_usage()

            display_monitor(
                cpu,
                memory,
                disk,
                uptime,
                gpu,
            )

    except KeyboardInterrupt:
        print("\nSystem monitor stopped.")


if __name__ == "__main__":
    main()