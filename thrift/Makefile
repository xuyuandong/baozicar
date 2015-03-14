LIB_PATH = -L /usr/local/lib/

AR = /usr/local/lib/libthrift.a /usr/local/lib/libhiredis.a

LIBS = -lrt -ldl
#-lthrift

INCLUDE = -I /usr/local/include/

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
	$(CC) $(CXXFLAGS) $^ -o $@ $(INCLUDE) $(AR) $(LIB_PATH) $(LIBS)

clean:
	rm $(OBJS) $(BIN)
