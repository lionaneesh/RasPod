RasPod
======

A simple music server for Raspberry Pi.

Setting Up RasPod
=================

Please check the wiki (https://github.com/lionaneesh/RasPod/wiki/Setting-up-RasPod) we created for this purpose.
The wiki can be edited by any registered Github user, so please help us make it more readable and cover most of the platforms.

Requirements
===========

As the project is based on python, you obviously require to have python installed.

The project has been tested on Python v2.7.

Also tornado server (v1.2 aleast), libVLC, alsa-utils are required.

	# sudo apt-get install python-tornado python-setuptools vlc alsa-utils

Running on Raspberry Pi
=======================

The following steps/commands have been tested on Debian Wheezy and Debian Squeeze.

- Install python-tornado (atleast v1.2)

Raspod uses python-tornado for handling HTTP requests.

	# sudo apt-get install python-tornado

Note: On Raspberry Pi [debian squeeze] you need to build the tornado server yourself,
as the latest package availiable is v1.0 [http://packages.debian.org/squeeze/python-tornado]
which would give out some errors.

- Install VLC and Alsa-drivers

Raspod uses libVLC to play audio.

	# sudo apt-get install vlc alsa-utils

- Enable Audio (Not needed for Debian Wheezy)

In most OS'es on Raspberry Pi sound is disabled by default because the ALSA sound driver is still "alpha"
(not fully tested). To enable sound

	# sudo modprobe snd_bcm2835

- Run


Develop
=======

	# python setup.py develop

Run Server
==========

	$ python server.py <port>

	As, a default the port is set to 8888

Tested On
=========

- Arch-linux 3.2
- Debian Wheezy
- Debian Squeeze

Ideas and Bug Reports
=====================

Please file your feature requests and bug reports in our issue tracker @ https://github.com/lionaneesh/RasPod/issues .

Developers
==========

	Aneesh Dogra (lionaneesh-at-gmail)