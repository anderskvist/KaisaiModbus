#!/usr/bin/env python3

# Inspiration: https://github.com/TheMiniatureGamer/Midea_Kaisai_modbus_sniffer/blob/main/heatpump-monitor.yaml
# Documentation: https://api.library.loxone.com/downloader/file/384/Modbus%20KHA_KMK,%20KHC%20v2.pdf

from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ModbusIOException
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from datetime import datetime, timezone
import time
import os
import json

# Modbus RTU client config
client = ModbusSerialClient(
    port='/dev/ttyAMA0',
    baudrate=9600,
    parity='N',
    stopbits=1,
    bytesize=8,
    timeout=1
)

def uint16_to_int16(x):
    return x - 0x10000 if x & 0x8000 else x

def get_reg(address, count=1, raw = False):
    result = client.read_holding_registers(
        address=address,
        count=count,
        slave=1
    )
    if result.isError():
        print("⚠️ Modbus error:", result)
    else:
        if raw:
            return result.registers
        else:
            return uint16_to_int16(result.registers[0])

def get_dword(address):
    registers = get_reg(address, count=2, raw=True)
    return client.convert_from_registers(registers, data_type=client.DATATYPE.INT32, word_order='big')

def print_reg(description, remark, address):
    print(f"{description} ({remark}): {uint16_to_int16(get_reg(address)[0])}")

def print_dword(description, remark, address):
    print(f"{description} ({remark}): {get_dword(address)}")

def print_bit(description, remark, address, bit):
    print(f"Defrost: {(get_reg(address)[0] & bit == bit)}")

def main():
    if not client.connect():
        print("❌ Unable to connect to Modbus device")
        return

    print("✅ Modbus connection established")

    timeserie = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "setting_water_temperature_t1s_zone1": get_reg(2) & 0xff,
        "setting_water_temperature_t1s_zone2": (get_reg(2) >> 8) & 0xff,
        "operating_frequency_hz": get_reg(100),
        "operating_mode": get_reg(101),
        "fan_speed_rpm": get_reg(102),
        "pmv_openness_p": round(get_reg(103)/4.8),
        "water_inlet_temp_c": get_reg(104),
        "water_outlet_temp_c": get_reg(105),
        "t3_condenser_temp_c": get_reg(106),
        "t4_ambient_temp_c": get_reg(107),
        "discharge_temp_c": get_reg(108),
        "return_air_temp_c": get_reg(109),
        "t1_total_water_outlet_c": get_reg(110),
        "t1b_water_outlet_after_heater_c": get_reg(111),
        "t2_refrigerant_liquid_c": get_reg(112),
        "t2b_refrigerant_gas_c": get_reg(113),
        "ta_room_temp_c": get_reg(114),
        "t5_water_tank_temp_c": get_reg(115),
        "pressure1_high_kpa": get_reg(116),
        "pressure2_low_kpa": get_reg(117),
        "outdoor_unit_current_a": get_reg(118),
        "outdoor_unit_voltage_v": get_reg(119),
        "compressor_operation_time_h": get_reg(122),
        "unit_capacity_kw": get_reg(123),
        "current_fault": get_reg(124),
        "fault_1": get_reg(125),
        "fault_2": get_reg(126),
        "fault_3": get_reg(127),
        "status_defrost": (get_reg(128) & 0x02 == 0x02),
        "unit_target_frequency_hz": get_reg(132),
        "dc_bus_current_a": get_reg(133),
        "dc_bus_voltage_v": get_reg(134),
        "tf_module_temp_c": get_reg(135),
        "climate_curve_t1s_calculated_value_1": get_reg(136),
        "climate_curve_t1s_calculated_value_2": get_reg(137),
        "water_flow_m3h": get_reg(138)/100,
        "limit_scheme_of_outdoor_unit_current": get_reg(139),
        "hydraulic_module_ability_kw": get_reg(140)/100,
        "electricity_consumption_kwh": get_dword(143),
        "power_output_kwh": get_dword(145)
    }

    data =  {
        "device": "KAISAI KHC-08RY3-B",
        "data_interval_minutes": 1,
        "unit": "kW",
        "timeseries": [
            timeserie
        ],
        "metadata": {
            "description": "",
            "location": "",
            "system_status": "",
            "total_duration_minutes": 60
        }
    }

    print(json.dumps(data, indent=2))

    with open('/dev/shm/kaisai.json', 'w') as f:
        json.dump(data, f)

if __name__ == "__main__":
    main()

