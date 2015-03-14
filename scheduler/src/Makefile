APP = $(PWD)/..
BIN = $(APP)/bin

LIB_PATH = /usr/local/lib

AR = $(APP)/lib/*.a $(LIB_PATH)/libhiredis.a $(LIB_PATH)/libthrift.a
SO = -L$(LIB_PATH) -lpthread -lrt -ldl

INCLUDE = -I $(APP)/common/ -I $(APP)/include/ -I /usr/local/include/

LDFLAGS = -shared -g -Wall -fPIC
CXXFLAGS = -fPIC -Wall -O3
CC = g++

OBJS = main.o \
       order_types.o \
       order_constants.o \
       dispatcher.o \
       carpooler.o \
       revoker.o \
       planner.o \
       repacker.o \
       recovery.o

TARGET = $(BIN)/scheduler

.PHONY : all clean lint

all: $(TARGET)

lint:
	python cpplint.py $(APP)/src/*.cc $(APP)/include/*.h

.cc.o:
	$(CC) $(CXXFLAGS) -c $< -o $@ $(INCLUDE)

$(TARGET): $(OBJS)
	$(CC) $(CXXFLAGS) $^ -o $@ $(INCLUDE) $(AR) $(SO)

clean:
	rm $(OBJS) $(TARGET)
