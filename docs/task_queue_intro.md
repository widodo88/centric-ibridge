# Creating a new task queue module

A task queue module is a collection of tasks or jobs which were executed during receiving message from 
Message Queue (RabbitMQ, ActiveMQ) or can also be triggered by submitting locally by using UNIX socket, 
or local TCP/IP.

The greatest benefit of implementing task queue was to provide additional functionalities in the term 
of jobs tasks to main system without burdening it by distributing them across network or machines 
using queue.

