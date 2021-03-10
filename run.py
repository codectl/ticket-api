from hpdasupport import database_setup
from hpdasupport.manager import Manager

if __name__ == '__main__':
    database_setup()
    Manager.main()
