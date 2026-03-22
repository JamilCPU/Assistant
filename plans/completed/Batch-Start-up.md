We need to contain this app within docker, so it cna be spinned up easily.
Additionally, this means we need to handle spinning up some other things.
WE will need a Database that we consistently connect to with a flyway for start-up
Note that towards the end of creating a DB we probably want to be saving our chats and our images

We will neeed to be starting up Automatic1111 alongside the application during startup too.
Maybe we can wrap Automatic1111 and put it in docker for ease of use?
