# Centric PLM Integration Bridge

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

Centric PLM Integration Bridge is a framework written in Python provide basic foundation and library required to access Centric PLM site and integrate it with Busana Apparel Group's internal system.

There would be no business logic provided in this framework, you are supposed to clone this library into your internal git repository and use this as your boilerplate to your integration task.

This repository will also provides as read-only, which means you should fork to your private repository and start there, any modification to the code provided was supposed to be submitted as pull-request.

## Key Features

- Daemon based using MQ subcriber (support MQTT, AMQP, and STOMP v2)
- Module wise Thread Pool instead of Global process pool 
- Module wise Message Queue instead of global queue
- Publishing event through command line

## Installation

Clone this repository to local
```sh
git clone https://github.com/busanagroup/centric-ibridge.git
```

Then locate the centric-ibridge folder and set it up:
```sh
cd ./centric-ibridge
python -m venv venv
source ./venv/bin/activate
pip install --upgrade pip
pip install -r ./requirements.txt
```

You can start the daemon with this command
```sh
cd ./centric-ibridge
source ./venv/bin/activate
python ./ibridge.py start
```



