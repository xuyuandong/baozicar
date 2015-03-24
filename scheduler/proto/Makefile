APP = $(PWD)/..
LIB_PATH = -L /usr/local/lib/

LIB_PATH = /usr/local/lib

AR = $(APP)/lib/*.a $(LIB_PATH)/libhiredis.a $(LIB_PATH)/libthrift.a
SO = -L$(LIB_PATH) -lpthread -lrt -ldl

INCLUDE = -I $(APP)/common/ -I $(APP)/include/ -I /usr/local/include/

CXXFLAGS = -fPIC -Wall -O2
CC = g++

BIN = testcpp

OBJS = test_thrift.o \
       gen-cpp/order_types.o \
       gen-cpp/order_constants.o

.PHONY : all clean
all: $(BIN)

.cc.o:
	$(CC) $(CXXFLAGS) -c $< -o $@ $(INCLUDE)

$(BIN): $(OBJS)
	$(CC) $(CXXFLAGS) $^ -o $@ $(INCLUDE) $(AR) $(SO)

clean:
	rm $(OBJS) $(BIN)
