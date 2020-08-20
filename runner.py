import argparse
from game import Game
from game_loop import GameLoop
from clients import ProcessClient, TCPClient
import asyncio
import json
import sys


async def get_process_clients(strategies):
    processes = []
    for strategy in strategies:
        process = asyncio.create_subprocess_shell(strategy,
                                                  stdin=asyncio.subprocess.PIPE,
                                                  stdout=asyncio.subprocess.PIPE,
                                                  stderr=asyncio.subprocess.DEVNULL)
        processes.append(process)

    processes = await asyncio.gather(*processes)
    clients = [ProcessClient(process) for process in processes]
    return clients


class Server:
    def __init__(self, game, host, port):
        self.clients = []
        self.need_clients = len(game.remaining_teams)
        self.game = game
        self.host = host
        self.port = port
        self.server = None

    async def run(self):
        self.server = await asyncio.start_server(self.on_connect, self.host, self.port)

        async with self.server:
            try:
                await self.server.serve_forever()
            except asyncio.exceptions.CancelledError:
                pass

    async def on_connect(self, reader, writer):
        if len(self.clients) < self.need_clients:
            self.clients.append(TCPClient(reader, writer))

            if len(self.clients) == self.need_clients:
                game_loop = GameLoop(self.game, self.clients)
                await game_loop.play()

                self.server.close()
        else:
            writer.close()


def run_server(game, args):
    server = Server(game, args.host, args.port)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(server.run())


def run_local(game, args):
    if len(args.strategies) != len(game.remaining_teams):
        sys.exit(1)

    loop = asyncio.get_event_loop()
    clients = loop.run_until_complete(get_process_clients(args.strategies))

    game_loop = GameLoop(game, clients)
    loop.run_until_complete(game_loop.play())


def parsing():
    # TODO proper usage
    parser = argparse.ArgumentParser()

    default_parser = argparse.ArgumentParser()
    default_parser.add_argument('--map', type=argparse.FileType(mode='r'), help='Path to the map file', required=True)

    subparsers = parser.add_subparsers(dest='mode', required=True)
    local_parser = subparsers.add_parser('local', parents=[default_parser], add_help=False)
    local_parser.add_argument('strategies', type=str,
                              help='Paths of strategies',
                              nargs='+')

    server_parser = subparsers.add_parser('server', parents=[default_parser], add_help=False)
    server_parser.add_argument('--host', type=str, required=True)
    server_parser.add_argument('--port', type=str, required=True)

    return parser.parse_args()


if __name__ == '__main__':
    args = parsing()

    # open map config and create a game to get count of teams
    map_config = json.load(args.map)
    game = Game.from_map_config(map_config)

    if args.mode == 'server':
        run_server(game, args)
    else:
        run_local(game, args)
