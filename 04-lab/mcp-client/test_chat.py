"""Script tiện ích kiểm tra nhanh Weather Agent qua dòng lệnh."""

import subprocess
import sys

def main():
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Thời tiết ở Hà Nội hôm nay thế nào?"
    print(f"👤 Query: {query}\n")
    subprocess.run([sys.executable, "-m", "google.adk.cli", "run", "weather_agent", query])

if __name__ == "__main__":
    main()
