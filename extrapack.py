# extrapack.py
import pyModeS as pms

def decode_adsb(message):
    """Decode ADS-B messages."""
    try:
        tc = pms.adsb.typecode(message)
        data = {
            "TypeCode": tc,
            "ICAO24": pms.adsb.icao(message),
            "DownlinkFormat": pms.adsb.df(message),
            # "Capability": pms.adsb.ca(message)
        }

        if 1 <= tc <= 4:
            data["Callsign"] = pms.adsb.callsign(message)
        elif 5 <= tc <= 8:
            data["SurfacePosition"] = pms.adsb.surface_position(message, oe_flag=None, t=None)
            data["SurfaceMovement"] = pms.adsb.surface_movement(message)
        # elif 9 <= tc <= 18:
            # data["AirbornePosition"] = pms.adsb.airborne_position(message)
            # data["VerticalStatus"] = pms.adsb.vs(message)
            # data["NICSupplementA"] = pms.adsb.nicsa(message)
        elif tc == 19:
            data["Velocity"] = pms.adsb.velocity(message)
            # data["Heading"] = pms.adsb.heading(message)
            # data["VerticalRate"] = pms.adsb.vert_rate(message)
            # data["SpeedType"] = pms.adsb.speedtype(message)
        elif 20 <= tc <= 22:
            data["Altitude"] = pms.adsb.altitude(message)
        # elif tc == 28:
            # data["AircraftStatus"] = pms.adsb.aircraft_status(message)
        # elif tc == 29:
            # data["EmergencyStateStatus"] = pms.adsb.emergency(message)
        # elif tc == 31:
            # data["OperationalStatus"] = pms.adsb.operational_status(message)
            # data["SystemCapability"] = pms.adsb.om_acas(message)

        return data
    except Exception as e:
        return {"Error": f"Failed to decode ADS-B message: {e}"}

def decode_comm_b(message):
    """Decode Comm-B messages."""
    try:
        data = {
            "BDSCode": pms.commb.bds(message)
        }

        # Extract Comm-B message type
        mdb_type = pms.commb.mdb_type(message)

        if mdb_type == "1":
            data["ACASResolutionAdvisory"] = pms.commb.mdac(message)
        elif mdb_type == "2":
            data["TargetState"] = pms.commb.mdts(message)
        elif mdb_type == "3":
            data["AirlineOperationalStatus"] = pms.commb.mdos(message)
        elif mdb_type == "4":
            data["MBData"] = pms.commb.mdb4(message)
        elif mdb_type == "5":
            data["MBData"] = pms.commb.mdb5(message)
        elif mdb_type == "6":
            data["MBData"] = pms.commb.mdb6(message)

        return data
    except Exception as e:
        return {"Error": f"Failed to decode Comm-B message: {e}"}

def decode_message(message):
    """Decode Mode-S message."""
    try:
        df = pms.df(message)
        data = {
            "DownlinkFormat": df
        }

        if df == 17:
            data.update(decode_adsb(message))
        elif df in [20, 21]:
            data.update(decode_comm_b(message))

        # If the ICAO address can be extracted, add it to the data.
        if df in [17, 18, 19, 20, 21]:
            data["ICAO"] = pms.adsb.icao(message)

        return data
    except Exception as e:
        return {"Error": f"Failed to decode Mode-S message: {e}"}