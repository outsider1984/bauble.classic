#  Copyright (c) 2005,2006,2007,2008  Brett Adams <brett@belizebotanic.org>
#  This is free software, see GNU General Public License v2 for details.

import traceback

from bauble.i18n import _
import bauble.error as error

SQLALCHEMY_DEBUG = False

try:
    import sqlalchemy as sa
    parts = sa.__version__.split('.')
    if int(parts[1]) < 5:
        msg = _('This version of Bauble requires SQLAlchemy 0.5.0 or greater.'\
                'Please download and install a newer version of SQLAlchemy ' \
                'from http://www.sqlalchemy.org or contact your system '
                'administrator.')
        raise error.SQLAlchemyVersionError(msg)
except ImportError:
    msg = _('SQLAlchemy not installed. Please install SQLAlchemy from ' \
            'http://www.sqlalchemy.org')
    raise


import gtk
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta

from bauble.types import DateTime, Date
import bauble.utils as utils
from bauble.utils.log import debug


if SQLALCHEMY_DEBUG:
    import logging
    global engine
    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    logging.getLogger('sqlalchemy.orm.unitofwork').setLevel(logging.DEBUG)


class MapperBase(DeclarativeMeta):
    """
    MapperBase adds the id, _created and _last_updated columns to all tables.
    """

    def __init__(cls, classname, bases, dict_):
        #print >>sys.stderr, dict_
        if '__tablename__' in dict_:
            seqname = '%s_id_seq' % dict_['__tablename__']
            dict_['id'] = sa.Column('id', sa.Integer, sa.Sequence(seqname),
                                    primary_key=True)
            dict_['_created'] = sa.Column('_created', DateTime(True),
                                          default=sa.func.now())
            dict_['_last_updated'] = sa.Column('_last_updated',
                                               DateTime(True),
                                               default=sa.func.now())
        super(MapperBase, cls).__init__(classname, bases, dict_)


engine = None
Base = declarative_base(metaclass=MapperBase)
metadata = Base.metadata
Session = None


def open(uri, verify=True, show_error_dialogs=False):
    """
    Open a database connection.  This function sets bauble.db.engine to
    the opened engined.

    Return bauble.db.engine if successful else returns None and
    bauble.db.engine remains unchanged.

    :param uri: The URI of the database to open.
    :type uri: str

    :param verify: Where the database we connect to should be verified
        as one created by Bauble.  This flag is used mostly for
        testing.
    :type verify: bool

    :param show_error_dialogs: A flag to indicate whether the error
        dialogs should be displayed.  This is used mostly for testing.
    :type show_error_dialogs: bool
    """

    # ** WARNING: this can print your passwd
##    debug('db.open(%s)' % uri)
    from sqlalchemy.orm import sessionmaker
    import bauble
    global engine
    new_engine = None
    new_engine = sa.create_engine(uri, echo=SQLALCHEMY_DEBUG)
    #new_engine.contextual_connect()
    new_engine.connect()#.close()
    def _bind():
        """bind metadata to engine and create sessionmaker """
        global Session, engine
        engine = new_engine
        metadata.bind = engine # make engine implicit for metadata
        Session = sessionmaker(bind=engine, autoflush=False)
        bauble.Session = sessionmaker(bind=engine, autoflush=False)

    if new_engine is not None and not verify:
        _bind()
        return engine
    elif new_engine is None:
        return None

    #_verify_connection(new_engine, show_error_dialogs)
    _bind()
    return engine


def create(import_defaults=True):
    """
    Create new Bauble database at the current connection

    :param import_defaults: A flag that is passed to each plugins
        install() method to indicate where it should import its
        default data.  This is mainly used for testing.  The default
        value is True
    :type import_defaults: bool

    """
    # TODO: when creating a database there shouldn't be any errors
    # on import since we are importing from the default values, we should
    # just force the import and send everything in the database at once
    # instead of using slices, this would make it alot faster but it may
    # make it more difficult to make the interface more responsive,
    # maybe we can use a dialog without the progress bar to show the status,
    # should probably work on the status bar to display this

    # TODO: we create a transaction here and the csv import creates another
    # nested transaction, we need to verify that if we rollback here then all
    # of the changes made by csv import are rolled back as well
##    debug('entered db.create()')
    import bauble
    import bauble.meta as meta
    import bauble.pluginmgr as pluginmgr
    from bauble.task import TaskQuitting
    import datetime
    connection = engine.contextual_connect()
    transaction = connection.begin()
    session = Session()
    try:
        # create fresh plugin registry seperate since
        # pluginmgr.install() will be changing it
        #debug('dropping and creating plugin registry')
        from bauble.pluginmgr import PluginRegistry
        #connection = None
        #PluginRegistry.__table__.drop(bind=connection, checkfirst=True)
        PluginRegistry.__table__.drop(bind=connection, checkfirst=True)
        #debug(' - d')
        PluginRegistry.__table__.create(bind=connection)
        #PluginRegistry.__table__.create()
        #debug(' - c')
    except Exception, e:
        debug(e)
        transaction.rollback()
        #connection.close()
        raise
    else:
        transaction.commit()

    connection = engine.contextual_connect()
    transaction = connection.begin()
    try:
        # TODO: here we are dropping/creating all the tables in the
        # metadata whether they are in the registry or not, we should
        # really only be creating those tables from registered
        # plugins, maybe with an uninstall() method on Plugin
        #debug('drop all')
        most_tables = metadata.sorted_tables
        most_tables.remove(pluginmgr.PluginRegistry.__table__)
        metadata.drop_all(bind=connection, tables=most_tables, checkfirst=True)
        #debug(' -- dropped')
        metadata.create_all(bind=connection, tables=most_tables)
        #debug('dropped and created')

        # TODO: clearing the insert menu probably shouldn't be here and should
        # probably be pushed into db.create, the problem is at the
        # moment the data is imported in the pluginmgr.init method so we would
        # have to separate table creations from the init menu

        # clear the insert menu
#         if gui is not None and hasattr(gui, 'insert_menu'):
#             menu = gui.insert_menu
#             submenu = menu.get_submenu()
#             for c in submenu.get_children():
#                 submenu.remove(c)
#             menu.show()

        # fill in the bauble meta table and install all the plugins
        meta_table = meta.BaubleMeta.__table__
        meta_table.insert(bind=connection).execute(name=meta.VERSION_KEY,
                                                 value=unicode(bauble.version))
        meta_table.insert(bind=connection).execute(name=meta.CREATED_KEY,
                                        value=unicode(datetime.datetime.now()))

    except (GeneratorExit, TaskQuitting), e:
        # this is here in case the main windows is closed in the middle
        # of a task
        debug(e)
#        debug('db.create(): rollback')
        transaction.rollback()
        #session.rollback()
        raise
    except Exception, e:
        debug(e)
        #debug('db.create(): rollback')
        transaction.rollback()
        raise
    else:
        transaction.commit()

    connection = engine.contextual_connect()
    transaction = connection.begin()
    try:
        pluginmgr.install('all', import_defaults, force=True)
    except (GeneratorExit, TaskQuitting), e:
        # this is here in case the main windows is closed in the middle
        # of a task
        debug(e)
#        debug('db.create(): rollback')
        transaction.rollback()
        #session.rollback()
        raise
    except Exception, e:
        debug(e)
        #debug('db.create(): rollback')
        transaction.rollback()
        #session.rollback()
#         msg = _('Error creating the database.\n\n%s') % utils.xml_safe_utf8(e)
#         debug(traceback.format_exc())
#         utils.message_details_dialog(msg, traceback.format_exc(),
#                                      gtk.MESSAGE_ERROR)
        raise
    else:
##        debug('db.create(): committing')
        #session.commit()
        transaction.commit()


def _verify_connection(engine, show_error_dialogs=False):
    """
    Test whether a connection to an engine is a valid Bauble database. This
    method will raise an error for the first problem it finds with the
    database.

    :param engine: the engine to test
    :type engine: :class:`sqlalchemy.engine.Engine`
    :param show_error_dialogs: flag for whether or not to show message
        dialogs detailing the error, default=False
    :type show_error_dialogs: bool
    """
##    debug('entered _verify_connection(%s)' % show_error_dialogs)
    import bauble
    import bauble.pluginmgr as pluginmgr
    if show_error_dialogs:
        try:
            return _verify_connection(engine, False)
        except error.EmptyDatabaseError:
            msg = _('The database you have connected to is empty.')
            utils.message_dialog(msg, gtk.MESSAGE_ERROR)
            raise
        except error.MetaTableError:
            msg = _('The database you have connected to does not have the '
                    'bauble meta table.  This usually means that the database '
                    'is either corrupt or it was created with an old version '
                    'of Bauble')
            utils.message_dialog(msg, gtk.MESSAGE_ERROR)
            raise
        except error.TimestampError:
            msg = _('The database you have connected to does not have a '\
                    'timestamp for when it was created. This usually means '\
                    'that there was a problem when you created the '\
                    'database or the database you connected to wasn\'t '\
                    'created with Bauble.')
            utils.message_dialog(msg, gtk.MESSAGE_ERROR)
            raise
        except error.VersionError, e:
            msg = _('You are using Bauble version %(version)s while the '\
                    'database you have connected to was created with '\
                    'version %(db_version)s\n\nSome things might not work as '\
                    'or some of your data may become unexpectedly '\
                    'corrupted.') % \
                    {'version': bauble.version,
                     'db_version':'%s' % e.version}
            utils.message_dialog(msg, gtk.MESSAGE_ERROR)
            raise

    if len(engine.table_names()) == 0:
        raise error.EmptyDatabaseError()

    import bauble.meta as meta
    # check that the database we connected to has the bauble meta table
    if not engine.has_table(meta.BaubleMeta.__tablename__):
        raise error.MetaTableError()

    from sqlalchemy.orm import sessionmaker
    # if we don't close this session before raising an exception then we
    # will probably get deadlocks....i'm not really sure why
    session = sessionmaker(bind=engine)()
    query = session.query#(meta.BaubleMeta)

    # check that the database we connected to has a "created" timestamp
    # in the bauble meta table
    result = query(meta.BaubleMeta).filter_by(name = meta.CREATED_KEY).first()
    if not result:
        session.close()
        raise error.TimestampError()

    # check that the database we connected to has a "version" in the bauble
    # meta table and the the major and minor version are the same
    result = query(meta.BaubleMeta).filter_by(name = meta.VERSION_KEY).first()
    if not result:
        session.close()
        raise error.VersionError(None)
    try:
        major, minor, revision = result.value.split('.')
    except:
        session.close()
        raise error.VersionError(result.value)

    if major != bauble.version_tuple[0] or minor != bauble.version_tuple[1]:
        session.close()
        raise error.VersionError(result.value)

    session.close()
    return True
