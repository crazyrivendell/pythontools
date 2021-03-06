/*
multicast.c
The following program sends or receives multicast packets. If invoked
with one argument, it sends a packet containing the current time to an
arbitrarily chosen multicast group and UDP port. If invoked with no
arguments, it receives and prints these packets. Start it as a server on
just one host and as a client on all the other hosts.
compile:
    gcc -Werror -o multicast multicast.c
Run Server:
    ./multicast
Run Client:
    ./multicast 1
Only support IPV4
TODO: support IPV6 if needed
*/

#include <time.h>
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <sys/fcntl.h> // for non-blocking

#define EXAMPLE_PORT 1900
#define EXAMPLE_GROUP "239.192.1.1"
//#define EXAMPLE_PORT 5353
//#define EXAMPLE_GROUP "224.0.0.254"
#define TIME_PERIOD 5   /* second */
#define DEFAULT_TTL 10   /* Increase to reach other networks */

void error(char *message, int sock)
{
    perror(message);
    if (sock > 0) {
        close(sock);
    }
    exit(1);
}


void server()
{
    struct sockaddr_in server_addr, client_addr;
    struct in_addr localInterface;
    int addrlen, sock, ret;
    char message[64];
    struct timeval wait;
    unsigned long second = 0;

    fd_set readfds;

    /*ignore signal*/
    signal(SIGPIPE, SIG_IGN);
    /* Server */
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        error("socket error\n", sock);
    }
    bzero((char *)&server_addr, sizeof(server_addr));
    bzero((char *)&client_addr, sizeof(client_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(EXAMPLE_PORT);
    server_addr.sin_addr.s_addr = inet_addr(EXAMPLE_GROUP);
    addrlen = sizeof(server_addr);
    
    /*set TTL, default is 1*/
    u_char ttl = DEFAULT_TTL;
    if (setsockopt(sock, IPPROTO_IP, IP_MULTICAST_TTL, &ttl, sizeof(ttl))) {
        error("setsockopt:IP_MULTICAST_TTL\n", sock); 
    }
    /* Disable loopback so you do not receive your own datagrams. */
    int loop = 0; 
    if (setsockopt(sock,IPPROTO_IP, IP_MULTICAST_LOOP,&loop, sizeof(loop)) < 0) { 
        error("setsockopt:IP_MULTICAST_LOOP\n", sock); 
    }
    //int flags = fcntl(sock, F_GETFL, 0);
    //fcntl(sock, F_SETFL, flags & ~O_NONBLOCK);
    
    while (1) {
        /*Search Message*/
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);
        wait.tv_sec = TIME_PERIOD;  /*wait time set as TIME_PERIOD*/
        wait.tv_usec = 0;
        int _fds = select(sock+1, &readfds, NULL, NULL, &wait);
        if (_fds == -1) {
            error("select error\n", sock); // error occurred in select()
        }
        else if (_fds == 0) {
            //printf("Timeout occurred!  No data after %d seconds.\n",TIME_PERIOD);
            second = time(NULL);
            bzero(message, sizeof(message));
            sprintf(message, "Searching----time is %-24.24s", ctime(&second));
            ret = sendto(sock, message, strlen(message), 0,(struct sockaddr *) &server_addr, addrlen);
            if (ret < 0) {
                error("sendto error\n", sock);
            }
        }
        else{
            if (FD_ISSET(sock, &readfds)) {
                /* Receive Response(Notifying) Message */
                FD_CLR(sock, &readfds);
                bzero(message, sizeof(message));
                ret = recvfrom(sock, message, sizeof(message), 0, (struct sockaddr *) &client_addr, &addrlen);
                //ret = read(sock, message, sizeof(message));
                if (ret < 0) {
                    error("recvfrom error\n", sock);
                } else if (ret == 0) {
                    break;
                }
                else {
                    printf("Server receive data:\n%s\nfrom Client:%s:%d\n", message, inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
                }
            }
            else
                printf("What?\n");
        }
    }
    close(sock);
}

void client()
{
    struct sockaddr_in server_addr, client_addr;
    int addrlen, sock, ret;
    struct ip_mreq mreq;
    char message[64];
    struct timeval wait;
    unsigned long second = 0;

    fd_set readfds;

    /*ignore signal*/
    signal(SIGPIPE, SIG_IGN);
    /* Client */
    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock < 0) {
        error("socket error\n", sock);
    }
    bzero((char *)&server_addr, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    server_addr.sin_port = htons(EXAMPLE_PORT);
    addrlen = sizeof(server_addr);
    
    /* Enable SO_REUSEADDR to allow multiple instances of this */
    /* application to receive copies of the multicast datagrams. */
    int reuse = 1;
    if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, (char *)&reuse, sizeof(reuse)) < 0) {
        error("Setting SO_REUSEADDR error\n", sock);
    }
    
    if (bind(sock, (struct sockaddr *) &server_addr, sizeof(server_addr)) < 0) {
        error("bind error\n", sock);
    }
    exit(1);
    mreq.imr_multiaddr.s_addr = inet_addr(EXAMPLE_GROUP);
    mreq.imr_interface.s_addr = htonl(INADDR_ANY);
    if (setsockopt(sock, IPPROTO_IP, IP_ADD_MEMBERSHIP, &mreq, sizeof(mreq)) < 0) {
        error("setsockopt:IP_ADD_MEMBERSHIP\n", sock);
    }
    
    while (1) {
        /* Receive Server(Searching) Message */
        FD_ZERO(&readfds);
        FD_SET(sock, &readfds);
        int _fds = select(sock+1, &readfds, NULL, NULL, NULL);
        if (_fds == -1){
            error("select error\n", sock); // error occurred in select()
        }
        else if (_fds == 0) {
            printf("Timeout occurred!\n");
        }
        else{
            if (FD_ISSET(sock, &readfds)) {
                FD_CLR(sock, &readfds);
                bzero(message, sizeof(message));
                ret = recvfrom(sock, message, sizeof(message), 0, (struct sockaddr *) &client_addr, &addrlen);
                if (ret < 0) {
                    perror("recvfrom error\n");
                    if (setsockopt(sock, IPPROTO_IP, IP_DROP_MEMBERSHIP, (void*)&mreq, sizeof(mreq)) < 0) {
                        error("setsockopt drop_mreq error\n", sock);
                    }
                    close(sock);
                    exit(1);
                } else if (ret == 0) {
                    break;
                }
                printf("Client receive data:\n%s\nfrom Server: %s:%d\n", message, inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));

                /*send */
                bzero(message, sizeof(message));
                second = time(NULL);
                sprintf(message, "Notifying----time is %-24.24s", ctime(&second));
                ret = sendto(sock, message, strlen(message), 0, (struct sockaddr *)&client_addr, addrlen);
                if (ret < 0) {
                    error("sendto error\n", sock);
                }
            }
            else
                printf("What?\n");

        }
    }
    close(sock);
}


int main(int argc)
{
    if (argc > 1) {
        server();
    } else {
        client();
    }
    return 1;
}