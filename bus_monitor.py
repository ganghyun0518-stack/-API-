import requests  # HTTP 요청을 위한 라이브러리
import xml.etree.ElementTree as ET  # XML 파싱을 위한 라이브러리
import time  # 시간 지연 및 측정을 위한 라이브러리
import winsound  # 윈도우 시스템 사운드 출력용 라이브러리
import os  # 운영체제 관련 기능을 위한 라이브러리
from datetime import datetime  # 날짜 및 시간 처리를 위한 라이브러리

def find_busstop_id(station_name):
    """
    정류장 이름으로 정류소 ID를 검색하는 함수
    Args:
        station_name (str): 검색할 정류장 이름
    Returns:
        list: 검색된 정류장 정보 목록 (이름, ID, ARS번호, 다음 정류장)
    """
    url = 'http://api.gwangju.go.kr/xml/stationInfo'
    params = {
        'serviceKey': '광주광역시 BIS 정류소 정보 API 키'  
        # 광주광역시 BIS 정류소 정보 조회를 위한 인증 키
    }

    try:
        # API 호출 및 응답 처리
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        found_stations = []
        
        # XML 응답에서 정류장 정보 추출
        for station in root.findall('.//STATION'):
            busstop_name = station.findtext('BUSSTOP_NAME', '')
            if station_name.lower() in busstop_name.lower():  # 대소문자 구분 없이 검색
                found_stations.append({
                    'name': busstop_name,
                    'id': station.findtext('BUSSTOP_ID', ''),
                    'ars_id': station.findtext('ARS_ID', ''),
                    'next_stop': station.findtext('NEXT_BUSSTOP', '')
                })
        
        return found_stations

    except Exception as e:
        print(f"오류 발생: {e}")
        return []

def get_bus_info(busstop_id, station_name, target_line=None):
    """
    특정 정류장의 버스 도착 정보를 조회하는 함수
    Args:
        busstop_id (str): 정류소 ID
        station_name (str): 정류장 이름
        target_line (str, optional): 특정 노선번호 (기본값: None - 전체 노선 조회)
    """
    url = 'http://api.gwangju.go.kr/xml/arriveInfo'
    params = {
        'serviceKey': '광주광역시 BIS 도착정보 API 키',
        'BUSSTOP_ID': busstop_id
    }

    try:
        # API 호출 및 화면 초기화
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        os.system('cls')  # 콘솔 화면 지우기
        
        # 현재 시간 표시
        current_time = datetime.now().strftime('%H:%M:%S')
        print(f"\n[{current_time}] {station_name} 버스 도착 정보")
        if target_line:
            print(f"검색 노선: {target_line}")
        print("=" * 60)
        
        # 버스 도착 정보 처리
        buses = root.findall('.//ARRIVE')
        if not buses:
            print("\n현재 운행 중인 버스 정보가 없습니다.")
            return

        # 남은 시간순으로 정렬
        buses_sorted = sorted(buses, key=lambda x: int(x.findtext('REMAIN_MIN', '999')))
        
        found = False
        for bus in buses_sorted:
            line_name = bus.findtext('LINE_NAME')
            
            # 특정 노선만 필터링
            if target_line and target_line != line_name:
                continue
                
            found = True
            remain_min = int(bus.findtext('REMAIN_MIN'))
            remain_stop = bus.findtext('REMAIN_STOP')
            location = bus.findtext('BUSSTOP_NAME')
            
            # 5분 이내 도착 예정인 버스는 경고음과 함께 특별 표시
            if remain_min <= 5:
                print("\n🚍 곧 도착합니다!")
                print(f"┌{'─' * 50}")
                print(f"│ [노선] {line_name}")
                print(f"│ [현재위치] {location}")
                print(f"│ [도착예정] ⚠️ {remain_min}분 후 (남은 정류장: {remain_stop}개)")
                print(f"└{'─' * 50}")
                winsound.Beep(1000, 200)  # 경고음 출력 (1000Hz, 0.2초)
            else:
                print(f"\n┌{'─' * 50}")
                print(f"│ [노선] {line_name}")
                print(f"│ [현재위치] {location}")
                print(f"│ [도착예정] {remain_min}분 후 (남은 정류장: {remain_stop}개)")
                print(f"└{'─' * 50}")
        
        if target_line and not found:
            print(f"\n{target_line} 노선의 운행 정보가 없습니다.")
    
    except Exception as e:
        print(f"오류 발생: {e}")

def show_available_lines(busstop_id):
    """
    정류장에서 현재 운행 중인 버스 노선 목록을 조회하는 함수
    Args:
        busstop_id (str): 정류소 ID
    Returns:
        set: 운행 중인 노선 번호 집합
    """
    url = 'http://api.gwangju.go.kr/xml/arriveInfo'
    params = {
        'serviceKey': 'bf0564a6a8d378acf44a5a385236e6e39642cb379b69202f86e6c1db3df99887',
        'BUSSTOP_ID': busstop_id
    }
    
    try:
        # API 호출 및 노선 정보 추출
        response = requests.get(url, params=params)
        root = ET.fromstring(response.content)
        lines = set()  # 중복 제거를 위해 집합 사용
        
        for bus in root.findall('.//ARRIVE'):
            lines.add(bus.findtext('LINE_NAME'))
        
        # 운행 중인 노선 출력
        if lines:
            print("\n현재 운행 중인 노선:")
            for line in sorted(lines):
                print(f"- {line}")
        else:
            print("\n현재 운행 중인 버스가 없습니다.")
        
        return lines
    except Exception as e:
        print(f"오류 발생: {e}")
        return set()

def main():
    """
    메인 실행 함수
    - 사용자 입력을 받아 버스 도착 정보를 지속적으로 모니터링
    """
    os.system('cls')  # 프로그램 시작 시 콘솔 화면 지우기
    print("광주광역시 버스 도착 정보 모니터링 시스템")
    print("=" * 50)
    
    while True:
        # 정류장 이름 입력 받기
        station_name = input("\n정류장 이름을 입력하세요: ").strip()
        if not station_name:
            print("정류장 이름을 입력해주세요.")
            continue
            
        print("\n검색 중...")
        stations = find_busstop_id(station_name)
        
        # 검색 결과가 없는 경우
        if not stations:
            print(f"\n'{station_name}'에 대한 검색 결과가 없습니다.")
            continue
            
        # 검색된 정류장 목록 출력
        print(f"\n'{station_name}' 검색 결과:")
        print("-" * 50)
        for idx, station in enumerate(stations, 1):
            print(f"{idx}. 정류소명: {station['name']}")
            print(f"   정류소ID: {station['id']}")
            print(f"   다음 정류장: {station['next_stop']}")
            print("-" * 50)
            
        # 정류장 선택
        while True:
            try:
                select = int(input("\n정류장 번호를 선택하세요: "))
                if 1 <= select <= len(stations):
                    selected_station = stations[select-1]
                    break
                else:
                    print("올바른 번호를 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
        
        # 운행 중인 노선 조회
        available_lines = show_available_lines(selected_station['id'])
        
        # 모니터링할 노선 선택
        while True:
            target_line = input("\n모니터링할 노선을 입력하세요 (전체 보기: Enter): ").strip()
            if target_line and target_line not in available_lines:
                print("※ 입력하신 노선이 현재 운행 중이 아닙니다.")
                continue
            break
        
        # 실시간 모니터링 시작
        print(f"\n{selected_station['name']} 버스 도착 정보 모니터링을 시작합니다. (종료: Ctrl+C)")
        try:
            while True:
                get_bus_info(selected_station['id'], selected_station['name'], target_line)
                time.sleep(1)  # 1초 간격으로 업데이트
        except KeyboardInterrupt:
            # Ctrl+C로 모니터링 중단 시 처리
            retry = input("\n\n다른 정류장을 검색하시겠습니까? (Y/N): ").strip().lower()
            if retry != 'y':
                print("\n프로그램을 종료합니다.")
                break

if __name__ == "__main__":
    main()
