CC = g++
CFLAGS = -Wall -std=c++20 -g -O0
LDFLAGS = -lpthread

all: server client

server: server.cpp
	$(CC) $(CFLAGS) -o server $^ $(LDFLAGS)

client: client.cpp
	$(CC) $(CFLAGS) -o client $^ $(LDFLAGS)

test: server
	python3 -m unittest discover -s tests -v

clean:
	rm -f server client

.PHONY: all clean test