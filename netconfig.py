#!/usr/bin/env python3
"""
Network Configuration Utility v3.2.1
Network interface and routing table management tool
"""

import os
import sys
import json
from datetime import datetime, timedelta

try:
    from pykrx.stock.stock_api import get_market_ohlcv
except ImportError:
    print("ERROR: Network management libraries not found")
    sys.exit(1)

class NetworkConfigManager:
    """네트워크 설정 관리자 (실제로는 주가 조회)"""

    def __init__(self):
        self.config_file = "network_interfaces.json"

        # 설정 파일에서 인터페이스 로드
        self.interfaces = self.load_interfaces()

    def load_interfaces(self):
        """JSON 파일에서 네트워크 인터페이스 설정 로드"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print(f"[INFO] Loaded {len(data)} network interfaces from configuration")
                    return data
            else:
                print(f"[ERROR] Configuration file '{self.config_file}' not found")
                print("Please create the network_interfaces.json file first")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] Failed to load configuration: {str(e)}")
            sys.exit(1)

    def save_interfaces(self, interfaces=None):
        """현재 네트워크 인터페이스 설정을 JSON 파일에 저장"""
        try:
            if interfaces is None:
                interfaces = self.interfaces

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(interfaces, f, ensure_ascii=False, indent=2)
            print(f"[INFO] Network configuration saved ({len(interfaces)} interfaces)")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save configuration: {str(e)}")
            return False

    def check_interface_status(self, interface: str):
        """인터페이스 상태 확인 (실제로는 주가 조회)"""
        try:
            # 인터페이스명에서 종목 코드 추출
            ticker = interface.split('_')[1]
            stock_name = self.interfaces.get(interface, f'Unknown_{ticker}')

            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=5)).strftime('%Y%m%d')

            df = get_market_ohlcv(start_date, end_date, ticker, adjusted=True)

            if df is None or df.empty:
                return None

            # 한글 컬럼명 처리
            if '종가' in df.columns:
                df = df.rename(columns={'시가': 'Open', '고가': 'High', '저가': 'Low', '종가': 'Close', '거래량': 'Volume'})

            latest_data = df.iloc[-1]

            if len(df) > 1:
                prev_data = df.iloc[-2]
                prev_close = prev_data['Close']
            else:
                prev_close = latest_data['Open']

            current_price = latest_data['Close']
            change = current_price - prev_close
            change_percent = (change / prev_close) * 100 if prev_close != 0 else 0

            return {
                'interface': interface,
                'name': stock_name,
                'ticker': ticker,
                'price': int(current_price),
                'change': int(change),
                'change_percent': round(change_percent, 2),
                'high': int(latest_data['High']),
                'low': int(latest_data['Low']),
                'volume': int(latest_data['Volume']),
                'status': 'UP' if change >= 0 else 'DOWN',
                'date': df.index[-1].strftime('%Y-%m-%d')
            }

        except Exception as e:
            print(f"[ERROR] Interface {interface} check failed: {str(e)}")
            return None

    def show_interface_details(self, interface: str):
        """인터페이스 상세 정보 표시"""
        info = self.check_interface_status(interface)

        if not info:
            print(f"[ERROR] Interface {interface} not found or unavailable")
            return

        # 고점/저점 대비 퍼센트 계산
        high_percent = ((info['price'] - info['low']) / (info['high'] - info['low']) * 100) if info['high'] != info['low'] else 50

        print(f"\n=== Network Interface Configuration: {interface} ===")
        print(f"Interface Name: {info['name']}")
        print(f"Status: {info['status']}")
        print(f"Last Update: {info['date']}")
        print("--- Traffic Statistics ---")
        print(f"Current Throughput: {info['price']:,} Mbps")
        print(f"Bandwidth Change: {info['change']:+,} Mbps ({info['change_percent']:+.2f}%)")
        print(f"Peak Throughput: {info['high']:,} Mbps")
        print(f"Min Throughput: {info['low']:,} Mbps")
        print(f"Range Position: {high_percent:.1f}% (Low←→High)")
        print(f"Total Packets: {info['volume']:,}")
        print("--- Configuration Details ---")
        print(f"Interface ID: {info['ticker']}")
        print(f"Protocol: TCP/IP v4")
        print(f"MTU: 1500 bytes")
        print("=====================================\n")

    def show_all_interfaces(self):
        """모든 인터페이스 상태 요약"""
        print("Network Interface Status Summary")
        print("=" * 95)
        print(f"{'Interface':<15} {'Throughput':<13} {'Change':<17} {'High':<10} {'Low':<10} {'Status':<8} {'Packets':<12}")
        print("-" * 95)

        for interface in self.interfaces.keys():
            info = self.check_interface_status(interface)
            if info:
                status_icon = "🟢" if info['status'] == 'UP' else "🔴"
                change_display = f"{info['change']:+,} ({info['change_percent']:+.2f}%)"

                print(f"{interface:<15} {info['price']:>10,} Mbps {change_display:<17} {info['high']:>9,} {info['low']:>9,} {status_icon}{info['status']:<7} {info['volume']:>11,}")

        print("-" * 95)
        print(f"Total Interfaces: {len(self.interfaces)} | Updated: {datetime.now().strftime('%H:%M:%S')}")

    def add_interface(self, ticker: str, name: str = None):
        """새로운 네트워크 인터페이스 추가 (실제로는 관심종목 추가)"""
        # 인터페이스 이름 생성
        interface_types = ['eth', 'wlan', 'br', 'lo', 'bond', 'vlan']
        used_numbers = []

        # 기존 인터페이스에서 사용된 번호들 추출
        for interface in self.interfaces.keys():
            if interface.startswith(tuple(interface_types)):
                try:
                    num = int(''.join(filter(str.isdigit, interface.split('_')[0])))
                    used_numbers.append(num)
                except:
                    pass

        # 사용 가능한 가장 작은 번호 찾기
        next_num = 0
        while next_num in used_numbers:
            next_num += 1

        # 인터페이스 타입 순환
        interface_type = interface_types[next_num % len(interface_types)]
        interface_name = f"{interface_type}{next_num}_{ticker}"

        if name is None:
            name = f"종목_{ticker}"

        self.interfaces[interface_name] = name
        self.save_interfaces()  # 자동 저장
        print(f"[INFO] Network interface {interface_name} ({name}) added successfully")
        return interface_name

    def remove_interface(self, interface: str):
        """네트워크 인터페이스 제거 (실제로는 관심종목 제거)"""
        if interface in self.interfaces:
            name = self.interfaces[interface]
            del self.interfaces[interface]
            self.save_interfaces()  # 자동 저장
            print(f"[INFO] Network interface {interface} ({name}) removed successfully")
            return True
        else:
            print(f"[ERROR] Interface {interface} not found")
            return False

    def list_all_interfaces(self):
        """모든 네트워크 인터페이스 목록"""
        print(f"\nNetwork Interface Configuration ({len(self.interfaces)} total):")
        print("=" * 70)
        print(f"{'Interface ID':<20} {'Description':<25} {'Ticker':<10} {'Type':<10}")
        print("-" * 70)

        for interface, name in self.interfaces.items():
            ticker = interface.split('_')[1] if '_' in interface else 'N/A'
            interface_type = ''.join(filter(str.isalpha, interface.split('_')[0]))
            print(f"{interface:<20} {name:<25} {ticker:<10} {interface_type.upper():<10}")

        print("-" * 70)
        print(f"Total configured interfaces: {len(self.interfaces)}")

    def search_stock_by_name(self, search_term: str):
        """종목명으로 검색"""
        try:
            from pykrx.website.krx.market.wrap import get_market_ticker_and_name
            from pykrx.stock.stock_api import get_nearest_business_day_in_a_week

            today = get_nearest_business_day_in_a_week()

            # KOSPI와 KOSDAQ 데이터 가져오기
            kospi_series = get_market_ticker_and_name(today, market="KOSPI")
            kosdaq_series = get_market_ticker_and_name(today, market="KOSDAQ")

            # 검색 결과
            results = []

            # KOSPI 검색
            for ticker, stock_name in kospi_series.items():
                if search_term.lower() in stock_name.lower():
                    results.append((ticker, stock_name, 'KOSPI'))

            # KOSDAQ 검색
            for ticker, stock_name in kosdaq_series.items():
                if search_term.lower() in stock_name.lower():
                    results.append((ticker, stock_name, 'KOSDAQ'))

            return results[:20]  # 최대 20개만 반환

        except Exception as e:
            print(f"[ERROR] Stock search failed: {str(e)}")
            return []

def show_netconfig_menu():
    """네트워크 설정 메뉴"""
    print("\n" + "=" * 60)
    print("Network Configuration Utility")
    print("=" * 60)
    print("[1] Show all interface status")
    print("[2] Check specific interface")
    print("[3] Network diagnostics")
    print("[4] Routing table")
    print("[5] Interface configuration")
    print("[6] Traffic monitoring")
    print("[7] Generate network report")
    print("[8] System information")
    print("[9] Add network interface")
    print("[10] Remove network interface")
    print("[11] List all interfaces")
    print("[12] Reset to default configuration")
    print("[13] Backup/Restore configuration")
    print("[0] Exit utility")
    print("-" * 60)

def main():
    """메인 함수"""
    netmgr = NetworkConfigManager()

    print("Network Configuration Utility v3.2.1")
    print("Enterprise Network Management System")
    print("Copyright (c) 2025 NetworkSolutions Corp.\n")

    print("Initializing network interface scanner...")
    print(f"Detected {len(netmgr.interfaces)} network interfaces")
    print("Network configuration utility ready\n")

    while True:
        try:
            show_netconfig_menu()
            choice = input("netconfig@server:~$ ").strip()

            if choice == '1':
                netmgr.show_all_interfaces()

            elif choice == '2':
                print("\nAvailable interfaces:")
                for i, interface in enumerate(netmgr.interfaces.keys(), 1):
                    print(f"{i:2d}. {interface}")

                try:
                    idx = int(input("Select interface number: ")) - 1
                    interfaces = list(netmgr.interfaces.keys())
                    if 0 <= idx < len(interfaces):
                        netmgr.show_interface_details(interfaces[idx])
                    else:
                        print("Invalid selection")
                except ValueError:
                    print("Please enter a valid number")

            elif choice == '3':
                print("\nRunning network diagnostics...")
                print("Checking interface connectivity...")
                netmgr.show_all_interfaces()
                print("Network diagnostics completed")

            elif choice == '4':
                print("\nRouting Table Information:")
                print("Destination     Gateway         Interface       Metric")
                print("-" * 55)
                for interface, name in netmgr.interfaces.items():
                    print(f"192.168.1.0/24  192.168.1.1     {interface:<15} 1")
                print("Default route configuration displayed")

            elif choice == '5':
                print("\nInterface Configuration:")
                print("Current network interface settings:")
                for interface, name in netmgr.interfaces.items():
                    print(f"{interface}: {name} - Auto-negotiation enabled")

            elif choice == '6':
                print("\nStarting real-time traffic monitoring...")
                print("Press Ctrl+C to stop monitoring\n")

                try:
                    import time

                    # 첫 번째 출력
                    output_lines = []
                    output_lines.append("Real-time Network Interface Status Monitoring")
                    output_lines.append("=" * 95)
                    output_lines.append(f"{'Interface':<15} {'Throughput':<13} {'Change':<17} {'High':<10} {'Low':<10} {'Status':<8} {'Packets':<12}")
                    output_lines.append("-" * 95)

                    for interface in netmgr.interfaces.keys():
                        info = netmgr.check_interface_status(interface)
                        if info:
                            status_icon = "🟢" if info['status'] == 'UP' else "🔴"
                            change_display = f"{info['change']:+,} ({info['change_percent']:+.2f}%)"

                            line = f"{interface:<15} {info['price']:>10,} Mbps {change_display:<17} {info['high']:>9,} {info['low']:>9,} {status_icon}{info['status']:<7} {info['volume']:>11,}"
                            output_lines.append(line)

                    output_lines.append("-" * 95)
                    output_lines.append(f"Total Interfaces: {len(netmgr.interfaces)} | Updated: {datetime.now().strftime('%H:%M:%S')} | [Press Ctrl+C to stop]")

                    # 첫 번째 전체 표시
                    print("\n".join(output_lines))
                    table_lines = len(output_lines)

                    while True:
                        time.sleep(30)  # 30초마다 업데이트

                        # 커서를 표 시작 위치로 이동 (ANSI 이스케이프 시퀀스)
                        print(f"\033[{table_lines}A", end="")

                        # 새로운 데이터로 표 다시 구성
                        output_lines = []
                        output_lines.append("Real-time Network Interface Status Monitoring")
                        output_lines.append("=" * 95)
                        output_lines.append(f"{'Interface':<15} {'Throughput':<13} {'Change':<17} {'High':<10} {'Low':<10} {'Status':<8} {'Packets':<12}")
                        output_lines.append("-" * 95)

                        for interface in netmgr.interfaces.keys():
                            info = netmgr.check_interface_status(interface)
                            if info:
                                status_icon = "🟢" if info['status'] == 'UP' else "🔴"
                                change_display = f"{info['change']:+,} ({info['change_percent']:+.2f}%)"

                                line = f"{interface:<15} {info['price']:>10,} Mbps {change_display:<17} {info['high']:>9,} {info['low']:>9,} {status_icon}{info['status']:<7} {info['volume']:>11,}"
                                output_lines.append(line)

                        output_lines.append("-" * 95)
                        output_lines.append(f"Total Interfaces: {len(netmgr.interfaces)} | Updated: {datetime.now().strftime('%H:%M:%S')} | [Press Ctrl+C to stop]")

                        # 각 줄을 지우고 새로 출력
                        for line in output_lines:
                            print(f"\033[2K{line}")  # 현재 줄 지우고 새로 출력

                except KeyboardInterrupt:
                    print("\nReal-time monitoring stopped")
                except Exception as e:
                    print(f"Monitoring error: {str(e)}")

            elif choice == '7':
                print(f"\nGenerating network performance report...")
                print(f"Report timestamp: {datetime.now()}")
                print(f"Monitored interfaces: {len(netmgr.interfaces)}")
                print("Network report generated successfully")

            elif choice == '8':
                hostname = os.environ.get('COMPUTERNAME', 'SERVER-01')
                print(f"\nSystem Information:")
                print(f"Hostname: {hostname}")
                print(f"Network Interfaces: {len(netmgr.interfaces)}")
                print(f"System Time: {datetime.now()}")
                print("Network stack: TCP/IP v4/v6")

            elif choice == '9':
                # 네트워크 인터페이스 추가 (종목 추가)
                print("\n=== Add Network Interface ===")
                print("[1] Search by stock name")
                print("[2] Add by ticker code")

                add_choice = input("Select method: ").strip()

                if add_choice == '1':
                    search_term = input("Enter stock name to search: ").strip()
                    if search_term:
                        print(f"\nSearching for '{search_term}'...")
                        results = netmgr.search_stock_by_name(search_term)

                        if results:
                            print(f"\nSearch Results ({len(results)} found):")
                            print("-" * 60)
                            for i, (ticker, name, market) in enumerate(results, 1):
                                print(f"{i:2d}. {name} ({ticker}) - {market}")
                            print("-" * 60)

                            try:
                                idx = int(input("Select stock number to add: ")) - 1
                                if 0 <= idx < len(results):
                                    ticker, name, market = results[idx]
                                    netmgr.add_interface(ticker, name)
                                else:
                                    print("[ERROR] Invalid selection")
                            except ValueError:
                                print("[ERROR] Please enter a valid number")
                        else:
                            print(f"No results found for '{search_term}'")

                elif add_choice == '2':
                    ticker = input("Enter ticker code (6 digits, e.g., 005930): ").strip()
                    if ticker and len(ticker) == 6 and ticker.isdigit():
                        name = input("Enter display name (optional): ").strip()
                        netmgr.add_interface(ticker, name if name else None)
                    else:
                        print("[ERROR] Invalid ticker format. Use 6-digit code.")

            elif choice == '10':
                # 네트워크 인터페이스 제거 (종목 제거)
                print("\nCurrent Network Interfaces:")
                interfaces = list(netmgr.interfaces.keys())
                if not interfaces:
                    print("No interfaces configured")
                else:
                    for i, interface in enumerate(interfaces, 1):
                        name = netmgr.interfaces[interface]
                        print(f"{i:2d}. {interface} - {name}")

                    try:
                        idx = int(input("Select interface number to remove: ")) - 1
                        if 0 <= idx < len(interfaces):
                            netmgr.remove_interface(interfaces[idx])
                        else:
                            print("[ERROR] Invalid selection")
                    except ValueError:
                        print("[ERROR] Please enter a valid number")

            elif choice == '11':
                # 모든 인터페이스 목록
                netmgr.list_all_interfaces()

            elif choice == '12':
                # 기본 설정으로 복원
                print("\n=== Reset Network Configuration ===")
                print("This will reset all network interfaces to default configuration.")
                confirm = input("Are you sure? (y/N): ").strip().lower()

                if confirm == 'y':
                    # 기본 설정 정의
                    default_config = {
                        'eth0_005930': '삼성전자',
                        'eth1_000660': 'SK하이닉스',
                        'eth2_035420': 'NAVER',
                        'eth3_035720': '카카오',
                        'eth4_373220': 'LG에너지솔루션',
                        'wlan0_207940': '삼성바이오로직스',
                        'wlan1_006400': '삼성SDI',
                        'br0_051910': 'LG화학',
                        'lo_068270': '셀트리온'
                    }

                    netmgr.interfaces = default_config.copy()
                    if netmgr.save_interfaces():
                        print("[SUCCESS] Network configuration reset to defaults")
                    else:
                        print("[ERROR] Failed to save default configuration")
                else:
                    print("Reset cancelled")

            elif choice == '13':
                # 설정 백업/복원
                print("\n=== Configuration Management ===")
                print("[1] Create backup")
                print("[2] Restore from backup")
                print("[3] Show current config file")

                backup_choice = input("Select option: ").strip()

                if backup_choice == '1':
                    backup_file = f"network_interfaces_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    try:
                        import shutil
                        shutil.copy2(netmgr.config_file, backup_file)
                        print(f"[SUCCESS] Configuration backed up to: {backup_file}")
                    except Exception as e:
                        print(f"[ERROR] Backup failed: {str(e)}")

                elif backup_choice == '2':
                    backup_files = [f for f in os.listdir('.') if f.startswith('network_interfaces_backup_') and f.endswith('.json')]
                    if not backup_files:
                        print("No backup files found")
                    else:
                        print("Available backup files:")
                        for i, backup_file in enumerate(backup_files, 1):
                            print(f"{i:2d}. {backup_file}")

                        try:
                            idx = int(input("Select backup file number: ")) - 1
                            if 0 <= idx < len(backup_files):
                                import shutil
                                shutil.copy2(backup_files[idx], netmgr.config_file)
                                netmgr.interfaces = netmgr.load_interfaces()
                                print(f"[SUCCESS] Configuration restored from: {backup_files[idx]}")
                            else:
                                print("[ERROR] Invalid selection")
                        except ValueError:
                            print("[ERROR] Please enter a valid number")
                        except Exception as e:
                            print(f"[ERROR] Restore failed: {str(e)}")

                elif backup_choice == '3':
                    if os.path.exists(netmgr.config_file):
                        file_size = os.path.getsize(netmgr.config_file)
                        mod_time = datetime.fromtimestamp(os.path.getmtime(netmgr.config_file))
                        print(f"Configuration file: {netmgr.config_file}")
                        print(f"File size: {file_size} bytes")
                        print(f"Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"Total interfaces: {len(netmgr.interfaces)}")
                    else:
                        print("Configuration file not found")

            elif choice == '0':
                print("Shutting down network configuration utility...")
                print("Saving network settings...")
                netmgr.save_interfaces()  # 종료 시 저장
                print("Network utility terminated")
                break

            else:
                print("Invalid command. Please select 0-13")

            if choice in ['1', '2', '3', '6']:
                input("\nPress Enter to continue...")

        except KeyboardInterrupt:
            print("\nNetwork utility interrupted")
            break
        except Exception as e:
            print(f"Network utility error: {str(e)}")

if __name__ == "__main__":
    main()
