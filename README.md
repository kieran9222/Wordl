# Wordl
A Python-based terminal wordle clone and user database. Users can download and run the client to connect to a server host. Users must make accounts, and their game history is stored in the database.

## Client
Terminal-based, ANSI wordle clone with standard rules, requires a connection to make an account/log in.
If you are attempting to play wordl without hosting a server (you must connect to a server to play), you can delete `Server/` and follow the instructions in [`Client/`](./Client/README.md).

## Server
A containerized server with an public access port can be created by following the instruction in [`Server/`](./Server/README.md). If you don't have a server to connect to, you must make one.