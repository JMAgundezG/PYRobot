packages_python="/usr/local/lib/python3.7/dist-packages"
dir_PYRobot="/home/pi/developing/PYRobot/"
dir_robots="/home/pi/developing/robots"

sudo cd $packages_python
sudo ln -s $dir_PYRobot PYRobot
cd
cad_export="export PYROBOTS=\""$dir_robots"\""
echo $cad_export >>/home/pi/.bashrc
$cad_export

sudo pip3 install netifaces
sudo pip3 install paho-mqtt
sudo pip3 install psutil
sudo pip3 install mprpc
sudo pip3 install pyparsing
sudo pip3 install termcolor
sudo pip3 install setproctitle
sudo pip3 install deepdiff


# instalar mosquitto en raspberry
sudo wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key
sudo apt-key add mosquitto-repo.gpg.key
cd /etc/apt/sources.list.d/
sudo wget http://repo.mosquitto.org/debian/mosquitto-buster.list
sudo -i
sudo apt install mosquitto
sudo apt install mosquitto-clients
sudo service mosquitto start
cd $dir_robots
cd bin/findrobots
./install_iamrobot.sh
cd $PYROBOTS
