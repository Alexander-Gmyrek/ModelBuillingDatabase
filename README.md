To run the Back-end database 
1. Navigate to Backend folder in terminal (cd ./Backend)
2. Then run: "docker-compose up --build"
3. Make sure there are no errors in boot.
4. navigate to: localhost:5000 in your browser to make sure the site works!
5. You can go to localhost:5000/help for info on how to use the API.

If someone is using your ports on windows try “netstat -ano | findstr :3306” then “taskkill /PID <pid_number> /F”
For MacOS try: "lsof -i :3306" then "kill -9 <PID>"(Replace PID with the PID from the first command)
"netstat -anv | grep LISTEN | grep PORT_NUMBER"

Recent versions of macOS have a system setting called AirPlay Receiver, under System Settings -> AirDrop and Handoff (v13.2 Ventura). When that setting is enabled, macOS uses an http connection via port 5000 to allow "nearby devices to send video and audio content to your Mac with AirPlay," it says here. I had checked that box when setting up a new OS.

Sure enough, disabling AirPlay Receiver released port 5000 and my plackup invocations worked again!
