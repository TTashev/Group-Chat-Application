CC = g++
CFLAGS = -Wall -std=c++20
LDFLAGS = -lpthread

all: server client

server: server.cpp
	$(CC) $(CFLAGS) -o server $^ $(LDFLAGS)

client: client.cpp
	$(CC) $(CFLAGS) -o client $^ $(LDFLAGS)
	
clean:
	rm -f server client
