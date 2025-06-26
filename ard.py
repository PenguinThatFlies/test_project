import smbus
import time

# I2C setup
bus = smbus.SMBus(1)  # Raspberry Pi 4/5 – I2C-1
arduino_address = 0x08  # იგივე მისამართი რაც Wire.begin(0x08) Arduino-ში

def read_sensor_data():
    try:
        raw_data = bus.read_i2c_block_data(arduino_address, 0, 32)
        message = ''.join([chr(b) for b in raw_data if b != 255 and b != 0])
        print("მიღებული მონაცემები:", message)
        return message
    except Exception as e:
        print("შეცდომა მონაცემების მიღებისას:", e)
        return ""

def send_command(command):
    try:
        # გადასცეს მაქსიმუმ 32 ბაიტი
        data = [ord(c) for c in command]
        bus.write_i2c_block_data(arduino_address, 0, data)
        print("გაგზავნილი ბრძანება:", command)
    except Exception as e:
        print("შეცდომა ბრძანების გაგზავნისას:", e)

def menu():
    print("\n--- მენიუ ---")
    print("1. წაიკითხე სენსორები")
    print("2. ჩართე რელე (მაგ. R1ON)")
    print("3. გამორთე რელე (მაგ. R1OFF)")
    print("0. გასვლა")

while True:
    menu()
    choice = input("აირჩიე: ").strip()

    if choice == "1":
        read_sensor_data()
    elif choice == "2":
        relay = input("ჩასართავი რელე (მაგ: R1ON): ").strip().upper()
        send_command(relay)
    elif choice == "3":
        relay = input("გასართავი რელე (მაგ: R1OFF): ").strip().upper()
        send_command(relay)
    elif choice == "0":
        print("გასვლა...")
        break
    else:
        print("არასწორი არჩევანი")
    
    time.sleep(1.5)
