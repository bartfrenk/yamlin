# yamlin

A small YAML loader with custom tags for resolving values at load time —
secrets from the OS keychain, values from the environment, and async
placeholders — then dumps the resolved result back out as plain YAML.

## Install

```sh
uv add yamlin
```

## Tags

- `!keychain <service>/<secret id>` — looks up a secret via
  [`keyring`](https://pypi.org/project/keyring/).
- `!env <NAME>` — looks up an environment variable.
- `!sleep <seconds>` — waits, then resolves to the number of seconds
  (useful for testing concurrent resolution).

## Example

```yaml
# config.yaml
database:
  password: !keychain myapp/db-password
  host: !env DB_HOST
```

```sh
uv run keyring set myapp db-password   # store the secret once
export DB_HOST=localhost

yamlin -f config.yaml
```

```yaml
database:
  host: localhost
  password: <value stored in the keychain>
```

Omit `-f` to read from stdin, and add `-o <file>` to write to a file instead
of stdout.
