# Wait for an element before clicking

The right pattern for flaky pages: wait → snapshot → act. Never click blind.

## Run

```bash
chmod +x recipe.sh
./recipe.sh https://example.com "#submit"
```

See [`recipe.sh`](./recipe.sh) for the full script.
