project = 'captain'
version = ''
release = ''
copyright = '2014 Thread, Inc.'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']
html_title = "%s documentation" % project
html_static_path = ['_static']
master_doc = 'index'
exclude_trees = ['_build']
templates_path = ['_templates']
latex_documents = [
  ('index', '%s.tex' % project, html_title, u'Thread', 'manual'),
]
intersphinx_mapping = {'http://docs.python.org/': None}
