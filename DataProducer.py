#!/usr/bin/env python

"""
Revision History:
  2017-09-05: KSB, created in support of TRA IRAD

"""
# define a version for the file
VERSION = "1.0.20170906a"

import cPickle as pickle
import datetime

import threading
import Queue
import time
import socket

class MyData():
  def __init__(self, h, m ,s):
    self.hour = h
    self.minute = m
    self.second = s
    return
  
  def show(self):
    return "%s:%s:%s"%(self.hour, self.minute, self.second)

class Producer(threading.Thread):
  def __init__(self, q):
    threading.Thread.__init__(self)
    self.q = q
    return
  
  def run(self):
    while True:
      timenow = datetime.datetime.now()
      h = timenow.strftime("%H")
      m = timenow.strftime("%M")
      s = timenow.strftime("%S")
      
      data = MyData(h, m, s)
      
      # show the user
      print "Producer: Data: %s"%data.show()
      
      # pickle the data
      pdata = pickle.dumps(data)
      
      # do some queue maintenance
      self.clear_queue()
      
      # send the data off
      self.q.put(pdata)
      
      # wait a bit
      time.sleep(1.0)
    return
  
  def clear_queue(self):
    # clean out what is there
    print "Queue Size: %d"%self.q.qsize()
    # if we clear the queue to zero length, there is a small
    # possibility that we could hang here if a reciever call
    # were to take the last record between us measuring the
    # size and getting a record, so only clear down to two
    # which generally leaves one after the get here.
    while self.q.qsize() > 1:
      self.q.get()
    return

class Transmitter(threading.Thread):
  def __init__(self, q, clientsocket):
    threading.Thread.__init__(self)
    self.q = q
    self.clientsocket = clientsocket
    return
  
  def run(self):
    # get the latest data
    newdata = self.q.get()
    
    # send our data
    packet = self.build_packet(newdata)
    try:
      self.send(packet)
    except RuntimeError, exc:
      print "Transmitter.send(): Unable to send data: %s"%exc
      return
    
    # we are all done with this socket
    self.clientsocket.shutdown(socket.SHUT_RDWR)
    self.clientsocket.close()
    
    return
  
  def build_packet(self, msg):
    """build a packet of data with a start flag and size"""
    packet = []
    
    # add the start flag and size (14 bytes)
    packet.append("START ")
    packet.append("%08d"%len(msg))
    
    # now add the data
    packet.append(msg)
    
    return b''.join(packet)
  
  def send(self, msg):
    totalsent = 0
    while totalsent < len(msg):
      sent = self.clientsocket.send(msg[totalsent:])
      if sent == 0:
        raise RuntimeError("transmitter.mysend(): socket connection broken")
      totalsent = totalsent + sent
  
if __name__ == '__main__':
  # create our Last In/First Out Queue to pass data between the producer and transmitter
  q = Queue.LifoQueue()
  
  # create our producer thread (data gatherer)
  producer = Producer(q)
  producer.daemon = True  # this ties the thread life to our main loop
  producer.start()
  
  # create our INET, STREAMing Server Socket
  serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  
  # bind the socket
  serversocket.bind(('192.168.0.77', 24831))
  
  # become a server
  serversocket.listen(1)
  
  # set a short timeout for accept...if we don't do this, we can block
  # and never answer a ctrl-c if there is no reciver.
  serversocket.settimeout(0.2)
  
  # main loop
  while True:
    
    # accept connections from outside
    try:
      clientsocket, address = serversocket.accept()
    except socket.timeout:
      pass
    except:
      raise "DataProducer.main(): Accept exception"
    else:
      # answer the call
      tx = Transmitter(q, clientsocket)
      tx.start()
