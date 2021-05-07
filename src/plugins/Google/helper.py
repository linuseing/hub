def ColorAttributes(model="rgb", temp_min=2000, temp_max=6500):
    return {
        "colorModel": model,
        "colorTemperatureRange": {
            "temperatureMinK": temp_min,
            "temperatureMaxK": temp_max,
        },
    }


attributes = {"ColorSetting": ColorAttributes}


def discovery(name: str, _type: str, _traits, **kwargs):
    base = {
        "id": name,
        "type": f"action.devices.types.{_type.upper()}",
        "traits": _traits,
        "name": {"defaultNames": [name], "name": name, "nicknames": [name]},
        "willReportState": False,
        "attributes": {},
        "deviceInfo": {
            "manufacturer": "Linus Eing",
            "model": ".",
            "hwVersion": "1.0",
            "swVersion": "1.0",
        },
    }
    for attr in base["attributes"]:
        base["attributes"].update(attributes["ColorSetting"](**kwargs))
    return base
