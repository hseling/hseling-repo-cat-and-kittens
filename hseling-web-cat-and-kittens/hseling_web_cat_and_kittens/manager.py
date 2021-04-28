from route import app, squlitedb
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager


migrate = Migrate(app, squlitedb)
manager = Manager(app)
manager.add_command('squlitedb', MigrateCommand)

if __name__ == '__main__':
    manager.run()
    