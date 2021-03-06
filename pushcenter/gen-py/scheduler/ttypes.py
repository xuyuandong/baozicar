#
# Autogenerated by Thrift Compiler (0.9.2)
#
# DO NOT EDIT UNLESS YOU ARE SURE THAT YOU KNOW WHAT YOU ARE DOING
#
#  options string: py
#

from thrift.Thrift import TType, TMessageType, TException, TApplicationException

from thrift.transport import TTransport
from thrift.protocol import TBinaryProtocol, TProtocol
try:
  from thrift.protocol import fastbinary
except:
  fastbinary = None



class Path:
  """
  Attributes:
   - fromcity
   - fromplace
   - tocity
   - toplace
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'fromcity', None, None, ), # 1
    (2, TType.STRING, 'fromplace', None, None, ), # 2
    (3, TType.STRING, 'tocity', None, None, ), # 3
    (4, TType.STRING, 'toplace', None, None, ), # 4
  )

  def __init__(self, fromcity=None, fromplace=None, tocity=None, toplace=None,):
    self.fromcity = fromcity
    self.fromplace = fromplace
    self.tocity = tocity
    self.toplace = toplace

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.fromcity = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRING:
          self.fromplace = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.STRING:
          self.tocity = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.STRING:
          self.toplace = iprot.readString();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Path')
    if self.fromcity is not None:
      oprot.writeFieldBegin('fromcity', TType.STRING, 1)
      oprot.writeString(self.fromcity)
      oprot.writeFieldEnd()
    if self.fromplace is not None:
      oprot.writeFieldBegin('fromplace', TType.STRING, 2)
      oprot.writeString(self.fromplace)
      oprot.writeFieldEnd()
    if self.tocity is not None:
      oprot.writeFieldBegin('tocity', TType.STRING, 3)
      oprot.writeString(self.tocity)
      oprot.writeFieldEnd()
    if self.toplace is not None:
      oprot.writeFieldBegin('toplace', TType.STRING, 4)
      oprot.writeString(self.toplace)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.fromcity)
    value = (value * 31) ^ hash(self.fromplace)
    value = (value * 31) ^ hash(self.tocity)
    value = (value * 31) ^ hash(self.toplace)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class Order:
  """
  Attributes:
   - id
   - path
   - phone
   - number
   - cartype
   - price
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'id', None, None, ), # 1
    (2, TType.STRUCT, 'path', (Path, Path.thrift_spec), None, ), # 2
    (3, TType.STRING, 'phone', None, None, ), # 3
    (4, TType.I32, 'number', None, None, ), # 4
    (5, TType.I32, 'cartype', None, None, ), # 5
    (6, TType.I32, 'price', None, None, ), # 6
  )

  def __init__(self, id=None, path=None, phone=None, number=None, cartype=None, price=None,):
    self.id = id
    self.path = path
    self.phone = phone
    self.number = number
    self.cartype = cartype
    self.price = price

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.STRUCT:
          self.path = Path()
          self.path.read(iprot)
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.STRING:
          self.phone = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.I32:
          self.number = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 5:
        if ftype == TType.I32:
          self.cartype = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 6:
        if ftype == TType.I32:
          self.price = iprot.readI32();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Order')
    if self.id is not None:
      oprot.writeFieldBegin('id', TType.STRING, 1)
      oprot.writeString(self.id)
      oprot.writeFieldEnd()
    if self.path is not None:
      oprot.writeFieldBegin('path', TType.STRUCT, 2)
      self.path.write(oprot)
      oprot.writeFieldEnd()
    if self.phone is not None:
      oprot.writeFieldBegin('phone', TType.STRING, 3)
      oprot.writeString(self.phone)
      oprot.writeFieldEnd()
    if self.number is not None:
      oprot.writeFieldBegin('number', TType.I32, 4)
      oprot.writeI32(self.number)
      oprot.writeFieldEnd()
    if self.cartype is not None:
      oprot.writeFieldBegin('cartype', TType.I32, 5)
      oprot.writeI32(self.cartype)
      oprot.writeFieldEnd()
    if self.price is not None:
      oprot.writeFieldBegin('price', TType.I32, 6)
      oprot.writeI32(self.price)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.id)
    value = (value * 31) ^ hash(self.path)
    value = (value * 31) ^ hash(self.phone)
    value = (value * 31) ^ hash(self.number)
    value = (value * 31) ^ hash(self.cartype)
    value = (value * 31) ^ hash(self.price)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class Driver:
  """
  Attributes:
   - phone
   - priority
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'phone', None, None, ), # 1
    (2, TType.I32, 'priority', None, None, ), # 2
  )

  def __init__(self, phone=None, priority=None,):
    self.phone = phone
    self.priority = priority

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.phone = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.I32:
          self.priority = iprot.readI32();
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Driver')
    if self.phone is not None:
      oprot.writeFieldBegin('phone', TType.STRING, 1)
      oprot.writeString(self.phone)
      oprot.writeFieldEnd()
    if self.priority is not None:
      oprot.writeFieldBegin('priority', TType.I32, 2)
      oprot.writeI32(self.priority)
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.phone)
    value = (value * 31) ^ hash(self.priority)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class HistoryDriver:
  """
  Attributes:
   - drivers
  """

  thrift_spec = (
    None, # 0
    (1, TType.SET, 'drivers', (TType.STRING,None), None, ), # 1
  )

  def __init__(self, drivers=None,):
    self.drivers = drivers

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.SET:
          self.drivers = set()
          (_etype3, _size0) = iprot.readSetBegin()
          for _i4 in xrange(_size0):
            _elem5 = iprot.readString();
            self.drivers.add(_elem5)
          iprot.readSetEnd()
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('HistoryDriver')
    if self.drivers is not None:
      oprot.writeFieldBegin('drivers', TType.SET, 1)
      oprot.writeSetBegin(TType.STRING, len(self.drivers))
      for iter6 in self.drivers:
        oprot.writeString(iter6)
      oprot.writeSetEnd()
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.drivers)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class PoolOrder:
  """
  Attributes:
   - id
   - cartype
   - order_list
   - pushtime
   - drivers
  """

  thrift_spec = (
    None, # 0
    (1, TType.STRING, 'id', None, None, ), # 1
    (2, TType.I32, 'cartype', None, None, ), # 2
    (3, TType.LIST, 'order_list', (TType.STRUCT,(Order, Order.thrift_spec)), None, ), # 3
    (4, TType.I64, 'pushtime', None, None, ), # 4
    (5, TType.LIST, 'drivers', (TType.STRING,None), None, ), # 5
  )

  def __init__(self, id=None, cartype=None, order_list=None, pushtime=None, drivers=None,):
    self.id = id
    self.cartype = cartype
    self.order_list = order_list
    self.pushtime = pushtime
    self.drivers = drivers

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.STRING:
          self.id = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.I32:
          self.cartype = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.LIST:
          self.order_list = []
          (_etype10, _size7) = iprot.readListBegin()
          for _i11 in xrange(_size7):
            _elem12 = Order()
            _elem12.read(iprot)
            self.order_list.append(_elem12)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.I64:
          self.pushtime = iprot.readI64();
        else:
          iprot.skip(ftype)
      elif fid == 5:
        if ftype == TType.LIST:
          self.drivers = []
          (_etype16, _size13) = iprot.readListBegin()
          for _i17 in xrange(_size13):
            _elem18 = iprot.readString();
            self.drivers.append(_elem18)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('PoolOrder')
    if self.id is not None:
      oprot.writeFieldBegin('id', TType.STRING, 1)
      oprot.writeString(self.id)
      oprot.writeFieldEnd()
    if self.cartype is not None:
      oprot.writeFieldBegin('cartype', TType.I32, 2)
      oprot.writeI32(self.cartype)
      oprot.writeFieldEnd()
    if self.order_list is not None:
      oprot.writeFieldBegin('order_list', TType.LIST, 3)
      oprot.writeListBegin(TType.STRUCT, len(self.order_list))
      for iter19 in self.order_list:
        iter19.write(oprot)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    if self.pushtime is not None:
      oprot.writeFieldBegin('pushtime', TType.I64, 4)
      oprot.writeI64(self.pushtime)
      oprot.writeFieldEnd()
    if self.drivers is not None:
      oprot.writeFieldBegin('drivers', TType.LIST, 5)
      oprot.writeListBegin(TType.STRING, len(self.drivers))
      for iter20 in self.drivers:
        oprot.writeString(iter20)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.id)
    value = (value * 31) ^ hash(self.cartype)
    value = (value * 31) ^ hash(self.order_list)
    value = (value * 31) ^ hash(self.pushtime)
    value = (value * 31) ^ hash(self.drivers)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)

class Message:
  """
  Attributes:
   - template_type
   - push_type
   - app_type
   - title
   - content
   - text
   - url
   - target
  """

  thrift_spec = (
    None, # 0
    (1, TType.I32, 'template_type', None, None, ), # 1
    (2, TType.I32, 'push_type', None, None, ), # 2
    (3, TType.I32, 'app_type', None, None, ), # 3
    (4, TType.STRING, 'title', None, None, ), # 4
    (5, TType.STRING, 'content', None, None, ), # 5
    (6, TType.STRING, 'text', None, None, ), # 6
    (7, TType.STRING, 'url', None, None, ), # 7
    (8, TType.LIST, 'target', (TType.STRING,None), None, ), # 8
  )

  def __init__(self, template_type=None, push_type=None, app_type=None, title=None, content=None, text=None, url=None, target=None,):
    self.template_type = template_type
    self.push_type = push_type
    self.app_type = app_type
    self.title = title
    self.content = content
    self.text = text
    self.url = url
    self.target = target

  def read(self, iprot):
    if iprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and isinstance(iprot.trans, TTransport.CReadableTransport) and self.thrift_spec is not None and fastbinary is not None:
      fastbinary.decode_binary(self, iprot.trans, (self.__class__, self.thrift_spec))
      return
    iprot.readStructBegin()
    while True:
      (fname, ftype, fid) = iprot.readFieldBegin()
      if ftype == TType.STOP:
        break
      if fid == 1:
        if ftype == TType.I32:
          self.template_type = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 2:
        if ftype == TType.I32:
          self.push_type = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 3:
        if ftype == TType.I32:
          self.app_type = iprot.readI32();
        else:
          iprot.skip(ftype)
      elif fid == 4:
        if ftype == TType.STRING:
          self.title = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 5:
        if ftype == TType.STRING:
          self.content = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 6:
        if ftype == TType.STRING:
          self.text = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 7:
        if ftype == TType.STRING:
          self.url = iprot.readString();
        else:
          iprot.skip(ftype)
      elif fid == 8:
        if ftype == TType.LIST:
          self.target = []
          (_etype24, _size21) = iprot.readListBegin()
          for _i25 in xrange(_size21):
            _elem26 = iprot.readString();
            self.target.append(_elem26)
          iprot.readListEnd()
        else:
          iprot.skip(ftype)
      else:
        iprot.skip(ftype)
      iprot.readFieldEnd()
    iprot.readStructEnd()

  def write(self, oprot):
    if oprot.__class__ == TBinaryProtocol.TBinaryProtocolAccelerated and self.thrift_spec is not None and fastbinary is not None:
      oprot.trans.write(fastbinary.encode_binary(self, (self.__class__, self.thrift_spec)))
      return
    oprot.writeStructBegin('Message')
    if self.template_type is not None:
      oprot.writeFieldBegin('template_type', TType.I32, 1)
      oprot.writeI32(self.template_type)
      oprot.writeFieldEnd()
    if self.push_type is not None:
      oprot.writeFieldBegin('push_type', TType.I32, 2)
      oprot.writeI32(self.push_type)
      oprot.writeFieldEnd()
    if self.app_type is not None:
      oprot.writeFieldBegin('app_type', TType.I32, 3)
      oprot.writeI32(self.app_type)
      oprot.writeFieldEnd()
    if self.title is not None:
      oprot.writeFieldBegin('title', TType.STRING, 4)
      oprot.writeString(self.title)
      oprot.writeFieldEnd()
    if self.content is not None:
      oprot.writeFieldBegin('content', TType.STRING, 5)
      oprot.writeString(self.content)
      oprot.writeFieldEnd()
    if self.text is not None:
      oprot.writeFieldBegin('text', TType.STRING, 6)
      oprot.writeString(self.text)
      oprot.writeFieldEnd()
    if self.url is not None:
      oprot.writeFieldBegin('url', TType.STRING, 7)
      oprot.writeString(self.url)
      oprot.writeFieldEnd()
    if self.target is not None:
      oprot.writeFieldBegin('target', TType.LIST, 8)
      oprot.writeListBegin(TType.STRING, len(self.target))
      for iter27 in self.target:
        oprot.writeString(iter27)
      oprot.writeListEnd()
      oprot.writeFieldEnd()
    oprot.writeFieldStop()
    oprot.writeStructEnd()

  def validate(self):
    return


  def __hash__(self):
    value = 17
    value = (value * 31) ^ hash(self.template_type)
    value = (value * 31) ^ hash(self.push_type)
    value = (value * 31) ^ hash(self.app_type)
    value = (value * 31) ^ hash(self.title)
    value = (value * 31) ^ hash(self.content)
    value = (value * 31) ^ hash(self.text)
    value = (value * 31) ^ hash(self.url)
    value = (value * 31) ^ hash(self.target)
    return value

  def __repr__(self):
    L = ['%s=%r' % (key, value)
      for key, value in self.__dict__.iteritems()]
    return '%s(%s)' % (self.__class__.__name__, ', '.join(L))

  def __eq__(self, other):
    return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

  def __ne__(self, other):
    return not (self == other)
