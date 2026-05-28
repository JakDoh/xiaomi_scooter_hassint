ESC = '55AA 03 20 01'
BMS = '55AA 03 22 01'

CMD_ESC_DATA_INITIAL = (f'{ESC} 10 16') # General info extended, unpack
CMD_ESC_DATA = (f'{ESC} 1B 36') # General info extended, unpack
CMD_ESC_DATA_EXT1 = (f'{ESC} 70 1C') # General info extended, unpack
CMD_ESC_DATA_EXT2 = (f'{ESC} B0 20') # General info extended, unpack

CMD_BMS_DATA_INITIAL = (f'{BMS} 10 16') # General info extended, unpack
CMD_BMS_DATA_CH1 = (f'{BMS} 1B 0A') # General info extended, unpack
CMD_BMS_DATA_CH2 = (f'{BMS} 30 18') # General info extended, unpack
CMD_BMS_DATA_CH3 = (f'{BMS} 40 14') # General info extended, unpack


CMD_SCOOTER_POWER = (f'{BMS} BD 02') # Scooter power in W
CMD_BOOLEAN_STATE = (f'{BMS} B2 02') # Scooter power in W
CMD_SPEED = (f'{ESC} 26 02') # Speed
CMD_OPER_MODE = (f'{ESC} 75 02') #Operating mode: 0 NORMAL; 1 ECO; 2 SPORT   
CMD_ESC_SERIAL_NUMBER = (f'{ESC} 10 0e') # Serial num
CMD_REMAIN_MILEAGE = f'{ESC} 24 02' # Actual remaining mileage, unit: 10m
CMD_PREDICTED_MILEAGE = f'{ESC} 25 02' # Actual remaining mileage, unit: 10m
CMD_TOTAL_MILEAGE = f'{ESC} 29 04' # Total mileage, m
CMD_TRIP_MILEAGE = f'{ESC} 2F 02' # Trip mileage, 10m
CMD_CURRENT_MILEAGE = (f'{ESC} 2F 02') # Current mileage
CMD_TOT_OPER_TIME = (f'{ESC} 32 04') # Total run time
CMD_TOT_RIDE_TIME = (f'{ESC} 34 04') # Total riding time
CMD_TRIP_OPER_TIME = (f'{ESC} 3A 04') # ? Single o eraton tme, sec
CMD_TRIP_RIDE_TIME = (f'{ESC} 3B 04') # ? Single riding tme, sec
CMD_BATT_PERCENT = f'{ESC} 22 02' # Batery  ercentage of the scooter, 0-100
CMD_BATT_VOLTAGE = (f'{ESC} 48 02') # Battery voltage  = (measured by ESC)
CMD_BATT_CURRENT = (f'{ESC} 50 02') # Battery current  = (measured by ESC)
CMD_BATT_TEMP = (f'{ESC} 3f 04') # Battery current  = (measured by ESC)
CMD_ESC_SUPPLY_VOLTAGE = (f'{ESC} 47 02') # ESC supply voltage  = (measured by ESC)
CMD_MOSFET_TEMP = (f'{ESC} 41 02') # Battery current 
CMD_FRAME_TEMP1 = (f'{ESC} BB 02') # Frame temperature
CMD_FRAME_TEMP2 = (f'{ESC} 3E 02') # Frame temperature
CMD_BMS_SERIAL_NUMBER = (f'{BMS} 10 0E') #Serial number
CMD_BMS_STATUS = (f'{BMS} 30 02') # Status
CMD_BMS_CELL_VOLTAGES = (f'{BMS} 40 14') # Cell Voltage 1 - 10
CMD_BMS_TEMPERATURES = (f'{BMS} 35 04') # bTemperature1:bTemperature2, Deg C, 0 is -20
CMD_BMS_CURRENT = (f'{BMS} 33 02') #Current, x10mA, positive - discharging, negative - charging
CMD_BMS_VOLTAGE = (f'{BMS} 34 02') #Current, x10mA, positive - discharging, negative - charging
CMD_BMS_BALANCE_ST = (f'{BMS} 36 02') #Current, x10mA, positive - discharging, negative - charging
CMD_BMS_FIRMWARE_VERSION = (f'{BMS} 17 02') #Firmware version
CMD_BMS_FACTORY_CAPACITY = (f'{BMS} 18 02') #Factory capacity
CMD_BMS_MANUFACTURE_DATE = (f'{BMS} 20 02') #Manufacture date
CMD_BMS_CHARGE_FULL_CYCLES = (f'{BMS} 1B 02') #Charge full cycles
CMD_BMS_CHARGE_COUNT = (f'{BMS} 1C 02') #Charge count
CMD_BMS_HEALTH = (f'{BMS} 3B 02') #Health, %

#CMD_BMS_STATUS response bitmask
BMS_BOOLMARK_PASSWORD = 0x0001
BMS_BOOLMARK_ACT = 0x0002
BMS_BOOLMARK_CHG_PROTECT = 0x0004
BMS_BOOLMARK_CMOS = 0x0008
BMS_BOOLMARK_WRITE_CMD = 0x0010
BMS_BOOLMARK_DISCHARGE = 0x0020
BMS_BOOLMARK_CHARGE = 0x0040
BMS_BOOLMARK_CHARGERIN = 0x0080
BMS_BOOLMARK_DISOVER = 0x0100
BMS_BOOLMARK_CHGOVER = 0x0200
BMS_BOOLMARK_VOERTEMP = 0x0400
BMS_BOOLMARK_TEST_MODE = 0x0800

SCOOTER_SN_MAP= {
    "13678": ("M365", "White", "China version", "Ninebot"),
    "13679": ("M365", "Black", "China version", "Ninebot"),
    "16057": ("M187", None, None, None),
    "16133": ("M365", "Black", "European version", "Ninebot"),
    "21074": ("M365", "Black", "European version", "Ninebot"),
    "16132": ("M365", "White", "European version", "Ninebot"),
    "21073": ("M365", "White", "European version", "Ninebot"),
    "16349": ("M365", "Black", "American version", "Ninebot"),
    "16348": ("M365", "White", "American version", "Ninebot"),
    "18832": ("M365 Pro", None, "Chinese version", "Ninebot"),
    "21886": ("M365 Pro", None, "European version", "Ninebot"),
    "30371": ("Mi Electric Scooter Pro 2", None, "Mercedes Edition", "Ninebot"),
    "26354": ("Mi Electric Scooter Pro 2", None, "European version", "Ninebot"),
    "25699": ("Mi Electric Scooter 1S", None, None, "Ninebot", "Ninebot"),
    "25702": ("Mi Electric Scooter Lite", None, "German version", "Ninebot"),
    "25600": ("Mi Electric Scooter Lite", None, "Global version", "Ninebot"),
    "30807": ("Mi Electric Scooter 3", "Black/Blue" ,None, "Ninebot"),
    "30806": ("Mi Electric Scooter 3", "White/Orange" ,None, "Ninebot"),
    "46442": ("Mi Electric Scooter 4", None, "German version", "Brightway (Navee)"),
    "46443": ("Mi Electric Scooter 4", None, "European version", "Brightway (Navee)"),
    "46441": ("Mi Electric Scooter 4", None, "Global version", "Brightway (Navee)"),
    "46440": ("Mi Electric Scooter 4", None, "Italian version", "Brightway (Navee)"),
    "46416": ("Mi Electric Scooter 4 Lite",None, "German version", "Brightway (Navee)"),
    "46419": ("Mi Electric Scooter 4 Lite",None, "European version", "Brightway (Navee)"),
    "46415": ("Mi Electric Scooter 4 Lite",None, "Global version", "Brightway (Navee)"),
    "46418": ("Mi Electric Scooter 4 Lite",None, "French version", "Brightway (Navee)"),
    "46417": ("Mi Electric Scooter 4 Lite",None, "Italian version", "Brightway (Navee)"),
    "40595": ("Mi Electric Scooter 4 Ultra",None, "German version", "Brightway (Navee)"),
    "37829": ("Mi Electric Scooter 4 Ultra",None, "Global version", "Brightway (Navee)"),
    "40594": ("Mi Electric Scooter 4 Ultra",None, "French version", "Brightway (Navee)"),
    "45482": ("Mi Electric Scooter 4 Go",None, "Global version", "Ninebot"),
    "45480": ("Mi Electric Scooter 4 Go",None, "French version", "Ninebot"),
    "45481": ("Mi Electric Scooter 4 Go",None, "Italian version", "Ninebot"),
    "35802": ("Mi Electric Scooter 4 Pro",None, "Global version", "Ninebot"),
    "38191": ("Mi Electric Scooter 4 Pro",None, "Global version", "Ninebot"),
    "35803": ("Mi Electric Scooter 4 Pro",None, "British version", "Ninebot"),
    "35804": ("Mi Electric Scooter 4 Pro",None, "French version", "Ninebot"),
    "35806": ("Mi Electric Scooter 4 Pro",None, "German version", "Ninebot"),
    "41839": ("Mi Electric Scooter 4 Pro",None, "Italian version", "Ninebot"),
}

BATTERY_SN_MAP = {
    "3JBG": ("Mi Electric Scooter Pro 2 battery" "Reinforced soldering & welds. First version (V1)"),
    "3JCG": ("Mi Electric Scooter Pro 2 battery. Reinforced welds on the cells. Second version (V2)"),
    "3JEE": ("Mi Electric Scooter Pro 2 battery. Reinforced soldering & welds. Third version (V3)"),
    "3GBG": ("Mi Electric Scooter Lite battery. Non-reinforced welds and soldering."),
    "4XFG": ("Mi Electric Scooter Pro 2 battery. Reinforced soldering & welds."),
    "BFAG": ("Mi Electric Scooter Pro 2 battery."),
    "BFFG": ("Mi Electric Scooter Pro 2 battery. EVE cells, limited charge."),
    "4XBG": ("Mi Electric Scooter Pro 1 battery (EU version). Reinforced soldering & welds."),
    "4XCG": ("Mi Electric Scooter Pro 1 battery (EU version). Reinforced soldering & welds."),
    "4XAA": ("Mi Electric Scooter Pro 1 battery (CN version). Reinforced soldering & welds."),
    "2JEG": ("Mi Electric Scooter 1S battery (EU version) with resistors on the BMS."),
    "2JAE": ("Mi Electric Scooter 1S battery with major changes to the BMS and rails (late 2020)."),
    "2JBE": ("Mi Electric Scooter 1S battery."),
    "2JAG": ("M365 battery with EVE cells, CN version."),
    "2JCG": ("M365 battery with EVE cells, EU version."),
    "0JEG": ("M365 1S battery with LG M26 cells."),
}


# N5GA - F20
# N5GB - F20D
# N5GC - F30
# N5GD - F30D
# N5GE - F40
# N5GF- F40E
# N5GG - F40D
# N5GH - F60
# N5GI - F60D/F60E
# N5GJ - F60D/F60E
# N5GM - F60A/F60 Asia
# N5GN - F25
# N5GO - F20A
# N5GQ - F30E
# N5GR - F40A
# N5GV - F40
# N5GW - F25E