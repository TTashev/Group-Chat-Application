CC = g++
CFLAGS = -Wall -std=c++11
LDFLAGS = -lpthread

all: server client

server: server.cpp
	$(CC) $(CFLAGS) -o server $^ $(LDFLAGS)

client: client.cpp
	$(CC) $(CFLAGS) -o client $^ $(LDFLAGS)
	
clean:
	rm -f server client
