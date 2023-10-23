# Shairport Sync for Cars
If your car audio has an AUX input, you can get AirPlay in your car using Shairport Sync. Together, Shairport Sync and an iPhone or an iPad with cellular capability can give you access to internet radio, YouTube, Apple Music, Spotify, etc. on the move. While Shairport Sync is no substitute for CarPlay, the audio quality is often much better than Bluetooth.

## The Basic Idea

The basic idea is to use a small Linux computer to create an isolated WiFi network (a "car network") and run Shairport Sync on it to provide an AirPlay service. An iPhone or an iPad with cellular capability can simultaneously connect to internet radio, YouTube, Apple Music, Spotify, etc. over the cellular network and send AirPlay audio through the car network to the AirPlay service provided by Shairport Sync. This sends the audio to the computer's DAC which is connected to the AUX input of your car audio.

Please note that Android phones and tablets can not, so far, do this trick of using the two networks simultaneously.

## Example

If you are updating an existing installation, please refer to the [updating](#updating) section below.

In this example, a Raspberry Pi Zero 2 W and a Pimoroni PHAT DAC are used. Shairport Sync will be built for AirPlay 2 operation, but you can build it for "classic" AirPlay (aka AirPlay 1) operation if you prefer. A Pi Zero W is powerful enough for classic AirPlay.

Please note that some of the details of setting up networks are specific to the version of Linux used.

### Prepare the initial SD Image
* Download Raspberry Pi OS (Lite) and install it onto an SD Card using `Raspberry Pi Imager`. The Lite version is preferable to the Desktop version as it doesn't include a sound server like PulseAudio or PipeWire that can prevent direct access to the audio output device.
* Before writing the image to the card, use the Settings control on `Raspberry Pi Imager` to set hostname, enable SSH and provide a username and password to use while building the system. Similarly, you can specify a wireless network the Pi will connect to while building the system. Later on, the Pi will be configured to start its own isolated network.
* The next few steps are to add the overlay needed for the sound card. This may not be necessary in your case, but in this example a Pimoroni PHAT is being used. If you do not need to add an overlay, skip these steps.
  * Mount the card on a Linux machine. Two drives should appear – a `boot` drive and a `rootfs` drive.
  * `cd` to the `boot` drive (since my username is `mike`, it will be `$ cd /media/mike/boot`).
  * Edit the `config.txt` file to add the overlay needed for the sound card. This may not be necessary in your case, but in this example a Pimoroni PHAT is being used and it needs the following entry to be added:
    ```
    dtoverlay=hifiberry-dac
    ```
  * Close the file and carefully dismount and eject the two drives. *Be sure to dismount and eject the drives properly; otherwise they may be corrupted.*
* Remove the SD card from the Linux machine, insert it into the Pi and reboot.

After a short time, the Pi should appear on your network – it may take a couple of minutes. To check, try to `ping` it at the `<hostname>.local`, e.g. if the hostname is `bmw` then use `$ ping bmw.local`. Once it has appeared, you can SSH into it and configure it.

### Boot, Configure, Update 
The first thing to do on a Pi would be to use the `raspi-config` tool to expand the file system to use the entire card. Next, do the usual update and upgrade:
```
# apt-get update
# apt-get upgrade
``` 

### Build and Install 
Let's get the tools and libraries for building and installing Shairport Sync (and NQPTP).

```
# apt install --no-install-recommends build-essential git xmltoman autoconf automake libtool \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev \
    libplist-dev libsodium-dev libavutil-dev libavcodec-dev libavformat-dev uuid-dev libgcrypt-dev xxd
```
If you are building classic Shairport Sync, the list of packages is shorter:
```
# apt-get install --no-install-recommends build-essential git xmltoman autoconf automake libtool \
    libpopt-dev libconfig-dev libasound2-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev
```

#### NQPTP
Skip this section if you are building classic Shairport Sync – NQPTP is not needed for classic Shairport Sync.

Download, install, enable and start NQPTP from [here](https://github.com/mikebrady/nqptp) following the guide for Linux.

#### Shairport Sync
Download Shairport Sync, check out the `development` branch and configure, compile and install it.

* Omit the `--with-airplay-2` from the `./configure` options if you are building classic Shairport Sync.

```
$ git clone https://github.com/mikebrady/shairport-sync.git
$ cd shairport-sync
$ git checkout development
$ autoreconf -fi
$ ./configure --sysconfdir=/etc --with-alsa \
    --with-soxr --with-avahi --with-ssl=openssl --with-systemd --with-airplay-2
$ make
# make install
```
The `autoreconf` step may take quite a while – please be patient!

**Note:** *Do not* enable Shairport Sync to start automatically at boot time – later on in this installation, we will arrange for it to start after the network has been set up.

### Configure Shairport Sync
Here are the important options for the Shairport Sync configuration file at `/etc/shairport-sync.conf`:
```
// Sample Configuration File for Shairport Sync for Car Audio with a Pimoroni PHAT
general =
{
	name = "BMW Radio";
	ignore_volume_control = "yes";
	volume_max_db = -3.00;
};

alsa =
{
	output_device = "hw:1"; // the name of the alsa output device. Use "alsamixer" or "aplay" to find out the names of devices, mixers, etc.
};

```
Two `general` settings are worth noting.
1. First, the option to ignore the sending device's volume control is enabled. This means that the car audio's volume control is the only one that affects the audio volume. This is a matter of personal preference.
   
2. Second, the maximum output offered by the DAC to the AUX port of the car audio can be reduced if it is overloading the car audio's input circuits and causing distortion. Again, that's a matter for personal selection and adjustment.

The `alsa` settings are for the Pimoroni PHAT – it does not have a hardware mixer, so no `mixer_control_name` is given.

The DAC's 32-bit capability is automatically selected if available, so there is no need to set it here. Similarly, since `soxr` support is included in the build, `soxr` interpolation will be automatically enabled if the device is fast enough.

### Extra Packages
A number of packages to enable the Pi to work as a WiFi base station are needed:
```
# apt install --no-install-recommends hostapd isc-dhcp-server
```
Disable both of these services from starting at boot time (this is because we will launch them sequentially later on):
```
# systemctl unmask hostapd
# systemctl disable hostapd
# systemctl disable isc-dhcp-server
```
#### Configure HostAPD
Configure `hostapd` by creating `/etc/hostapd/hostapd.conf` with the following contents which will set up an open network with the name BMW. You might wish to change the name:
``` 
# Thanks to https://wiki.gentoo.org/wiki/Hostapd#802.11b.2Fg.2Fn_triple_AP

# The interface used by the AP
interface=wlan0

# This is the name of the network -- yours may be different
ssid=BMW

# "g" simply means 2.4GHz band
hw_mode=g

# Channel to use
channel=11

# Limit the frequencies used to those allowed in the country
ieee80211d=1

# The country code
country_code=IE

# Enable 802.11n support
ieee80211n=1

# QoS support, also required for full speed on 802.11n/ac/ax
wmm_enabled=1

```
Note that, since the car network is isolated from the Internet, you don't really need to secure it with a password.

#### Configure DHCP server

First, replace the contents of `/etc/dhcp/dhcpd.conf` with this:
```
subnet 10.0.10.0 netmask 255.255.255.0 {
     range 10.0.10.5 10.0.10.150;
     #option routers <the-IP-address-of-your-gateway-or-router>;
     #option broadcast-address <the-broadcast-IP-address-for-your-network>;
}
```
Second, modify the `INTERFACESv4` entry at the end of the file `/etc/default/isc-dhcp-server` to look as follows:
```
INTERFACESv4="wlan0"
INTERFACESv6=""
```
### Set up the Startup Sequence
Configure the startup sequence by adding commands to `/etc/rc.local` to start `hostapd` and the `dhcp` server and then to start `shairport-sync` automatically after startup. Its contents should look like this:
```
#!/bin/sh -e
#
# rc.local
#
# This script is executed at the end of each multiuser runlevel.
# Make sure that the script will "exit 0" on success or any other
# value on error.

# Uncomment the next line to exit the script here, skipping the remainder of the script where the WiFi access point and Shairport Sync itself are started.
# exit 0 # uncomment this line to exit the script here

/sbin/iw dev wlan0 set power_save off
/usr/sbin/hostapd -B -P /run/hostapd.pid /etc/hostapd/hostapd.conf
/sbin/ip addr add 10.0.10.1/24 dev wlan0
/bin/sleep 1
/bin/systemctl start isc-dhcp-server
/bin/sleep 2
/bin/systemctl start shairport-sync

exit 0 # normal exit here
```
As you can see, the effect of these commands is to start the WiFi transmitter, give the base station the IP address `10.0.10.1`, start a DHCP server and finally start the Shairport Sync service.

### Final Steps
You should now disable either the `NetworkManager` or the `dhcpcd` service (whichever is in your system) so that they won't run when the system reboots. You can find out which is in your system using the `ps -aux` command and looking for either `NetworkManager` or `dhcpcd`. Here is an example from a system running `dhcpcd`:
```
$ ps aux | grep 'NetworkManager\|dhcpcd' | grep -v grep
root         596  0.0  0.2   3112  2216 ?        Ss   Oct08   0:51 /usr/sbin/dhcpcd -w -q
```
Once you have identified which service to disable, perform the appropriate one of the following commands:
```
# systemctl disable NetworkManager
```
or 
```
# systemctl disable dhcpcd
```
Now you should also disable the `wpa_supplicant` service.

```
# systemctl disable wpa_supplicant
```

From this point on, at least on the Raspberry Pi, if you were to power off and reboot the machine, it would not reconnect to your network. Instead, it would act as the WiFi base station you have configured with `hostapd` and `isc-dhcp-server`. 

**Note:** The WiFi credentials you used to connect to the initial network (e.g. your home network) will have been stored in the system in plain text. This is convenient for when you want to reconnect to update (see later), but if you wish to delete them for any reason, they will be in `/etc/wpa_supplicant/wpa_supplicant.conf`

When you are finished (including any optional steps below), carefully power down the machine before unplugging it from power:
```
# poweroff
```
#### Optional: Optimise startup time – Raspberry Pi Specific
These optional steps have been tested on a Raspberry Pi only. They have not been tested on other systems.
Some services are not necessary for this setup. These commands disable them:
```
# systemctl disable systemd-timesyncd
# systemctl disable keyboard-setup
# systemctl disable triggerhappy
# systemctl disable dphys-swapfile
```
#### Optional: Read-only mode – Raspberry Pi Specific
This optional step is applicable to a Raspberry Pi only. Run `sudo raspi-config` and then choose `Performance Options` > `Overlay Filesystem` and choose to enable the overlay filesystem, and to set the boot partition to be write-protected. 

### Ready
Install the Raspberry Pi in your car. It should be powered from a source that is switched off when you leave the car, otherwise the slight current drain will eventually flatten the car's battery.

When the power source is switched on, typically when you start the car, it will take maybe a minute for the system to boot up.

### Enjoy!
---
## Updating
From time to time, you may wish to update this installation. Assuming you haven't deleted your original WiFi network credentials, the easiest thing is to temporarily reconnect to the network you used when you created the system. To do that, you have to temporarily undo the "Final Steps" and some of the "Raspberry Pi Specific" steps you used. This will enable you to connect your device back to the network it was created on. You should then be able to update the operating system and libraries in the normal way and then update Shairport Sync.

Note that if you're upgrading the operating system to e.g. from Bullseye to Bookworm, the names and index numbers of the output devices may change, and the names of the mixer controls may also change. You can use [`sps-alsa-explore`](https://github.com/mikebrady/sps-alsa-explore) to discover device names and mixer names.

To update, take the following steps:
### Temporarily reconnect to the original network and update
1. If it's a Raspberry Pi and you have enabled the Read-only mode, you must take the device out of Read-only mode:  
Run `sudo raspi-config` and then choose `Performance Options` > `Overlay Filesystem` and choose to disable the overlay filesystem and to set the boot partition not to be write-protected. This is so that changes can be written to the file system; you can make the filesystem read-only again later. Save the changes and reboot the system.

2. Undo a modification you may have made during previous installations.

   Remove a possible modification from a file. If there is a file called `/etc/dhcpcd.conf` and if the first line reads:
   ```
   denyinterfaces wlan0
   ```
   then delete that line or comment it out -- it it no longer needed going forward.
   If the file `/etc/dhcpcd.conf` doesn't exist, or if the first line is not `denyinterfaces wlan0` as given here, then you don't need to do anything.
      
   (The reason for this suggestion is that a simpler way is now used to prevent the `dhcpcd` service from trying to manage the interface -- the `dhcpcd` service is now completely disabled.)

4. Re-enable either `NetworkManager` or `dhcpcd` as appropriate:
   ```
   # systemctl enable NetworkManager
   ```
   or
   ```
   # systemctl enable dhcpcd
   ```
   (Just FYI, even though the `wpa_supplicant` service has previously been disabled from starting automatically, it will be turned on by `NetworkManager` or `dhcpcd` after reboot.)
   
5. If you had disabled the `systemd-timesyncd` service as suggested in the "Optimise startup time -- Raspberry Pi Specific" section, you need to temporarily re-enable it:   
   ```
   # systemctl enable systemd-timesyncd
   ```
   This is needed because the correct time is necessary for detemininig what has been updated.

6. Edit `/etc/rc.local` to exit the script before enabling the WiFi access point and starting Shairport Sync. Do this by uncommenting the line:
   ```
   # exit 0 # uncomment this line to exit the script here
   ```
   so that it looks like this:
   ```
   exit 0 # uncomment this line to exit the script here
   ```
Save the changes.

From this point on, if you reboot the machine, it will connect to the network it was configured on, i.e. the network you used when you set it up for the first time. This is because the name and password of the network it was created on would have been placed in `/etc/wpa_supplicant/wpa_supplicant` when the system was initially configured and will still be there.

7. Reboot and do normal updating.

### Revert to normal operation
When you are finished updating, you need to undo the temporary changes you made to the setup, as follows:

1. First, disable `NetworkManager` or `dhcpcd` as appropriate:
   ```
   # systemctl disable NetworkManager
   ```
   or 
   ```
   # systemctl disable dhcpcd
   ```
2. Also, ensure that the `wpa_supplicant` service is disabled.
   ```
   # systemctl disable wpa_supplicant
   ```
3. Next, if you had temporarily re-enabled services that are normally disabled, then it's time to disable them again:
   ```
   # systemctl disable systemd-timesyncd 
   ```
4. Edit `/etc/rc.local` to perform the entire script before exiting, so that it enables the WiFi access point and starts Shairport Sync. Do this by commenting out the line:
   ```
   exit 0 # uncomment this line to exit the script now
   ```
   so that it loooks like this:
   ```
   # exit 0 # uncomment this line to exit the script now
   ```
   Save the changes.

5. Reboot. The system should start as it would if it was in the car.

5. If the device is a Raspberry Pi and you wish to make the file system read-only, connect to the system, run `sudo raspi-config` and then choose `Performance Options` > `Overlay Filesystem`. In there, choose to enable the overlay filesystem, and to set the boot partition to be write-protected. Do a final reboot and check that everyting is in order.
