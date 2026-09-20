
import subprocess
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from monitor import (
    create_progress_bar,
    get_cpu_temperature,
    get_cpu_usage,
    get_disk_usage,
    get_gpu_usage,
    get_memory_usage,
    get_uptime,
)


# ============================================================
# CPU USAGE TESTS
# ============================================================

class TestGetCpuUsage(unittest.TestCase):

    def test_cpu_usage_at_zero_percent(self):
        previous = (1000, 600)
        current = (1200, 800)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 0.0)

    def test_cpu_usage_at_fifty_percent(self):
        previous = (1000, 600)
        current = (1200, 700)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 50.0)

    def test_cpu_usage_at_hundred_percent(self):
        previous = (1000, 600)
        current = (1200, 600)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 100.0)

    def test_cpu_usage_with_no_elapsed_time(self):
        previous = (1000, 600)
        current = (1000, 600)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 0.0)

    def test_cpu_usage_with_negative_elapsed_time(self):
        previous = (1200, 700)
        current = (1000, 600)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 0.0)

    def test_cpu_usage_rounds_to_two_decimal_places(self):
        previous = (1000, 600)
        current = (1300, 700)

        result = get_cpu_usage(previous, current)

        self.assertEqual(result, 66.67)


# ============================================================
# PROGRESS BAR TESTS
# ============================================================

class TestProgressBar(unittest.TestCase):

    def test_progress_bar_at_zero_percent(self):
        result = create_progress_bar(0)

        self.assertIn("[--------------------]", result)
        self.assertIn("0.00%", result)

    def test_progress_bar_at_fifty_percent(self):
        result = create_progress_bar(50)

        self.assertIn("[██████████----------]", result)
        self.assertIn("50.00%", result)

    def test_progress_bar_at_hundred_percent(self):
        result = create_progress_bar(100)

        self.assertIn("[████████████████████]", result)
        self.assertIn("100.00%", result)

    def test_progress_bar_uses_custom_width(self):
        result = create_progress_bar(50, width=10)

        self.assertIn("[█████-----]", result)

    def test_progress_bar_is_green_below_fifty_percent(self):
        result = create_progress_bar(49)

        self.assertTrue(
            result.startswith("\033[38;2;34;197;94m")
        )

    def test_progress_bar_is_yellow_at_fifty_percent(self):
        result = create_progress_bar(50)

        self.assertTrue(
            result.startswith("\033[38;2;234;179;8m")
        )

    def test_progress_bar_is_yellow_below_eighty_five_percent(self):
        result = create_progress_bar(84)

        self.assertTrue(
            result.startswith("\033[38;2;234;179;8m")
        )

    def test_progress_bar_is_red_at_eighty_five_percent(self):
        result = create_progress_bar(85)

        self.assertTrue(
            result.startswith("\033[38;2;239;68;68m")
        )

    def test_progress_bar_clamps_negative_percentage(self):
        result = create_progress_bar(-10)

        self.assertIn("[--------------------]", result)
        self.assertIn("0.00%", result)

    def test_progress_bar_clamps_percentage_above_hundred(self):
        result = create_progress_bar(150)

        self.assertIn("[████████████████████]", result)
        self.assertIn("100.00%", result)

    def test_progress_bar_resets_terminal_color(self):
        result = create_progress_bar(50)

        self.assertIn("\033[0m", result)
        self.assertTrue(result.endswith("50.00%"))


# ============================================================
# MEMORY TESTS
# ============================================================

class TestGetMemoryUsage(unittest.TestCase):

    @patch("builtins.open")
    def test_memory_usage_calculation(self, mock_open):
        mock_open.return_value.__enter__.return_value = iter(
            [
                "MemTotal:       1048576 kB\n",
                "MemFree:         131072 kB\n",
                "MemAvailable:    262144 kB\n",
            ]
        )

        usage, total_gib, available_gib = get_memory_usage()

        self.assertEqual(usage, 75.0)
        self.assertEqual(total_gib, 1.0)
        self.assertEqual(available_gib, 0.25)


# ============================================================
# DISK TESTS
# ============================================================

class TestGetDiskUsage(unittest.TestCase):

    @patch("monitor.shutil.disk_usage")
    def test_disk_usage_calculation(self, mock_disk_usage):
        gib = 1024 ** 3

        mock_disk_usage.return_value = MagicMock(
            total=100 * gib,
            used=25 * gib,
        )

        usage, total_gib, used_gib = get_disk_usage()

        mock_disk_usage.assert_called_once_with("/")

        self.assertEqual(usage, 25.0)
        self.assertEqual(total_gib, 100.0)
        self.assertEqual(used_gib, 25.0)


# ============================================================
# UPTIME TESTS
# ============================================================

class TestGetUptime(unittest.TestCase):

    @patch("builtins.open")
    def test_uptime_conversion(self, mock_open):
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "7380.00 12000.00\n"
        )

        hours, minutes = get_uptime()

        self.assertEqual(hours, 2)
        self.assertEqual(minutes, 3)


# ============================================================
# NVIDIA GPU TESTS
# ============================================================

class TestGetGpuUsage(unittest.TestCase):

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_four_metrics(self, mock_run):
        mock_run.return_value.stdout = "25, 45, 1024, 6144\n"

        result = get_gpu_usage()

        self.assertEqual(result, (25, 45, 1024, 6144))

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_for_empty_output(self, mock_run):
        mock_run.return_value.stdout = ""

        result = get_gpu_usage()

        self.assertIsNone(result)

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_for_missing_fields(self, mock_run):
        mock_run.return_value.stdout = "25, 45, 1024\n"

        result = get_gpu_usage()

        self.assertIsNone(result)

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_for_invalid_values(self, mock_run):
        mock_run.return_value.stdout = "25, N/A, 1024, 6144\n"

        result = get_gpu_usage()

        self.assertIsNone(result)

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_when_command_is_missing(self, mock_run):
        mock_run.side_effect = FileNotFoundError

        result = get_gpu_usage()

        self.assertIsNone(result)

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_when_command_fails(self, mock_run):
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="nvidia-smi",
        )

        result = get_gpu_usage()

        self.assertIsNone(result)

    @patch("monitor.subprocess.run")
    def test_gpu_usage_returns_none_on_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd="nvidia-smi",
            timeout=5,
        )

        result = get_gpu_usage()

        self.assertIsNone(result)


# ============================================================
# CPU TEMPERATURE TESTS
# ============================================================

class TestGetCpuTemperature(unittest.TestCase):

    @patch("monitor.Path")
    def test_cpu_temperature_reads_package_sensor(self, mock_path):
        mock_root = MagicMock()
        mock_device = MagicMock()
        mock_label_file = MagicMock()
        mock_temp_file = MagicMock()

        mock_path.return_value = mock_root
        mock_root.glob.return_value = [mock_device]

        mock_device.__truediv__.return_value.read_text.return_value = (
            "coretemp\n"
        )

        mock_device.glob.return_value = [mock_label_file]

        mock_label_file.read_text.return_value = "Package id 0\n"
        mock_label_file.name = "temp1_label"
        mock_label_file.with_name.return_value = mock_temp_file

        mock_temp_file.read_text.return_value = "37000\n"

        result = get_cpu_temperature()

        self.assertEqual(result, 37.0)

    @patch("monitor.Path")
    def test_cpu_temperature_returns_none_without_coretemp(self, mock_path):
        mock_root = MagicMock()
        mock_device = MagicMock()

        mock_path.return_value = mock_root
        mock_root.glob.return_value = [mock_device]

        mock_device.__truediv__.return_value.read_text.return_value = (
            "nvme\n"
        )

        result = get_cpu_temperature()

        self.assertIsNone(result)

    @patch("monitor.Path")
    def test_cpu_temperature_returns_none_without_package_sensor(
        self, mock_path
    ):
        mock_root = MagicMock()
        mock_device = MagicMock()
        mock_label_file = MagicMock()

        mock_path.return_value = mock_root
        mock_root.glob.return_value = [mock_device]

        mock_device.__truediv__.return_value.read_text.return_value = (
            "coretemp\n"
        )

        mock_device.glob.return_value = [mock_label_file]
        mock_label_file.read_text.return_value = "Core 0\n"

        result = get_cpu_temperature()

        self.assertIsNone(result)

    @patch("monitor.Path")
    def test_cpu_temperature_returns_none_for_invalid_reading(
        self, mock_path
    ):
        mock_root = MagicMock()
        mock_device = MagicMock()
        mock_label_file = MagicMock()
        mock_temp_file = MagicMock()

        mock_path.return_value = mock_root
        mock_root.glob.return_value = [mock_device]

        mock_device.__truediv__.return_value.read_text.return_value = (
            "coretemp\n"
        )

        mock_device.glob.return_value = [mock_label_file]

        mock_label_file.read_text.return_value = "Package id 0\n"
        mock_label_file.name = "temp1_label"
        mock_label_file.with_name.return_value = mock_temp_file

        mock_temp_file.read_text.return_value = "N/A\n"

        result = get_cpu_temperature()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()