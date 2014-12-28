
import sys
import locale
from pyramid.config import Configurator
from pyramid_beaker import session_factory_from_settings
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import has_permission
from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid.interfaces import IRoutesMapper
from pyramid.httpexceptions import (
    default_exceptionresponse_view,
    HTTPFound,
    HTTPNotFound
    )

from sqlalchemy import engine_from_config

from .security import group_finder, get_user
from .models import (
    DBSession,
    Base,
    init_model,
    )
from .models.base_model import (
    RouteModel)
    
from .tools import DefaultTimeZone, get_months


# http://stackoverflow.com/questions/9845669/pyramid-inverse-to-add-notfound-viewappend-slash-true    
class RemoveSlashNotFoundViewFactory(object):
    def __init__(self, notfound_view=None):
        if notfound_view is None:
            notfound_view = default_exceptionresponse_view
        self.notfound_view = notfound_view

    def __call__(self, context, request):
        if not isinstance(context, Exception):
            # backwards compat for an append_notslash_view registered via
            # config.set_notfound_view instead of as a proper exception view
            context = getattr(request, 'exception', None) or context
        path = request.path
        registry = request.registry
        mapper = registry.queryUtility(IRoutesMapper)
        if mapper is not None and path.endswith('/'):
            noslash_path = path.rstrip('/')
            for route in mapper.get_routes():
                if route.match(noslash_path) is not None:
                    qs = request.query_string
                    if qs:
                        noslash_path += '?' + qs
                    return HTTPFound(location=noslash_path)
        #routes = request.registry.settings.getRoutes() 
        #print list(routes)
        #return HTTPNotFound()
        request.session.flash('Halaman yang anda cari tidak ditemukan','error')
        
        return request.user and HTTPFound('/main') or HTTPFound('/') #self.notfound_view(context, request)
    
    
# https://groups.google.com/forum/#!topic/pylons-discuss/QIj4G82j04c
def url_has_permission(request, permission):
    print 'P******',permission, request.context, request
    sys.exit()
    return has_permission(permission, request.context, request)

@subscriber(BeforeRender)
def add_global(event):
     event['permission'] = url_has_permission

def get_title(request):
    route_name = request.matched_route.name
    return titles[route_name]

routes = [    
    ('home', '/', 'Home',''), #resource_id
    ('login', '/login', 'Login',''),
    ('logout', '/logout', 'Logout',''),
    ('password', '/password', 'Change password',''),

    ('main', '/main', 'Utama',''),
    #('main-act', '/main/act/{act}', 'Action','osipkd.models.GajiFactory'),
    
    ('admin', '/admin', 'Administrator',''),
    ('user', '/user', 'Users','osipkd.models.AdminFactory'),
    ('user-act', '/user/act/{act}', 'Users','osipkd.models.AdminFactory'),
    ('user-add', '/user/add', 'Tambah user','osipkd.models.AdminFactory'),
    ('user-edit', '/user/{id}/edit', 'Edit user','osipkd.models.AdminFactory'),
    ('user-delete', '/user/{id}/delete', 'Hapus user','osipkd.models.AdminFactory'),

    ('change-act', '/change/{act}', 'change',''),
    
    ('group', '/group', 'Groups','osipkd.models.AdminFactory'),
    ('group-act', '/group/act/{act}', '','osipkd.models.AdminFactory'),
    ('group-add', '/group/add', 'Tambah group','osipkd.models.AdminFactory'),
    ('group-edit', '/group/{id}/edit', 'Edit group','osipkd.models.AdminFactory'),
    ('group-delete', '/group/{id}/delete', 'Hapus group','osipkd.models.AdminFactory'),

    ('urusan', '/urusan', 'urusans','osipkd.models.AdminFactory'),
    ('urusan-add', '/urusan/add', 'Tambah urusan','osipkd.models.AdminFactory'),
    ('urusan-edit', '/urusan/{id}/edit', 'Edit urusan','osipkd.models.AdminFactory'),
    ('urusan-delete', '/urusan/{id}/delete', 'Hapus urusan','osipkd.models.AdminFactory'),
    ('urusan-act', '/urusan/act/{act}', 'Action','osipkd.models.AdminFactory'),

    ('unit', '/unit', 'units','osipkd.models.AdminFactory'),
    ('unit-add', '/unit/add', 'Tambah unit','osipkd.models.AdminFactory'),
    ('unit-edit', '/unit/{id}/edit', 'Edit unit','osipkd.models.AdminFactory'),
    ('unit-delete', '/unit/{id}/delete', 'Hapus unit','osipkd.models.AdminFactory'),
    ('unit-act', '/unit/act/{act}', 'AdminFactory','osipkd.models.AdminFactory'),

    ('user-unit', '/user/unit', 'User Unit','osipkd.models.AdminFactory'),
    ('user-unit-act', '/user/unit/act/{act}', 'Action','osipkd.models.AdminFactory'),
    ('user-unit-add', '/user/unit/add', 'Tambah user unit','osipkd.models.AdminFactory'),
    ('user-unit-edit', '/user/unit/{id}/edit', 'Edit user unit','osipkd.models.AdminFactory'),
    ('user-unit-delete', '/user/unit/{id}/delete', 'Hapus user unit','osipkd.models.AdminFactory'),

    ('user-group', '/user/group', 'User group','osipkd.models.AdminFactory'),
    ('user-group-act', '/user/group/act/{act}', 'Action','osipkd.models.AdminFactory'),
    ('user-group-add', '/user/group/add', 'Tambah user group','osipkd.models.AdminFactory'),
    ('user-group-edit', '/user/group/{id}/edit', 'Edit user group','osipkd.models.AdminFactory'),
    ('user-group-delete', '/user/group/{id}/delete', 'Hapus user group','osipkd.models.AdminFactory'),

    ('rekening', '/rekening', 'Rekening','osipkd.models.AdminFactory'),
    ('rekening-act', '/rekening/act/{act}', 'Action','osipkd.models.AdminFactory'),
    ('rekening-add', '/rekening/add', 'Tambah Rekening','osipkd.models.AdminFactory'),
    ('rekening-edit', '/rekening/{id}/edit', 'Edit Rekening','osipkd.models.AdminFactory'),
    ('rekening-delete', '/rekening/{id}/delete', 'Hapus Rekening','osipkd.models.AdminFactory'),
    
    ('gaji', '/gaji', 'Gaji Main',''),
    ('gaji-act', '/gaji/act/{act}', 'Action','osipkd.models.GajiFactory'),

    ('gaji-peg', '/gaji-peg', 'Gaji', 'osipkd.models.GajiFactory',),
    ('gaji-peg-act', '/gaji-peg/act/{act}', 'Action','osipkd.models.GajiFactory'),
    ('gaji-peg-csv', '/gaji-peg/csv', 'CSV','osipkd.models.GajiFactory'),
    
    ('gaji-potongan', '/gaji-potongan', 'Potongan Gaji','osipkd.models.GajiFactory'),
    ('gaji-potongan-add', '/gaji-potongan/add', 'Tambah Potongan','osipkd.models.GajiFactory'),
    ('gaji-potongan-edit', '/gaji-potongan/{id}/edit', 'Edit Potongan','osipkd.models.GajiFactory'),
    ('gaji-potongan-delete', '/gaji-potongan/{id}/delete', 'Hapus Potongan','osipkd.models.GajiFactory'),
    ('gaji-potongan-act', '/gaji-potongan/act/{act}', '','osipkd.models.GajiFactory'),
    ('gaji-potongan-csv', '/gaji-potongan/csv', 'CSV','osipkd.models.GajiFactory'),
    
    ('eis', '/eis', 'Eksekutif Summary',''),
    ('eis-act', '/eis/act/{act}', 'Data For Grid',''),

    ('eis-slide',        '/eis-slide',             'Daftar Slide',  'osipkd.models.AdminFactory'),
    ('eis-slide-add',    '/eis-slide/add',         'Tambah Slide',  'osipkd.models.AdminFactory'),
    ('eis-slide-edit',   '/eis-slide/{id}/edit',   'Edit Slide',    'osipkd.models.AdminFactory'),
    ('eis-slide-delete', '/eis-slide/{id}/delete', 'Hapus  Slide',  'osipkd.models.AdminFactory'),
    ('eis-slide-act',    '/eis-slide/act/{act}',   'Action',           'osipkd.models.AdminFactory'),
    ('eis-slide-csv',    '/eis-slide/csv',         'CSV',              'osipkd.models.AdminFactory'),

    ('eis-chart',        '/eis-chart',             'Daftar Chart',  'osipkd.models.AdminFactory'),
    ('eis-chart-add',    '/eis-chart/add',         'Tambah Chart',  'osipkd.models.AdminFactory'),
    ('eis-chart-edit',   '/eis-chart/{id}/edit',   'Edit Chart',    'osipkd.models.AdminFactory'),
    ('eis-chart-delete', '/eis-chart/{id}/delete', 'Hapus  Chart',  'osipkd.models.AdminFactory'),
    ('eis-chart-act',    '/eis-chart/act/{act}',   'Action',           'osipkd.models.AdminFactory'),
    ('eis-chart-csv',    '/eis-chart/csv',         'CSV',              'osipkd.models.AdminFactory'),

    ('eis-chart-item',        '/eis-chart-item/{chart_id}',             'Daftar Chart Detail',  'osipkd.models.AdminFactory'),
    ('eis-chart-item-add',    '/eis-chart-item/{chart_id}/add',         'Tambah Chart Detail',  'osipkd.models.AdminFactory'),
    ('eis-chart-item-edit',   '/eis-chart-item/{chart_id}/{id}/edit',   'Edit Chart Detail',    'osipkd.models.AdminFactory'),
    ('eis-chart-item-delete', '/eis-chart-item/{chart_id}/{id}/delete', 'Hapus  Chart Detail',  'osipkd.models.AdminFactory'),
    ('eis-chart-item-act',    '/eis-chart-item/{chart_id}/act/{act}',   'Action',           'osipkd.models.AdminFactory'),
    ('eis-chart-item-csv',    '/eis-chart-item/{chart_id}/csv',         'CSV',              'osipkd.models.AdminFactory'),
    
    ('carousel',        '/carousel',             'Daftar Tabular',  'osipkd.models.AdminFactory'),
    ('carousel-add',    '/carousel/add',         'Tambah Tabular',  'osipkd.models.AdminFactory'),
    ('carousel-edit',   '/carousel/{id}/edit',   'Edit Tabular',    'osipkd.models.AdminFactory'),
    ('carousel-delete', '/carousel/{id}/delete', 'Hapus  Tabular',  'osipkd.models.AdminFactory'),
    ('carousel-act',    '/carousel/act/{act}',   'Action',           'osipkd.models.AdminFactory'),
    ('carousel-csv',    '/carousel/csv',         'CSV',              'osipkd.models.AdminFactory'),
    ]

main_title = 'osipkd'
titles = {}
#for name, path, title, factory in routes2:
#    if title:
#        titles[name] = ' - '.join([main_title, title])


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    engine = engine_from_config(settings, 'sqlalchemy.')
    #engine.echo = True
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine
    init_model()

    session_factory = session_factory_from_settings(settings)
    if 'localization' not in settings:
        settings['localization'] = 'id_ID.UTF-8'
    locale.setlocale(locale.LC_ALL, settings['localization'])        
    if 'timezone' not in settings:
        settings['timezone'] = DefaultTimeZone
    config = Configurator(settings=settings,
                          root_factory='osipkd.models.RootFactory',
                          session_factory=session_factory)
                          
    config.include('pyramid_beaker')                          
    config.include('pyramid_chameleon')

    authn_policy = AuthTktAuthenticationPolicy('sosecret',
                    callback=group_finder, hashalg='sha512')
    authz_policy = ACLAuthorizationPolicy()                          
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_request_method(get_user, 'user', reify=True)
    config.add_request_method(get_title, 'title', reify=True)
    config.add_request_method(get_months, 'months', reify=True)
    config.add_notfound_view(RemoveSlashNotFoundViewFactory())        
                          
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_static_view('deform_static', 'deform:static')
    
    config.add_renderer('csv', '.tools.CSVRenderer')
    
    #routes = DBSession.query(RouteModel.kode, RouteModel.path, RouteModel.nama, RouteModel.factory).all()
    """
    for route in routes:
        if route.factory: 
            config.add_route(route.kode, route.path, factory=(route.factory).encode("utf8"))
        else:
            config.add_route(route.kode, route.path)
    """    
    #    if route.nama:
    #        titles[route.kode] = route.nama #' - '.join([main_title, title])
    
    for name, path, title, factory in routes:
        if factory: 
            config.add_route(name, path, factory=factory)
        else:
            config.add_route(name, path)
        if name:
            titles[name] = title
    config.scan()
    return config.make_wsgi_app()
