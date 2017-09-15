#!/usr/bin/env python

"""
***************************************************************************
Copyright 2017 (C) Lockheed Martin (LM)
                   All Rights Reserved
This source code is being provided to facilitate use of WindTracer data.
This code may not be redistributed without written permission from LM.
***************************************************************************
Revision History:
  2017-09-05: KSB, created in support of TRA IRAD

"""
from DataProducer import MyData

from random import randint
import cPickle as pickle
import time
import socket

# define a version for the file
VERSION = "1.0.20170906a"

class Receiver():
  def __init__(self):
    return
  
  def get_data(self):
    # create an INET, STREAMing socket
    self.rx_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # connect to the server
    try:
      self.rx_socket.connect((socket.gethostname(), 4831))
    except socket.error, exc:
      print "Receiver.get_data(): Unable to connect: %s"%exc
      return
    
    try:
      data = pickle.loads(self.rx_data())
    except RuntimeError, exc:
      print "Receiver.get_data(): Unable to received data: %s"%exc
      return
    
    # show what we got
    print data.show()
    
    return
  
  def rx_data(self):
    header = []
    header_length = 14
    bytes_received = 0
    
    # get the header to find the length
    header = self.rx_bytes(header_length)
    flag, data_length = header.split(' ')
    
    # get the datablock
    return self.rx_bytes(int(data_length))
  
  def rx_bytes(self, length):
    chunks = []
    bytes_received = 0
    while bytes_received < length:
      chunk = self.rx_socket.recv(length-bytes_received)
      if chunk == b'':
        raise RuntimeError("Receiver.rx_data: socket connection broken")
      chunks.append(chunk)
      bytes_received += len(chunk)
    return b''.join(chunks)

# only run main if this file is run directly
if __name__ == '__main__':
  # start here
  rx = Receiver()
  
  while True:
    delay = randint(1,5)
    print "Sleeping %d seconds"%delay
    time.sleep(delay)
    
    # get the data
    rx.get_data()
  
