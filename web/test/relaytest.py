import asyncio, json, struct
from websockets.asyncio.client import connect
async def main():
    async with connect('ws://ra-relay-test:8081/redalert/net?room=test', origin='http://localhost:8099') as a, connect('ws://ra-relay-test:8081/redalert/net?room=test', origin='http://localhost:8099') as b:
        ha = json.loads(await a.recv()); hb = json.loads(await b.recv())
        await a.send(struct.pack('>I', 0xFFFFFFFF) + b'hello')
        m = await asyncio.wait_for(b.recv(), 3)
        print('b got', struct.unpack('>I', m[:4])[0] == ha['id'], m[4:])
        await b.send(struct.pack('>I', ha['id']) + b'direct')
        m = await asyncio.wait_for(a.recv(), 3)
        print('a got', struct.unpack('>I', m[:4])[0] == hb['id'], m[4:], 'peers seen by b:', hb['peers'])
asyncio.run(main())
