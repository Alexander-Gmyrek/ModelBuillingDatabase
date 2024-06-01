To run the Back-end database 
1. Navigate to Backend folder in terminal (cd ./Backend)
2. Then run: "docker-compose up --build"
3. Make sure there are no errors in boot.
4. navigate to: localhost:5000 in your browser to make sure the site works!
5. You can go to localhost:5000/help for info on how to use the API.

If someone is using your ports on windows try “netstat -ano | findstr :3306” then “taskkill /PID <pid_number> /F”
For MacOS try: "lsof -i :3306" then "kill -9 <PID>"(Replace PID with the PID from the first command)
