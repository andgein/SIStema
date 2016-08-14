from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.inbox, name='inbox'),
    url(r'^page/(?P<page_index>[^/]+)/$', views.inbox, name='inbox_page'),
    url(r'^webhook/', views.incoming_webhook),
    url(r'^sent/$', views.sent, name='sent'),
    url(r'^sent/page/(?P<page_index>[^/]+)/$', views.sent, name='sent_page'),
    url(r'^drafts/$', views.drafts_list, name='drafts'),
    url(r'^drafts/page/(?P<page_index>[^/]+)/', views.drafts_list, name='drafts_page'),
    url(r'^write/$', views.write, name='write'),
    url(r'^write/(?P<recipient_hash>[^/]+)/$', views.write_to, name='write_to'),
    url(r'^compose/', views.compose, name='compose'),
    url(r'^contacts/', views.contacts, name='contacts'),
    url(r'^contact_list/', views.contact_list, name='contact_list'),
    url(r'^sis_users/', views.sis_users, name='sis_users'),
    url(r'^attachment/(?P<attachment_id>[^/]+)/$', views.download_attachment, name='download_attachment'),
    url(r'^attachment/(?P<attachment_id>[^/]+)/preview', views.preview, name='preview'),
    url(r'^delete/', views.delete_all, name='delete_all'),
    url(r'^(?P<message_id>[^/]+)/delete/', views.delete_email, name='delete'),
    url(r'^(?P<message_id>[^/]+)/save/', views.save_changes, name='save'),
    url(r'^(?P<message_id>[^/]+)/reply/', views.reply, name='reply'),
    url(r'^(?P<message_id>[^/]+)/edit/', views.edit, name='edit'),
    url(r'^(?P<message_id>[^/]+)/download_all/', views.download_all, name='download_all'),
    url(r'^(?P<message_id>[^/]+)/$', views.message, name='message'),
]
