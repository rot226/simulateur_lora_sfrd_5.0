# Validation

This validation step runs the project's full test suite. Due to network restrictions, the required Python packages could not be installed:

```
WARNING: Retrying (Retry(total=4, connect=None, read=None, redirect=None, status=None)) after connection broken by 'ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed: 403 Forbidden'))': /simple/numpy/
ERROR: Could not find a version that satisfies the requirement numpy>=1.21 (from versions: none)
ERROR: No matching distribution found for numpy>=1.21
```

As a result, `pytest` could not be executed in this environment.

To reproduce the validation locally:

1. Ensure all dependencies from `requirements.txt` are installed.
2. Run the full test suite with `pytest -q`.
3. Record the average metrics, p-values and standard deviations from the tests, if available, and include them here.


