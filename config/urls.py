"""
URL configuration for VIVO Django project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path

from vivo_app import views as vivo_views

# Set custom error handlers
handler404 = 'vivo_app.views.page_not_found'
handler500 = 'vivo_app.views.server_error'

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    # # Standard application support endpoints
    path('error_check/', vivo_views.error_check, name='error_check'),
    path('version/', vivo_views.version, name='version'),
    # # Authentication
    # path('accounts/register/', register, name='register'),
    # path('accounts/login/', custom_login, name='login'),
    # path('accounts/logout/', custom_logout, name='logout'),
    # path('accounts/profile/', profile, name='profile'),
    # path('accounts/change-password/', change_password, name='change_password'),
    # path(
    #     'accounts/password_reset/',
    #     auth_views.PasswordResetView.as_view(
    #         template_name='registration/password_reset_form.html',
    #         email_template_name='registration/password_reset_email.html',
    #         subject_template_name='registration/password_reset_subject.txt',
    #     ),
    #     name='password_reset',
    # ),
    # path(
    #     'accounts/password_reset/done/',
    #     auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
    #     name='password_reset_done',
    # ),
    # path(
    #     'accounts/reset/<uidb64>/<token>/',
    #     auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
    #     name='password_reset_confirm',
    # ),
    # path(
    #     'accounts/reset/done/',
    #     auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
    #     name='password_reset_complete',
    # ),
    # Home and static pages
    path('', vivo_views.home_index, name='home'),
    path('about', vivo_views.home_about, name='about'),
    path('about/', vivo_views.home_about, name='about_slash'),
    path('faq', vivo_views.home_faq, name='faq'),
    path('faq/', vivo_views.home_faq, name='faq_slash'),
    path('help', vivo_views.home_help, name='help'),
    path('help/', vivo_views.home_help, name='help_slash'),
    path('history', vivo_views.home_history, name='history'),
    path('history/', vivo_views.home_history, name='history_slash'),
    path('publications', vivo_views.home_publications, name='publications'),
    path('publications/', vivo_views.home_publications, name='publications_slash'),
    path('roadmap', vivo_views.home_roadmap, name='roadmap'),
    path('roadmap/', vivo_views.home_roadmap, name='roadmap_slash'),
    path('termsOfUse', vivo_views.home_terms, name='terms'),
    path('termsOfUse/', vivo_views.home_terms, name='terms_slash'),
    path('brown', vivo_views.home_brown, name='brown'),
    path('brown/', vivo_views.home_brown, name='brown_slash'),
    path('help/viz', vivo_views.home_help_viz, name='help_viz'),
    path('help/viz/', vivo_views.home_help_viz, name='help_viz_slash'),
    path('status/', vivo_views.home_status, name='status'),
    path('status', vivo_views.home_status, name='status_public'),
    path('side_stuff/brown_classic/', vivo_views.home_brown_classic, name='brown_classic'),
    path('side_stuff/brown_classic/<str:name>/', vivo_views.home_brown_classic, name='brown_classic_named'),
    # Display functionality
    path('display/', vivo_views.display_index, name='display_index'),
    path('display/<str:id>/', vivo_views.display_show, name='display_show'),
    path('display/<str:id>', vivo_views.display_show, name='display_show_public'),
    path(
        'display/<str:id>/publications.tsv', vivo_views.organization_publications_tsv, name='organization_publications_tsv'
    ),
    path('display/<str:id>/publications/', vivo_views.display_publications, name='display_publications'),
    # Visualizations
    path('display/<str:id>/viz/', vivo_views.visualization_home, name='visualization_home'),
    path(
        'display/<str:id>/viz/collab.json',
        vivo_views.visualization_graph_json,
        {'kind': 'collaborators'},
        name='collab_json',
    ),
    path(
        'display/<str:id>/viz/coauthor.json',
        vivo_views.visualization_graph_json,
        {'kind': 'coauthors'},
        name='coauthor_json',
    ),
    path(
        'display/<str:id>/viz/collab.csv',
        vivo_views.visualization_graph_csv,
        {'kind': 'collaborators'},
        name='collab_csv',
    ),
    path(
        'display/<str:id>/viz/coauthor.csv',
        vivo_views.visualization_graph_csv,
        {'kind': 'coauthors'},
        name='coauthor_csv',
    ),
    path('display/<str:id>/viz/coauthor', vivo_views.visualization_coauthor, name='visualization_coauthor'),
    path('display/<str:id>/viz/coauthor/', vivo_views.visualization_coauthor, name='visualization_coauthor_slash'),
    path(
        'display/<str:id>/viz/coauthor_treemap',
        vivo_views.visualization_coauthor_treemap,
        name='visualization_coauthor_treemap',
    ),
    path(
        'display/<str:id>/viz/coauthor_treemap/',
        vivo_views.visualization_coauthor_treemap,
        name='visualization_coauthor_treemap_slash',
    ),
    path('display/<str:id>/viz/collab', vivo_views.visualization_collab, name='visualization_collab'),
    path('display/<str:id>/viz/collab/', vivo_views.visualization_collab, name='visualization_collab_slash'),
    path(
        'display/<str:id>/viz/publications.json',
        vivo_views.visualization_publications,
        {'fmt': 'json'},
        name='visualization_publications_json',
    ),
    path(
        'display/<str:id>/viz/publications.csv',
        vivo_views.visualization_publications,
        {'fmt': 'csv'},
        name='visualization_publications_csv',
    ),
    path('display/<str:id>/viz/publications', vivo_views.visualization_publications, name='visualization_publications'),
    path(
        'display/<str:id>/viz/publications/', vivo_views.visualization_publications, name='visualization_publications_slash'
    ),
    path(
        'display/<str:id>/viz/research.json',
        vivo_views.visualization_research,
        {'fmt': 'json'},
        name='visualization_research_json',
    ),
    path('display/<str:id>/viz/research', vivo_views.visualization_research, name='visualization_research'),
    path('display/<str:id>/viz/research/', vivo_views.visualization_research, name='visualization_research_slash'),
    # Edit functionality
    # path('edit/fast/search/', vivo_views.edit_fast_search, name='edit_fast_search'),
    # path('edit/<str:id>/', vivo_views.edit_profile, name='edit_profile'),
    # path('edit/overview/<str:faculty_id>/update', vivo_views.overview_update, name='overview_update'),
    # path('edit/research_area/<str:faculty_id>/add', vivo_views.research_area_add, name='research_area_add'),
    # path('edit/research_area/<str:faculty_id>/delete', vivo_views.research_area_delete, name='research_area_delete'),
    # path('edit/web_link/<str:faculty_id>/save', vivo_views.web_link_save, name='web_link_save'),
    # path('edit/web_link/<str:faculty_id>/delete', vivo_views.web_link_delete, name='web_link_delete'),
    # Search
    path('search', vivo_views.search, name='search'),
    path('search/advanced', vivo_views.advanced_search, name='advanced_search'),
    path('search_facets', vivo_views.search_facets),
    path('__prepared_assets/<str:name>', vivo_views.prepared_asset, name='prepared_asset'),
    path('source-images/<path:filename>', vivo_views.source_image, name='source_image'),
    path('source-documents/<path:filename>', vivo_views.source_document, name='source_document'),
    path('docs/<path:filename>', vivo_views.prepared_document, name='prepared_document'),
    path('search/', vivo_views.search, name='search_slash'),
    path('search/advanced/', vivo_views.advanced_search, name='advanced_search_slash'),
    path('search_facets/', vivo_views.search_facets, name='search_facets'),
    # Reports
    path('reports/subject-lib', vivo_views.subject_lib_list, name='subject_lib_list_public'),
    path('reports/subject-lib/', vivo_views.subject_lib_list, name='subject_lib_list'),
    path('reports/subject-lib/<str:list_id>/', vivo_views.subject_lib, name='subject_lib'),
    # Existing public data service, outside the Django application mount
    path('services/data/v1/faculty/<str:id>', vivo_views.faculty_service_redirect, name='faculty_service'),
    path('services/data/v1/faculty/<str:id>/', vivo_views.faculty_service_redirect, name='faculty_service_slash'),
    # Bot detection
    path('challenge', vivo_views.bot_detect_challenge, name='bot_detect_challenge'),
    path('challenge/', vivo_views.bot_detect_challenge),
    # Legacy VIVO URLs
    path('people', vivo_views.people, name='people'),
    path('people/', vivo_views.people),
    path('ous', vivo_views.organizations, name='organizations'),
    path('ous/', vivo_views.organizations),
    path('file/<str:id>/<str:file_name>/', vivo_views.old_image, name='old_image'),
    path('file/<str:id>/<str:file_name>', vivo_views.old_image, name='old_image_public'),
    # Individual (legacy VIVO export and redirect)
    # Export routes must come before the generic redirect to avoid matching 'n123.json' as <id>
    re_path(
        r'^individual/(?P<id>[^/]+)/(?P<id2>[^/]+)\.(?P<fmt>[^/]+)$',
        vivo_views.individual_export,
        name='individual_export_public',
    ),
    # e.g., /individual/n123/n123.json/
    re_path(
        r'^individual/(?P<id>[^/]+)/(?P<id2>[^/]+)\.(?P<fmt>[^/]+)/$',
        vivo_views.individual_export,
        name='individual_export_double',
    ),
    # e.g., /individual/n123.json/
    re_path(r'^individual/(?P<id>[^/]+)\.(?P<fmt>[^/]+)/$', vivo_views.individual_export, name='individual_export'),
    path('individual/<str:id>/', vivo_views.individual_redirect, name='individual_redirect'),
    path('individual/<str:id>', vivo_views.individual_redirect, name='individual_redirect_public'),
]

# Serve static and media files in development
if settings.DEBUG:
    if getattr(settings, 'ENABLE_BROWSER_RELOAD', False):
        urlpatterns += [path('__reload__/', include('django_browser_reload.urls'))]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
