# BSB Lan climate and sensor 

This custom component handles the communication to a BSB-Lan Module and create the entities for Home Assistant.

info for the BSB-LAN Module
https://github.com/fredlcore/bsb_lan


### Installation

download the bsb_lan folder and
copy this folder to `<config_dir>/custom_components/`.

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
HOST_HERE = ip-address

For the Payload look it up in your bsb-lan server the desired parameter you want to read

add the following entry for climate component in your `configuration.yaml`:

```yaml
climate:
  - platform: bsb_lan
    host: HOST_HERE
```

