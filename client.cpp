#include <iostream>
#include <vector>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

void* receiveIncomingData(void * socketData)
{
    std::vector<char> buffer(1024);
    int clientSocketFD;
    clientSocketFD = *(int *) socketData;
    while(1)
    {   
        size_t message_len = recv(clientSocketFD, &buffer[0], buffer.size(), 0);
	if(message_len > 0)
	{
            std::cout << buffer.data() << std::endl;
	}
	buffer.clear();
	buffer.resize(1024);
    }

    close(clientSocketFD);

    return nullptr;
}


int main()
{
    int socketFD = socket(AF_INET, SOCK_STREAM, 0);

    //char ip[] = "142.250.188.46";
    char ip[] = "127.0.0.1";
    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_port = htons(2000);
    inet_pton(AF_INET, ip, &address.sin_addr.s_addr);

    int result = connect(socketFD, (struct sockaddr *) &address, sizeof(address));

    if(result == 0)
    {
	std::cout << "Connection was succesful" << std::endl;
    }

    pthread_t id;
    pthread_create(&id, nullptr, &receiveIncomingData, &socketFD);


    std::string name;
    std::cout << "Please enter your name: ";
    std::getline(std::cin, name);
    name += " :";
   

    std::string line;
    while(1)
    {
        std::getline(std::cin, line);
        line.insert(0, name);
        send(socketFD, line.c_str(), line.size(), 0);
    }

    return 0;
}
