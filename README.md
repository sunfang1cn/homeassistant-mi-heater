# homeassistant-mi-heater
xiaomi zhimi heater（小米 智米电暖器智能版） component for home-assistant
![p](https://ss2.baidu.com/6ONYsjip0QIZ8tyhnq/it/u=517081421,2856515870&fm=173&app=49&f=JPEG?w=640&h=582&s=D5FAA7770132738A17D890E603001021)
### Install
place miheater.py to your ````<home-assistant-config-path>/custom_components/climate/````  path
 (home-assistant 0.88 or upper please use miheater2.py instead)
### Configuration.yaml

````
climate:
  - platform: miheater  # miheater2 in 0.88+
    host: <your device ip address>
    token: <your device miio token>
    name: xiaomi_heater
````


### Features

* supporting power on/off
* supporting setting temperature
* supporting read temperature/humidity from device

![xx](https://bbs.hassbian.com/data/attachment/forum/201812/25/003901jd82efz3hkgh639v.png)

### Notice
token must got from APP miio2.db, not from "miio discover" on PC
