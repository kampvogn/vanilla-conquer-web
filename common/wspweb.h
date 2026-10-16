//
// Copyright 2026 kampvogn.dk
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
#ifndef WSPWEB_H
#define WSPWEB_H

#ifdef __EMSCRIPTEN__

#include "wsproto.h"

/*
** Network transport for the browser build. Packets go through the web page
** to a WebSocket relay that acts as a virtual LAN per room. Addresses are
** handled like UDPInterfaceClass does it: the 4 bytes at Address + 4 hold the
** peer's id (the relay hands each browser one, like an IPv4 address).
*/
class WebInterfaceClass : public WinsockInterfaceClass
{
public:
    virtual bool Open_Socket(SOCKET socketnum);
    virtual void Close_Socket(void);
    virtual bool Start_Listening(void)
    {
        return true;
    }
    virtual void Stop_Listening(void)
    {
    }
    virtual void Broadcast(void* buffer, int buffer_len);
    virtual int Message_Handler();
    virtual ProtocolEnum Get_Protocol(void)
    {
        return (PROTOCOL_UDP);
    }
    virtual int Protocol_Event_Message(void)
    {
        return (WM_UDPASYNCEVENT);
    }
};

#endif // __EMSCRIPTEN__
#endif // WSPWEB_H
