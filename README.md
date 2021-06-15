# MiiSmartNotifier
---
## Summary

##### This small application is to maintain/monitor my home server's HDD status by referring s.m.a.r.t information and notify via Line.  
##### It'll compare between worst value of s.m.a.r.t information aquired from all attached devices and value configure in json file.

---
## Usage  
1. Install the below application/software.
2. Put your line notification token on the `token` section of `config.json`.
3. Check/modify the `warn` and `error` sections for each attribute in `config.json`.
4. `sudo python3 miismartnotifier.py`

##### Always place `config.json` at the same directory as `miismartnotifier.py`.
##### Triggering by scheduling app such as `cron` would notify periodically.
##### Note : This application can only be executed by superuser due to `smartctl(smartmontools)` can only aquire s.m.a.r.t information by superuser.
---
## Environment & Softwares
- Python 3.7.5
- smartctl 6.6
- pySMART 1.0
- Raspbeey Pi 4 / Raspbian 10
---
## S.M.A.R.T Attributes
##### This app will check for below attributes in s.m.a.r.t information.  If your HDD does not support or has no attribute as follows, this app might not work properly.
##### If the s.m.a.r.t worst value acquired from HDD is less than the `warn` value in `config.json` it will raise a warning alert. The same thing works for error alerts.
##### `194:temperature_celsius` is the only exception. If the worst value is **more** than the config value it'll raise an alert.
##### When `warn` or `error` value is set 0 in `config.json` it'll replace as threshold value from its HDD.

| id | attribute name | warning(default) | error(default)|
|----|----------------|------------------|---------------|
|1|Raw Read Error Rate|40|0(Threshold)|
|3|Spin Up Time|60|40|
|4|Start/Stop Count|50|0(Threshold)|
|5|Realocated Sectore Count|100|98|
|7|Seek Error Rate|50|0(Threshold)|
|9|Power On Hours|50|25|
|10(0A)|Spin Retry Count|99|98|
|12(0C)|Power Cycle Count|50|20|
|194(C2)|Temperature Celsius|55|60|
|197(C5)|Current Pending Sector|100|98|
---
## Caution
Use at your own risk.
