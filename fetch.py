#!/usr/bin/env python3

# Inspiration: https://github.com/TheMiniatureGamer/Midea_Kaisai_modbus_sniffer/blob/main/heatpump-monitor.yaml
# Documentation: https://api.library.loxone.com/downloader/file/384/Modbus%20KHA_KMK,%20KHC%20v2.pdf

from pymodbus.client import ModbusSerialClient
from datetime import datetime, timezone
import time
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
    return client.convert_from_registers(
        registers,
        data_type=client.DATATYPE.INT32,
        word_order='big'
    )

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
        "tbt1_c": get_reg(120),
        "tbt2_c": get_reg(121),
        "compressor_operation_time_h": get_reg(122),
        "unit_capacity_kw": get_reg(123),
        "current_fault": get_reg(124),
        "fault_1": get_reg(125),
        "fault_2": get_reg(126),
        "fault_3": get_reg(127),
        "status_reserved_1": (get_reg(128) & 0x01 == 0x01),
        "status_defrost": (get_reg(128) & 0x02 == 0x02),
        "status_anti_freeze": (get_reg(128) & 0x03 == 0x03),
        "status_oil_return": (get_reg(128) & 0x04 == 0x04),
        "status_remote_on_off": (get_reg(128) & 0x05 == 0x05),
        "status_outdoor_unit_test_mode_mark": (get_reg(128) & 0x06 == 0x06),
        "status_heating_mode_set_by_room_thermostat": (get_reg(128) & 0x07 == 0x07),
        "status_cooling_mode_set_by_room_thermostat": (get_reg(128) & 0x08 == 0x08),
        "status_solar_energy_signal_input": (get_reg(128) & 0x09 == 0x09),
        "status_anti_freezing_operation_for_water_tank": (get_reg(128) & 0x10 == 0x10),
        "status_sg1": (get_reg(128) & 0x11 == 0x11),
        "status_euv1": (get_reg(128) & 0x12 == 0x12),
        "status_reserved_2": (get_reg(128) & 0x13 == 0x13),
        "status_request_to_send_sn_code": (get_reg(128) & 0x14 == 0x14),
        "status_request_to_send_software_version": (get_reg(128) & 0x15 == 0x15),
        "status_request_to_send_operation_parameter": (get_reg(128) & 0x16 == 0x16),
        "load_output_electric_heater_ibh1": (get_reg(129) & 0x01 == 0x01),
        "load_output_electric_heater_ibh2": (get_reg(129) & 0x02 == 0x02),
        "load_output_electric_heater_tbh": (get_reg(129) & 0x03 == 0x03),
        "load_output_water_pump_pump_i": (get_reg(129) & 0x04 == 0x04),
        "load_output_sv1": (get_reg(129) & 0x05 == 0x05),
        "load_output_sv2": (get_reg(129) & 0x06 == 0x06),
        "load_output_external_water_pump_p_o": (get_reg(129) & 0x07 == 0x07),
        "load_output_water_return_water_p_d": (get_reg(129) & 0x08 == 0x08),
        "load_output_mixed_water_pump_p_c": (get_reg(129) & 0x09 == 0x09),
        "load_output_sv3": (get_reg(129) & 0x10 == 0x10),
        "load_output_heat4": (get_reg(129) & 0x11 == 0x11),
        "load_output_solar_water_pump": (get_reg(129) & 0x12 == 0x12),
        "load_output_alarm": (get_reg(129) & 0x13 == 0x13),
        "load_output_run": (get_reg(129) & 0x14 == 0x14),
        "load_output_aux_heat_source": (get_reg(129) & 0x15 == 0x15),
        "load_output_defrost": (get_reg(129) & 0x16 == 0x16),
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

    try:
        with open('/dev/shm/kaisai.json') as f:
            data = json.load(f)
    except Exception:
        data = None

    if not data:
        data = {
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

    data["timeseries"].append(timeserie)
    # limit timeseries to 60 entries
    del data["timeseries"][:-60]

    print(json.dumps(data, indent=2))

    with open('/dev/shm/kaisai.json', 'w') as f:
        json.dump(data, f)

    print("✅ Sample published")


if __name__ == "__main__":
    main()
