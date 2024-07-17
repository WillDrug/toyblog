


sudo docker build -t toyblog .
sudo docker run -d --name toyblog --hostname toyblog -e MONGO_USER=${MONGO_USER} -e MONGO_PASSWORD=${MONGO_PASSWORD} toyblog
sudo docker network connect toynet toyblog
sudo docker network connect toysupport toyblog