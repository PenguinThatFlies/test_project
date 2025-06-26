from flask import Flask, jsonify, request
import smbus
import time

app = Flask(__name__)

# I2C setup
bus = smbus.SMBus(1)  # Raspberry Pi 4/5 – I2C-1
arduino_address = 0x08  # Same address as Wire.begin(0x08) in Arduino

# Store relay states (assuming 4 relays)
relay_states = {
    'relay1': False,
    'relay2': False,
    'relay3': False,
    'relay4': False
}

def read_sensor_data():
    try:
        raw_data = bus.read_i2c_block_data(arduino_address, 0, 32)
        message = ''.join([chr(b) for b in raw_data if b != 255 and b != 0])
        
        # Parse sensor data (assuming format like "temp:23.5,hum:65,light:512")
        sensor_data = {}
        parts = message.split(',')
        for part in parts:
            if ':' in part:
                key, value = part.split(':')
                sensor_data[key.strip()] = value.strip()
        
        print("Received sensor data:", sensor_data)
        return sensor_data
    except Exception as e:
        print("Error reading sensor data:", e)
        return {"error": str(e)}

def send_command(command):
    try:
        # Send maximum 32 bytes
        data = [ord(c) for c in command]
        bus.write_i2c_block_data(arduino_address, 0, data)
        
        # Update relay states based on command
        cmd = command.upper()
        if cmd.endswith('ON'):
            relay_num = cmd[1]  # Assuming format like "R1ON"
            relay_states[f'relay{relay_num}'] = True
        elif cmd.endswith('OFF'):
            relay_num = cmd[1]  # Assuming format like "R1OFF"
            relay_states[f'relay{relay_num}'] = False
            
        print("Sent command:", command)
        return True
    except Exception as e:
        print("Error sending command:", e)
        return False

@app.route('/data', methods=['GET'])
def get_sensor_data():
    data = read_sensor_data()
    return jsonify(data)

@app.route('/relay-status', methods=['GET'])
def get_relay_status():
    return jsonify(relay_states)

@app.route('/relay-control', methods=['POST'])
def control_relay():
    data = request.json
    relay_num = data.get('relay')
    state = data.get('state')
    
    if not relay_num or state not in ['on', 'off']:
        return jsonify({"error": "Invalid parameters"}), 400
    
    command = f"R{relay_num}{state.upper()}"
    success = send_command(command)
    
    if success:
        return jsonify({"status": "success", "relay": relay_num, "state": state})
    else:
        return jsonify({"error": "Failed to send command"}), 500

@app.route('/relay', methods=['GET'])
def direct_relay_control():
    # Alternative endpoint for simpler GET requests
    relay_num = request.args.get('num')
    state = request.args.get('state')
    
    if not relay_num or state not in ['on', 'off']:
        return jsonify({"error": "Invalid parameters"}), 400
    
    command = f"R{relay_num}{state.upper()}"
    success = send_command(command)
    
    if success:
        return jsonify({"status": "success", "relay": relay_num, "state": state})
    else:
        return jsonify({"error": "Failed to send command"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
