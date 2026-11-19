pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'hello'
gnome = import('gnome')

blueprint_compiler = find_program('blueprint-compiler')
blueprint_command = [
  blueprint_compiler,
  'compile',
  '@INPUT@',
  '--output',
  '@OUTPUT@',
]

# One generated .ui per source so Ninja tracks every output explicitly.
blueprints = []
foreach name : ['shortcuts-dialog', 'window']
  blueprints += custom_target(
    name + '.ui',
    input: name + '.blp',
    output: name + '.ui',
    command: blueprint_command,
  )
endforeach

hello_resources = gnome.compile_resources('hello',
  'hello.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
  dependencies: blueprints,
)

python = import('python')
python3 = python.find_installation('python3')

conf = configuration_data()
conf.set('PYTHON', python3.full_path())
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

# Ship bytecode: read-only installs would otherwise recompile on every launch.
meson.add_install_script(
  python3,
  files('../scripts/compile-bytecode.py'),
  get_option('datadir') / meson.project_name(),
)

test_env = [
  'PYTHONPATH=' + meson.project_source_root(),
  'APP_RESOURCE=' + hello_resources[0].full_path(),
  # Keep tests away from the host session bus, credentials and user dirs.
  'DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent',
  'LC_ALL=C',
  'LANG=C',
  'TERM=dumb',
  'NO_AT_BRIDGE=1',
  'PYTHONDONTWRITEBYTECODE=1',
  'GTK_IM_MODULE=gtk-im-context-simple',
  'HOME=' + (meson.current_build_dir() / 'test-home'),
  'XDG_CONFIG_HOME=' + (meson.current_build_dir() / 'test-config'),
  'XDG_STATE_HOME=' + (meson.current_build_dir() / 'test-state'),
  'XDG_RUNTIME_DIR=' + (meson.current_build_dir() / 'test-runtime'),
  'XDG_CACHE_HOME=' + (meson.current_build_dir() / 'test-cache'),
  'XDG_DATA_HOME=' + (meson.current_build_dir() / 'test-data'),
  'GSETTINGS_SCHEMA_DIR=' + (meson.project_build_root() / 'data'),
  'GSETTINGS_BACKEND=memory',
]

test('Initializer helpers', python3, args: [files('../tests/test_init.py')],
  env: test_env)
test('Window smoke test', python3, args: [files('../tests/test_window.py')],
  depends: test_schemas,
  env: test_env)
test('Application lifecycle', python3, args: [files('../tests/test_lifecycle.py')],
  depends: test_schemas,
  env: test_env)
test('Lazy startup imports', python3, args: [files('../tests/test_startup.py')],
  env: test_env)
