import docker
import subprocess
from docker.utils import kwargs_from_env

client = docker.from_env()

new_image = client.images.build(path="./", tag="tess2")
# image = client.images.get("tess2")
# client.login(username='chatterbotadmin', password='123AdminDB')
# image.tag("chatterbotadmin/bots_list", "tess2")
# print(client.images.push("chatterbotadmin/bots_list", tag="tess2"))
#
