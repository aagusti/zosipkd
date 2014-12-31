from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
########
# APP Home #
########
@view_config(route_name='anggaran', renderer='templates/home.pt', permission='view')
def view_app(request):
    return dict(project='anggaran')
        