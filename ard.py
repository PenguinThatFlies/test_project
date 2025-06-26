from flask import Flask, jsonify, request
import smbus
import time
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# I2C setup
bus = smbus.SMBus(1)  # Raspberry Pi 4/5 – I2C-1
arduino_address = 0x08  # Same as in Arduino's Wire.begin(0x08)

# Store relay states (matches Arduino's relayStates array)
relay_states = {
    'relay1': False,
    'relay2': False,
    'relay3': False,
    'relay4': False
}

def read_sensor_data():
    try:
        # Read 32 bytes from Arduino
        raw_data = bus.read_i2c_block_data(arduino_address, 0, 32)
        
        # Convert to string and clean up
        message = ''.join([chr(b) for b in raw_data if b != 0 and b != 255])
        message = message.split('\x00')[0]  # Remove any null bytes
        
        # Parse the comma-separated values (temp,humidity,light,distance)
        parts = message.split(',')
        if len(parts) >= 4:
            sensor_data = {
                'temperature': float(parts[0]),
                'humidity': int(float(parts[1])),
                'light': int(parts[2]),
                'distance': float(parts[3])
            }
            print("Received sensor data:", sensor_data)
            return sensor_data
        else:
            print("Incomplete data received:", message)
            return {"error": "Incomplete data", "raw": message}
            
    except Exception as e:
        print("Error reading sensor data:", e)
        return {"error": str(e), "raw": message if 'message' in locals() else None}

def send_command(command):
    try:
        # Convert command to bytes and send
        data = [ord(c) for c in command]
        bus.write_i2c_block_data(arduino_address, 0, data)
        
        # Update relay states based on command (R1ON, R2OFF, etc.)
        cmd = command.upper()
        if len(cmd) >= 3 and cmd[0] == 'R':
            relay_num = int(cmd[1])  # R1ON → 1
            if 1 <= relay_num <= 4:
                if cmd.endswith('ON'):
                    relay_states[f'relay{relay_num}'] = True
                elif cmd.endswith('OFF'):
                    relay_states[f'relay{relay_num}'] = False
        
        print("Sent command:", command)
        return True
    except Exception as e:
        print("Error sending command:", e)
        return False

@app.route('/api/data', methods=['GET'])
def get_sensor_data():
    data = read_sensor_data()
    return jsonify(data)

@app.route('/api/relay-status', methods=['GET'])
def get_relay_status():
    return jsonify(relay_states)

@app.route('/api/relay-control', methods=['POST'])
def control_relay():
    try:
        data = request.get_json()
        relay_num = data.get('relay')
        state = data.get('state')
        
        # Validate input
        if relay_num not in ['1', '2', '3', '4'] or state not in ['on', 'off']:
            return jsonify({"error": "Invalid parameters"}), 400
        
        command = f"R{relay_num}{state.upper()}"
        if send_command(command):
            return jsonify({
                "status": "success",
                "relay": relay_num,
                "state": state,
                "message": f"Relay {relay_num} turned {state}"
            })
        else:
            return jsonify({"error": "Failed to send command"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/relay', methods=['GET'])
def direct_relay_control():
    try:
        relay_num = request.args.get('num')
        state = request.args.get('state')
        
        # Validate input
        if relay_num not in ['1', '2', '3', '4'] or state not in ['on', 'off']:
            return jsonify({"error": "Invalid parameters"}), 400
        
        command = f"R{relay_num}{state.upper()}"
        if send_command(command):
            return jsonify({
                "status": "success",
                "relay": relay_num,
                "state": state
            })
        else:
            return jsonify({"error": "Failed to send command"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
