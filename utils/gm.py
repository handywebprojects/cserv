###################################################

import argparse
from github import Github
from getpass import getpass
import webbrowser
from sys import exit
from time import sleep
from subprocess import Popen
from shutil import copy

###################################################

gituser = "handywebprojects"
defaultrepo = "cserv"
defaultdescription = "chess server"

###################################################

parser = argparse.ArgumentParser(description = 'Manage github repos')

parser.add_argument('-l', '--list', action = "store_true", help = 'list repos')
parser.add_argument('--removegit', help = 'remove git', action = "store_true")
parser.add_argument('--creategit', help = 'create git', action = "store_true")
parser.add_argument('-d', '--delete', help = 'delete repo', nargs = '?', const = defaultrepo, type = str)
parser.add_argument('-c', '--create', help = 'create repo', nargs = '?', const = defaultrepo, type = str)
parser.add_argument('--recreate', help = 'recreate', action = "store_true")
parser.add_argument('--description', help = 'repo description', nargs = '?', const = defaultdescription, default = defaultdescription,  type = str)
parser.add_argument('-o', '--open', help = 'open repo', nargs = '?', const = defaultrepo, type = str)

args = parser.parse_args()

print(args)

###################################################

if args.open:
    name = args.open
    webbrowser.open(f"https://github.com/{gituser}/{name}")
    webbrowser.open(f"https://gitlab.com/{gituser}/{name}")
    exit()

if args.removegit:
    print("removing git")
    Popen(["s\\rg.bat"]).wait()    
    print("done")
    sleep(3)
    if args.recreate:
        args.creategit = args.removegit
    else:
        exit()

if args.creategit:
    print("creating git")
    Popen(["git", "init"]).wait()
    copy("config", ".git/config")
    print("done")
    exit()

###################################################

gitpass = getpass()

g = Github(gituser, gitpass)

u = g.get_user()

###################################################

if args.delete:    
    name = args.delete    
    print(f"deleting repo {name}")
    u.get_repo(name).delete()
    args.list = True
    sleep(3)
    if args.recreate:
        args.create = args.delete

if args.create:
    name = args.create
    description = args.description
    print(f"creating repo {name} descripiton {description}")    
    u.create_repo(name, description = description)
    args.list = True
    sleep(3)

if args.list:
    for repo in u.get_repos():
        print(repo.name)

###################################################