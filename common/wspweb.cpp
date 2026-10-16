//
// Copyright 2026 kampvogn.dk
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
#ifdef __EMSCRIPTEN__

#include "wspweb.h"
#include <emscripten.h>
#include <string.h>

/*
** The page keeps Module.net = { ws, id, inbox: [ { src, data } ] }.
** Wire format (binary): to the relay [dest id (4)][payload], from the relay
** [source id (4)][payload]; dest 0xFFFFFFFF is a broadcast to the room.
*/
EM_JS(int, web_net_id, (), {
    const n = Module.net;
    return n && n.ws && n.ws.readyState === 1 && n.id ? n.id : 0;
});

EM_JS(void, web_net_send, (unsigned dest, const unsigned char* data, int len), {
    const n = Module.net;
    if (!n || !n.ws || n.ws.readyState !== 1) return;
    const out = new Uint8Array(4 + len);
    new DataView(out.buffer).setUint32(0, dest >>> 0);
    out.set(HEAPU8.subarray(data, data + len), 4);
    n.ws.send(out);
});

EM_JS(int, web_net_recv, (unsigned char* data, int max, unsigned* src), {
    const n = Module.net;
    if (!n || !n.inbox.length) return 0;
    const p = n.inbox.shift();
    const len = Math.min(p.data.length, max);
    HEAPU8.set(p.data.subarray(0, len), data);
    HEAPU32[src >> 2] = p.src;
    return len;
});

static void Put_Id(unsigned char* address, unsigned id)
{
    memset(address, 0, 8);
    address[4] = (id >> 24) & 0xFF;
    address[5] = (id >> 16) & 0xFF;
    address[6] = (id >> 8) & 0xFF;
    address[7] = id & 0xFF;
}

static unsigned Get_Id(const unsigned char* address)
{
    return (unsigned(address[4]) << 24) | (unsigned(address[5]) << 16) | (unsigned(address[6]) << 8) | address[7];
}

bool WebInterfaceClass::Open_Socket(SOCKET)
{
    Discard_In_Buffers();
    Discard_Out_Buffers();
    return web_net_id() != 0;
}

void WebInterfaceClass::Close_Socket(void)
{
    Discard_In_Buffers();
    Discard_Out_Buffers();
}

void WebInterfaceClass::Broadcast(void* buffer, int buffer_len)
{
    WinsockBufferType* packet = new WinsockBufferType;
    memcpy(packet->Buffer, buffer, buffer_len);
    packet->BufferLen = buffer_len;
    packet->IsBroadcast = true;
    Put_Id(packet->Address, 0xFFFFFFFF);
    OutBuffers.Add(packet);
}

int WebInterfaceClass::Message_Handler()
{
    /*
    ** Send everything queued, then pick up what the page has received.
    */
    while (OutBuffers.Count() != 0) {
        WinsockBufferType* packet = OutBuffers[0];
        web_net_send(packet->IsBroadcast ? 0xFFFFFFFF : Get_Id(packet->Address), packet->Buffer, packet->BufferLen);
        OutBuffers.Delete(0);
        delete packet;
    }

    for (;;) {
        WinsockBufferType* packet = new WinsockBufferType;
        unsigned src = 0;
        int len = web_net_recv(packet->Buffer, sizeof(packet->Buffer), &src);
        if (len <= 0) {
            delete packet;
            break;
        }
        packet->BufferLen = len;
        packet->IsBroadcast = false;
        memset(packet->Address, 0, sizeof(packet->Address));
        Put_Id(packet->Address, src);
        InBuffers.Add(packet);
    }
    return 0;
}

#endif // __EMSCRIPTEN__
