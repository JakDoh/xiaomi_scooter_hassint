# Xiaomi Mi Electric Scooter Integration for Home Assistant

This is a custom Home Assistant integration for monitoring Xiaomi/Ninebot electric scooters (M365, Pro, Pro 2, 1S, Essential, Scooter 3). 

Unlike older integrations, this version is designed for modern security requirements. It features a full re-implementation of **NinebotCrypto** and **miauth**, enabling it to communicate with newer, encrypted firmware versions that standard BLE trackers cannot access.

## 🚀 Features
- **Config Flow Support:** Easy setup via the Home Assistant UI (no YAML editing required).
- **Auto-Discovery:** Automatically finds nearby scooters via Bluetooth.
- **Encrypted Communication:** Full support for AES-128 secure handshakes.
- **Rich Telemetry:** Monitors battery levels, cell voltages, speed, mileage, temperature, and more.
- **BLE Proxy Compatible:** Works with ESP32 Bluetooth Proxies.

## 🛠 Supported Versions
This integration is specifically built to handle the encryption used in:
- **BLE Versions:** 1.2.9, 1.3.x, 1.5.x and newer.
- **Models:** All scooters using the Ninebot/Xiaomi protocol (M365 series, Pro series, 1S, Essential, Scooter 3).

## 🚲 How to Setup

### 1. Preparation
*   Ensure your Home Assistant has a working Bluetooth adapter or an **ESP32 Bluetooth Proxy**.
*   The scooter must be **turned on**.
*   Ensure the scooter is **not connected** to the Mi Home app or any other app (only one connection is allowed at a time).

### 2. Installation
*   **Via HACS (Recommended):** 
    1. Go to **HACS** > **Integrations** > 3 dots > **Custom repositories**.
    2. Add `https://github.com/JakDoh/xiaomi_scooter_hassint` as an **Integration**.
    3. Click **Install** and then **Restart Home Assistant**.
*   **Manual:** Copy the `custom_components/xiaomi_scooter/` folder to your `config/custom_components/` directory and restart.

### 3. Configuration (UI)
1. In Home Assistant, navigate to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **Xiaomi Scooter**.
3. Select your scooter from the discovered list.
4. **The Pairing Handshake (Crucial):**
    *   During setup, the scooter will start **beeping**.
    *   **Press the Power Button once** on the scooter dashboard to authorize the connection.
    *   The integration will complete the secure handshake and create your sensors.

## 📝 Important Notes

### Authentication Handshake
The `miauth` protocol requires physical confirmation. If you do not press the button on the scooter when it starts beeping during the configuration flow, the authentication will fail.

### Connection Stability
*   **Range:** BLE is distance-sensitive. For best results, keep the scooter within 5 meters of the Bluetooth receiver or use a Proxy.
*   **Sleep Mode:** When the scooter is turned off, the sensors will show as "Unavailable" in Home Assistant. They will update once the scooter is turned back on.

## 🛠 Technical Credits
This integration is a Python re-implementation of research and code from:
*   [NinebotCrypto](https://github.com/scooterhacking/NinebotCrypto) (ScooterHacking)
*   [miauth](https://github.com/dnandha/miauth) (dnandha)

## ⚠️ Disclaimer
This is an experimental community-driven project and is not affiliated with Xiaomi or Ninebot. Use it at your own risk.
