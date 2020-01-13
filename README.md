# BSB Lan climate and sensor

![Project Stage][project-stage-shield]
![Project Maintenance][maintenance-shield]

## Breaking this custom component doesn't work with current home assistent version

This custom component handles the communication to a BSB-Lan Module and create the entities for Home Assistant.

info for the [BSB-LAN Module][bsb-lan]

dicussion about this component in the [forum][forum]

[bug report](src/bug_report.md)

[feature request](src/feature_request.md)

### Installation

download the bsb_lan folder and
copy this folder to `<config_dir>/custom_components/`.

## Sensor component install

Add the following entry for your sensor in your `configuration.yaml`:

```yaml
sensor:
  - platform: bsb_lan
    host: HOST_HERE
    payload:
      - '8700'
      - '8830'
      - '8740'
      - '8006'
      - '8003'
      - '1600'
```

HOST_HERE = ip-address of your bsb-lan device. For example 10.0.1.10

For the Payload look it up in your bsb-lan server the desired parameter you want to read

## Climate component install

add the following entry for climate component in your `configuration.yaml`:

```yaml
climate:
  - platform: bsb_lan
    host: HOST_HERE
```

Web-Interface screenshots:

<img src="https://github.com/liudger/BSB-LAN-Component-for-Home-Assistant/blob/master/src/overviewClimate.png" size="50%">

<img src="https://github.com/liudger/BSB-LAN-Component-for-Home-Assistant/blob/master/src/readingSensor_outsideTemp.png" size="50%">

[maintenance-shield]: https://img.shields.io/maintenance/yes/2019.svg
[project-stage-shield]: https://img.shields.io/badge/project%20stage-%20!%20DEPRECATED%20%20%20!-ff0000.svg
[bsb-lan]: https://github.com/fredlcore/bsb_lan
