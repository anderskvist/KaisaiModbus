#!/usr/bin/env python3

from flask import Flask, jsonify, render_template
import json
import os
import sys
import time
import math
import random

app = Flask(__name__)

DATA_FILE = "/dev/shm/kaisai.json"
TEST_MODE = "--test" in sys.argv


def generate_test_data():
    """Generate synthetic oscillating data for testing without fetch.py."""
    now = time.time()
    points = []
    modes = [0, 2, 3, 3, 3, 3, 3, 3]  # mostly heating
    for i in range(30):
        t = now - (29 - i) * 600  # 10-min intervals
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))
        phase = i * 0.3
        freq = 43 + 3 * math.sin(phase)
        t4 = -2 + 1.5 * math.sin(phase * 0.5)
        tw_in = 30 + 2 * math.sin(phase)
        tw_out = tw_in + 5 + 0.5 * math.sin(phase * 0.7)
        current = 4.0 + 0.5 * math.sin(phase)
        voltage = 224 + 3 * math.sin(phase * 0.3)
        defrost = (i % 15 == 0)  # defrost every 15th point
        fault_val = 21 if (i == 25) else 0  # one fault for testing
        points.append({
            "timestamp": ts,
            "operating_frequency_hz": round(freq),
            "operating_mode": random.choice(modes),
            "fan_speed_rpm": round(540 + 20 * math.sin(phase)),
            "pmv_openness_p": round(90 + 8 * math.sin(phase)),
            "water_inlet_temp_c": round(tw_in, 1),
            "water_outlet_temp_c": round(tw_out, 1),
            "t3_condenser_temp_c": round(-5 + 1.5 * math.sin(phase), 1),
            "t4_ambient_temp_c": round(t4, 1),
            "discharge_temp_c": round(46 + 3 * math.sin(phase), 1),
            "return_air_temp_c": round(-5 + 1.5 * math.sin(phase), 1),
            "t1_total_water_outlet_c": round(tw_out - 1, 1),
            "t1b_water_outlet_after_heater_c": round(25 + math.sin(phase), 1),
            "t2_refrigerant_liquid_c": round(32 + 2 * math.sin(phase), 1),
            "t2b_refrigerant_gas_c": round(39 + 2 * math.sin(phase), 1),
            "ta_room_temp_c": round(25 + 0.5 * math.sin(phase * 0.2), 1),
            "pressure1_high_kpa": round(2160 + 30 * math.sin(phase)),
            "pressure2_low_kpa": round(2100 + 20 * math.sin(phase)),
            "outdoor_unit_current_a": round(current, 1),
            "outdoor_unit_voltage_v": round(voltage),
            "compressor_operation_time_h": round(4221 + i * 0.17, 2),
            "unit_capacity_kw": 8,
            "current_fault": fault_val if i == len(points) else 0,
            "fault_1": fault_val,
            "fault_2": 0,
            "fault_3": 0,
            "unit_target_frequency_hz": round(freq + 1),
            "dc_bus_current_a": round(current, 1),
            "dc_bus_voltage_v": round(37 + math.sin(phase), 1),
            "tf_module_temp_c": round(19 + 2 * math.sin(phase), 1),
            "water_flow_m3h": round(0.73 + 0.05 * math.sin(phase), 2),
            "hydraulic_module_ability_kw": round(3.95 + 0.3 * math.sin(phase), 2),
            "electricity_consumption_kwh": round(3449 + i * 0.7, 1),
            "power_output_kwh": round(15025 + i * 3.1, 1),
            "status_defrost": defrost,
            "setting_water_temperature_t1s_zone1": 35,
        })
    # Make the last point have the current fault for dashboard visibility
    points[-1]["current_fault"] = 21
    return {
        "device": "kaisai_khc_08ry3_test",
        "metadata": {
            "description": "Kaisai KHC-08RY3 Heat Pump (TEST MODE)",
            "location": "Test Environment",
            "system_status": "test_mode",
            "total_duration_minutes": 290,
        },
        "timeseries": points,
    }


def read_data():
    try:
        if TEST_MODE:
            return generate_test_data()
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return {"device": "", "metadata": {}, "timeseries": []}


@app.route("/")
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/latest")
def api_latest():
    data = read_data()
    ts = data.get("timeseries", [])
    latest = ts[-1] if ts else {}
    return jsonify(latest)


@app.route("/api/timeseries")
def api_timeseries():
    data = read_data()
    return jsonify(data.get("timeseries", []))


@app.route("/api/errorcodes")
def api_errorcodes():
    try:
        ec_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "errorcodes.json")
        with open(ec_path, "r") as f:
            return jsonify(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError, IOError):
        return jsonify({})


@app.route("/api/metadata")
def api_metadata():
    data = read_data()
    return jsonify({
        "device": data.get("device", ""),
        "metadata": data.get("metadata", {}),
    })


if __name__ == "__main__":
    if TEST_MODE:
        print("*** RUNNING IN TEST MODE — synthetic data ***")
    app.run(debug=True, host="0.0.0.0", port=8080)
