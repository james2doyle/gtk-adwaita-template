pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'hello'
gnome = import('gnome')

blueprints = custom_target('blueprints',
  input: files(
    'shortcuts-dialog.blp',
    'window.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '--minify', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@'],
)

hello_resources = gnome.compile_resources('hello',
  'hello.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'hello.in',
  output: 'hello',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'rwxr-xr-x'
)

hello_sources = [
  '__init__.py',
  'main.py',
  'window.py',
]

install_data(hello_sources, install_dir: moduledir)

python3 = python.find_installation('python3')

test_env = [
  'PYTHONPATH=' + meson.project_source_root(),
  'APP_RESOURCE=' + hello_resources[0].full_path(),
  # Keep tests away from the host session bus, credentials and user dirs.
  'DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent',
  'LC_ALL=C',
  'LANG=C',
  'TERM=dumb',
  'HOME=' + (meson.current_build_dir() / 'test-home'),
  'XDG_CONFIG_HOME=' + (meson.current_build_dir() / 'test-config'),
  'XDG_STATE_HOME=' + (meson.current_build_dir() / 'test-state'),
  'XDG_RUNTIME_DIR=' + (meson.current_build_dir() / 'test-runtime'),
  'XDG_CACHE_HOME=' + (meson.current_build_dir() / 'test-cache'),
  'XDG_DATA_HOME=' + (meson.current_build_dir() / 'test-data'),
]

test('Window smoke test', python3, args: [files('../tests/test_window.py')],
  env: test_env)
