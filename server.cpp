#include <iostream>
#include <vector>
#include <functional>
#include <sys/socket.h>
#include <cstring>
#include <pthread.h>
#include <thread>
#include <mutex>
#include <unistd.h>
#include <netinet/in.h>
#include <arpa/inet.h>

std::vector<int> acceptedSockets;
int acceptedClientSockets = 0;

constexpr int BUFFER_SIZE = 1024;
constexpr int MAX_CLIENTS = 10;


std::mutex handleClientsMutex;

void broadcastMessageToClients(int* clientSocketFD, std::vector<char> &buffer)
{
    std::lock_guard<std::mutex> lock (handleClientsMutex);
    for(int i = 0; i < acceptedClientSockets; i++)
    {
        if(acceptedSockets[i] != *clientSocketFD)
        {
            send(acceptedSockets[i], buffer.data(), buffer.size(), 0);
        }
    }
}

void* receiveIncomingData(void * socketData)
{
    std::vector<char> buffer(BUFFER_SIZE);
    int* clientSocketFD;
    clientSocketFD = (int *) socketData;
    std::function<void(int *, std::vector<char>&)> onReceiveMessage = &broadcastMessageToClients;
    while(1)
    {
	size_t message_len = recv(*clientSocketFD, &buffer[0], buffer.size(), 0);
	if(message_len == 0)
	{
	    std::cout << "Client has been disconnected.\n";
	    break;
	}
	if(message_len > 0)
	{
            std::string msg = std::string(buffer.data(), message_len);
            std::cout << msg << "\n";

            onReceiveMessage(clientSocketFD, buffer);
	}
	if(message_len < 0)
	{
	    std::cout << "Error, client has been disconnected.\n";
            break;
	}
	buffer.clear();
	buffer.resize(1024);
    }
    std::cout << "Client connection has been closed.\n";

    {
        std::lock_guard<std::mutex> lock(handleClientsMutex);
        acceptedSockets.erase(std::remove(acceptedSockets.begin(), acceptedSockets.end(), *clientSocketFD), acceptedSockets.end());
    }

    close(*clientSocketFD);
    delete clientSocketFD;

    return nullptr;
}

int main()
{
    int socketFD = socket(AF_INET, SOCK_STREAM, 0);

    //char ip[] = "";
    struct sockaddr_in serverAddress;
    serverAddress.sin_family = AF_INET;
    serverAddress.sin_port = htons(2000);
    serverAddress.sin_addr.s_addr = INADDR_ANY;

    if (bind(socketFD, (struct sockaddr*)&serverAddress, sizeof(serverAddress)) < 0) {
        std::cerr << "Bind failed" << std::endl;
        return 1;
    }

    if (listen(socketFD, MAX_CLIENTS) < 0) {
        std::cerr << "Listen failed" << std::endl;
        return 1;
    }

    std::cout << "Server socket was established successfully." << std::endl;
    std::jthread clientThread;

    while(1)
    {
        struct sockaddr_in clientAddress;
        int clientAddressSize = sizeof(struct sockaddr_in);
	int* clientSocketFD = new int;
        *clientSocketFD = accept(socketFD, (struct sockaddr *) &clientAddress, (socklen_t*)&clientAddressSize);
        if(*clientSocketFD > 0)
        {
            std::cout << "Client connection was successful, client socked id: " << clientSocketFD << std::endl;

	    {
	        std::lock_guard<std::mutex> lock(handleClientsMutex);
	        acceptedSockets.emplace_back(*clientSocketFD);
                acceptedClientSockets++;
	    }

            pthread_t id;
            pthread_create(&id, nullptr, &receiveIncomingData, clientSocketFD);
        }
    }

    close(socketFD);
    shutdown(socketFD, SHUT_RDWR);

    return 0;
}

